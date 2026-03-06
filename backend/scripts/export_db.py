#!/usr/bin/env python3
"""
Database Export Script
Exports all MongoDB collections to JSON files for backup/migration.
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

# Collections to export
COLLECTIONS = [
    'users',
    'customers',
    'orders',
    'wallet_transactions',
    'points_transactions',
    'coupons',
    'coupon_usages',
    'segments',
    'loyalty_settings',
    'feedback',
    'whatsapp_templates',
    'automation_rules',
    'campaigns',
    'campaign_messages'
]

# Output directory
EXPORT_DIR = ROOT_DIR.parent / 'db_export'


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle MongoDB ObjectId and datetime."""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return {"$oid": str(obj)}
        if isinstance(obj, datetime):
            return {"$date": obj.isoformat()}
        return super().default(obj)


async def export_collection(db, collection_name: str, export_dir: Path) -> dict:
    """Export a single collection to a JSON file."""
    collection = db[collection_name]
    documents = await collection.find({}).to_list(length=None)
    
    if not documents:
        return {"collection": collection_name, "count": 0, "file": None}
    
    # Convert ObjectId to string for JSON serialization
    file_path = export_dir / f"{collection_name}.json"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(documents, f, cls=JSONEncoder, indent=2, ensure_ascii=False)
    
    return {
        "collection": collection_name,
        "count": len(documents),
        "file": str(file_path)
    }


async def export_database():
    """Export all collections from the database."""
    print(f"\n{'='*50}")
    print(f"Database Export Tool")
    print(f"{'='*50}")
    print(f"Database: {db_name}")
    print(f"Export Directory: {EXPORT_DIR}")
    print(f"{'='*50}\n")
    
    # Create export directory
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    results = []
    total_documents = 0
    
    for collection_name in COLLECTIONS:
        try:
            result = await export_collection(db, collection_name, EXPORT_DIR)
            results.append(result)
            
            if result['count'] > 0:
                print(f"✓ {collection_name}: {result['count']} documents exported")
                total_documents += result['count']
            else:
                print(f"○ {collection_name}: empty (skipped)")
                
        except Exception as e:
            print(f"✗ {collection_name}: Error - {str(e)}")
            results.append({
                "collection": collection_name,
                "count": 0,
                "error": str(e)
            })
    
    # Create export metadata
    metadata = {
        "export_date": datetime.now(timezone.utc).isoformat(),
        "database": db_name,
        "total_documents": total_documents,
        "collections": results
    }
    
    metadata_path = EXPORT_DIR / "_export_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n{'='*50}")
    print(f"Export Complete!")
    print(f"Total Documents: {total_documents}")
    print(f"Export Location: {EXPORT_DIR}")
    print(f"{'='*50}\n")
    
    # Close connection
    client.close()
    
    return metadata


if __name__ == "__main__":
    asyncio.run(export_database())
