"""
Import JSON data from /app/db_export/ into MongoDB.
Run: python3 scripts/db_import.py

Options:
  --drop   Drop existing collections before importing (fresh import)
  --merge  Skip docs that already exist (by 'id' field). Default behaviour.

Usage:
  python3 scripts/db_import.py          # merge mode (safe, skips duplicates)
  python3 scripts/db_import.py --drop   # drops collections first, then imports all
"""
import json
import os
import sys
from pymongo import MongoClient

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")
EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db_export")


def import_db(drop_first=False):
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]

    if not os.path.isdir(EXPORT_DIR):
        print(f"ERROR: Export directory not found: {EXPORT_DIR}")
        sys.exit(1)

    json_files = [f for f in os.listdir(EXPORT_DIR) if f.endswith(".json") and not f.startswith("_")]

    if not json_files:
        print("No collection JSON files found in db_export/")
        sys.exit(1)

    for filename in sorted(json_files):
        collection_name = filename.replace(".json", "")
        filepath = os.path.join(EXPORT_DIR, filename)

        with open(filepath, "r") as f:
            docs = json.load(f)

        if not docs:
            print(f"  {collection_name}: 0 docs (skipped)")
            continue

        collection = db[collection_name]

        if drop_first:
            collection.drop()
            collection.insert_many(docs)
            print(f"  {collection_name}: {len(docs)} docs imported (dropped & replaced)")
        else:
            inserted = 0
            skipped = 0
            for doc in docs:
                doc_id = doc.get("id")
                if doc_id and collection.find_one({"id": doc_id}):
                    skipped += 1
                else:
                    collection.insert_one(doc)
                    inserted += 1
            print(f"  {collection_name}: {inserted} inserted, {skipped} skipped (already exist)")

    print(f"\nImport complete from {EXPORT_DIR}")
    client.close()


if __name__ == "__main__":
    drop_mode = "--drop" in sys.argv
    if drop_mode:
        print("MODE: DROP & REPLACE (all existing data will be wiped)\n")
    else:
        print("MODE: MERGE (skipping existing docs by 'id' field)\n")
    import_db(drop_first=drop_mode)
