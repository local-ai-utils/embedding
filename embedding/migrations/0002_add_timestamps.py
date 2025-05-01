import pyarrow as pa
import lancedb
import logging
from datetime import datetime, timezone
from embedding.schema import EMBEDDING_TABLE_NAME

log = logging.getLogger(__name__)

def up(db: lancedb.DBConnection):
    """Adds created_date and relevant_date columns to the embeddings table."""
    log.info("Applying migration 0002_add_timestamps...")

    tbl = db.open_table(EMBEDDING_TABLE_NAME)
    current_schema = tbl.schema

    added_columns = {}

    # Use epoch for created_date to signify it wasn't originally tracked
    default_created_ts = datetime(1970, 1, 1, tzinfo=timezone.utc)
    default_created_str = default_created_ts.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    added_columns["created_date"] = f"CAST('{default_created_str}' AS timestamp)"

    added_columns["relevant_date"] = "CAST(NULL AS timestamp)"

    try:
        log.info(f"Applying schema alteration: adding {list(added_columns.keys())}")
        tbl.add_columns(added_columns)
    except Exception as e:
        log.error(f"Error during migration 0002 schema alteration: {e}", exc_info=True)
        raise # Propagate error to stop the migration process

    log.info("Migration 0002_add_timestamps finished.")


def down(db: lancedb.DBConnection):
    log.warning("Applying down migration 0002_add_timestamps (dropping columns)...")
    tbl = db.open_table(EMBEDDING_TABLE_NAME)
    tbl.drop_columns(['created_date', 'relevant_date'])
    log.warning("Down migration 0002_add_timestamps finished.")