import os
import lancedb
import numpy as np
from platformdirs import user_data_dir
import uuid as uuid_module
import pandas as pd
from datetime import datetime, timezone, timedelta
import logging

from local_ai_utils_core import LocalAIUtilsCore
from .constants import VECTOR_DIM, EMBEDDING_TABLE_NAME
from .migration_runner import run_migrations
from .schema import TARGET_SCHEMA

log = logging.getLogger(__name__)

# Define allowed operators and fields centrally for validation
ALLOWED_FILTER_OPERATORS = {'>', '<', '=', '>=', '<=', '~', '~>', '<~'}
ALLOWED_FILTER_FIELDS = {'created_date', 'relevant_date'}
RECENCY_OPERATORS = {'~', '~>', '<~'}
STRICT_OPERATORS = ALLOWED_FILTER_OPERATORS - RECENCY_OPERATORS
RERANK_FETCH_MULTIPLIER = 10
RERANK_FETCH_MIN = 50
RECENCY_WINDOW = timedelta(weeks=1)

def generate_embeddings(prompt, save=False, relevant_date=None, no_index=False):
    """Generates embedding and optionally saves it."""
    core = LocalAIUtilsCore()
    client = core.clients.open_ai()
    response = client.embeddings.create(input=prompt, model="text-embedding-3-large")
    embedding = response.data[0].embedding
    if save:
        add_embedding(embedding, prompt, relevant_date, no_index=no_index)

    return embedding

def get_datafile_path(filename):
    """
    Determine the storage path for the FAISS index file.
    - Uses the `LAIU_DATA_DIR` environment variable if set.
    - Otherwise, defaults to the OS-specific application data directory.
    """
    env_path = os.getenv("LAIU_DATA_DIR")
    if env_path:
        os.makedirs(env_path, exist_ok=True)
        return os.path.join(env_path, filename)
    app_dir = user_data_dir("LAUI_embed", "local-ai-utils")
    db_dir = os.path.join(app_dir, "embeddings")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, filename)

def get_db():
    """Connects to the LanceDB database and ensures migrations are applied."""
    db_path = get_datafile_path("embeddings.lance")
    db = lancedb.connect(db_path)

    try:
        run_migrations(db)
    except Exception as e:
        log.error(f"Database migration failed: {e}. Cannot proceed.", exc_info=True)
        raise SystemExit("Database migration failed.") from e

    return db

def add_embedding(embedding, metadata, relevant_date=None, no_index=False):
    """
    Adds an embedding with metadata to the LanceDB database.

    Args:
        embedding (list or np.array): The vector to be stored.
        metadata (dict): Associated metadata (e.g., {'text': 'example text'})
        relevant_date (datetime, optional): The date to be stored in the 'relevant_date' field.
        no_index (bool, optional): If True and saving, skips the index rebuild step. Defaults to False.
    """
    if len(embedding) != VECTOR_DIM:
        raise ValueError(f"Embedding dimension mismatch: expected {VECTOR_DIM}, got {len(embedding)}")

    db = get_db()
    table = db.open_table(EMBEDDING_TABLE_NAME)
    vector_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding

    data_to_insert = {
        "uuid": str(uuid_module.uuid4()),
        "vector": vector_list,
        "metadata": metadata,
        "created_date": datetime.now(timezone.utc).replace(tzinfo=None),
        "relevant_date": relevant_date
    }

    try:
        table.add([data_to_insert])
        if not no_index:
            rebuild_index(force=True)
    except Exception as e:
        log.error(f"Failed to add embedding: {e}", exc_info=True)

def rebuild_index(force=False):
    """Rebuilds vector and scalar indices if needed or forced."""
    try:
        db = get_db()
        if EMBEDDING_TABLE_NAME not in db.table_names():
            log.info("Table not found, skipping index rebuild.")
            return
        table = db.open_table(EMBEDDING_TABLE_NAME)
        n_rows = table.count_rows()

        # Heuristic: Rebuild only if > N rows or forced. Otherwise we leave the index out and do full scans
        vector_rebuild_threshold = 200
        if force or n_rows >= vector_rebuild_threshold:
             table.create_index(metric="cosine", replace=True)

    except Exception as e:
        log.error(f"Error during index rebuild: {e}", exc_info=True)


# --- Search Logic Helper Functions ---

def _validate_filters(filters):
    """Validates the structure and content of parsed filters."""
    if not filters:
        return []
    validated = []
    for f in filters:
        field = f.get("field")
        op = f.get("operator")
        ts_obj = f.get("timestamp")

        if field not in ALLOWED_FILTER_FIELDS:
            log.warning(f"Invalid filter field '{field}'. Ignoring filter: {f}")
            continue
        if op not in ALLOWED_FILTER_OPERATORS:
             log.warning(f"Invalid filter operator '{op}'. Ignoring filter: {f}")
             continue
        if not isinstance(ts_obj, datetime):
            log.warning(f"Invalid timestamp type '{type(ts_obj)}' for filter. Ignoring filter: {f}")
            continue
        
        # Ensure timestamp is naive (should be handled by CLI, but double-check)
        if ts_obj.tzinfo is not None:
             f["timestamp"] = ts_obj.astimezone(timezone.utc).replace(tzinfo=None)

        validated.append(f)
        
    return validated

def _build_strict_where_clause(strict_filters):
    """Builds the SQL WHERE clause string from validated strict filters."""
    if not strict_filters:
        return None
    parts = []
    for f in strict_filters:
        ts_str = f['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')
        parts.append(f"{f['field']} {f['operator']} timestamp '{ts_str}'")
    return " AND ".join(parts) if parts else None

def _execute_lancedb_search(table, query_vector, limit, strict_where_clause):
    """Executes the core LanceDB search."""
    search_query = table.search(query_vector).limit(limit)
    if strict_where_clause:
        search_query = search_query.where(strict_where_clause)
        
    try:
        results = search_query.to_list()
        return results
    except Exception as e:
         log.error(f"LanceDB search query failed: {e}", exc_info=True)
         return []

def _calculate_proximity_score(result_ts, target_ts, op, window_seconds):
    """Calculates the recency proximity score for a single filter."""
    if result_ts is None or pd.isna(result_ts):
        return 0.0
    if not isinstance(result_ts, datetime):
        log.warning(f"Result timestamp is not a datetime object: {type(result_ts)}. Proximity score is 0.")
        return 0.0
    # Ensure naive comparison
    if result_ts.tzinfo is not None:
         result_ts = result_ts.astimezone(timezone.utc).replace(tzinfo=None)

    delta_seconds = (result_ts - target_ts).total_seconds()
    abs_delta_seconds = abs(delta_seconds)
    proximity_score = 0.0

    if op == '~':
        if abs_delta_seconds <= window_seconds:
            proximity_score = 1.0 - (abs_delta_seconds / window_seconds)
    elif op == '~>':
        if delta_seconds > 0: # Strictly after target
            proximity_score = 1.0
        elif delta_seconds <= 0 and abs_delta_seconds <= window_seconds: # Within window before target
            proximity_score = 1.0 - (abs_delta_seconds / window_seconds)
    elif op == '<~':
        if delta_seconds < 0: # Strictly before target
            proximity_score = 1.0
        elif delta_seconds >= 0 and abs_delta_seconds <= window_seconds: # Within window after target
            proximity_score = 1.0 - (abs_delta_seconds / window_seconds)

    return max(0.0, min(1.0, proximity_score)) # Clamp score between 0 and 1

def _rerank_results(results, recency_filters):
    """Applies recency re-ranking to a list of search results."""
    if not recency_filters or not results:
        return results

    window_seconds = RECENCY_WINDOW.total_seconds()
    reranked_results = []

    for res in results:
        # Calculate average proximity score across all recency filters
        total_proximity_score = 0.0
        num_filters_applied = 0
        for filt in recency_filters:
            result_ts = res.get(filt['field'])
            target_ts = filt['timestamp']
            op = filt['operator']
            total_proximity_score += _calculate_proximity_score(result_ts, target_ts, op, window_seconds)
            num_filters_applied += 1

        avg_proximity_score = (total_proximity_score / num_filters_applied) if num_filters_applied > 0 else 1.0

        # Combine with vector distance
        distance = res.get('_distance', 2.0) # Default to max distance if missing
        vector_similarity = 1.0 / (1.0 + max(0, distance)) # Ensure distance >= 0
        res['final_score'] = vector_similarity * avg_proximity_score
        res['debug_proximity_score'] = avg_proximity_score # Keep for debugging

        reranked_results.append(res)

    # Sort by the combined final score (descending)
    reranked_results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
    return reranked_results


# --- Main Search Function ---

def search_similar(query_embedding, k=5, filters=None):
    """
    Searches LanceDB for similar embeddings, applying filters and re-ranking.

    Args:
        query_embedding (list or np.ndarray): The vector to search for.
        k (int): Final number of results desired.
        filters (list[dict], optional): List of filter dictionaries from CLI.

    Returns:
        List of result dictionaries, sorted by relevance.
    """
    if not isinstance(query_embedding, (list, np.ndarray)):
        raise TypeError("Query embedding must be a list or numpy array")
    if len(query_embedding) != VECTOR_DIM:
        raise ValueError(f"Query embedding dimension mismatch: expected {VECTOR_DIM}, got {len(query_embedding)}")
    query_vector = query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding

    validated_filters = _validate_filters(filters)
    strict_filters = [f for f in validated_filters if f['operator'] in STRICT_OPERATORS]
    recency_filters = [f for f in validated_filters if f['operator'] in RECENCY_OPERATORS]

    strict_where_clause = _build_strict_where_clause(strict_filters)

    query_limit = k

    # If there are recency filters, we need to fetch more results to re-rank
    if recency_filters:
        query_limit = max(k * RERANK_FETCH_MULTIPLIER, RERANK_FETCH_MIN)

    db = get_db()
    table = db.open_table(EMBEDDING_TABLE_NAME)
    initial_results = _execute_lancedb_search(table, query_vector, query_limit, strict_where_clause)

    reranked_results = _rerank_results(initial_results, recency_filters)

    return reranked_results[:k]