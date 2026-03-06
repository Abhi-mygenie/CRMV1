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
    Sync orders from MyGenie POS API.
    
    Expected MyGenie Order API Response Structure:
    {
        "orders": [
            {
                "order_id": "ORD-123",
                "restaurant_id": "478",
                "restaurant_name": "18march",
                "user_id": "12345",  # pos_customer_id
                "cust_mobile": "9653078025",
                "cust_name": "Piyush",
                "cust_email": "piyush@example.com",
                "order_amount": 987.0,
                "order_sub_total_amount": 987.0,
                "order_discount": 0.0,
                "self_discount": 0.0,
                "coupon_code": "",
                "coupon_discount": 0.0,
                "wallet_used": 0.0,
                "tax_amount": 0.0,
                "gst_tax": 0.0,
                "vat_tax": 0.0,
                "service_tax": 0.0,
                "service_gst_tax_amount": 0.0,
                "tip_amount": 0.0,
                "tip_tax_amount": 0.0,
                "delivery_charge": 0.0,
                "round_up": 0.0,
                "payment_method": "TAB",
                "payment_status": "success",
                "payment_type": "prepaid",
                "transaction_id": "",
                "order_type": "pos",
                "table_id": "0",
                "waiter_id": "1703",
                "print_kot": "Yes",
                "paid_room": "",
                "room_id": "",
                "address_id": "",
                "order_note": "",
                "created_at": "2026-03-05T10:30:00Z",
                "cart": [
                    {
                        "food_id": 62118,
                        "item_name": "Butter Chicken",
                        "item_category": "North Indian",
                        "quantity": 1,
                        "food_amount": 987.0,
                        "variant": "",
                        "variations": [],
                        "add_on_ids": [],
                        "add_on_qtys": [],
                        "add_ons": [],
                        "variation_amount": 0.0,
                        "addon_amount": 0.0,
                        "discount_amount": 0.0,
                        "service_charge": 0.0,
                        "gst_amount": 0.0,
                        "vat_amount": 0.0,
                        "station": "OTHER",
                        "food_level_notes": "Less spicy"
                    }
                ]
            }
        ]
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
    
    # TODO: Replace with actual MyGenie order list API endpoint when provided
    # Expected endpoint: POST /api/v2/vendoremployee/order-history or similar
    order_list_endpoint = f"{mygenie_api_url}/api/v2/vendoremployee/order-history"
    
    now = datetime.now(timezone.utc).isoformat()
    synced_count = 0
    updated_count = 0
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                order_list_endpoint,
                headers={
                    "Authorization": f"Bearer {mygenie_token}",
                    "Content-Type": "application/json; charset=UTF-8",
                    "X-localization": "en"
                },
                json={},  # Add any required parameters
                timeout=30.0
            )
            
            if resp.status_code != 200:
                return {
                    "success": False,
                    "synced": 0,
                    "updated": 0,
                    "total": 0,
                    "message": f"MyGenie API error: {resp.status_code}",
                    "note": "Order sync API endpoint may not be configured correctly"
                }
            
            data = resp.json()
            order_list = data.get("orders", [])
            
            for mygenie_order in order_list:
                # Check if order already exists
                existing_order = await db.orders.find_one({
                    "user_id": user["id"],
                    "pos_order_id": mygenie_order.get("order_id")
                })
                
                # Find or create customer
                customer = None
                pos_customer_id = mygenie_order.get("user_id")
                cust_mobile = mygenie_order.get("cust_mobile")
                
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
                
                # Build order document with ALL fields
                order_doc = {
                    "user_id": user["id"],
                    "customer_id": customer["id"] if customer else None,
                    
                    # POS Identification
                    "pos_id": "mygenie",
                    "pos_restaurant_id": mygenie_order.get("restaurant_id"),
                    "restaurant_name": mygenie_order.get("restaurant_name"),
                    "pos_order_id": mygenie_order.get("order_id"),
                    "pos_customer_id": pos_customer_id,
                    
                    # Customer Info
                    "cust_mobile": cust_mobile,
                    "cust_name": mygenie_order.get("cust_name"),
                    "cust_email": mygenie_order.get("cust_email"),
                    
                    # Amounts
                    "order_amount": float(mygenie_order.get("order_amount") or 0),
                    "order_sub_total": float(mygenie_order.get("order_sub_total_amount") or 0),
                    
                    # Discounts
                    "order_discount": float(mygenie_order.get("order_discount") or 0),
                    "self_discount": float(mygenie_order.get("self_discount") or 0),
                    "coupon_code": mygenie_order.get("coupon_code"),
                    "coupon_discount": float(mygenie_order.get("coupon_discount") or 0),
                    
                    # Wallet
                    "wallet_used": float(mygenie_order.get("wallet_used") or 0),
                    
                    # Taxes
                    "tax_amount": float(mygenie_order.get("tax_amount") or 0),
                    "gst_tax": float(mygenie_order.get("gst_tax") or 0),
                    "vat_tax": float(mygenie_order.get("vat_tax") or 0),
                    "service_tax": float(mygenie_order.get("service_tax") or 0),
                    "service_gst_tax_amount": float(mygenie_order.get("service_gst_tax_amount") or 0),
                    
                    # Tips & Charges
                    "tip_amount": float(mygenie_order.get("tip_amount") or 0),
                    "tip_tax_amount": float(mygenie_order.get("tip_tax_amount") or 0),
                    "delivery_charge": float(mygenie_order.get("delivery_charge") or 0),
                    "round_up": float(mygenie_order.get("round_up") or 0),
                    
                    # Payment Info
                    "payment_method": mygenie_order.get("payment_method"),
                    "payment_status": mygenie_order.get("payment_status"),
                    "payment_type": mygenie_order.get("payment_type"),
                    "transaction_id": mygenie_order.get("transaction_id"),
                    
                    # Order Meta
                    "order_type": mygenie_order.get("order_type"),
                    "table_id": mygenie_order.get("table_id"),
                    "waiter_id": mygenie_order.get("waiter_id"),
                    "print_kot": mygenie_order.get("print_kot"),
                    
                    # Room/Address
                    "paid_room": mygenie_order.get("paid_room"),
                    "room_id": mygenie_order.get("room_id"),
                    "address_id": mygenie_order.get("address_id"),
                    
                    # Notes
                    "order_notes": mygenie_order.get("order_note"),
                    
                    # Items
                    "items": [],
                    
                    # Sync flags
                    "mygenie_synced": True,
                    "last_synced_at": now,
                    "points_earned": 0,
                    "off_peak_bonus": 0,
                }
                
                # Process cart items
                cart_items = mygenie_order.get("cart", [])
                for item in cart_items:
                    order_doc["items"].append({
                        "item_name": item.get("item_name", f"Item {item.get('food_id')}"),
                        "pos_food_id": item.get("food_id"),
                        "item_category": item.get("item_category"),
                        "item_qty": item.get("quantity", 1),
                        "item_price": float(item.get("food_amount") or 0),
                        "variant": item.get("variant"),
                        "variations": item.get("variations", []),
                        "add_on_ids": item.get("add_on_ids", []),
                        "add_on_qtys": item.get("add_on_qtys", []),
                        "add_ons": item.get("add_ons", []),
                        "variation_amount": float(item.get("variation_amount") or 0),
                        "addon_amount": float(item.get("addon_amount") or 0),
                        "discount_amount": float(item.get("discount_amount") or 0),
                        "service_charge": float(item.get("service_charge") or 0),
                        "gst_amount": float(item.get("gst_amount") or 0),
                        "vat_amount": float(item.get("vat_amount") or 0),
                        "station": item.get("station"),
                        "item_notes": item.get("food_level_notes"),
                    })
                
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
            
            # Update last sync timestamp
            await db.users.update_one(
                {"id": user["id"]},
                {"$set": {"last_order_sync_at": now}}
            )
            
            return {
                "success": True,
                "synced": synced_count,
                "updated": updated_count,
                "total": len(order_list),
                "message": f"Successfully synced {synced_count} new and updated {updated_count} existing orders from MyGenie"
            }
            
    except httpx.TimeoutException:
        return {
            "success": False,
            "synced": 0,
            "updated": 0,
            "total": 0,
            "message": "MyGenie API timeout - please try again"
        }
    except Exception as e:
        return {
            "success": False,
            "synced": 0,
            "updated": 0,
            "total": 0,
            "message": f"Error syncing orders: {str(e)}",
            "note": "Order sync API endpoint may not be available yet"
        }
