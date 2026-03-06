from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid
import os

from core.database import db
from core.auth import hash_password, verify_password, create_token, generate_api_key, get_current_user
from core.helpers import get_default_templates_and_automation
from models.schemas import UserCreate, UserLogin, UserResponse, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Demo user credentials
DEMO_EMAIL = "demo@restaurant.com"
DEMO_PASSWORD = "demo123"


async def create_default_whatsapp_templates(user_id: str):
    """Create default WhatsApp templates and automation rules for a new user"""
    templates, automation_rules = get_default_templates_and_automation(user_id)
    
    # Insert templates
    if templates:
        await db.whatsapp_templates.insert_many(templates)
    
    # Insert automation rules
    if automation_rules:
        await db.automation_rules.insert_many(automation_rules)


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    # Check if email exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    api_key = generate_api_key()
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "restaurant_name": user_data.restaurant_name,
        "phone": user_data.phone,
        "password_hash": hash_password(user_data.password),
        "api_key": api_key,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    # Create default loyalty settings
    settings_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "min_order_value": 100.0,
        "bronze_earn_percent": 5.0,
        "silver_earn_percent": 7.0,
        "gold_earn_percent": 10.0,
        "platinum_earn_percent": 15.0,
        "redemption_value": 0.25,
        "min_redemption_points": 100,
        "max_redemption_percent": 50.0,
        "max_redemption_amount": 500.0,
        "points_expiry_months": 6,
        "expiry_reminder_days": 30,
        "tier_silver_min": 500,
        "tier_gold_min": 1500,
        "tier_platinum_min": 5000,
        "birthday_bonus_enabled": True,
        "birthday_bonus_points": 100,
        "birthday_bonus_days_before": 0,
        "birthday_bonus_days_after": 7,
        "anniversary_bonus_enabled": True,
        "anniversary_bonus_points": 150,
        "anniversary_bonus_days_before": 0,
        "anniversary_bonus_days_after": 7,
        "first_visit_bonus_enabled": True,
        "first_visit_bonus_points": 50,
        "off_peak_bonus_enabled": False,
        "off_peak_start_time": "14:00",
        "off_peak_end_time": "17:00",
        "off_peak_bonus_type": "multiplier",
        "off_peak_bonus_value": 2.0,
        "feedback_bonus_enabled": True,
        "feedback_bonus_points": 25
    }
    await db.loyalty_settings.insert_one(settings_doc)
    
    # Create default WhatsApp templates and automation rules
    await create_default_whatsapp_templates(user_id)
    
    token = create_token(user_id)
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=user_data.email,
            restaurant_name=user_data.restaurant_name,
            phone=user_data.phone,
            created_at=user_doc["created_at"]
        )
    )

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """
    Unified login endpoint - routes to MyGenie authentication
    Kept for backward compatibility, calls mygenie_login internally
    """
    return await mygenie_login(credentials)

@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        email=user["email"],
        restaurant_name=user["restaurant_name"],
        phone=user["phone"],
        pos_id=user.get("pos_id", ""),
        pos_name=user.get("pos_name", ""),
        created_at=user["created_at"]
    )

@router.put("/profile")
async def update_profile(updates: dict, user: dict = Depends(get_current_user)):
    allowed = {"phone", "address"}
    filtered = {k: v for k, v in updates.items() if k in allowed and v is not None}
    if not filtered:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    await db.users.update_one({"id": user["id"]}, {"$set": filtered})
    updated = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    return {"business_name": updated.get("restaurant_name", ""), "phone": updated.get("phone", ""), "address": updated.get("address", ""), "email": updated.get("email", ""), "pos_id": updated.get("pos_id", ""), "pos_name": updated.get("restaurant_name", "")}

@router.post("/demo-login", response_model=TokenResponse)
async def demo_login():
    """
    Demo mode login - uses local test user without MyGenie authentication
    For testing and demonstration purposes only
    """
    user = await db.users.find_one({"email": DEMO_EMAIL}, {"_id": 0})
    
    if not user:
        raise HTTPException(
            status_code=404, 
            detail="Demo user not found. Please run setup first."
        )
    
    token = create_token(user["id"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            restaurant_name=user["restaurant_name"],
            phone=user["phone"],
            pos_id=user.get("pos_id", ""),
            pos_name=user.get("pos_name", ""),
            created_at=user["created_at"]
        ),
        is_demo=True
    )

@router.post("/mygenie-login", response_model=TokenResponse)
async def mygenie_login(credentials: UserLogin):
    """
    Login flow:
    1. Check local DB by email - if user exists with password_hash, authenticate locally
    2. If user not in local DB, authenticate via MyGenie API and create user
    """
    import httpx
    
    # Step 1: Check local DB first
    local_user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    
    if local_user and local_user.get("password_hash") and local_user.get("api_key"):
        # Existing user - authenticate locally
        if not verify_password(credentials.password, local_user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_token(local_user["id"])
        return TokenResponse(
            access_token=token,
            user=UserResponse(
                id=local_user["id"],
                email=local_user["email"],
                restaurant_name=local_user.get("restaurant_name", "Unknown"),
                phone=local_user.get("phone", ""),
                pos_id=local_user.get("pos_id", ""),
                pos_name=local_user.get("pos_name", ""),
                created_at=local_user["created_at"]
            ),
            is_demo=False
        )
    
    # Step 2: User not in local DB - authenticate via MyGenie
    mygenie_api_url = os.getenv("MYGENIE_API_URL", "https://preprod.mygenie.online")
    login_endpoint = os.getenv("MYGENIE_LOGIN_ENDPOINT", "/api/v1/auth/vendoremployee/login")
    profile_endpoint = os.getenv("MYGENIE_PROFILE_ENDPOINT", "/api/v1/vendoremployee/profile")
    
    async with httpx.AsyncClient() as client:
        try:
            login_response = await client.post(
                f"{mygenie_api_url}{login_endpoint}",
                json={
                    "email": credentials.email,
                    "password": credentials.password
                },
                headers={"Content-Type": "application/json"},
                timeout=10.0
            )
            
            if login_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            login_data = login_response.json()
            mygenie_token = login_data.get("token")
            
            if not mygenie_token:
                raise HTTPException(
                    status_code=500,
                    detail="MyGenie authentication failed - no token received"
                )
            
            profile_response = await client.get(
                f"{mygenie_api_url}{profile_endpoint}",
                headers={
                    "Authorization": f"Bearer {mygenie_token}",
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )
            
            if profile_response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to fetch user profile from MyGenie"
                )
            
            profile_data = profile_response.json()
            
            email = profile_data.get("emp_email") or credentials.email
            first_name = profile_data.get("emp_f_name", "")
            last_name = profile_data.get("emp_l_name", "") or ""
            restaurant_name = "Unknown"
            phone = ""
            restaurant_id = None
            
            if profile_data.get("restaurants") and len(profile_data["restaurants"]) > 0:
                restaurant = profile_data["restaurants"][0]
                restaurant_name = restaurant.get("name", "Unknown")
                phone = restaurant.get("phone", "")
                restaurant_id = str(restaurant.get("id", ""))
            
            # pos_id and pos_name hardcoded for now, will be dynamic later
            pos_id = "0001"
            pos_name = "MyGenie"
            user_id = f"pos_{pos_id}_restaurant_{restaurant_id}"
            
            # Check if user already exists (e.g. created before password_hash was added)
            existing_user = await db.users.find_one({"pos_id": pos_id, "restaurant_id": restaurant_id}, {"_id": 0})
            if existing_user:
                # Add password_hash to existing user
                await db.users.update_one(
                    {"id": existing_user["id"]},
                    {"$set": {"password_hash": hash_password(credentials.password)}}
                )
                token = create_token(existing_user["id"])
                return TokenResponse(
                    access_token=token,
                    user=UserResponse(
                        id=existing_user["id"],
                        email=existing_user.get("email", email),
                        restaurant_name=existing_user.get("restaurant_name", restaurant_name),
                        phone=existing_user.get("phone", phone),
                        pos_id=existing_user.get("pos_id", ""),
                        pos_name=existing_user.get("pos_name", ""),
                        created_at=existing_user["created_at"]
                    ),
                    is_demo=False
                )
            
            # Create new user with password_hash
            api_key = generate_api_key()
            now = datetime.now(timezone.utc).isoformat()
            user_doc = {
                "id": user_id,
                "pos_id": pos_id,
                "pos_name": pos_name,
                "restaurant_id": restaurant_id,
                "api_key": api_key,
                "email": email,
                "password_hash": hash_password(credentials.password),
                "restaurant_name": restaurant_name,
                "phone": phone,
                "first_name": first_name,
                "last_name": last_name,
                "mygenie_token": mygenie_token,
                "mygenie_synced": True,
                "created_at": now,
                "last_login": now
            }
            await db.users.insert_one(user_doc)
            
            # Create default loyalty settings
            settings_doc = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "min_order_value": 100.0,
                "bronze_earn_percent": 5.0,
                "silver_earn_percent": 7.0,
                "gold_earn_percent": 10.0,
                "platinum_earn_percent": 15.0,
                "redemption_value": 0.25,
                "min_redemption_points": 100,
                "max_redemption_percent": 50.0,
                "max_redemption_amount": 500.0,
                "points_expiry_months": 6,
                "expiry_reminder_days": 30,
                "tier_silver_min": 500,
                "tier_gold_min": 1500,
                "tier_platinum_min": 5000,
                "birthday_bonus_enabled": True,
                "birthday_bonus_points": 100,
                "birthday_bonus_days_before": 0,
                "birthday_bonus_days_after": 7,
                "anniversary_bonus_enabled": True,
                "anniversary_bonus_points": 150,
                "anniversary_bonus_days_before": 0,
                "anniversary_bonus_days_after": 7,
                "first_visit_bonus_enabled": True,
                "first_visit_bonus_points": 50,
                "off_peak_bonus_enabled": False,
                "off_peak_start_time": "14:00",
                "off_peak_end_time": "17:00",
                "off_peak_bonus_type": "multiplier",
                "off_peak_bonus_value": 2.0,
                "feedback_bonus_enabled": True,
                "feedback_bonus_points": 25
            }
            await db.loyalty_settings.insert_one(settings_doc)
            
            # Create default WhatsApp templates and automation rules
            await create_default_whatsapp_templates(user_id)
            
            token = create_token(user_id)
            return TokenResponse(
                access_token=token,
                user=UserResponse(
                    id=user_id,
                    email=email,
                    restaurant_name=restaurant_name,
                    phone=phone,
                    pos_id=pos_id,
                    pos_name=pos_name,
                    created_at=now
                ),
                is_demo=False
            )
            
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="MyGenie API timeout")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"MyGenie API error: {str(e)}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")
