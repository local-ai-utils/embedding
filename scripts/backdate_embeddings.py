#!/usr/bin/env python

import lancedb
import pandas as pd
import random
from datetime import datetime, timedelta, timezone
import logging
import sys
from pathlib import Path

# --- Configuration ---
# Assuming this script is run from the project root
try:
    # When running from project root, we need to use absolute imports
    from embedding.main import get_datafile_path # Function to locate DB
    from embedding.schema import EMBEDDING_TABLE_NAME # Target schema definition
except ImportError:
    print("Error: Could not import necessary modules from 'embedding'.")
    print("Please run this script from the root of the 'embedding' project directory.")
    sys.exit(1)

MAX_CREATED_DAYS_AGO = 90
RELEVANT_DATE_CHANCE = 0.30 # 30% chance of having a relevant_date
RELEVANT_DATE_WINDOW_DAYS = 30 # +/- 30 days from created_date

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def generate_random_past_datetime(max_days_ago: int) -> datetime:
    """Generates a random datetime between now and max_days_ago."""
    now = datetime.now(timezone.utc)
    days_ago = random.uniform(0, max_days_ago)
    # Add random hours/minutes/seconds/microseconds for more variety
    seconds_offset = random.uniform(0, days_ago * 24 * 60 * 60)
    return now - timedelta(seconds=seconds_offset)

def generate_relevant_datetime(created_dt: datetime, window_days: int) -> datetime:
    """Generates a random datetime +/- window_days from the created_dt."""
    offset_days = random.uniform(-window_days, window_days)
    # Add random time component as well
    offset_seconds = offset_days * 24 * 60 * 60 + random.uniform(-12*3600, 12*3600)
    return created_dt + timedelta(seconds=offset_seconds)

def main():
    log.info("Starting script to backdate embedding timestamps...")

    try:
        db_path = get_datafile_path("embeddings.lance")
        log.info(f"Connecting to database at: {db_path}")
        db = lancedb.connect(db_path)

        if EMBEDDING_TABLE_NAME not in db.table_names():
            log.error(f"Error: Table '{EMBEDDING_TABLE_NAME}' not found in the database.")
            log.error("Ensure migrations have run and the table exists.")
            return

        tbl = db.open_table(EMBEDDING_TABLE_NAME)
        current_schema = tbl.schema

        # *** Crucial Check: Ensure UUID and date columns exist ***
        required_cols = ["uuid", "created_date", "relevant_date"]
        missing_cols = [col for col in required_cols if col not in current_schema.names]
        if missing_cols:
             log.error(f"Error: Table '{EMBEDDING_TABLE_NAME}' is missing required columns: {missing_cols}.")
             log.error("Please ensure migrations up to '0003_add_uuid_pk' have run successfully.")
             return

        log.info(f"Found {tbl.count_rows()} existing embeddings.")

        try:
            # Read only UUIDs to iterate over
            uuid_table = tbl.to_lance().to_table(columns=["uuid"])
            uuids = uuid_table['uuid'].to_pylist()

        except Exception as e:
            log.error(f"Failed to read UUIDs from LanceDB table: {e}", exc_info=True)
            return

        log.info("Starting row-by-row timestamp update...")
        update_errors = 0
        updated_count = 0

        for i, row_uuid in enumerate(uuids):
            if i % 50 == 0: # Log progress every 50 rows
                 log.info(f"Processing row {i+1}/{len(uuids)}...")

            try:
                # Generate new timestamps for this row
                new_created_date = generate_random_past_datetime(MAX_CREATED_DAYS_AGO)
                new_relevant_date = None # LanceDB handles None for nullable fields
                if random.random() < RELEVANT_DATE_CHANCE:
                    new_relevant_date = generate_relevant_datetime(new_created_date, RELEVANT_DATE_WINDOW_DAYS)

                # Construct the update values dictionary
                # Timestamps should be datetime objects, LanceDB handles conversion
                update_values = {
                    "created_date": new_created_date,
                    "relevant_date": new_relevant_date
                }

                # Construct the WHERE clause using the unique UUID
                where_clause = f"uuid = '{row_uuid}'"

                # Perform the update for this single row
                # Note: Each update might create a new version/fragment internally
                tbl.update(values=update_values, where=where_clause)
                updated_count += 1

            except Exception as e:
                log.error(f"Failed to update row with UUID '{row_uuid}': {e}", exc_info=False) # Keep log concise
                update_errors += 1

        log.info("Finished row-by-row updates.")
        log.info(f"Successfully updated: {updated_count} rows.")
        if update_errors > 0:
            log.warning(f"Failed to update: {update_errors} rows.")

    except Exception as e:
        log.exception(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
