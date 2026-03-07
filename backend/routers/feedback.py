from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone, timedelta
import uuid
import asyncio

from core.database import db
from core.auth import get_current_user
from core.whatsapp import trigger_whatsapp_event
from models.schemas import Feedback, FeedbackCreate, DashboardStats

router = APIRouter(prefix="/feedback", tags=["Feedback"])
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.post("", response_model=Feedback)
async def create_feedback(feedback_data: FeedbackCreate, user: dict = Depends(get_current_user)):
    feedback_id = str(uuid.uuid4())
    
    feedback_doc = {
        "id": feedback_id,
        "user_id": user["id"],
        "customer_id": feedback_data.customer_id,
        "customer_name": feedback_data.customer_name,
        "customer_phone": feedback_data.customer_phone,
        "rating": feedback_data.rating,
        "message": feedback_data.message,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.feedback.insert_one(feedback_doc)
    
    customer = None
    
    # Award feedback bonus points if enabled
    if feedback_data.customer_id:
        settings = await db.loyalty_settings.find_one({"user_id": user["id"]}, {"_id": 0})
        customer = await db.customers.find_one({"id": feedback_data.customer_id})
        
        if settings and settings.get("feedback_bonus_enabled", False) and customer:
            bonus_points = settings.get("feedback_bonus_points", 25)
            new_balance = customer.get("total_points", 0) + bonus_points
            await db.customers.update_one(
                {"id": feedback_data.customer_id},
                {"$set": {"total_points": new_balance}}
            )
            
            tx_doc = {
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "customer_id": feedback_data.customer_id,
                "points": bonus_points,
                "transaction_type": "bonus",
                "description": "Feedback bonus",
                "bill_amount": None,
                "balance_after": new_balance,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.points_transactions.insert_one(tx_doc)
            
            # Update customer for trigger
            customer["total_points"] = new_balance
    
    # Fire feedback_received WhatsApp trigger
    if customer:
        asyncio.create_task(trigger_whatsapp_event(
            db, user["id"], "feedback_received", customer,
            {
                "rating": feedback_data.rating,
                "feedback_message": feedback_data.message or "",
                "feedback_id": feedback_id
            }
        ))
    
    return Feedback(**feedback_doc)

@router.get("", response_model=List[Feedback])
async def list_feedback(
    status: str = None,
    rating: int = None,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    query = {"user_id": user["id"]}
    if status:
        query["status"] = status
    if rating:
        query["rating"] = rating
    
    feedbacks = await db.feedback.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return [Feedback(**f) for f in feedbacks]

@router.put("/{feedback_id}/resolve")
async def resolve_feedback(feedback_id: str, user: dict = Depends(get_current_user)):
    result = await db.feedback.update_one(
        {"id": feedback_id, "user_id": user["id"]},
        {"$set": {"status": "resolved"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return {"message": "Feedback marked as resolved"}


# Analytics endpoints
@analytics_router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    
    # Header metrics: Loyalty Orders % and Repeat vs New Revenue
    # Get all repeat customer IDs (total_visits >= 2)
    repeat_customers = await db.customers.find(
        {"user_id": user_id, "total_visits": {"$gte": 2}},
        {"id": 1}
    ).to_list(None)
    repeat_customer_ids = [c["id"] for c in repeat_customers]
    
    # Get all new customer IDs (total_visits = 1)
    new_customers = await db.customers.find(
        {"user_id": user_id, "total_visits": 1},
        {"id": 1}
    ).to_list(None)
    new_customer_ids = [c["id"] for c in new_customers]
    
    # Total orders
    total_orders_count = await db.orders.count_documents({"user_id": user_id})
    
    # Loyalty orders (from repeat customers)
    loyalty_orders_count = await db.orders.count_documents({
        "user_id": user_id,
        "customer_id": {"$in": repeat_customer_ids}
    }) if repeat_customer_ids else 0
    
    loyalty_orders_percent = round((loyalty_orders_count / total_orders_count * 100), 1) if total_orders_count > 0 else 0.0
    
    # Revenue from repeat customers
    repeat_revenue_pipeline = [
        {"$match": {"user_id": user_id, "customer_id": {"$in": repeat_customer_ids}}},
        {"$group": {"_id": None, "total": {"$sum": "$order_amount"}}}
    ]
    repeat_revenue_result = await db.orders.aggregate(repeat_revenue_pipeline).to_list(1) if repeat_customer_ids else []
    repeat_revenue = repeat_revenue_result[0].get("total", 0) if repeat_revenue_result else 0
    
    # Revenue from new customers
    new_revenue_pipeline = [
        {"$match": {"user_id": user_id, "customer_id": {"$in": new_customer_ids}}},
        {"$group": {"_id": None, "total": {"$sum": "$order_amount"}}}
    ]
    new_revenue_result = await db.orders.aggregate(new_revenue_pipeline).to_list(1) if new_customer_ids else []
    new_revenue = new_revenue_result[0].get("total", 0) if new_revenue_result else 0
    
    total_revenue_for_percent = repeat_revenue + new_revenue
    repeat_revenue_percent = round((repeat_revenue / total_revenue_for_percent * 100), 1) if total_revenue_for_percent > 0 else 0.0
    new_revenue_percent = round((new_revenue / total_revenue_for_percent * 100), 1) if total_revenue_for_percent > 0 else 0.0
    
    # Row 1: Customer Health
    total_customers = await db.customers.count_documents({"user_id": user_id})
    
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    active_30d = await db.customers.count_documents({
        "user_id": user_id,
        "last_visit": {"$gte": thirty_days_ago}
    })
    
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    new_7d = await db.customers.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": seven_days_ago}
    })
    
    # Row 2: Repeat Customers
    repeat_2_plus = await db.customers.count_documents({
        "user_id": user_id,
        "total_visits": {"$gte": 2}
    })
    repeat_5_plus = await db.customers.count_documents({
        "user_id": user_id,
        "total_visits": {"$gte": 5}
    })
    repeat_10_plus = await db.customers.count_documents({
        "user_id": user_id,
        "total_visits": {"$gte": 10}
    })
    
    # Row 3: Inactive Customers (no visit in last X days)
    sixty_days_ago = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    ninety_days_ago = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    
    inactive_30d = await db.customers.count_documents({
        "user_id": user_id,
        "$or": [
            {"last_visit": {"$lt": thirty_days_ago}},
            {"last_visit": None}
        ]
    })
    inactive_60d = await db.customers.count_documents({
        "user_id": user_id,
        "$or": [
            {"last_visit": {"$lt": sixty_days_ago}},
            {"last_visit": None}
        ]
    })
    inactive_90d = await db.customers.count_documents({
        "user_id": user_id,
        "$or": [
            {"last_visit": {"$lt": ninety_days_ago}},
            {"last_visit": None}
        ]
    })
    
    # Row 3: Orders
    total_orders = await db.orders.count_documents({"user_id": user_id})
    
    order_value_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$order_amount"},
            "count": {"$sum": 1}
        }}
    ]
    order_result = await db.orders.aggregate(order_value_pipeline).to_list(1)
    total_revenue = order_result[0].get("total_revenue", 0) if order_result else 0
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0
    
    # Avg orders per day (last 30 days)
    orders_30d = await db.orders.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": thirty_days_ago}
    })
    avg_orders_per_day = round(orders_30d / 30, 1)
    
    # Row 4: Points
    points_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$transaction_type",
            "total": {"$sum": "$points"}
        }}
    ]
    points_stats = await db.points_transactions.aggregate(points_pipeline).to_list(10)
    
    points_issued = 0
    points_redeemed = 0
    for stat in points_stats:
        if stat["_id"] in ["earn", "bonus"]:
            points_issued += stat["total"]
        elif stat["_id"] == "redeem":
            points_redeemed += stat["total"]
    points_balance = points_issued - points_redeemed
    
    # Row 5: Wallet
    wallet_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$transaction_type",
            "total": {"$sum": "$amount"}
        }}
    ]
    wallet_stats = await db.wallet_transactions.aggregate(wallet_pipeline).to_list(10)
    
    wallet_issued = 0.0
    wallet_used = 0.0
    for stat in wallet_stats:
        if stat["_id"] == "credit":
            wallet_issued += stat["total"]
        elif stat["_id"] == "debit":
            wallet_used += stat["total"]
    wallet_balance = wallet_issued - wallet_used
    
    # Row 7: Coupons (from coupon_transactions)
    total_coupons = await db.coupons.count_documents({"user_id": user_id})
    coupons_used = await db.coupon_transactions.count_documents({"user_id": user_id})
    
    # Discount availed from coupon_transactions
    coupon_discount_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": None,
            "total_discount": {"$sum": "$discount_amount"}
        }}
    ]
    coupon_discount_result = await db.coupon_transactions.aggregate(coupon_discount_pipeline).to_list(1)
    discount_availed = coupon_discount_result[0].get("total_discount", 0) if coupon_discount_result else 0.0
    
    # Rating (legacy)
    rating_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": None,
            "avg_rating": {"$avg": "$rating"},
            "count": {"$sum": 1}
        }}
    ]
    rating_result = await db.feedback.aggregate(rating_pipeline).to_list(1)
    
    avg_rating = 0.0
    total_feedback = 0
    if rating_result:
        avg_rating = round(rating_result[0].get("avg_rating", 0) or 0, 1)
        total_feedback = rating_result[0].get("count", 0)
    
    # Get loyalty settings for conditional display
    loyalty_settings = await db.loyalty_settings.find_one({"user_id": user_id})
    loyalty_enabled = loyalty_settings.get("loyalty_enabled", True) if loyalty_settings else True
    wallet_enabled = loyalty_settings.get("wallet_enabled", False) if loyalty_settings else False
    coupon_enabled = loyalty_settings.get("coupon_enabled", False) if loyalty_settings else False
    
    # Row 8: Revenue calculations
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_iso = today.isoformat()
    thirty_one_days_ago = (today - timedelta(days=31)).isoformat()
    eight_days_ago = (today - timedelta(days=8)).isoformat()
    
    # Total Revenue (all time)
    total_revenue_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": None, "total": {"$sum": "$order_amount"}}}
    ]
    total_revenue_result = await db.orders.aggregate(total_revenue_pipeline).to_list(1)
    total_revenue = total_revenue_result[0].get("total", 0) if total_revenue_result else 0.0
    
    # Revenue 30D (excluding today)
    revenue_30d_pipeline = [
        {"$match": {"user_id": user_id, "created_at": {"$gte": thirty_one_days_ago, "$lt": today_iso}}},
        {"$group": {"_id": None, "total": {"$sum": "$order_amount"}}}
    ]
    revenue_30d_result = await db.orders.aggregate(revenue_30d_pipeline).to_list(1)
    revenue_30d = revenue_30d_result[0].get("total", 0) if revenue_30d_result else 0.0
    
    # Revenue 7D (excluding today)
    revenue_7d_pipeline = [
        {"$match": {"user_id": user_id, "created_at": {"$gte": eight_days_ago, "$lt": today_iso}}},
        {"$group": {"_id": None, "total": {"$sum": "$order_amount"}}}
    ]
    revenue_7d_result = await db.orders.aggregate(revenue_7d_pipeline).to_list(1)
    revenue_7d = revenue_7d_result[0].get("total", 0) if revenue_7d_result else 0.0
    
    # Row 9: Top 3 Selling Items
    # Top items 30D
    top_items_30d_pipeline = [
        {"$match": {"user_id": user_id, "created_at": {"$gte": thirty_days_ago}}},
        {"$group": {"_id": "$item_name", "qty": {"$sum": "$item_qty"}}},
        {"$sort": {"qty": -1}},
        {"$limit": 3},
        {"$project": {"name": "$_id", "qty": 1, "_id": 0}}
    ]
    top_items_30d = await db.order_items.aggregate(top_items_30d_pipeline).to_list(3)
    
    # Top items 7D
    top_items_7d_pipeline = [
        {"$match": {"user_id": user_id, "created_at": {"$gte": seven_days_ago}}},
        {"$group": {"_id": "$item_name", "qty": {"$sum": "$item_qty"}}},
        {"$sort": {"qty": -1}},
        {"$limit": 3},
        {"$project": {"name": "$_id", "qty": 1, "_id": 0}}
    ]
    top_items_7d = await db.order_items.aggregate(top_items_7d_pipeline).to_list(3)
    
    # Top items all time
    top_items_all_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$item_name", "qty": {"$sum": "$item_qty"}}},
        {"$sort": {"qty": -1}},
        {"$limit": 3},
        {"$project": {"name": "$_id", "qty": 1, "_id": 0}}
    ]
    top_items_all_time = await db.order_items.aggregate(top_items_all_pipeline).to_list(3)
    
    return DashboardStats(
        loyalty_orders_percent=loyalty_orders_percent,
        repeat_revenue_percent=repeat_revenue_percent,
        new_revenue_percent=new_revenue_percent,
        total_customers=total_customers,
        active_customers_30d=active_30d,
        new_customers_7d=new_7d,
        repeat_2_plus=repeat_2_plus,
        repeat_5_plus=repeat_5_plus,
        repeat_10_plus=repeat_10_plus,
        inactive_30d=inactive_30d,
        inactive_60d=inactive_60d,
        inactive_90d=inactive_90d,
        total_orders=total_orders,
        avg_order_value=avg_order_value,
        avg_orders_per_day=avg_orders_per_day,
        total_points_issued=points_issued,
        total_points_redeemed=points_redeemed,
        points_balance=points_balance,
        wallet_issued=wallet_issued,
        wallet_used=wallet_used,
        wallet_balance=wallet_balance,
        total_coupons=total_coupons,
        coupons_used=coupons_used,
        discount_availed=discount_availed,
        total_revenue=total_revenue,
        revenue_30d=revenue_30d,
        revenue_7d=revenue_7d,
        top_items_30d=top_items_30d,
        top_items_7d=top_items_7d,
        top_items_all_time=top_items_all_time,
        avg_rating=avg_rating,
        total_feedback=total_feedback,
        loyalty_enabled=loyalty_enabled,
        wallet_enabled=wallet_enabled,
        coupon_enabled=coupon_enabled
    )
