from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone

from core.database import db
from core.auth import get_current_user

router = APIRouter(prefix="/migration", tags=["Migration"])


@router.get("/status")
async def get_migration_status(user: dict = Depends(get_current_user)):
    """
    Get the current migration status for the user
    Returns sync counts and confirmation status
    """
    user_record = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    
    # Count synced data
    customers_count = await db.customers.count_documents({
        "user_id": user["id"],
        "mygenie_synced": True
    })
    
    orders_count = await db.orders.count_documents({
        "user_id": user["id"],
        "mygenie_synced": True
    })
    
    return {
        "migration_confirmed": user_record.get("migration_confirmed", False),
        "migration_confirmed_at": user_record.get("migration_confirmed_at"),
        "customers_synced": customers_count,
        "orders_synced": orders_count,
        "last_customer_sync": user_record.get("last_customer_sync_at"),
        "last_order_sync": user_record.get("last_order_sync_at")
    }


@router.post("/confirm")
async def confirm_migration(user: dict = Depends(get_current_user)):
    """
    Confirm the migration - marks sync as complete
    After confirmation, the migration section will be hidden
    """
    now = datetime.now(timezone.utc).isoformat()
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "migration_confirmed": True,
            "migration_confirmed_at": now
        }}
    )
    
    return {
        "success": True,
        "message": "Migration confirmed successfully",
        "confirmed_at": now
    }


@router.post("/revert")
async def revert_migration(user: dict = Depends(get_current_user)):
    """
    Revert the migration - deletes all synced customers and orders
    Allows user to sync again from scratch
    """
    # Delete synced customers (only those marked as mygenie_synced)
    customers_result = await db.customers.delete_many({
        "user_id": user["id"],
        "mygenie_synced": True
    })
    
    # Delete synced orders
    orders_result = await db.orders.delete_many({
        "user_id": user["id"],
        "mygenie_synced": True
    })
    
    # Delete related order_items
    await db.order_items.delete_many({
        "user_id": user["id"]
    })
    
    # Delete related points_transactions from synced orders
    await db.points_transactions.delete_many({
        "user_id": user["id"],
        "description": {"$regex": "synced from MyGenie", "$options": "i"}
    })
    
    # Reset migration status
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "migration_confirmed": False,
            "migration_confirmed_at": None,
            "last_customer_sync_at": None,
            "last_order_sync_at": None
        }}
    )
    
    return {
        "success": True,
        "message": "Migration reverted successfully",
        "customers_deleted": customers_result.deleted_count,
        "orders_deleted": orders_result.deleted_count
    }


@router.post("/revert-customers")
async def revert_customers(user: dict = Depends(get_current_user)):
    """
    Revert only synced customers - keeps orders intact
    """
    # Delete synced customers (only those marked as mygenie_synced)
    customers_result = await db.customers.delete_many({
        "user_id": user["id"],
        "mygenie_synced": True
    })
    
    # Reset customer sync timestamp
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_customer_sync_at": None}}
    )
    
    return {
        "success": True,
        "message": "Customers reverted successfully",
        "customers_deleted": customers_result.deleted_count
    }


@router.post("/revert-orders")
async def revert_orders(user: dict = Depends(get_current_user)):
    """
    Revert only synced orders - keeps customers intact
    """
    # Delete synced orders
    orders_result = await db.orders.delete_many({
        "user_id": user["id"],
        "mygenie_synced": True
    })
    
    # Delete related order_items
    await db.order_items.delete_many({
        "user_id": user["id"]
    })
    
    # Reset order sync timestamp
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_order_sync_at": None}}
    )
    
    return {
        "success": True,
        "message": "Orders reverted successfully",
        "orders_deleted": orders_result.deleted_count
    }


@router.post("/sync-orders")
async def sync_orders_from_mygenie(user: dict = Depends(get_current_user)):
    """
    Placeholder for order sync from MyGenie
    Will be implemented when MyGenie order API endpoint is provided
    """
    # For now, return a placeholder response
    # This will be implemented once the MyGenie order API endpoint is known
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Update last sync timestamp
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_order_sync_at": now}}
    )
    
    return {
        "success": True,
        "synced": 0,
        "updated": 0,
        "total": 0,
        "message": "Order sync endpoint ready - awaiting MyGenie API integration",
        "note": "This feature will sync orders once MyGenie order API is configured"
    }
