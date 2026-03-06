from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional, List
import httpx
import os
import uuid

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
    Sync orders from MyGenie POS API with pagination support.
    
    API Endpoint: POST /api/v1/vendoremployee/whatsappcrm/customer-order-migration?page=N
    
    Response structure:
    {
        "current_page": 1,
        "last_page": 80,
        "per_page": 25,
        "total_orders": 1979,
        "orders": [...]
    }
    """
    # Get user's MyGenie token
    user_record = await db.users.find_one({"id": user["id"]})
    mygenie_token = user_record.get("mygenie_token") if user_record else None
    
    if not mygenie_token:
        return {
            "success": False,
            "synced": 0,
            "updated": 0,
            "total": 0,
            "message": "MyGenie token not found. Please login with MyGenie credentials first."
        }
    
    mygenie_api_url = os.getenv("MYGENIE_API_URL", "https://preprod.mygenie.online")
    order_list_endpoint = f"{mygenie_api_url}/api/v1/vendoremployee/whatsappcrm/customer-order-migration"
    
    now = datetime.now(timezone.utc).isoformat()
    synced_count = 0
    updated_count = 0
    total_orders = 0
    
    try:
        async with httpx.AsyncClient() as client:
            # Pagination loop
            page = 1
            last_page = 1
            
            while page <= last_page:
                resp = await client.post(
                    f"{order_list_endpoint}?page={page}",
                    headers={
                        "Authorization": f"Bearer {mygenie_token}",
                        "Content-Type": "application/json; charset=UTF-8",
                        "X-localization": "en"
                    },
                    json={},
                    timeout=60.0
                )
                
                if resp.status_code != 200:
                    return {
                        "success": False,
                        "synced": synced_count,
                        "updated": updated_count,
                        "total": total_orders,
                        "message": f"MyGenie API error on page {page}: {resp.status_code}"
                    }
                
                data = resp.json()
                last_page = data.get("last_page", 1)
                total_orders = data.get("total_orders", 0)
                order_list = data.get("orders", [])
                
                for mygenie_order in order_list:
                    # Extract customer info from nested user object
                    user_obj = mygenie_order.get("user") or {}
                    pos_customer_id = mygenie_order.get("user_id")
                    cust_mobile = user_obj.get("phone", "")
                    cust_name = f"{user_obj.get('f_name', '')} {user_obj.get('l_name', '')}".strip()
                    cust_email = user_obj.get("email", "")
                    
                    # Extract employee info
                    employee_obj = mygenie_order.get("vendorEmployee") or {}
                    employee_name = f"{employee_obj.get('f_name', '')} {employee_obj.get('l_name', '')}".strip()
                    
                    # Check if order already exists (using 'id' field from API)
                    pos_order_id = mygenie_order.get("id")
                    existing_order = await db.orders.find_one({
                        "user_id": user["id"],
                        "pos_order_id": pos_order_id
                    })
                    
                    # Find customer by pos_customer_id or phone
                    customer = None
                    if pos_customer_id:
                        customer = await db.customers.find_one({
                            "user_id": user["id"],
                            "pos_customer_id": pos_customer_id
                        })
                    
                    if not customer and cust_mobile:
                        customer = await db.customers.find_one({
                            "user_id": user["id"],
                            "phone": cust_mobile
                        })
                    
                    # Build order document with corrected field mappings
                    order_doc = {
                        "user_id": user["id"],
                        "customer_id": customer["id"] if customer else None,
                        
                        # POS Identification
                        "pos_id": "mygenie",
                        "pos_restaurant_id": mygenie_order.get("restaurant_id"),
                        "pos_order_id": pos_order_id,
                        "restaurant_order_id": mygenie_order.get("restaurant_order_id"),
                        "pos_customer_id": pos_customer_id,
                        
                        # Customer Info (from nested user object)
                        "cust_mobile": cust_mobile,
                        "cust_name": cust_name,
                        "cust_email": cust_email,
                        
                        # Amounts
                        "order_amount": float(mygenie_order.get("order_amount") or 0),
                        "delivery_charge": float(mygenie_order.get("delivery_charge") or 0),
                        
                        # Payment Info
                        "payment_method": mygenie_order.get("payment_method"),
                        "payment_status": mygenie_order.get("payment_status"),
                        
                        # Order Status
                        "order_status": mygenie_order.get("order_status"),
                        "order_type": mygenie_order.get("order_type"),
                        
                        # Order Meta
                        "table_id": mygenie_order.get("table_id"),
                        "waiter_id": mygenie_order.get("waiter_id"),
                        "employee_id": mygenie_order.get("employee_id"),
                        "employee_name": employee_name,
                        "print_kot": mygenie_order.get("print_kot"),
                        "print_bill_status": mygenie_order.get("print_bill_status"),
                        
                        # Notes
                        "order_notes": mygenie_order.get("order_note"),
                        
                        # Timestamps
                        "order_created_at": mygenie_order.get("created_at"),
                        "order_updated_at": mygenie_order.get("updated_at"),
                        
                        # Items
                        "items": [],
                        
                        # Sync flags
                        "mygenie_synced": True,
                        "last_synced_at": now,
                        "points_earned": 0,
                        "off_peak_bonus": 0,
                    }
                    
                    # Process orderDetails (cart items) with corrected field mappings
                    order_details = mygenie_order.get("orderDetails", [])
                    for item in order_details:
                        food_details = item.get("food_details") or {}
                        
                        order_doc["items"].append({
                            "item_name": food_details.get("name", f"Item {food_details.get('id')}"),
                            "pos_food_id": food_details.get("id"),
                            "item_category": food_details.get("category_id"),
                            "item_qty": item.get("quantity", 1),
                            "item_price": float(item.get("price") or item.get("unit_price") or 0),
                            "variation": item.get("variation", []),
                            "add_ons": item.get("add_ons", []),
                            "station": item.get("station"),
                            "item_type": item.get("item_type"),
                            "item_notes": item.get("food_level_notes"),
                            "is_veg": food_details.get("veg"),
                            "tax": food_details.get("tax"),
                            "tax_type": food_details.get("tax_type"),
                            "food_status": item.get("food_status"),
                            "ready_at": item.get("ready_at"),
                            "serve_at": item.get("serve_at"),
                            "cancel_at": item.get("cancel_at"),
                        })
                        
                        # Get restaurant name from first item if available
                        if not order_doc.get("restaurant_name") and food_details.get("restaurant_name"):
                            order_doc["restaurant_name"] = food_details.get("restaurant_name")
                    
                    if existing_order:
                        # Update existing order
                        await db.orders.update_one(
                            {"id": existing_order["id"]},
                            {"$set": order_doc}
                        )
                        updated_count += 1
                    else:
                        # Insert new order
                        order_doc["id"] = str(uuid.uuid4())
                        order_doc["created_at"] = mygenie_order.get("created_at", now)
                        await db.orders.insert_one(order_doc)
                        synced_count += 1
                        
                        # Also insert into order_items collection for AI analytics
                        if order_doc["items"] and customer:
                            order_items_docs = []
                            for item in order_doc["items"]:
                                order_items_docs.append({
                                    "id": str(uuid.uuid4()),
                                    "order_id": order_doc["id"],
                                    "customer_id": customer["id"],
                                    "user_id": user["id"],
                                    **item,
                                    "created_at": now,
                                })
                            if order_items_docs:
                                await db.order_items.insert_many(order_items_docs)
                
                # Move to next page
                page += 1
            
            # Update last sync timestamp
            await db.users.update_one(
                {"id": user["id"]},
                {"$set": {"last_order_sync_at": now}}
            )
            
            return {
                "success": True,
                "synced": synced_count,
                "updated": updated_count,
                "total": total_orders,
                "message": f"Successfully synced {synced_count} new and updated {updated_count} existing orders from MyGenie"
            }
            
    except httpx.TimeoutException:
        return {
            "success": False,
            "synced": synced_count,
            "updated": updated_count,
            "total": total_orders,
            "message": "MyGenie API timeout - please try again"
        }
    except Exception as e:
        return {
            "success": False,
            "synced": synced_count,
            "updated": updated_count,
            "total": total_orders,
            "message": f"Error syncing orders: {str(e)}"
        }

