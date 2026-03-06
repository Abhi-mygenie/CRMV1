from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, timezone, timedelta
import uuid

from core.database import db
from core.auth import get_current_user
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
    
    # Award feedback bonus points if enabled
    if feedback_data.customer_id:
        settings = await db.loyalty_settings.find_one({"user_id": user["id"]}, {"_id": 0})
        if settings and settings.get("feedback_bonus_enabled", False):
            bonus_points = settings.get("feedback_bonus_points", 25)
            customer = await db.customers.find_one({"id": feedback_data.customer_id})
            if customer:
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
    
    total_customers = await db.customers.count_documents({"user_id": user_id})
    
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
    
    return DashboardStats(
        total_customers=total_customers,
        total_points_issued=points_issued,
        total_points_redeemed=points_redeemed,
        active_customers_30d=active_30d,
        new_customers_7d=new_7d,
        avg_rating=avg_rating,
        total_feedback=total_feedback
    )
