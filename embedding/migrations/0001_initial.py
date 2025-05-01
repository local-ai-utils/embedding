import pyarrow as pa
import lancedb
import logging
from embedding.schema import EMBEDDING_TABLE_NAME, VERSION_TABLE_NAME, VECTOR_DIM

log = logging.getLogger(__name__)

# Define the schema *as it should exist after this migration*
SCHEMA_AT_0001 = pa.schema([
    pa.field("vector", pa.list_(pa.float32(), VECTOR_DIM)),
    pa.field("metadata", pa.string())
])

# Define the schema for the migration version table
VERSION_SCHEMA = pa.schema([pa.field("migration_id", pa.int64())])

def up(db: lancedb.DBConnection):
    """Creates the initial embeddings table and the migration tracking table."""
    log.info("Applying migration 0001_initial...")

    # Create embeddings table if it doesn't exist
    if EMBEDDING_TABLE_NAME not in db.table_names():
        log.info(f"Creating table '{EMBEDDING_TABLE_NAME}' with initial schema.")
        db.create_table(EMBEDDING_TABLE_NAME, schema=SCHEMA_AT_0001)
    else:
        log.info(f"Table '{EMBEDDING_TABLE_NAME}' already exists.")

    # Create migration tracking table if it doesn't exist
    if VERSION_TABLE_NAME not in db.table_names():
        log.info(f"Creating migration tracking table '{VERSION_TABLE_NAME}'.")
        db.create_table(VERSION_TABLE_NAME, schema=VERSION_SCHEMA)
    else:
        log.info(f"Migration tracking table '{VERSION_TABLE_NAME}' already exists.")

    log.info("Migration 0001_initial finished.")

def down(db: lancedb.DBConnection):
    log.warning("Applying down migration 0001_initial (dropping tables)...")
    if EMBEDDING_TABLE_NAME in db.table_names():
        db.drop_table(EMBEDDING_TABLE_NAME)
    if VERSION_TABLE_NAME in db.table_names():
        db.drop_table(VERSION_TABLE_NAME)
