import os
import lancedb
import numpy as np
from platformdirs import user_data_dir
import pyarrow as pa

from local_ai_utils_core import LocalAIUtilsCore

VECTOR_DIM=3072

def generate_embeddings(prompt, save=False):
    core = LocalAIUtilsCore()
    client = core.clients.open_ai()

    response = client.embeddings.create(
        input=prompt,
        model="text-embedding-3-large"
    )

    embedding = response.data[0].embedding

    if save:
        add_embedding(embedding, prompt)

    return embedding

def get_datafile_path(filename):
    """
    Determine the storage path for the FAISS index file.
    - Uses the `LAIU_DATA_DIR` environment variable if set.
    - Otherwise, defaults to the OS-specific application data directory.
    """
    env_path = os.getenv("LAIU_DATA_DIR")
    if env_path:
        file_path = os.path.join(env_path, filename)
        os.makedirs(os.path.dirname(env_path), exist_ok=True)
        return file_path
    
    # Default to platform-specific data directory
    
    app_dir = user_data_dir("LAUI_embed", "local-ai-utils")
    index_dir = os.path.join(app_dir, "embeddings")
    os.makedirs(index_dir, exist_ok=True)
    return os.path.join(index_dir, filename)

def rebuild_index():
    db     = get_db()
    table  = db.open_table("embeddings")
    n_rows = table.count_rows()

    if n_rows < 200: # Flat scan is faster than building an index
        return

    table.create_index(
        index_type="IVF_HNSW_SQ",   # pure HNSW graph over SQ-compressed vecs
        metric="cosine",            # MUST match query-time metric
        m=16,                        # graph degree (16 is a common default)
        ef_construction=128,
        replace=True                # overwrite any previous index
    )

def get_db():
    """
    Opens (or creates) the LanceDB database.
    """
    db_path = get_datafile_path("embeddings.lance")
    
    db = lancedb.connect(db_path)
    if "embeddings" not in db.table_names():
        schema = pa.schema([
            pa.field("vector", pa.list_(pa.float32(), VECTOR_DIM)),
            pa.field("metadata", pa.string())
        ])
        db.create_table("embeddings", schema=schema)

    return db

def add_embedding(embedding, metadata):
    """
    Adds an embedding with metadata to the LanceDB database.

    Args:
        embedding (list or np.array): The vector to be stored.
        metadata (dict): Associated metadata (e.g., {'text': 'example text'})
    """
    if len(embedding) != VECTOR_DIM:
        raise ValueError(f"Embedding must be of dimension {VECTOR_DIM}, but got {len(embedding)}")

    db = get_db()

    table = db.open_table("embeddings")

    # Convert to list and store with metadata
    embedding = np.array(embedding, dtype="float32").tolist()
    table.add([{"vector": embedding, "metadata": metadata}])

    rebuild_index()

def search_similar(query_embedding, k=5):
    """
    Searches the LanceDB for the `k` most similar embeddings to the provided query.

    Args:
        query_embedding (list or np.array): The vector to search for.
        k (int): Number of results to retrieve.

    Returns:
        List of tuples (metadata, vector, distance).
    """
    if len(query_embedding) != VECTOR_DIM:
        raise ValueError(f"Query embedding must be of dimension {VECTOR_DIM}, but got {len(query_embedding)}")

    db = get_db()
    table = db.open_table("embeddings")

    query_embedding = np.array(query_embedding, dtype="float32").tolist()
    results = table.search(query_embedding).distance_type("cosine").limit(k).to_list()

    # Extract metadata, vector and distance from results
    return [(item["metadata"], item["vector"], item["_distance"]) for item in results]