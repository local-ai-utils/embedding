import os
import re
import importlib
import lancedb
from pathlib import Path
import logging

from .schema import VERSION_TABLE_NAME, TARGET_SCHEMA, EMBEDDING_TABLE_NAME # Need TARGET_SCHEMA for final check

log = logging.getLogger(__name__)

MIGRATION_DIR = Path(__file__).parent / "migrations"
MIGRATION_FILE_PATTERN = re.compile(r"^(\d{4})_.*\.py$")

def _get_migration_definitions():
    """Scans the migration directory and loads migration functions."""
    migrations = []
    if not MIGRATION_DIR.is_dir():
        log.warning(f"Migration directory not found: {MIGRATION_DIR}")
        return []

    for filename in sorted(os.listdir(MIGRATION_DIR)):
        match = MIGRATION_FILE_PATTERN.match(filename)
        if match:
            migration_id_str = match.group(1)
            migration_id = int(migration_id_str) # Keep as int for comparison
            module_name = f"embedding.migrations.{filename[:-3]}" # Adjust import path
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "up"):
                    migrations.append({
                        "id": migration_id,
                        "name": filename[:-3],
                        "up_func": module.up,
                        "down_func": module.down
                    })
                else:
                    log.warning(f"Migration file {filename} is missing 'up' function.")
            except ImportError as e:
                log.error(f"Failed to import migration module {module_name}: {e}", exc_info=True)
                raise # Fail fast if a migration can't be loaded
            except Exception as e:
                log.error(f"Error loading migration {filename}: {e}", exc_info=True)
                raise

    # Ensure migrations are sorted numerically by ID (even though listdir might sort alphabetically)
    migrations.sort(key=lambda m: m["id"])
    return migrations

def _get_current_migration_id(db: lancedb.DBConnection) -> str:
    """Gets the ID of the last applied migration from the database."""
    try:
        if VERSION_TABLE_NAME not in db.table_names():
            # If the version table doesn't exist, no migrations have run.
            # The first migration (0001) should create it.
            log.info(f"'{VERSION_TABLE_NAME}' table not found. Assuming no migrations applied (ID '0000').")
            return 0 # Represents state before first migration

        version_tbl = db.open_table(VERSION_TABLE_NAME)
        version_data = version_tbl.to_lance().to_table().to_pydict()

        if not version_data or 'migration_id' not in version_data or not version_data['migration_id']:
             # Table exists but is empty or invalid, treat as unmigrated
             log.warning(f"'{VERSION_TABLE_NAME}' table is empty or invalid. Assuming no migrations applied (ID '0000').")
             return 0

        # Assuming only one row stores the latest applied migration ID
        last_id = version_data['migration_id'][-1] # Get the last entry if multiple somehow exist
        log.info(f"Found last applied migration ID: {last_id}")
        return last_id

    except Exception as e:
         log.error(f"Error accessing LanceDB during migration check: {e}")
         raise
    except Exception as e:
        log.error(f"Unexpected error getting migration ID: {e}", exc_info=True)
        raise ValueError("Failed to determine database migration state.") from e


def _update_db_migration_id(db: lancedb.DBConnection, migration_id: int):
    """Updates the migration ID in the database."""
    try:
        version_tbl = db.open_table(VERSION_TABLE_NAME)
        # Simple approach: delete existing and add new ID.
        # More robust: Check if ID exists before deleting/adding, or use update if available.
        version_tbl.delete("True") # Clear previous state
        version_tbl.add([{"migration_id": migration_id}])
        log.info(f"Database migration state updated to: {migration_id}")
    except Exception as e:
        log.error(f"Failed to update migration state to {migration_id}: {e}", exc_info=True)
        raise # Fail migration if state update fails


def run_migrations(db: lancedb.DBConnection):
    """Checks DB migration state and runs necessary migrations."""
    last_applied_id = _get_current_migration_id(db)
    all_migrations = _get_migration_definitions()

    if not all_migrations:
        log.info("No migration files found.")
        return

    target_migration_id = all_migrations[-1]['id']

    if last_applied_id >= target_migration_id:
        log.info(f"Database is up to date (last applied migration: {last_applied_id}).")
        return

    log.info(f"Current migration level: {last_applied_id}. Target level: {target_migration_id}. Applying pending migrations...")

    applied_count = 0
    for migration in all_migrations:
      if migration['id'] >= last_applied_id:
        log.info(f"Applying {migration['name']} ({migration['id']})...")
        try:
            migration['up_func'](db)
            _update_db_migration_id(db, migration['id'])
            last_applied_id = migration['id'] # Update our tracked state
            applied_count += 1
            log.info(f"Successfully applied {migration['name']} ({migration['id']}).")
        except Exception as e:
            log.error(f"Migration {migration['name']} ({migration['id']}) FAILED: {e}", exc_info=True)
            raise RuntimeError(f"Migration failed at {migration['name']}")

    log.info(f"Applied {applied_count} migration(s). Database is now at migration level {last_applied_id}.")
