import pyarrow as pa
from .constants import VECTOR_DIM, EMBEDDING_TABLE_NAME, VERSION_TABLE_NAME

# --- Current Target Schema Definition ---
# This represents the schema we want the database to have *after* all migrations.
# Migrations themselves will define the intermediate steps.
TARGET_SCHEMA = pa.schema([
    pa.field("uuid", pa.string()),
    pa.field("vector", pa.list_(pa.float32(), VECTOR_DIM)),
    pa.field("metadata", pa.string()),
    pa.field("created_date", pa.timestamp('us')),
    pa.field("relevant_date", pa.timestamp('us'))
])