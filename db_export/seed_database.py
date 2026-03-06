"""
DinePoints CRM - Complete Database Seed Script
================================================
This script imports all data into MongoDB.

Usage:
  1. Place all JSON files in the same directory as this script
  2. Set environment variables (or use defaults):
     - MONGO_URL (default: mongodb://localhost:27017)
     - DB_NAME (default: test_database)
  3. Run: python seed_database.py

Options:
  --clear    Clear all collections before importing (fresh start)
  --update   Update existing documents (upsert mode - default)
"""

import asyncio
import json
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB Connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

# Collection import order (to handle dependencies)
IMPORT_ORDER = [
    "users",
    "loyalty_settings",
    "customers",
    "segments",
    "coupons",
    "orders",
    "order_items",
    "points_transactions",
    "wallet_transactions",
    "feedback",
    "automation_rules",
    "whatsapp_templates",
    "whatsapp_event_template_map",
    "whatsapp_template_variable_map",
    "whatsapp_message_logs",
]


async def clear_database(db):
    """Clear all collections"""
    print("\n🗑️  Clearing all collections...")
    collections = await db.list_collection_names()
    for coll_name in collections:
        await db[coll_name].delete_many({})
        print(f"   Cleared: {coll_name}")
    print("✅ Database cleared\n")


async def import_collection(db, coll_name, filepath, mode="update"):
    """Import a single collection"""
    try:
        with open(filepath, 'r') as f:
            docs = json.load(f)
        
        if not docs:
            return 0
        
        collection = db[coll_name]
        count = 0
        
        for doc in docs:
            if mode == "update" and 'id' in doc:
                # Upsert based on 'id' field
                await collection.update_one(
                    {"id": doc["id"]},
                    {"$set": doc},
                    upsert=True
                )
            else:
                # Simple insert
                try:
                    await collection.insert_one(doc)
                except Exception:
                    pass  # Skip duplicates
            count += 1
        
        return count
        
    except FileNotFoundError:
        return -1
    except Exception as e:
        print(f"   Error: {e}")
        return -1


async def main():
    # Parse arguments
    clear_mode = "--clear" in sys.argv
    
    print("=" * 60)
    print("  DinePoints CRM - Database Seed Script")
    print("=" * 60)
    print(f"\n📊 MongoDB: {MONGO_URL}")
    print(f"📁 Database: {DB_NAME}")
    print(f"🔧 Mode: {'Clear & Import' if clear_mode else 'Update/Upsert'}")
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Test connection
    try:
        await client.admin.command('ping')
        print("✅ Connected to MongoDB\n")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return
    
    # Clear database if requested
    if clear_mode:
        await clear_database(db)
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Import collections
    print("📥 Importing collections...")
    print("-" * 60)
    
    total_docs = 0
    
    for coll_name in IMPORT_ORDER:
        filepath = os.path.join(script_dir, f"{coll_name}.json")
        count = await import_collection(db, coll_name, filepath, "update" if not clear_mode else "insert")
        
        if count == -1:
            print(f"   ⚪ {coll_name}: Not found (skipped)")
        elif count == 0:
            print(f"   ⚪ {coll_name}: 0 documents")
        else:
            print(f"   ✅ {coll_name}: {count} documents")
            total_docs += count
    
    # Check for any additional JSON files not in the order
    all_json_files = [f.replace('.json', '') for f in os.listdir(script_dir) 
                      if f.endswith('.json') and not f.startswith('_')]
    extra_files = set(all_json_files) - set(IMPORT_ORDER)
    
    for coll_name in extra_files:
        filepath = os.path.join(script_dir, f"{coll_name}.json")
        count = await import_collection(db, coll_name, filepath, "update" if not clear_mode else "insert")
        if count > 0:
            print(f"   ✅ {coll_name}: {count} documents (extra)")
            total_docs += count
    
    print("-" * 60)
    print(f"\n✅ Import complete! Total: {total_docs} documents")
    print("=" * 60)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
