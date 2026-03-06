#!/usr/bin/env python3
"""
Database Import Script
Imports MongoDB collections from JSON backup files.
"""
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

# Import directory
IMPORT_DIR = ROOT_DIR.parent / 'db_export'


def restore_object_id(obj):
    """Recursively restore ObjectId and datetime from JSON."""
    if isinstance(obj, dict):
        if "$oid" in obj:
            return ObjectId(obj["$oid"])
        if "$date" in obj:
            return datetime.fromisoformat(obj["$date"].replace('Z', '+00:00'))
        return {k: restore_object_id(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [restore_object_id(item) for item in obj]
    return obj


async def import_collection(db, collection_name: str, import_dir: Path, drop_existing: bool = False) -> dict:
    """Import a single collection from a JSON file."""
    file_path = import_dir / f"{collection_name}.json"
    
    if not file_path.exists():
        return {"collection": collection_name, "count": 0, "status": "file_not_found"}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    if not documents:
        return {"collection": collection_name, "count": 0, "status": "empty_file"}
    
    # Restore ObjectId and datetime objects
    documents = restore_object_id(documents)
    
    collection = db[collection_name]
    
    if drop_existing:
        await collection.delete_many({})
    
    # Insert documents
    result = await collection.insert_many(documents)
    
    return {
        "collection": collection_name,
        "count": len(result.inserted_ids),
        "status": "success"
    }


async def import_database(drop_existing: bool = False):
    """Import all collections to the database."""
    print(f"\n{'='*50}")
    print(f"Database Import Tool")
    print(f"{'='*50}")
    print(f"Database: {db_name}")
    print(f"Import Directory: {IMPORT_DIR}")
    print(f"Drop Existing: {drop_existing}")
    print(f"{'='*50}\n")
    
    if not IMPORT_DIR.exists():
        print(f"Error: Import directory does not exist: {IMPORT_DIR}")
        return None
    
    # Read metadata
    metadata_path = IMPORT_DIR / "_export_metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        print(f"Importing from backup dated: {metadata.get('export_date', 'Unknown')}")
        print(f"Original total documents: {metadata.get('total_documents', 'Unknown')}\n")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    results = []
    total_imported = 0
    
    # Get all JSON files in import directory
    json_files = list(IMPORT_DIR.glob("*.json"))
    collection_names = [f.stem for f in json_files if not f.stem.startswith("_")]
    
    for collection_name in collection_names:
        try:
            result = await import_collection(db, collection_name, IMPORT_DIR, drop_existing)
            results.append(result)
            
            if result['status'] == 'success':
                print(f"✓ {collection_name}: {result['count']} documents imported")
                total_imported += result['count']
            else:
                print(f"○ {collection_name}: {result['status']}")
                
        except Exception as e:
            print(f"✗ {collection_name}: Error - {str(e)}")
            results.append({
                "collection": collection_name,
                "count": 0,
                "status": "error",
                "error": str(e)
            })
    
    print(f"\n{'='*50}")
    print(f"Import Complete!")
    print(f"Total Documents Imported: {total_imported}")
    print(f"{'='*50}\n")
    
    # Close connection
    client.close()
    
    return {
        "import_date": datetime.now(timezone.utc).isoformat(),
        "total_imported": total_imported,
        "collections": results
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Import database from JSON backup')
    parser.add_argument('--drop', action='store_true', help='Drop existing collections before import')
    args = parser.parse_args()
    
    asyncio.run(import_database(drop_existing=args.drop))
