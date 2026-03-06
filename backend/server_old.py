from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import qrcode
import io
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'dinepoints-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(title="DinePoints - Loyalty & CRM")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

security = HTTPBearer()

# ============ MODELS ============

# Auth Models
class UserBase(BaseModel):
    email: EmailStr
    restaurant_name: str
    phone: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    restaurant_name: str
    phone: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Customer Models
class CustomerBase(BaseModel):
    name: str
    phone: str
    country_code: str = "+91"  # Default to India
    email: Optional[str] = None
    notes: Optional[str] = None
    dob: Optional[str] = None  # Date of Birth (ISO format)
    anniversary: Optional[str] = None  # Anniversary Date (ISO format)
    customer_type: str = "normal"  # normal or corporate
    gst_name: Optional[str] = None  # GST Name (for corporate)
    gst_number: Optional[str] = None  # GST Number (for corporate)
    # Delivery Address (optional section)
    address: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    # Allergies (list of allergy types)
    allergies: Optional[List[str]] = None
    # Custom fields (always shown, field 1 is dropdown, 2-3 are text)
    custom_field_1: Optional[str] = None  # Dropdown field
    custom_field_2: Optional[str] = None  # Text field
    custom_field_3: Optional[str] = None  # Text field
    # Favorites for segmentation
    favorites: Optional[List[str]] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    country_code: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None
    dob: Optional[str] = None
    anniversary: Optional[str] = None
    customer_type: Optional[str] = None
    gst_name: Optional[str] = None
    gst_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    allergies: Optional[List[str]] = None
    custom_field_1: Optional[str] = None
    custom_field_2: Optional[str] = None
    custom_field_3: Optional[str] = None
    favorites: Optional[List[str]] = None

class Customer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    name: str
    phone: str
    country_code: str = "+91"
    email: Optional[str] = None
    notes: Optional[str] = None
    dob: Optional[str] = None
    anniversary: Optional[str] = None
    customer_type: str = "normal"
    gst_name: Optional[str] = None
    gst_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    allergies: Optional[List[str]] = None
    custom_field_1: Optional[str] = None
    custom_field_2: Optional[str] = None
    custom_field_3: Optional[str] = None
    favorites: Optional[List[str]] = None
    total_points: int = 0
    wallet_balance: float = 0.0  # Virtual wallet balance in ₹
    total_visits: int = 0
    total_spent: float = 0.0
    tier: str = "Bronze"
    created_at: str
    last_visit: Optional[str] = None

# Wallet Transaction Models
class WalletTransactionCreate(BaseModel):
    customer_id: str
    amount: float
    transaction_type: str  # credit, debit
    description: str
    payment_method: Optional[str] = None  # cash, upi, card

class WalletTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    customer_id: str
    amount: float
    transaction_type: str
    description: str
    payment_method: Optional[str] = None
    balance_after: float
    created_at: str

# Coupon Models
class CouponCreate(BaseModel):
    code: str  # Coupon code (e.g., SAVE10, WELCOME20)
    discount_type: str  # "percentage" or "fixed"
    discount_value: float  # Discount amount (% or fixed ₹)
    start_date: str  # ISO date string
    end_date: str  # ISO date string
    usage_limit: Optional[int] = None  # Total usage limit (None = unlimited)
    per_user_limit: int = 1  # Max times a single user can use
    min_order_value: float = 0  # Minimum order to apply coupon
    max_discount: Optional[float] = None  # Max discount for percentage type
    specific_users: Optional[List[str]] = None  # List of customer IDs (None = all users)
    applicable_channels: List[str] = ["delivery", "takeaway", "dine_in"]  # Where coupon applies
    description: Optional[str] = None

class CouponUpdate(BaseModel):
    code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    usage_limit: Optional[int] = None
    per_user_limit: Optional[int] = None
    min_order_value: Optional[float] = None
    max_discount: Optional[float] = None
    specific_users: Optional[List[str]] = None
    applicable_channels: Optional[List[str]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Coupon(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    code: str
    discount_type: str
    discount_value: float
    start_date: str
    end_date: str
    usage_limit: Optional[int] = None
    per_user_limit: int = 1
    min_order_value: float = 0
    max_discount: Optional[float] = None
    specific_users: Optional[List[str]] = None
    applicable_channels: List[str] = ["delivery", "takeaway", "dine_in"]
    description: Optional[str] = None
    is_active: bool = True
    total_used: int = 0
    created_at: str

# Segment Models
class SegmentCreate(BaseModel):
    name: str
    filters: dict  # JSON object with filter criteria

class SegmentUpdate(BaseModel):
    name: Optional[str] = None
    filters: Optional[dict] = None

class Segment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    name: str
    filters: dict
    customer_count: int = 0
    created_at: str
    updated_at: str

class CouponUsage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    coupon_id: str
    customer_id: str
    order_value: float
    discount_applied: float
    channel: str
    used_at: str

# Points Transaction Models
class PointsTransactionType(str):
    EARN = "earn"
    REDEEM = "redeem"
    BONUS = "bonus"
    EXPIRED = "expired"

class PointsTransactionCreate(BaseModel):
    customer_id: str
    points: int
    transaction_type: str  # earn, redeem, bonus, expired
    description: str
    bill_amount: Optional[float] = None

class PointsTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    customer_id: str
    points: int
    transaction_type: str
    description: str
    bill_amount: Optional[float] = None
    balance_after: int
    created_at: str

# Loyalty Settings Models
class LoyaltySettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    # Earning settings - percentage based
    min_order_value: float = 100.0  # Minimum bill to earn points
    bronze_earn_percent: float = 5.0  # 5% of bill as points for Bronze
    silver_earn_percent: float = 7.0  # 7% for Silver
    gold_earn_percent: float = 10.0  # 10% for Gold
    platinum_earn_percent: float = 15.0  # 15% for Platinum
    # Redemption settings
    redemption_value: float = 1.0  # 1 point = ₹1
    min_redemption_points: int = 50  # Minimum 50 points (₹50) to redeem
    max_redemption_percent: float = 50.0  # Max 50% of bill can be paid with points
    max_redemption_amount: float = 500.0  # Max ₹500 can be redeemed per transaction
    # Points expiry
    points_expiry_months: int = 6  # Points expire after 6 months (0 = never)
    expiry_reminder_days: int = 30  # Remind X days before expiry
    # Tier thresholds (points needed to reach tier)
    tier_silver_min: int = 500
    tier_gold_min: int = 1500
    tier_platinum_min: int = 5000
    # Custom field labels for customer form
    custom_field_1_label: str = "Custom Field 1"
    custom_field_2_label: str = "Custom Field 2"
    custom_field_3_label: str = "Custom Field 3"
    custom_field_1_enabled: bool = False
    custom_field_2_enabled: bool = False
    custom_field_3_enabled: bool = False
    # Birthday/Anniversary Bonus
    birthday_bonus_enabled: bool = True
    birthday_bonus_points: int = 100
    birthday_bonus_days_before: int = 0  # Days before birthday to give bonus
    birthday_bonus_days_after: int = 7  # Days after birthday bonus is valid
    anniversary_bonus_enabled: bool = True
    anniversary_bonus_points: int = 150
    anniversary_bonus_days_before: int = 0
    anniversary_bonus_days_after: int = 7
    # First Visit Bonus
    first_visit_bonus_enabled: bool = True
    first_visit_bonus_points: int = 50
    # Off-Peak Hours Bonus
    off_peak_bonus_enabled: bool = False
    off_peak_start_time: str = "14:00"  # 2 PM (24-hour format HH:MM)
    off_peak_end_time: str = "17:00"  # 5 PM
    off_peak_bonus_type: str = "multiplier"  # "multiplier" or "flat"
    off_peak_bonus_value: float = 2.0  # 2x points or flat 50 points
    # Feedback/Review Bonus
    feedback_bonus_enabled: bool = True
    feedback_bonus_points: int = 25

class LoyaltySettingsUpdate(BaseModel):
    min_order_value: Optional[float] = None
    bronze_earn_percent: Optional[float] = None
    silver_earn_percent: Optional[float] = None
    gold_earn_percent: Optional[float] = None
    platinum_earn_percent: Optional[float] = None
    redemption_value: Optional[float] = None
    min_redemption_points: Optional[int] = None
    max_redemption_percent: Optional[float] = None
    max_redemption_amount: Optional[float] = None
    points_expiry_months: Optional[int] = None
    expiry_reminder_days: Optional[int] = None
    tier_silver_min: Optional[int] = None
    tier_gold_min: Optional[int] = None
    tier_platinum_min: Optional[int] = None
    custom_field_1_label: Optional[str] = None
    custom_field_2_label: Optional[str] = None
    custom_field_3_label: Optional[str] = None
    custom_field_1_enabled: Optional[bool] = None
    custom_field_2_enabled: Optional[bool] = None
    custom_field_3_enabled: Optional[bool] = None
    # Birthday/Anniversary Bonus
    birthday_bonus_enabled: Optional[bool] = None
    birthday_bonus_points: Optional[int] = None
    birthday_bonus_days_before: Optional[int] = None
    birthday_bonus_days_after: Optional[int] = None
    anniversary_bonus_enabled: Optional[bool] = None
    anniversary_bonus_points: Optional[int] = None
    anniversary_bonus_days_before: Optional[int] = None
    anniversary_bonus_days_after: Optional[int] = None
    # First Visit Bonus
    first_visit_bonus_enabled: Optional[bool] = None
    first_visit_bonus_points: Optional[int] = None
    # Off-Peak Hours Bonus
    off_peak_bonus_enabled: Optional[bool] = None
    off_peak_start_time: Optional[str] = None
    off_peak_end_time: Optional[str] = None
    off_peak_bonus_type: Optional[str] = None
    off_peak_bonus_value: Optional[float] = None
    # Feedback/Review Bonus
    feedback_bonus_enabled: Optional[bool] = None
    feedback_bonus_points: Optional[int] = None

# Feedback Models
class FeedbackCreate(BaseModel):
    customer_id: Optional[str] = None
    customer_name: str
    customer_phone: str
    rating: int = Field(..., ge=1, le=5)
    message: Optional[str] = None

class Feedback(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    customer_id: Optional[str] = None
    customer_name: str
    customer_phone: str
    rating: int
    message: Optional[str] = None
    status: str = "pending"  # pending, resolved
    created_at: str

# Analytics Models
class DashboardStats(BaseModel):
    total_customers: int
    total_points_issued: int
    total_points_redeemed: int
    active_customers_30d: int
    new_customers_7d: int
    avg_rating: float
    total_feedback: int

# ============ HELPERS ============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def generate_api_key() -> str:
    """Generate a secure API key for POS integration"""
    import secrets
    return f"dp_live_{secrets.token_urlsafe(32)}"

async def verify_api_key(api_key: str):
    """Verify API key and return user"""
    user = await db.users.find_one({"api_key": api_key}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def calculate_tier(total_points: int, settings: dict) -> str:
    if total_points >= settings.get('tier_platinum_min', 5000):
        return "Platinum"
    elif total_points >= settings.get('tier_gold_min', 1500):
        return "Gold"
    elif total_points >= settings.get('tier_silver_min', 500):
        return "Silver"
    return "Bronze"

def get_earn_percent_for_tier(tier: str, settings: dict) -> float:
    """Get earning percentage based on customer tier"""
    tier_percents = {
        "Bronze": settings.get('bronze_earn_percent', 5.0),
        "Silver": settings.get('silver_earn_percent', 7.0),
        "Gold": settings.get('gold_earn_percent', 10.0),
        "Platinum": settings.get('platinum_earn_percent', 15.0)
    }
    return tier_percents.get(tier, 5.0)

def generate_qr_code(data: str) -> str:
    """Generate QR code as base64 string"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()

def check_birthday_bonus(customer: dict, settings: dict) -> tuple[bool, int, str]:
    """Check if customer is eligible for birthday bonus"""
    if not settings.get('birthday_bonus_enabled', False):
        return False, 0, ""
    
    if not customer.get('dob'):
        return False, 0, ""
    
    try:
        dob_str = customer['dob']
        dob = datetime.fromisoformat(dob_str.replace('Z', '+00:00'))
        today = datetime.now(timezone.utc)
        
        # Create birthday for this year
        birthday_this_year = dob.replace(year=today.year)
        
        # Check if within bonus window
        days_before = settings.get('birthday_bonus_days_before', 0)
        days_after = settings.get('birthday_bonus_days_after', 7)
        
        start_date = birthday_this_year - timedelta(days=days_before)
        end_date = birthday_this_year + timedelta(days=days_after)
        
        if start_date <= today <= end_date:
            bonus_points = settings.get('birthday_bonus_points', 100)
            return True, bonus_points, f"Birthday bonus! Happy Birthday 🎂"
    except Exception as e:
        pass
    
    return False, 0, ""

def check_anniversary_bonus(customer: dict, settings: dict) -> tuple[bool, int, str]:
    """Check if customer is eligible for anniversary bonus"""
    if not settings.get('anniversary_bonus_enabled', False):
        return False, 0, ""
    
    if not customer.get('anniversary'):
        return False, 0, ""
    
    try:
        anniversary = datetime.fromisoformat(customer['anniversary'].replace('Z', '+00:00'))
        today = datetime.now(timezone.utc)
        
        # Create anniversary for this year
        anniversary_this_year = anniversary.replace(year=today.year)
        
        # Check if within bonus window
        days_before = settings.get('anniversary_bonus_days_before', 0)
        days_after = settings.get('anniversary_bonus_days_after', 7)
        
        start_date = anniversary_this_year - timedelta(days=days_before)
        end_date = anniversary_this_year + timedelta(days=days_after)
        
        if start_date <= today <= end_date:
            bonus_points = settings.get('anniversary_bonus_points', 150)
            return True, bonus_points, f"Anniversary bonus! Happy Anniversary 🎉"
    except:
        pass
    
    return False, 0, ""

def check_first_visit_bonus(customer: dict, settings: dict) -> tuple[bool, int, str]:
    """Check if customer is eligible for first visit bonus"""
    if not settings.get('first_visit_bonus_enabled', False):
        return False, 0, ""
    
    # First visit means total_visits is currently 0 (before incrementing)
    if customer.get('total_visits', 0) == 0:
        bonus_points = settings.get('first_visit_bonus_points', 50)
        return True, bonus_points, "Welcome bonus! Thanks for your first visit 🎁"
    
    return False, 0, ""

def check_off_peak_bonus(settings: dict) -> tuple[bool, float, str, str]:
    """Check if current time is in off-peak hours and return bonus multiplier or flat amount"""
    if not settings.get('off_peak_bonus_enabled', False):
        return False, 1.0, "multiplier", ""
    
    try:
        now = datetime.now(timezone.utc)
        # Convert to local time (assuming IST for Indian restaurants)
        # You can make timezone configurable too
        local_time = now + timedelta(hours=5, minutes=30)  # IST offset
        current_time = local_time.strftime("%H:%M")
        
        start_time = settings.get('off_peak_start_time', '14:00')
        end_time = settings.get('off_peak_end_time', '17:00')
        
        if start_time <= current_time <= end_time:
            bonus_type = settings.get('off_peak_bonus_type', 'multiplier')
            bonus_value = settings.get('off_peak_bonus_value', 2.0)
            
            if bonus_type == 'multiplier':
                message = f"Off-peak hours bonus! {bonus_value}x points ⏰"
            else:
                message = f"Off-peak hours bonus! +{int(bonus_value)} points ⏰"
            
            return True, bonus_value, bonus_type, message
    except:
        pass
    
    return False, 1.0, "multiplier", ""

# ============ AUTH ROUTES ============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    # Check if email exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    api_key = generate_api_key()  # Generate API key for POS integration
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "restaurant_name": user_data.restaurant_name,
        "phone": user_data.phone,
        "password_hash": hash_password(user_data.password),
        "api_key": api_key,  # Store API key for POS
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

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            restaurant_name=user["restaurant_name"],
            phone=user["phone"],
            created_at=user["created_at"]
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        email=user["email"],
        restaurant_name=user["restaurant_name"],
        phone=user["phone"],
        created_at=user["created_at"]
    )

# ============ CUSTOMER ROUTES ============

@api_router.post("/customers", response_model=Customer)
async def create_customer(customer_data: CustomerCreate, user: dict = Depends(get_current_user)):
    # Check if phone exists for this user
    existing = await db.customers.find_one({"user_id": user["id"], "phone": customer_data.phone})
    if existing:
        raise HTTPException(status_code=400, detail="Customer with this phone already exists")
    
    customer_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    customer_doc = {
        "id": customer_id,
        "user_id": user["id"],
        "name": customer_data.name,
        "phone": customer_data.phone,
        "country_code": customer_data.country_code,
        "email": customer_data.email,
        "notes": customer_data.notes,
        "dob": customer_data.dob,
        "anniversary": customer_data.anniversary,
        "customer_type": customer_data.customer_type,
        "gst_name": customer_data.gst_name,
        "gst_number": customer_data.gst_number,
        "address": customer_data.address,
        "city": customer_data.city,
        "pincode": customer_data.pincode,
        "allergies": customer_data.allergies or [],
        "custom_field_1": customer_data.custom_field_1,
        "custom_field_2": customer_data.custom_field_2,
        "custom_field_3": customer_data.custom_field_3,
        "favorites": customer_data.favorites or [],
        "total_points": 0,
        "wallet_balance": 0.0,
        "total_visits": 0,
        "total_spent": 0.0,
        "tier": "Bronze",
        "created_at": now,
        "last_visit": None
    }
    
    await db.customers.insert_one(customer_doc)
    return Customer(**customer_doc)

@api_router.get("/customers", response_model=List[Customer])
async def list_customers(
    search: Optional[str] = None,
    tier: Optional[str] = None,
    customer_type: Optional[str] = None,
    has_allergies: Optional[bool] = None,
    last_visit_days: Optional[int] = None,  # Customers who haven't visited in X days
    favorite: Optional[str] = None,  # Filter by favorite item
    city: Optional[str] = None,
    sort_by: str = "created_at",  # created_at, last_visit, total_spent, total_points
    sort_order: str = "desc",  # asc or desc
    limit: int = 100,
    skip: int = 0,
    user: dict = Depends(get_current_user)
):
    query = {"user_id": user["id"]}
    and_conditions = []
    
    if search:
        and_conditions.append({
            "$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"phone": {"$regex": search, "$options": "i"}}
            ]
        })
    
    if tier:
        query["tier"] = tier
    
    if customer_type:
        query["customer_type"] = customer_type
    
    if has_allergies:
        query["allergies"] = {"$exists": True, "$ne": []}
    
    if last_visit_days:
        # Find customers who haven't visited in X days (for win-back campaigns)
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=last_visit_days)).isoformat()
        # Find customers with either no visit or last visit before cutoff date
        and_conditions.append({
            "$or": [
                {"last_visit": {"$lt": cutoff_date}},
                {"last_visit": None}
            ]
        })
    
    if favorite:
        query["favorites"] = {"$in": [favorite]}
    
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    
    # Combine $and conditions if any
    if and_conditions:
        query["$and"] = and_conditions
    
    # Sorting
    sort_direction = -1 if sort_order == "desc" else 1
    sort_field = sort_by if sort_by in ["created_at", "last_visit", "total_spent", "total_points", "name"] else "created_at"
    
    customers = await db.customers.find(query, {"_id": 0}).sort(sort_field, sort_direction).skip(skip).limit(limit).to_list(limit)
    return [Customer(**c) for c in customers]

# Endpoint to get customer segments for campaigns
@api_router.get("/customers/segments/stats")
async def get_customer_segments(user: dict = Depends(get_current_user)):
    """Get customer segment statistics for campaign targeting"""
    user_id = user["id"]
    
    # Total customers
    total = await db.customers.count_documents({"user_id": user_id})
    
    # By tier
    tier_stats = {}
    for tier in ["Bronze", "Silver", "Gold", "Platinum"]:
        tier_stats[tier.lower()] = await db.customers.count_documents({"user_id": user_id, "tier": tier})
    
    # By customer type
    normal_count = await db.customers.count_documents({"user_id": user_id, "customer_type": "normal"})
    corporate_count = await db.customers.count_documents({"user_id": user_id, "customer_type": "corporate"})
    
    # Inactive customers (no visit in 30 days)
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    inactive_30d = await db.customers.count_documents({
        "user_id": user_id,
        "$or": [
            {"last_visit": {"$lt": thirty_days_ago}},
            {"last_visit": None}
        ]
    })
    
    # Inactive customers (no visit in 60 days)
    sixty_days_ago = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    inactive_60d = await db.customers.count_documents({
        "user_id": user_id,
        "$or": [
            {"last_visit": {"$lt": sixty_days_ago}},
            {"last_visit": None}
        ]
    })
    
    # Customers with allergies
    with_allergies = await db.customers.count_documents({
        "user_id": user_id,
        "allergies": {"$exists": True, "$ne": []}
    })
    
    # Get unique cities
    cities_pipeline = [
        {"$match": {"user_id": user_id, "city": {"$exists": True, "$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$city", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    cities = await db.customers.aggregate(cities_pipeline).to_list(10)
    
    # Get common favorites
    favorites_pipeline = [
        {"$match": {"user_id": user_id, "favorites": {"$exists": True, "$ne": []}}},
        {"$unwind": "$favorites"},
        {"$group": {"_id": "$favorites", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_favorites = await db.customers.aggregate(favorites_pipeline).to_list(10)
    
    return {
        "total": total,
        "by_tier": tier_stats,
        "by_type": {"normal": normal_count, "corporate": corporate_count},
        "inactive_30_days": inactive_30d,
        "inactive_60_days": inactive_60d,
        "with_allergies": with_allergies,
        "top_cities": [{"city": c["_id"], "count": c["count"]} for c in cities],
        "top_favorites": [{"item": f["_id"], "count": f["count"]} for f in top_favorites]
    }

@api_router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str, user: dict = Depends(get_current_user)):
    customer = await db.customers.find_one({"id": customer_id, "user_id": user["id"]}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return Customer(**customer)

@api_router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, update_data: CustomerUpdate, user: dict = Depends(get_current_user)):
    customer = await db.customers.find_one({"id": customer_id, "user_id": user["id"]})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    # Check phone uniqueness if phone is being updated
    if "phone" in update_dict and update_dict["phone"] != customer.get("phone"):
        existing = await db.customers.find_one({
            "user_id": user["id"], 
            "phone": update_dict["phone"],
            "id": {"$ne": customer_id}  # Exclude current customer
        })
        if existing:
            raise HTTPException(status_code=400, detail="Another customer with this phone already exists")
    
    if update_dict:
        await db.customers.update_one({"id": customer_id}, {"$set": update_dict})
    
    updated = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    return Customer(**updated)

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str, user: dict = Depends(get_current_user)):
    result = await db.customers.delete_one({"id": customer_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Also delete related transactions
    await db.points_transactions.delete_many({"customer_id": customer_id})
    return {"message": "Customer deleted"}

# ============ SEGMENTS ROUTES ============

@api_router.post("/segments", response_model=Segment)
async def create_segment(segment_data: SegmentCreate, user: dict = Depends(get_current_user)):
    """Create a new customer segment with filters"""
    segment_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Count customers matching filters
    customer_count = await count_customers_by_filters(user["id"], segment_data.filters)
    
    segment_doc = {
        "id": segment_id,
        "user_id": user["id"],
        "name": segment_data.name,
        "filters": segment_data.filters,
        "customer_count": customer_count,
        "created_at": now,
        "updated_at": now
    }
    
    await db.segments.insert_one(segment_doc)
    return Segment(**segment_doc)

@api_router.get("/segments", response_model=List[Segment])
async def list_segments(user: dict = Depends(get_current_user)):
    """List all segments for the current user"""
    segments = await db.segments.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    
    # Update customer counts for each segment
    for segment in segments:
        count = await count_customers_by_filters(user["id"], segment["filters"])
        segment["customer_count"] = count
        # Update in database
        await db.segments.update_one(
            {"id": segment["id"]},
            {"$set": {"customer_count": count}}
        )
    
    return [Segment(**s) for s in segments]

@api_router.get("/segments/{segment_id}", response_model=Segment)
async def get_segment(segment_id: str, user: dict = Depends(get_current_user)):
    """Get a specific segment"""
    segment = await db.segments.find_one({"id": segment_id, "user_id": user["id"]}, {"_id": 0})
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    # Update customer count
    count = await count_customers_by_filters(user["id"], segment["filters"])
    segment["customer_count"] = count
    
    return Segment(**segment)

@api_router.get("/segments/{segment_id}/customers", response_model=List[Customer])
async def get_segment_customers(segment_id: str, user: dict = Depends(get_current_user)):
    """Get all customers in a segment"""
    segment = await db.segments.find_one({"id": segment_id, "user_id": user["id"]}, {"_id": 0})
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    # Build MongoDB query from filters
    query = build_customer_query(user["id"], segment["filters"])
    customers = await db.customers.find(query, {"_id": 0}).to_list(1000)
    
    return [Customer(**c) for c in customers]

@api_router.put("/segments/{segment_id}", response_model=Segment)
async def update_segment(segment_id: str, update_data: SegmentUpdate, user: dict = Depends(get_current_user)):
    """Update a segment"""
    segment = await db.segments.find_one({"id": segment_id, "user_id": user["id"]})
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if update_dict:
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # If filters changed, recalculate customer count
        if "filters" in update_dict:
            count = await count_customers_by_filters(user["id"], update_dict["filters"])
            update_dict["customer_count"] = count
        
        await db.segments.update_one({"id": segment_id}, {"$set": update_dict})
    
    updated_segment = await db.segments.find_one({"id": segment_id}, {"_id": 0})
    return Segment(**updated_segment)

@api_router.delete("/segments/{segment_id}")
async def delete_segment(segment_id: str, user: dict = Depends(get_current_user)):
    """Delete a segment"""
    result = await db.segments.delete_one({"id": segment_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Segment not found")
    return {"message": "Segment deleted"}

# Helper function to count customers by filters
async def count_customers_by_filters(user_id: str, filters: dict) -> int:
    """Count customers matching the given filters"""
    query = build_customer_query(user_id, filters)
    return await db.customers.count_documents(query)

# Helper function to build MongoDB query from filters
def build_customer_query(user_id: str, filters: dict) -> dict:
    """Build MongoDB query from filter dictionary"""
    query = {"user_id": user_id}
    
    # Tier filter
    if filters.get("tier"):
        query["tier"] = {"$in": filters["tier"]} if isinstance(filters["tier"], list) else filters["tier"]
    
    # City filter
    if filters.get("city"):
        query["city"] = {"$in": filters["city"]} if isinstance(filters["city"], list) else filters["city"]
    
    # Points range
    if filters.get("points_min") is not None:
        query["total_points"] = query.get("total_points", {})
        query["total_points"]["$gte"] = filters["points_min"]
    if filters.get("points_max") is not None:
        query["total_points"] = query.get("total_points", {})
        query["total_points"]["$lte"] = filters["points_max"]
    
    # Visits range
    if filters.get("visits_min") is not None:
        query["total_visits"] = query.get("total_visits", {})
        query["total_visits"]["$gte"] = filters["visits_min"]
    if filters.get("visits_max") is not None:
        query["total_visits"] = query.get("total_visits", {})
        query["total_visits"]["$lte"] = filters["visits_max"]
    
    # Spent range
    if filters.get("spent_min") is not None:
        query["total_spent"] = query.get("total_spent", {})
        query["total_spent"]["$gte"] = filters["spent_min"]
    if filters.get("spent_max") is not None:
        query["total_spent"] = query.get("total_spent", {})
        query["total_spent"]["$lte"] = filters["spent_max"]
    
    # Dietary preference
    if filters.get("dietary"):
        query["dietary"] = {"$in": filters["dietary"]} if isinstance(filters["dietary"], list) else filters["dietary"]
    
    # Allergies
    if filters.get("allergies"):
        query["allergies"] = {"$in": filters["allergies"]} if isinstance(filters["allergies"], list) else filters["allergies"]
    
    # Favorite food
    if filters.get("favorite_food"):
        query["favorite_food"] = {"$regex": filters["favorite_food"], "$options": "i"}
    
    # Search by name or phone
    if filters.get("search"):
        search_regex = {"$regex": filters["search"], "$options": "i"}
        query["$or"] = [
            {"name": search_regex},
            {"phone": search_regex},
            {"email": search_regex}
        ]
    
    return query

# ============ POINTS ROUTES ============

@api_router.post("/points/transaction", response_model=PointsTransaction)
async def create_points_transaction(tx_data: PointsTransactionCreate, user: dict = Depends(get_current_user)):
    customer = await db.customers.find_one({"id": tx_data.customer_id, "user_id": user["id"]})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    settings = await db.loyalty_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    if not settings:
        settings = {"tier_bronze_min": 0, "tier_silver_min": 500, "tier_gold_min": 1500, "tier_platinum_min": 5000}
    
    current_points = customer.get("total_points", 0)
    
    if tx_data.transaction_type == "redeem":
        if current_points < tx_data.points:
            raise HTTPException(status_code=400, detail="Insufficient points")
        new_balance = current_points - tx_data.points
    else:
        new_balance = current_points + tx_data.points
    
    # Calculate new tier
    new_tier = calculate_tier(new_balance, settings)
    
    # Update customer
    update_data = {
        "total_points": new_balance,
        "tier": new_tier,
        "last_visit": datetime.now(timezone.utc).isoformat()
    }
    
    if tx_data.transaction_type == "earn" and tx_data.bill_amount:
        update_data["total_spent"] = customer.get("total_spent", 0) + tx_data.bill_amount
        update_data["total_visits"] = customer.get("total_visits", 0) + 1
    
    await db.customers.update_one({"id": tx_data.customer_id}, {"$set": update_data})
    
    # Create transaction record
    tx_id = str(uuid.uuid4())
    tx_doc = {
        "id": tx_id,
        "user_id": user["id"],
        "customer_id": tx_data.customer_id,
        "points": tx_data.points,
        "transaction_type": tx_data.transaction_type,
        "description": tx_data.description,
        "bill_amount": tx_data.bill_amount,
        "balance_after": new_balance,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.points_transactions.insert_one(tx_doc)
    return PointsTransaction(**tx_doc)

@api_router.get("/points/transactions/{customer_id}", response_model=List[PointsTransaction])
async def get_customer_transactions(customer_id: str, limit: int = 50, user: dict = Depends(get_current_user)):
    transactions = await db.points_transactions.find(
        {"customer_id": customer_id, "user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return [PointsTransaction(**t) for t in transactions]

@api_router.post("/points/earn")
async def earn_points(customer_id: str, bill_amount: float, user: dict = Depends(get_current_user)):
    """Quick endpoint to earn points based on bill amount and tier"""
    customer = await db.customers.find_one({"id": customer_id, "user_id": user["id"]})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    settings = await db.loyalty_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    if not settings:
        settings = {
            "min_order_value": 100.0,
            "bronze_earn_percent": 5.0,
            "silver_earn_percent": 7.0,
            "gold_earn_percent": 10.0,
            "platinum_earn_percent": 15.0
        }
    
    # Check minimum order value
    min_order = settings.get("min_order_value", 100.0)
    if bill_amount < min_order:
        raise HTTPException(status_code=400, detail=f"Minimum order value is ₹{min_order}")
    
    # Get earning percentage based on customer tier
    customer_tier = customer.get("tier", "Bronze")
    earn_percent = get_earn_percent_for_tier(customer_tier, settings)
    
    # Calculate points as percentage of bill
    points_earned = int(bill_amount * earn_percent / 100)
    
    tx_data = PointsTransactionCreate(
        customer_id=customer_id,
        points=points_earned,
        transaction_type="earn",
        description=f"Earned {earn_percent}% on bill of ₹{bill_amount}",
        bill_amount=bill_amount
    )
    
    return await create_points_transaction(tx_data, user)

# ============ LOYALTY SETTINGS ROUTES ============

@api_router.get("/loyalty/settings", response_model=LoyaltySettings)
async def get_loyalty_settings(user: dict = Depends(get_current_user)):
    settings = await db.loyalty_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    if not settings:
        # Create default settings
        settings = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "min_order_value": 100.0,
            "bronze_earn_percent": 5.0,
            "silver_earn_percent": 7.0,
            "gold_earn_percent": 10.0,
            "platinum_earn_percent": 15.0,
            "redemption_value": 1.0,
            "min_redemption_points": 50,
            "max_redemption_percent": 50.0,
            "max_redemption_amount": 500.0,
            "points_expiry_months": 6,
            "expiry_reminder_days": 30,
            "tier_silver_min": 500,
            "tier_gold_min": 1500,
            "tier_platinum_min": 5000,
            "custom_field_1_label": "Custom Field 1",
            "custom_field_2_label": "Custom Field 2",
            "custom_field_3_label": "Custom Field 3",
            "custom_field_1_enabled": False,
            "custom_field_2_enabled": False,
            "custom_field_3_enabled": False
        }
        await db.loyalty_settings.insert_one(settings)
    return LoyaltySettings(**settings)

@api_router.put("/loyalty/settings", response_model=LoyaltySettings)
async def update_loyalty_settings(update_data: LoyaltySettingsUpdate, user: dict = Depends(get_current_user)):
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if update_dict:
        await db.loyalty_settings.update_one({"user_id": user["id"]}, {"$set": update_dict})
    
    settings = await db.loyalty_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    return LoyaltySettings(**settings)

@api_router.get("/points/expiring/{customer_id}")
async def get_expiring_points(customer_id: str, user: dict = Depends(get_current_user)):
    """Get points that are expiring soon for a customer"""
    customer = await db.customers.find_one({"id": customer_id, "user_id": user["id"]})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    settings = await db.loyalty_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    expiry_months = settings.get("points_expiry_months", 6) if settings else 6
    reminder_days = settings.get("expiry_reminder_days", 30) if settings else 30
    
    if expiry_months == 0:
        return {"expiring_soon": 0, "expiring_date": None, "already_expired": 0}
    
    now = datetime.now(timezone.utc)
    expiry_cutoff = now - timedelta(days=expiry_months * 30)
    reminder_cutoff = now - timedelta(days=(expiry_months * 30) - reminder_days)
    
    # Get all earn transactions for this customer
    transactions = await db.points_transactions.find({
        "customer_id": customer_id,
        "user_id": user["id"],
        "transaction_type": {"$in": ["earn", "bonus"]}
    }, {"_id": 0}).to_list(1000)
    
    expiring_soon = 0
    already_expired = 0
    earliest_expiry = None
    
    for tx in transactions:
        tx_date = datetime.fromisoformat(tx["created_at"].replace("Z", "+00:00")) if isinstance(tx["created_at"], str) else tx["created_at"]
        
        if tx_date < expiry_cutoff:
            already_expired += tx["points"]
        elif tx_date < reminder_cutoff:
            expiring_soon += tx["points"]
            expiry_date = tx_date + timedelta(days=expiry_months * 30)
            if earliest_expiry is None or expiry_date < earliest_expiry:
                earliest_expiry = expiry_date
    
    return {
        "expiring_soon": max(0, expiring_soon),
        "expiring_date": earliest_expiry.isoformat() if earliest_expiry else None,
        "already_expired": max(0, already_expired),
        "expiry_months": expiry_months
    }

@api_router.post("/points/expire")
async def expire_old_points(user: dict = Depends(get_current_user)):
    """Expire old points for all customers (run periodically)"""
    settings = await db.loyalty_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    expiry_months = settings.get("points_expiry_months", 6) if settings else 6
    
    if expiry_months == 0:
        return {"message": "Points expiry is disabled", "expired_count": 0}
    
    now = datetime.now(timezone.utc)
    expiry_cutoff = (now - timedelta(days=expiry_months * 30)).isoformat()
    
    # Find all customers with points
    customers = await db.customers.find({"user_id": user["id"], "total_points": {"$gt": 0}}, {"_id": 0}).to_list(1000)
    
    total_expired = 0
    customers_affected = 0
    
    for customer in customers:
        # Calculate points to expire based on old earn transactions
        old_transactions = await db.points_transactions.find({
            "customer_id": customer["id"],
            "user_id": user["id"],
            "transaction_type": {"$in": ["earn", "bonus"]},
            "created_at": {"$lt": expiry_cutoff}
        }, {"_id": 0}).to_list(1000)
        
        points_to_expire = sum(tx["points"] for tx in old_transactions)
        
        if points_to_expire > 0:
            # Don't expire more than current balance
            points_to_expire = min(points_to_expire, customer["total_points"])
            
            if points_to_expire > 0:
                # Create expiry transaction
                tx_doc = {
                    "id": str(uuid.uuid4()),
                    "user_id": user["id"],
                    "customer_id": customer["id"],
                    "points": points_to_expire,
                    "transaction_type": "expired",
                    "description": f"Points expired (older than {expiry_months} months)",
                    "bill_amount": None,
                    "balance_after": customer["total_points"] - points_to_expire,
                    "created_at": now.isoformat()
                }
                await db.points_transactions.insert_one(tx_doc)
                
                # Update customer points
                await db.customers.update_one(
                    {"id": customer["id"]},
                    {"$inc": {"total_points": -points_to_expire}}
                )
                
                total_expired += points_to_expire
                customers_affected += 1
    
    return {
        "message": f"Expired {total_expired} points from {customers_affected} customers",
        "total_expired": total_expired,
        "customers_affected": customers_affected
    }

# ============ QR CODE ROUTES ============

@api_router.get("/qr/generate")
async def generate_customer_qr(user: dict = Depends(get_current_user)):
    """Generate QR code for customer registration"""
    frontend_url = os.environ.get('FRONTEND_URL', 'https://cmv2-crm-dev.preview.emergentagent.com')
    registration_url = f"{frontend_url}/register-customer/{user['id']}"
    
    qr_base64 = generate_qr_code(registration_url)
    
    return {
        "qr_code": f"data:image/png;base64,{qr_base64}",
        "registration_url": registration_url,
        "restaurant_name": user["restaurant_name"]
    }

@api_router.post("/qr/register/{restaurant_id}")
async def register_via_qr(restaurant_id: str, customer_data: CustomerCreate):
    """Register customer via QR code (no auth required)"""
    user = await db.users.find_one({"id": restaurant_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Check if phone exists
    existing = await db.customers.find_one({"user_id": restaurant_id, "phone": customer_data.phone})
    if existing:
        raise HTTPException(status_code=400, detail="Customer already registered")
    
    customer_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    customer_doc = {
        "id": customer_id,
        "user_id": restaurant_id,
        "name": customer_data.name,
        "phone": customer_data.phone,
        "country_code": customer_data.country_code,
        "email": customer_data.email,
        "notes": customer_data.notes,
        "dob": customer_data.dob,
        "anniversary": customer_data.anniversary,
        "customer_type": customer_data.customer_type,
        "gst_name": customer_data.gst_name,
        "gst_number": customer_data.gst_number,
        "address": customer_data.address,
        "city": customer_data.city,
        "pincode": customer_data.pincode,
        "allergies": customer_data.allergies or [],
        "custom_field_1": customer_data.custom_field_1,
        "custom_field_2": customer_data.custom_field_2,
        "custom_field_3": customer_data.custom_field_3,
        "favorites": customer_data.favorites or [],
        "total_points": 0,
        "wallet_balance": 0.0,
        "total_visits": 0,
        "total_spent": 0.0,
        "tier": "Bronze",
        "created_at": now,
        "last_visit": None
    }
    
    await db.customers.insert_one(customer_doc)
    return {"message": "Registration successful", "customer_id": customer_id}

# ============ WALLET ROUTES ============

@api_router.post("/wallet/transaction", response_model=WalletTransaction)
async def create_wallet_transaction(tx_data: WalletTransactionCreate, user: dict = Depends(get_current_user)):
    customer = await db.customers.find_one({"id": tx_data.customer_id, "user_id": user["id"]})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    current_balance = customer.get("wallet_balance", 0.0)
    
    if tx_data.transaction_type == "debit":
        if current_balance < tx_data.amount:
            raise HTTPException(status_code=400, detail="Insufficient wallet balance")
        new_balance = current_balance - tx_data.amount
    else:  # credit
        new_balance = current_balance + tx_data.amount
    
    # Update customer wallet balance
    await db.customers.update_one(
        {"id": tx_data.customer_id},
        {"$set": {"wallet_balance": new_balance}}
    )
    
    # Create transaction record
    tx_id = str(uuid.uuid4())
    tx_doc = {
        "id": tx_id,
        "user_id": user["id"],
        "customer_id": tx_data.customer_id,
        "amount": tx_data.amount,
        "transaction_type": tx_data.transaction_type,
        "description": tx_data.description,
        "payment_method": tx_data.payment_method,
        "balance_after": new_balance,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.wallet_transactions.insert_one(tx_doc)
    return WalletTransaction(**tx_doc)

@api_router.get("/wallet/transactions/{customer_id}", response_model=List[WalletTransaction])
async def get_wallet_transactions(customer_id: str, limit: int = 50, user: dict = Depends(get_current_user)):
    transactions = await db.wallet_transactions.find(
        {"customer_id": customer_id, "user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return [WalletTransaction(**t) for t in transactions]

@api_router.get("/wallet/balance/{customer_id}")
async def get_wallet_balance(customer_id: str, user: dict = Depends(get_current_user)):
    customer = await db.customers.find_one({"id": customer_id, "user_id": user["id"]}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"balance": customer.get("wallet_balance", 0.0)}

# ============ COUPON ROUTES ============

@api_router.post("/coupons", response_model=Coupon)
async def create_coupon(coupon_data: CouponCreate, user: dict = Depends(get_current_user)):
    """Create a new coupon"""
    # Check if code already exists
    existing = await db.coupons.find_one({"user_id": user["id"], "code": coupon_data.code.upper()})
    if existing:
        raise HTTPException(status_code=400, detail="Coupon code already exists")
    
    coupon_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    coupon_doc = {
        "id": coupon_id,
        "user_id": user["id"],
        "code": coupon_data.code.upper(),
        "discount_type": coupon_data.discount_type,
        "discount_value": coupon_data.discount_value,
        "start_date": coupon_data.start_date,
        "end_date": coupon_data.end_date,
        "usage_limit": coupon_data.usage_limit,
        "per_user_limit": coupon_data.per_user_limit,
        "min_order_value": coupon_data.min_order_value,
        "max_discount": coupon_data.max_discount,
        "specific_users": coupon_data.specific_users,
        "applicable_channels": coupon_data.applicable_channels,
        "description": coupon_data.description,
        "is_active": True,
        "total_used": 0,
        "created_at": now
    }
    
    await db.coupons.insert_one(coupon_doc)
    return Coupon(**coupon_doc)

@api_router.get("/coupons", response_model=List[Coupon])
async def list_coupons(
    active_only: bool = False,
    user: dict = Depends(get_current_user)
):
    """List all coupons"""
    query = {"user_id": user["id"]}
    if active_only:
        query["is_active"] = True
    
    coupons = await db.coupons.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return [Coupon(**c) for c in coupons]

@api_router.get("/coupons/{coupon_id}", response_model=Coupon)
async def get_coupon(coupon_id: str, user: dict = Depends(get_current_user)):
    """Get a specific coupon"""
    coupon = await db.coupons.find_one({"id": coupon_id, "user_id": user["id"]}, {"_id": 0})
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return Coupon(**coupon)

@api_router.put("/coupons/{coupon_id}", response_model=Coupon)
async def update_coupon(coupon_id: str, coupon_data: CouponUpdate, user: dict = Depends(get_current_user)):
    """Update a coupon"""
    coupon = await db.coupons.find_one({"id": coupon_id, "user_id": user["id"]})
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    update_data = {k: v for k, v in coupon_data.model_dump().items() if v is not None}
    if "code" in update_data:
        update_data["code"] = update_data["code"].upper()
        # Check if new code conflicts with another coupon
        existing = await db.coupons.find_one({
            "user_id": user["id"], 
            "code": update_data["code"],
            "id": {"$ne": coupon_id}
        })
        if existing:
            raise HTTPException(status_code=400, detail="Coupon code already exists")
    
    if update_data:
        await db.coupons.update_one({"id": coupon_id}, {"$set": update_data})
    
    updated = await db.coupons.find_one({"id": coupon_id}, {"_id": 0})
    return Coupon(**updated)

@api_router.delete("/coupons/{coupon_id}")
async def delete_coupon(coupon_id: str, user: dict = Depends(get_current_user)):
    """Delete a coupon"""
    result = await db.coupons.delete_one({"id": coupon_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Coupon not found")
    # Also delete usage records
    await db.coupon_usage.delete_many({"coupon_id": coupon_id})
    return {"message": "Coupon deleted"}

@api_router.post("/coupons/{coupon_id}/toggle")
async def toggle_coupon(coupon_id: str, user: dict = Depends(get_current_user)):
    """Toggle coupon active status"""
    coupon = await db.coupons.find_one({"id": coupon_id, "user_id": user["id"]})
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    new_status = not coupon.get("is_active", True)
    await db.coupons.update_one({"id": coupon_id}, {"$set": {"is_active": new_status}})
    return {"is_active": new_status}

@api_router.post("/coupons/validate")
async def validate_coupon(
    code: str,
    customer_id: str,
    order_value: float,
    channel: str,
    user: dict = Depends(get_current_user)
):
    """Validate if a coupon can be applied"""
    coupon = await db.coupons.find_one({
        "user_id": user["id"],
        "code": code.upper(),
        "is_active": True
    }, {"_id": 0})
    
    if not coupon:
        raise HTTPException(status_code=404, detail="Invalid coupon code")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Check date validity
    if coupon["start_date"] > now:
        raise HTTPException(status_code=400, detail="Coupon not yet active")
    if coupon["end_date"] < now:
        raise HTTPException(status_code=400, detail="Coupon has expired")
    
    # Check usage limit
    if coupon.get("usage_limit") and coupon.get("total_used", 0) >= coupon["usage_limit"]:
        raise HTTPException(status_code=400, detail="Coupon usage limit reached")
    
    # Check per user limit
    user_usage = await db.coupon_usage.count_documents({
        "coupon_id": coupon["id"],
        "customer_id": customer_id
    })
    if user_usage >= coupon.get("per_user_limit", 1):
        raise HTTPException(status_code=400, detail="You have already used this coupon")
    
    # Check minimum order value
    if order_value < coupon.get("min_order_value", 0):
        raise HTTPException(
            status_code=400, 
            detail=f"Minimum order value is ₹{coupon['min_order_value']}"
        )
    
    # Check channel
    if channel not in coupon.get("applicable_channels", []):
        raise HTTPException(status_code=400, detail="Coupon not valid for this order type")
    
    # Check specific users
    if coupon.get("specific_users") and customer_id not in coupon["specific_users"]:
        raise HTTPException(status_code=400, detail="Coupon not valid for this customer")
    
    # Calculate discount
    if coupon["discount_type"] == "percentage":
        discount = (order_value * coupon["discount_value"]) / 100
        if coupon.get("max_discount"):
            discount = min(discount, coupon["max_discount"])
    else:
        discount = min(coupon["discount_value"], order_value)
    
    return {
        "valid": True,
        "coupon": Coupon(**coupon),
        "discount": round(discount, 2),
        "final_amount": round(order_value - discount, 2)
    }

@api_router.post("/coupons/apply")
async def apply_coupon(
    code: str,
    customer_id: str,
    order_value: float,
    channel: str,
    user: dict = Depends(get_current_user)
):
    """Apply coupon and record usage"""
    # First validate
    validation = await validate_coupon(code, customer_id, order_value, channel, user)
    
    coupon = await db.coupons.find_one({"user_id": user["id"], "code": code.upper()})
    
    # Record usage
    usage_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    usage_doc = {
        "id": usage_id,
        "coupon_id": coupon["id"],
        "customer_id": customer_id,
        "order_value": order_value,
        "discount_applied": validation["discount"],
        "channel": channel,
        "used_at": now
    }
    
    await db.coupon_usage.insert_one(usage_doc)
    
    # Increment total used count
    await db.coupons.update_one(
        {"id": coupon["id"]},
        {"$inc": {"total_used": 1}}
    )
    
    return {
        "success": True,
        "discount": validation["discount"],
        "final_amount": validation["final_amount"],
        "usage_id": usage_id
    }

@api_router.get("/coupons/{coupon_id}/usage")
async def get_coupon_usage(coupon_id: str, user: dict = Depends(get_current_user)):
    """Get usage history for a coupon"""
    coupon = await db.coupons.find_one({"id": coupon_id, "user_id": user["id"]})
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    usage = await db.coupon_usage.find({"coupon_id": coupon_id}, {"_id": 0}).sort("used_at", -1).to_list(100)
    
    # Get customer names for each usage
    for u in usage:
        customer = await db.customers.find_one({"id": u["customer_id"]}, {"_id": 0, "name": 1, "phone": 1})
        if customer:
            u["customer_name"] = customer.get("name")
            u["customer_phone"] = customer.get("phone")
    
    return {
        "coupon": Coupon(**coupon),
        "usage": usage,
        "total_discount_given": sum(u["discount_applied"] for u in usage)
    }

# ============ FEEDBACK ROUTES ============

@api_router.post("/feedback", response_model=Feedback)
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
    
    # Award feedback bonus if enabled
    settings = await db.loyalty_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    if settings and settings.get("feedback_bonus_enabled", True):
        bonus_points = settings.get("feedback_bonus_points", 25)
        
        # Get customer to check if they already received feedback bonus
        customer = await db.customers.find_one({"id": feedback_data.customer_id}, {"_id": 0})
        
        if customer:
            # Check if customer already got feedback bonus (only once per customer)
            existing_bonus = await db.points_transactions.find_one({
                "customer_id": feedback_data.customer_id,
                "transaction_type": "bonus",
                "description": {"$regex": "Feedback bonus"}
            })
            
            if not existing_bonus:
                # Award bonus points
                new_balance = customer.get("total_points", 0) + bonus_points
                
                await db.customers.update_one(
                    {"id": customer["id"]},
                    {"$set": {"total_points": new_balance}}
                )
                
                # Create bonus transaction
                bonus_tx = {
                    "id": str(uuid.uuid4()),
                    "user_id": user["id"],
                    "customer_id": customer["id"],
                    "points": bonus_points,
                    "transaction_type": "bonus",
                    "description": f"Feedback bonus! Thanks for your review ⭐",
                    "bill_amount": None,
                    "balance_after": new_balance,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.points_transactions.insert_one(bonus_tx)
    
    return Feedback(**feedback_doc)

@api_router.get("/feedback", response_model=List[Feedback])
async def list_feedback(status: Optional[str] = None, limit: int = 100, user: dict = Depends(get_current_user)):
    query = {"user_id": user["id"]}
    if status:
        query["status"] = status
    
    feedback_list = await db.feedback.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return [Feedback(**f) for f in feedback_list]

@api_router.put("/feedback/{feedback_id}/resolve")
async def resolve_feedback(feedback_id: str, user: dict = Depends(get_current_user)):
    result = await db.feedback.update_one(
        {"id": feedback_id, "user_id": user["id"]},
        {"$set": {"status": "resolved"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return {"message": "Feedback resolved"}

# ============ ANALYTICS ROUTES ============

@api_router.get("/analytics/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    user_id = user["id"]
    
    # Total customers
    total_customers = await db.customers.count_documents({"user_id": user_id})
    
    # Points stats
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$transaction_type",
            "total": {"$sum": "$points"}
        }}
    ]
    points_stats = await db.points_transactions.aggregate(pipeline).to_list(10)
    
    total_earned = 0
    total_redeemed = 0
    for stat in points_stats:
        if stat["_id"] in ["earn", "bonus"]:
            total_earned += stat["total"]
        elif stat["_id"] == "redeem":
            total_redeemed += stat["total"]
    
    # Active customers (last 30 days)
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    active_customers = await db.customers.count_documents({
        "user_id": user_id,
        "last_visit": {"$gte": thirty_days_ago}
    })
    
    # New customers (last 7 days)
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    new_customers = await db.customers.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": seven_days_ago}
    })
    
    # Feedback stats
    total_feedback = await db.feedback.count_documents({"user_id": user_id})
    
    rating_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}}
    ]
    rating_result = await db.feedback.aggregate(rating_pipeline).to_list(1)
    avg_rating = rating_result[0]["avg_rating"] if rating_result else 0.0
    
    return DashboardStats(
        total_customers=total_customers,
        total_points_issued=total_earned,
        total_points_redeemed=total_redeemed,
        active_customers_30d=active_customers,
        new_customers_7d=new_customers,
        avg_rating=round(avg_rating, 1),
        total_feedback=total_feedback
    )

# ============ MESSAGING (MOCK) ============

class MessageRequest(BaseModel):
    customer_id: str
    message: str
    channel: str = "whatsapp"  # whatsapp, sms

@api_router.post("/messaging/send")
async def send_message(msg_data: MessageRequest, user: dict = Depends(get_current_user)):
    """Mock messaging endpoint - ready for real provider integration"""
    customer = await db.customers.find_one({"id": msg_data.customer_id, "user_id": user["id"]})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Log the message (mock implementation)
    message_log = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "customer_id": msg_data.customer_id,
        "customer_phone": customer["phone"],
        "message": msg_data.message,
        "channel": msg_data.channel,
        "status": "sent",  # Mock status
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.message_logs.insert_one(message_log)
    
    return {
        "message": "Message sent successfully (MOCK)",
        "log_id": message_log["id"],
        "note": "Real messaging provider integration pending"
    }

# ============ POS GATEWAY API ============

# POS Webhook Models
class POSPaymentWebhook(BaseModel):
    customer_phone: str  # Customer's phone number
    bill_amount: float  # Total bill amount
    channel: str = "dine_in"  # dine_in, takeaway, delivery
    coupon_code: Optional[str] = None  # Optional coupon to apply
    redeem_points: Optional[int] = None  # Optional points to redeem
    bill_id: Optional[str] = None  # POS bill reference ID
    metadata: Optional[dict] = None  # Additional POS metadata

class POSCustomerLookup(BaseModel):
    phone: str  # Customer phone to lookup

class POSResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

# API Key Authentication Dependency
async def verify_pos_api_key(api_key: str = Depends(lambda: None)):
    """Verify API key from header"""
    from fastapi import Header
    
    async def get_api_key(x_api_key: str = Header(None)):
        if not x_api_key:
            raise HTTPException(status_code=401, detail="API key required in X-API-Key header")
        
        user = await db.users.find_one({"api_key": x_api_key}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return user
    
    return get_api_key

@api_router.post("/pos/webhook/payment-received", response_model=POSResponse)
async def pos_payment_received(
    webhook_data: POSPaymentWebhook,
    x_api_key: str = Header(None)
):
    """
    POS Webhook: Called when payment is received
    
    This is the main integration endpoint for POS systems.
    
    Headers:
        X-API-Key: Restaurant's API key
    
    Request Body:
        customer_phone: Customer's phone number
        bill_amount: Total bill amount
        channel: Order channel (dine_in, takeaway, delivery)
        coupon_code: Optional coupon code to apply
        bill_id: Optional POS bill reference
        metadata: Optional additional data
    
    Response:
        success: Whether operation succeeded
        message: Human-readable message
        data: {
            customer: Customer details
            points_earned: Points awarded
            points_balance: New points balance
            wallet_deducted: Amount deducted from wallet (if any)
            coupon_discount: Discount from coupon (if any)
            final_amount: Final amount after all deductions
            tier: Customer's current tier
        }
    """
    # Verify API key
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    
    user = await db.users.find_one({"api_key": x_api_key}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Find customer by phone
    customer = await db.customers.find_one({
        "user_id": user["id"],
        "phone": webhook_data.customer_phone
    }, {"_id": 0})
    
    if not customer:
        return POSResponse(
            success=False,
            message=f"Customer with phone {webhook_data.customer_phone} not found. Please register first.",
            data=None
        )
    
    # Get loyalty settings
    settings = await db.loyalty_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    if not settings:
        settings = {
            "min_order_value": 100.0,
            "bronze_earn_percent": 5.0,
            "silver_earn_percent": 7.0,
            "gold_earn_percent": 10.0,
            "platinum_earn_percent": 15.0,
            "redemption_value": 0.25,
            "min_redemption_points": 100,
            "max_redemption_percent": 50.0,
            "max_redemption_amount": 500.0,
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
    else:
        # Ensure all new fields have defaults if missing
        settings.setdefault("birthday_bonus_enabled", True)
        settings.setdefault("birthday_bonus_points", 100)
        settings.setdefault("birthday_bonus_days_before", 0)
        settings.setdefault("birthday_bonus_days_after", 7)
        settings.setdefault("anniversary_bonus_enabled", True)
        settings.setdefault("anniversary_bonus_points", 150)
        settings.setdefault("anniversary_bonus_days_before", 0)
        settings.setdefault("anniversary_bonus_days_after", 7)
        settings.setdefault("first_visit_bonus_enabled", True)
        settings.setdefault("first_visit_bonus_points", 50)
        settings.setdefault("off_peak_bonus_enabled", False)
        settings.setdefault("off_peak_start_time", "14:00")
        settings.setdefault("off_peak_end_time", "17:00")
        settings.setdefault("off_peak_bonus_type", "multiplier")
        settings.setdefault("off_peak_bonus_value", 2.0)
        settings.setdefault("redemption_value", 0.25)
        settings.setdefault("min_redemption_points", 100)
        settings.setdefault("max_redemption_percent", 50.0)
        settings.setdefault("max_redemption_amount", 500.0)
        settings.setdefault("feedback_bonus_enabled", True)
        settings.setdefault("feedback_bonus_points", 25)
    
    response_data = {
        "customer": {
            "id": customer["id"],
            "name": customer["name"],
            "phone": customer["phone"],
            "email": customer.get("email"),
            "tier": customer.get("tier", "Bronze")
        },
        "points_earned": 0,
        "points_balance": customer.get("total_points", 0),
        "wallet_deducted": 0.0,
        "coupon_discount": 0.0,
        "final_amount": webhook_data.bill_amount,
        "tier": customer.get("tier", "Bronze")
    }
    
    current_amount = webhook_data.bill_amount
    
    # Step 1: Apply coupon if provided
    if webhook_data.coupon_code:
        try:
            coupon = await db.coupons.find_one({
                "user_id": user["id"],
                "code": webhook_data.coupon_code.upper(),
                "is_active": True
            }, {"_id": 0})
            
            if coupon:
                now = datetime.now(timezone.utc).isoformat()
                
                # Validate coupon
                if (coupon["start_date"] <= now <= coupon["end_date"] and
                    (not coupon.get("usage_limit") or coupon.get("total_used", 0) < coupon["usage_limit"])):
                    
                    # Check user usage
                    user_usage = await db.coupon_usage.count_documents({
                        "coupon_id": coupon["id"],
                        "customer_id": customer["id"]
                    })
                    
                    if user_usage < coupon.get("per_user_limit", 1):
                        # Check minimum order value
                        if current_amount >= coupon.get("min_order_value", 0):
                            # Check channel
                            if webhook_data.channel in coupon.get("applicable_channels", []):
                                # Calculate discount
                                if coupon["discount_type"] == "percentage":
                                    discount = (current_amount * coupon["discount_value"]) / 100
                                    if coupon.get("max_discount"):
                                        discount = min(discount, coupon["max_discount"])
                                else:
                                    discount = min(coupon["discount_value"], current_amount)
                                
                                current_amount -= discount
                                response_data["coupon_discount"] = round(discount, 2)
                                
                                # Record usage
                                usage_doc = {
                                    "id": str(uuid.uuid4()),
                                    "coupon_id": coupon["id"],
                                    "customer_id": customer["id"],
                                    "order_value": webhook_data.bill_amount,
                                    "discount_applied": discount,
                                    "channel": webhook_data.channel,
                                    "used_at": now
                                }
                                await db.coupon_usage.insert_one(usage_doc)
                                await db.coupons.update_one(
                                    {"id": coupon["id"]},
                                    {"$inc": {"total_used": 1}}
                                )
        except Exception as e:
            # Continue even if coupon fails
            pass
    
    # Step 1.5: Redeem points if requested
    points_redeemed = 0
    if webhook_data.redeem_points and webhook_data.redeem_points > 0:
        customer_points = customer.get("total_points", 0)
        
        # Validate redemption
        min_redeem = settings.get("min_redemption_points", 50)
        max_redeem_percent = settings.get("max_redemption_percent", 50.0)
        max_redeem_amount = settings.get("max_redemption_amount", 500.0)
        redemption_value = settings.get("redemption_value", 0.25)  # 1 point = ₹0.25
        
        if webhook_data.redeem_points < min_redeem:
            # Minimum not met, ignore redemption
            pass
        elif webhook_data.redeem_points > customer_points:
            # Not enough points, ignore redemption
            pass
        else:
            # Calculate redemption amount
            redemption_amount = webhook_data.redeem_points * redemption_value
            max_allowed_redemption = current_amount * (max_redeem_percent / 100)
            
            # Apply limits
            redemption_amount = min(redemption_amount, max_allowed_redemption, max_redeem_amount)
            
            # Calculate actual points used (in case amount was capped)
            points_redeemed = int(redemption_amount / redemption_value)
            
            # Apply redemption
            current_amount -= redemption_amount
            response_data["points_redeemed"] = points_redeemed
            response_data["redemption_amount"] = round(redemption_amount, 2)
            
            # Create redemption transaction (will update customer points later)
            redeem_tx = {
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "customer_id": customer["id"],
                "points": points_redeemed,
                "transaction_type": "redeem",
                "description": f"Redeemed {points_redeemed} points for ₹{redemption_amount:.2f} discount",
                "bill_amount": webhook_data.bill_amount,
                "balance_after": customer_points - points_redeemed,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.points_transactions.insert_one(redeem_tx)
    
    # Step 2: Calculate and award points (based on original bill amount, not discounted)
    bonus_messages = []
    total_bonus_points = 0
    
    if webhook_data.bill_amount >= settings.get("min_order_value", 100.0):
        customer_tier = customer.get("tier", "Bronze")
        earn_percent = get_earn_percent_for_tier(customer_tier, settings)
        base_points = int(webhook_data.bill_amount * earn_percent / 100)
        
        # Check for off-peak hours bonus
        is_off_peak, off_peak_value, off_peak_type, off_peak_msg = check_off_peak_bonus(settings)
        if is_off_peak:
            if off_peak_type == "multiplier":
                base_points = int(base_points * off_peak_value)
            else:  # flat bonus
                total_bonus_points += int(off_peak_value)
            bonus_messages.append(off_peak_msg)
        
        # Check for first visit bonus
        is_first_visit, first_visit_points, first_visit_msg = check_first_visit_bonus(customer, settings)
        if is_first_visit:
            total_bonus_points += first_visit_points
            bonus_messages.append(first_visit_msg)
        
        # Check for birthday bonus
        is_birthday, birthday_points, birthday_msg = check_birthday_bonus(customer, settings)
        if is_birthday:
            total_bonus_points += birthday_points
            bonus_messages.append(birthday_msg)
        
        # Check for anniversary bonus
        is_anniversary, anniversary_points, anniversary_msg = check_anniversary_bonus(customer, settings)
        if is_anniversary:
            total_bonus_points += anniversary_points
            bonus_messages.append(anniversary_msg)
        
        # Total points earned
        points_earned = base_points + total_bonus_points
        
        # Calculate final balance (earned - redeemed)
        new_points_balance = customer.get("total_points", 0) + points_earned - points_redeemed
        new_tier = calculate_tier(new_points_balance, settings)
        
        # Build description
        description_parts = [f"Earned {earn_percent}% on bill of ₹{webhook_data.bill_amount}"]
        if bonus_messages:
            description_parts.extend(bonus_messages)
        description = " | ".join(description_parts)
        
        # Update customer
        await db.customers.update_one(
            {"id": customer["id"]},
            {
                "$set": {
                    "total_points": new_points_balance,
                    "tier": new_tier,
                    "last_visit": datetime.now(timezone.utc).isoformat()
                },
                "$inc": {
                    "total_spent": webhook_data.bill_amount,
                    "total_visits": 1
                }
            }
        )
        
        # Create points transaction
        tx_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "customer_id": customer["id"],
            "points": points_earned,
            "transaction_type": "earn",
            "description": description,
            "bill_amount": webhook_data.bill_amount,
            "balance_after": new_points_balance,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.points_transactions.insert_one(tx_doc)
        
        # Create separate bonus transactions for tracking
        if is_first_visit:
            bonus_tx = {
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "customer_id": customer["id"],
                "points": first_visit_points,
                "transaction_type": "bonus",
                "description": first_visit_msg,
                "bill_amount": None,
                "balance_after": new_points_balance,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.points_transactions.insert_one(bonus_tx)
        
        if is_birthday:
            bonus_tx = {
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "customer_id": customer["id"],
                "points": birthday_points,
                "transaction_type": "bonus",
                "description": birthday_msg,
                "bill_amount": None,
                "balance_after": new_points_balance,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.points_transactions.insert_one(bonus_tx)
        
        if is_anniversary:
            bonus_tx = {
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "customer_id": customer["id"],
                "points": anniversary_points,
                "transaction_type": "bonus",
                "description": anniversary_msg,
                "bill_amount": None,
                "balance_after": new_points_balance,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.points_transactions.insert_one(bonus_tx)
        
        response_data["points_earned"] = points_earned
        response_data["points_balance"] = new_points_balance
        response_data["tier"] = new_tier
        if bonus_messages:
            response_data["bonus_applied"] = bonus_messages
    
    response_data["final_amount"] = round(current_amount, 2)
    
    return POSResponse(
        success=True,
        message="Payment processed successfully",
        data=response_data
    )

@api_router.post("/pos/customer-lookup", response_model=POSResponse)
async def pos_customer_lookup(
    lookup_data: POSCustomerLookup,
    x_api_key: str = Header(None)
):
    """
    POS Customer Lookup: Find customer by phone number
    
    Headers:
        X-API-Key: Restaurant's API key
    
    Request Body:
        phone: Customer's phone number
    
    Response:
        success: Whether customer was found
        message: Human-readable message
        data: Customer details with points and wallet balance
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    
    user = await db.users.find_one({"api_key": x_api_key}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    customer = await db.customers.find_one({
        "user_id": user["id"],
        "phone": lookup_data.phone
    }, {"_id": 0})
    
    if not customer:
        return POSResponse(
            success=False,
            message=f"Customer with phone {lookup_data.phone} not found",
            data=None
        )
    
    return POSResponse(
        success=True,
        message="Customer found",
        data={
            "id": customer["id"],
            "name": customer["name"],
            "phone": customer["phone"],
            "email": customer.get("email"),
            "points_balance": customer.get("total_points", 0),
            "wallet_balance": customer.get("wallet_balance", 0.0),
            "tier": customer.get("tier", "Bronze"),
            "total_visits": customer.get("total_visits", 0),
            "total_spent": customer.get("total_spent", 0.0),
            "last_visit": customer.get("last_visit")
        }
    )

@api_router.get("/pos/api-key")
async def get_api_key(user: dict = Depends(get_current_user)):
    """
    Get restaurant's API key for POS integration
    
    Requires JWT authentication (restaurant owner login)
    
    Response:
        api_key: The API key to configure in POS
        restaurant_name: Restaurant name
        instructions: How to use the API key
    """
    return {
        "api_key": user.get("api_key"),
        "restaurant_name": user.get("restaurant_name"),
        "instructions": "Add this API key to your POS system configuration as 'X-API-Key' header"
    }

@api_router.post("/pos/api-key/regenerate")
async def regenerate_api_key(user: dict = Depends(get_current_user)):
    """
    Regenerate API key (invalidates old key)
    
    Requires JWT authentication (restaurant owner login)
    
    Response:
        api_key: New API key
        message: Warning message
    """
    new_api_key = generate_api_key()
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"api_key": new_api_key}}
    )
    
    return {
        "api_key": new_api_key,
        "message": "API key regenerated. Update your POS configuration immediately. Old key is now invalid."
    }

# ============ WHATSAPP TEMPLATES & AUTOMATION ============

# WhatsApp Template Models
class WhatsAppTemplateCreate(BaseModel):
    name: str
    message: str
    media_type: Optional[str] = None  # image, video, document, None
    media_url: Optional[str] = None
    variables: Optional[List[str]] = None  # e.g., ["customer_name", "points", "amount"]

class WhatsAppTemplateUpdate(BaseModel):
    name: Optional[str] = None
    message: Optional[str] = None
    media_type: Optional[str] = None
    media_url: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None

class WhatsAppTemplate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    name: str
    message: str
    media_type: Optional[str] = None
    media_url: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: bool = True
    created_at: str
    updated_at: str

# Automation Event Types
AUTOMATION_EVENTS = [
    "points_earned",        # When customer earns points from a purchase
    "points_redeemed",      # When customer redeems points
    "bonus_points",         # When bonus points are given manually
    "wallet_credit",        # When money is added to wallet
    "wallet_debit",         # When money is deducted from wallet
    "birthday",             # On customer's birthday
    "anniversary",          # On customer's anniversary
    "first_visit",          # After first purchase
    "tier_upgrade",         # When customer upgrades tier
    "coupon_earned",        # When customer receives a coupon
    "points_expiring",      # When points are about to expire
    "feedback_received",    # When customer submits feedback
    "inactive_reminder"     # When customer hasn't visited in X days
]

class AutomationRuleCreate(BaseModel):
    event_type: str  # One of AUTOMATION_EVENTS
    template_id: str
    is_enabled: bool = True
    delay_minutes: int = 0  # Delay before sending (0 = immediate)
    conditions: Optional[dict] = None  # Additional conditions (e.g., {"min_points": 100})

class AutomationRuleUpdate(BaseModel):
    event_type: Optional[str] = None
    template_id: Optional[str] = None
    is_enabled: Optional[bool] = None
    delay_minutes: Optional[int] = None
    conditions: Optional[dict] = None

class AutomationRule(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    event_type: str
    template_id: str
    is_enabled: bool = True
    delay_minutes: int = 0
    conditions: Optional[dict] = None
    created_at: str
    updated_at: str

# WhatsApp Template CRUD Endpoints
@api_router.post("/whatsapp/templates", response_model=WhatsAppTemplate)
async def create_whatsapp_template(template_data: WhatsAppTemplateCreate, user: dict = Depends(get_current_user)):
    """Create a new WhatsApp message template"""
    template_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    template_doc = {
        "id": template_id,
        "user_id": user["id"],
        "name": template_data.name,
        "message": template_data.message,
        "media_type": template_data.media_type,
        "media_url": template_data.media_url,
        "variables": template_data.variables or [],
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    
    await db.whatsapp_templates.insert_one(template_doc)
    return WhatsAppTemplate(**template_doc)

@api_router.get("/whatsapp/templates", response_model=List[WhatsAppTemplate])
async def list_whatsapp_templates(active_only: bool = False, user: dict = Depends(get_current_user)):
    """List all WhatsApp templates for the user"""
    query = {"user_id": user["id"]}
    if active_only:
        query["is_active"] = True
    
    templates = await db.whatsapp_templates.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return [WhatsAppTemplate(**t) for t in templates]

@api_router.get("/whatsapp/templates/{template_id}", response_model=WhatsAppTemplate)
async def get_whatsapp_template(template_id: str, user: dict = Depends(get_current_user)):
    """Get a specific WhatsApp template"""
    template = await db.whatsapp_templates.find_one({"id": template_id, "user_id": user["id"]}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return WhatsAppTemplate(**template)

@api_router.put("/whatsapp/templates/{template_id}", response_model=WhatsAppTemplate)
async def update_whatsapp_template(template_id: str, template_data: WhatsAppTemplateUpdate, user: dict = Depends(get_current_user)):
    """Update a WhatsApp template"""
    template = await db.whatsapp_templates.find_one({"id": template_id, "user_id": user["id"]})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_dict = {k: v for k, v in template_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if update_dict:
        await db.whatsapp_templates.update_one({"id": template_id}, {"$set": update_dict})
    
    updated = await db.whatsapp_templates.find_one({"id": template_id}, {"_id": 0})
    return WhatsAppTemplate(**updated)

@api_router.delete("/whatsapp/templates/{template_id}")
async def delete_whatsapp_template(template_id: str, user: dict = Depends(get_current_user)):
    """Delete a WhatsApp template"""
    # First check if template is used in any automation rule
    rule_using_template = await db.automation_rules.find_one({"template_id": template_id, "user_id": user["id"]})
    if rule_using_template:
        raise HTTPException(status_code=400, detail="Cannot delete template that is used in automation rules. Remove the rules first.")
    
    result = await db.whatsapp_templates.delete_one({"id": template_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted"}

# Automation Rules CRUD Endpoints
@api_router.post("/whatsapp/automation", response_model=AutomationRule)
async def create_automation_rule(rule_data: AutomationRuleCreate, user: dict = Depends(get_current_user)):
    """Create a new automation rule (event -> template mapping)"""
    # Validate event type
    if rule_data.event_type not in AUTOMATION_EVENTS:
        raise HTTPException(status_code=400, detail=f"Invalid event type. Must be one of: {', '.join(AUTOMATION_EVENTS)}")
    
    # Validate template exists
    template = await db.whatsapp_templates.find_one({"id": rule_data.template_id, "user_id": user["id"]})
    if not template:
        raise HTTPException(status_code=400, detail="Template not found")
    
    # Check if rule already exists for this event
    existing = await db.automation_rules.find_one({"user_id": user["id"], "event_type": rule_data.event_type})
    if existing:
        raise HTTPException(status_code=400, detail=f"An automation rule already exists for event '{rule_data.event_type}'. Update or delete the existing rule.")
    
    rule_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    rule_doc = {
        "id": rule_id,
        "user_id": user["id"],
        "event_type": rule_data.event_type,
        "template_id": rule_data.template_id,
        "is_enabled": rule_data.is_enabled,
        "delay_minutes": rule_data.delay_minutes,
        "conditions": rule_data.conditions,
        "created_at": now,
        "updated_at": now
    }
    
    await db.automation_rules.insert_one(rule_doc)
    return AutomationRule(**rule_doc)

@api_router.get("/whatsapp/automation", response_model=List[AutomationRule])
async def list_automation_rules(user: dict = Depends(get_current_user)):
    """List all automation rules"""
    rules = await db.automation_rules.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return [AutomationRule(**r) for r in rules]

@api_router.get("/whatsapp/automation/events")
async def get_automation_events():
    """Get list of available automation events"""
    event_descriptions = {
        "points_earned": "When customer earns points from a purchase",
        "points_redeemed": "When customer redeems points",
        "bonus_points": "When bonus points are given manually",
        "wallet_credit": "When money is added to wallet",
        "wallet_debit": "When money is deducted from wallet",
        "birthday": "On customer's birthday",
        "anniversary": "On customer's anniversary",
        "first_visit": "After customer's first purchase",
        "tier_upgrade": "When customer upgrades to a higher tier",
        "coupon_earned": "When customer receives a coupon",
        "points_expiring": "When points are about to expire (reminder)",
        "feedback_received": "When customer submits feedback",
        "inactive_reminder": "When customer hasn't visited in X days"
    }
    return [{"event": e, "description": event_descriptions.get(e, "")} for e in AUTOMATION_EVENTS]

@api_router.get("/whatsapp/automation/{rule_id}", response_model=AutomationRule)
async def get_automation_rule(rule_id: str, user: dict = Depends(get_current_user)):
    """Get a specific automation rule"""
    rule = await db.automation_rules.find_one({"id": rule_id, "user_id": user["id"]}, {"_id": 0})
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    return AutomationRule(**rule)

@api_router.put("/whatsapp/automation/{rule_id}", response_model=AutomationRule)
async def update_automation_rule(rule_id: str, rule_data: AutomationRuleUpdate, user: dict = Depends(get_current_user)):
    """Update an automation rule"""
    rule = await db.automation_rules.find_one({"id": rule_id, "user_id": user["id"]})
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    
    update_dict = {k: v for k, v in rule_data.model_dump().items() if v is not None}
    
    # Validate event type if being updated
    if "event_type" in update_dict and update_dict["event_type"] not in AUTOMATION_EVENTS:
        raise HTTPException(status_code=400, detail=f"Invalid event type")
    
    # Validate template if being updated
    if "template_id" in update_dict:
        template = await db.whatsapp_templates.find_one({"id": update_dict["template_id"], "user_id": user["id"]})
        if not template:
            raise HTTPException(status_code=400, detail="Template not found")
    
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if update_dict:
        await db.automation_rules.update_one({"id": rule_id}, {"$set": update_dict})
    
    updated = await db.automation_rules.find_one({"id": rule_id}, {"_id": 0})
    return AutomationRule(**updated)

@api_router.delete("/whatsapp/automation/{rule_id}")
async def delete_automation_rule(rule_id: str, user: dict = Depends(get_current_user)):
    """Delete an automation rule"""
    result = await db.automation_rules.delete_one({"id": rule_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    return {"message": "Automation rule deleted"}

@api_router.post("/whatsapp/automation/{rule_id}/toggle")
async def toggle_automation_rule(rule_id: str, user: dict = Depends(get_current_user)):
    """Toggle automation rule enabled/disabled status"""
    rule = await db.automation_rules.find_one({"id": rule_id, "user_id": user["id"]})
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")
    
    new_status = not rule.get("is_enabled", True)
    await db.automation_rules.update_one(
        {"id": rule_id},
        {"$set": {"is_enabled": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"is_enabled": new_status}

# Helper to get automation rules with template details
@api_router.get("/whatsapp/automation-with-templates")
async def get_automation_with_templates(user: dict = Depends(get_current_user)):
    """Get all automation rules with their associated template details"""
    rules = await db.automation_rules.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    templates = await db.whatsapp_templates.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    
    # Create template lookup
    template_lookup = {t["id"]: t for t in templates}
    
    # Enrich rules with template details
    result = []
    for rule in rules:
        rule_with_template = dict(rule)
        template = template_lookup.get(rule["template_id"])
        if template:
            rule_with_template["template"] = template
        result.append(rule_with_template)
    
    return {
        "rules": result,
        "available_events": AUTOMATION_EVENTS,
        "templates": templates
    }

# ============ ROOT ROUTES ============

@api_router.get("/")
async def root():
    return {"message": "DinePoints API - Loyalty & CRM for Restaurants"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
