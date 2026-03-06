"""
MongoDB Data Import Script
Usage: python import_data.py

Place all JSON files in the same directory as this script.
This will import all collections into your MongoDB.
"""

import asyncio
import json
import os
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB Connection - Update these for your target database
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

async def import_all():
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Find all JSON files (except _summary.json)
    json_files = [f for f in os.listdir(script_dir) if f.endswith('.json') and not f.startswith('_')]
    
    print(f"Found {len(json_files)} collections to import")
    print("-" * 50)
    
    for filename in json_files:
        coll_name = filename.replace('.json', '')
        filepath = os.path.join(script_dir, filename)
        
        try:
            with open(filepath, 'r') as f:
                docs = json.load(f)
            
            if docs:
                collection = db[coll_name]
                
                # Option 1: Clear existing and insert (uncomment if needed)
                # await collection.delete_many({})
                
                # Option 2: Upsert based on 'id' field
                for doc in docs:
                    if 'id' in doc:
                        await collection.update_one(
                            {"id": doc["id"]},
                            {"$set": doc},
                            upsert=True
                        )
                    else:
                        await collection.insert_one(doc)
                
                print(f"✅ {coll_name}: {len(docs)} documents imported")
            else:
                print(f"⚪ {coll_name}: 0 documents (skipped)")
                
        except Exception as e:
            print(f"❌ {coll_name}: Error - {e}")
    
    print("-" * 50)
    print("✅ Import complete!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(import_all())
