#!/usr/bin/env python

import lancedb
import pyarrow as pa # To check types
import json
import logging
import sys
import argparse
from datetime import datetime, date # Need date for isinstance check

# --- Configuration ---
try:
    from embedding.main import get_datafile_path # Function to locate DB
    from embedding.schema import EMBEDDING_TABLE_NAME # Target schema definition
except ImportError:
    print("Error: Could not import necessary modules from 'embedding'.")
    print("Please run this script from the root of the 'local-ai-utils' project directory.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def format_value(value):
    """Converts values to JSON serializable formats, handling datetimes."""
    if isinstance(value, (datetime, date)):
        # Format datetime/date objects as ISO 8601 strings
        return value.isoformat()
    # Add handling for other non-serializable types if necessary
    return value

def main(output_file):
    log.info(f"Starting embedding export to '{output_file}'...")

    try:
        db_path = get_datafile_path("embeddings.lance")
        log.info(f"Connecting to database at: {db_path}")
        db = lancedb.connect(db_path)

        if EMBEDDING_TABLE_NAME not in db.table_names():
            log.error(f"Error: Table '{EMBEDDING_TABLE_NAME}' not found.")
            return

        tbl = db.open_table(EMBEDDING_TABLE_NAME)
        initial_count = tbl.count_rows()
        if initial_count == 0:
            log.warning("Table is empty. Exporting an empty file.")
            # Create an empty file
            with open(output_file, 'w') as f:
                pass # Just create the file
            return

        log.info(f"Found {initial_count} embeddings. Reading data...")

        # Read all data. .to_pylist() converts Arrow table to list of dicts
        try:
            # Selecting all columns explicitly ensures order if needed, but not strictly required
            # arrow_table = tbl.to_lance().to_table(columns=tbl.schema.names)
            arrow_table = tbl.to_lance().to_table() # Read all columns
            records = arrow_table.to_pylist() # Converts rows to dictionaries
            log.info(f"Successfully read {len(records)} records.")
            if len(records) != initial_count:
                log.warning(f"Row count mismatch: Read {len(records)}, expected {initial_count}")

        except Exception as e:
            log.error(f"Failed to read data from LanceDB table: {e}", exc_info=True)
            return

        log.info(f"Writing records to JSONL file: '{output_file}'...")
        exported_count = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            for record in records:
                 try:
                     # Format each value in the dictionary, especially datetimes
                     formatted_record = {k: format_value(v) for k, v in record.items()}
                     # Convert the formatted dictionary to a JSON string
                     json_line = json.dumps(formatted_record, ensure_ascii=False)
                     f.write(json_line + '\n')
                     exported_count += 1
                 except TypeError as e:
                     log.error(f"Skipping record due to serialization error: {e}. Record: {record}")
                 except Exception as e:
                     log.error(f"Skipping record due to unexpected error: {e}. Record: {record}")


        log.info(f"Finished exporting {exported_count}/{len(records)} records to '{output_file}'.")

    except Exception as e:
        log.exception(f"An unexpected error occurred during export: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export LanceDB embeddings table to a JSONL seed file.")
    parser.add_argument("output_file", help="Path to the output JSONL file (e.g., embedding/seeds/embeddings.jsonl)")
    args = parser.parse_args()

    main(args.output_file)
