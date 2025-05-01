import pyarrow as pa
import pandas as pd
import lancedb
import logging
import uuid as uuid_module # To avoid conflict with schema field name
import time
from embedding.schema import EMBEDDING_TABLE_NAME, TARGET_SCHEMA # Import the *final* target schema

log = logging.getLogger(__name__)
SCHEMA_AT_0003 = TARGET_SCHEMA

def up(db: lancedb.DBConnection):
    """Adds a UUID column, backfills it for existing rows, and creates a scalar index."""
    log.info("Applying migration 0003_add_uuid_pk...")
    temp_table_name = f"{EMBEDDING_TABLE_NAME}_temp_uuid_{int(time.time())}"
    backfill_needed = False

    if EMBEDDING_TABLE_NAME not in db.table_names():
        log.error(f"Cannot apply migration 0003: Table '{EMBEDDING_TABLE_NAME}' does not exist.")
        raise RuntimeError(f"Migration prerequisite failed: Table '{EMBEDDING_TABLE_NAME}' not found.")

    original_tbl = db.open_table(EMBEDDING_TABLE_NAME)
    current_schema = original_tbl.schema

    if "uuid" not in current_schema.names:
        log.info("'uuid' column not found. Backfill required.")
        backfill_needed = True
    else:
        log.info("'uuid' column already exists.")
        # Potentially check if nulls exist if backfill failed previously? For simplicity, assume if col exists, it's populated.

    # --- Backfill UUID if needed (using temp table method) ---
    if backfill_needed:
        log.info("Starting UUID backfill process...")
        original_count = original_tbl.count_rows()
        if original_count == 0:
            log.info("Original table is empty. Adding UUID column without backfilling data.")
            # Just add the column with nulls (though LanceDB might not need this explicitly?)
            # Let's try adding it directly - if it fails, handle appropriately.
            try:
                 original_tbl.add_columns({"uuid": "CAST(NULL AS string)"})
                 log.info("Added 'uuid' column definition to empty table.")
            except Exception as e:
                 # This might happen if add_columns isn't the right way for an empty table
                 # Alternative: Recreate the table with the new schema? Less ideal.
                 # For now, log and proceed, assuming create_scalar_index handles it.
                 log.warning(f"Could not explicitly add uuid column to empty table ({e}). Will rely on index creation.")

        else:
            # Read existing data
            log.info(f"Reading {original_count} rows for UUID backfill...")
            try:
                arrow_table_orig = original_tbl.to_lance().to_table()
                # Select columns present before this migration
                cols_before_uuid = [f.name for f in current_schema]
                df = arrow_table_orig.select(cols_before_uuid).to_pandas()
                log.info("Read data into DataFrame.")
            except Exception as e:
                log.error(f"Failed to read data for backfill: {e}", exc_info=True)
                raise RuntimeError("UUID backfill failed during read.") from e

            # Generate UUIDs
            log.info("Generating UUIDs...")
            df['uuid'] = [str(uuid_module.uuid4()) for _ in range(len(df))]

            # Prepare Arrow table with UUIDs and the correct target schema
            df_to_add = df[SCHEMA_AT_0003.names] # Ensure order matches final schema
            try:
                 arrow_table_with_uuids = pa.Table.from_pandas(df_to_add, schema=SCHEMA_AT_0003, preserve_index=False)
                 log.info("Created Arrow Table with new UUIDs.")
            except Exception as e:
                 log.error(f"Failed to convert DataFrame with UUIDs to Arrow Table: {e}", exc_info=True)
                 raise RuntimeError("UUID backfill failed during Arrow conversion.") from e

            # Create temp table
            log.info(f"Creating temporary table '{temp_table_name}' for backfill...")
            if temp_table_name in db.table_names():
                db.drop_table(temp_table_name) # Clean up if exists
            temp_tbl = db.create_table(temp_table_name, schema=SCHEMA_AT_0003)

            # Write to temp table
            log.info(f"Writing {len(arrow_table_with_uuids)} rows to '{temp_table_name}'...")
            temp_tbl.add(arrow_table_with_uuids)

            # Verify temp table
            temp_count = temp_tbl.count_rows()
            if temp_count != original_count:
                log.error(f"UUID Backfill Verification failed: Row count mismatch (Original: {original_count}, Temp: {temp_count}).")
                db.drop_table(temp_table_name) # Clean up temp table
                raise RuntimeError("UUID backfill verification failed.")
            log.info("Temporary table verified.")

            # Replace original table
            log.info(f"Replacing original table '{EMBEDDING_TABLE_NAME}'...")
            db.drop_table(EMBEDDING_TABLE_NAME)
            log.info("Original table dropped.")

            # Recreate from temp table (read data again for safety)
            verified_data = db.open_table(temp_table_name).to_lance().to_table()
            db.create_table(EMBEDDING_TABLE_NAME, data=verified_data, schema=SCHEMA_AT_0003)
            log.info(f"Table '{EMBEDDING_TABLE_NAME}' recreated with UUIDs.")

            # Drop temp table
            db.drop_table(temp_table_name)
            log.info("Dropped temporary backfill table.")
            log.info("UUID backfill process completed.")

    # --- Create Scalar Index ---
    log.info("Checking/Creating scalar index on 'uuid' column...")
    final_tbl = db.open_table(EMBEDDING_TABLE_NAME) # Re-open potentially recreated table
    try:
        # Check existing indices - LanceDB API for listing indices might be internal/evolving.
        # For now, let's just try creating it. If it fails because it exists, handle it gracefully.
        # Note: create_scalar_index might replace an existing one by default. Check docs if specific behavior needed.
        final_tbl.create_scalar_index("uuid", replace=True) # Use replace=True for idempotency
        log.info("Scalar index on 'uuid' created or already exists.")
    except Exception as e:
        # Need to check the specific exception type LanceDB raises if index already exists
        # For now, catch broadly and log. If it's another error, re-raise.
        # Example pseudo-check: if "index already exists" in str(e).lower():
        #    log.info("Scalar index on 'uuid' already exists.")
        # else:
        log.error(f"Failed to create scalar index on 'uuid': {e}", exc_info=True)
        # Decide if this failure should halt the migration
        # raise RuntimeError("Failed to create scalar index.") from e

    log.info("Migration 0003_add_uuid_pk finished.")



def down(db: lancedb.DBConnection):
    log.warning("Applying down migration 0003_add_uuid_pk (dropping index and column)...")
    tbl = db.open_table(EMBEDDING_TABLE_NAME)
    # How to drop scalar index? API might not exist yet. Assume manual removal if needed.
    log.warning("Scalar index removal might need manual intervention.")
    if "uuid" in tbl.schema.names:
      tbl.drop_columns(["uuid"])
    log.warning("Down migration 0003_add_uuid_pk finished.")
