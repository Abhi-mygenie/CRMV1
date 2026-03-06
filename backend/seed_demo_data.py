#!/usr/bin/env python3
"""
Seed demo data into MongoDB for demo account
Creates a demo restaurant account with 55+ customers and all features
Run: python3 backend/seed_demo_data.py
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
import bcrypt
import random
import uuid

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "test_database")
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

print("Starting Demo Data Seeding...")

# Clear existing demo data
print("Clearing existing demo data...")
demo_user = db.users.find_one({"email": "demo@restaurant.com"})
if demo_user:
    demo_user_id = demo_user["id"]
    db.customers.delete_many({"$or": [{"user_id": demo_user_id}, {"restaurant_id": demo_user_id}]})
    db.points_transactions.delete_many({"$or": [{"user_id": demo_user_id}, {"restaurant_id": demo_user_id}]})
    db.wallet_transactions.delete_many({"$or": [{"user_id": demo_user_id}, {"restaurant_id": demo_user_id}]})
    db.orders.delete_many({"$or": [{"user_id": demo_user_id}, {"restaurant_id": demo_user_id}]})
    db.order_items.delete_many({"$or": [{"user_id": demo_user_id}, {"restaurant_id": demo_user_id}]})
    db.coupons.delete_many({"$or": [{"user_id": demo_user_id}, {"restaurant_id": demo_user_id}]})
    db.segments.delete_many({"$or": [{"user_id": demo_user_id}, {"restaurant_id": demo_user_id}]})
    db.feedback.delete_many({"$or": [{"user_id": demo_user_id}, {"restaurant_id": demo_user_id}]})
    db.whatsapp_templates.delete_many({"$or": [{"user_id": demo_user_id}, {"restaurant_id": demo_user_id}]})
    db.automation_rules.delete_many({"$or": [{"user_id": demo_user_id}, {"restaurant_id": demo_user_id}]})
    db.loyalty_settings.delete_many({"user_id": demo_user_id})
    db.users.delete_one({"id": demo_user_id})
    print(f"  Cleared data for existing demo user")

# Create demo user
print("Creating demo user account...")
demo_user_id = "demo-user-restaurant"

password = "demo123"
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

demo_user = {
    "id": demo_user_id,
    "email": "demo@restaurant.com",
    "password_hash": hashed_password,
    "api_key": "demo-api-key-12345",
    "restaurant_name": "Demo Restaurant & Cafe",
    "phone": "+919876543210",
    "created_at": datetime.now(timezone.utc).isoformat()
}
db.users.insert_one(demo_user)
print(f"  Created demo user: demo@restaurant.com / demo123")

# Helper functions
def random_date_ago(max_days):
    days_ago = random.randint(1, max_days)
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()

# Reference data
cities = ["Mumbai", "Delhi", "Bangalore", "Pune", "Hyderabad", "Chennai", "Kolkata", "Ahmedabad"]
states = {"Mumbai": "Maharashtra", "Delhi": "Delhi", "Bangalore": "Karnataka", "Pune": "Maharashtra",
          "Hyderabad": "Telangana", "Chennai": "Tamil Nadu", "Kolkata": "West Bengal", "Ahmedabad": "Gujarat"}
pincodes = {"Mumbai": "400", "Delhi": "110", "Bangalore": "560", "Pune": "411",
            "Hyderabad": "500", "Chennai": "600", "Kolkata": "700", "Ahmedabad": "380"}

first_names_m = ["Rajesh", "Amit", "Vikram", "Sanjay", "Rahul", "Arjun", "Karan", "Rohan", "Aditya", "Nikhil",
                 "Varun", "Akash", "Siddharth", "Harsh", "Manish"]
first_names_f = ["Priya", "Sneha", "Anita", "Kavita", "Deepika", "Pooja", "Neha", "Anjali", "Riya", "Simran",
                 "Swati", "Meera", "Nisha", "Tanvi", "Isha"]
last_names = ["Sharma", "Patel", "Kumar", "Singh", "Reddy", "Iyer", "Gupta", "Joshi", "Shah", "Mehta",
              "Rao", "Nair", "Verma", "Desai", "Pillai", "Agarwal", "Chopra", "Malhotra", "Saxena", "Bhatia"]

genders = ["male", "female", "other"]
languages = ["en", "hi", "mr", "ta", "te", "kn", "bn", "gu"]
diet_preferences = ["vegetarian", "non-vegetarian", "vegan", "eggetarian", "jain"]
dining_types = ["dine-in", "takeaway", "delivery", "buffet"]
time_slots = ["breakfast", "lunch", "evening", "dinner", "late-night"]
spice_levels = ["mild", "medium", "spicy", "extra-spicy"]
cuisines = ["North Indian", "South Indian", "Chinese", "Continental", "Italian", "Thai", "Mexican", "Japanese"]
payment_modes = ["cash", "upi", "card", "wallet"]
lead_sources = ["Walk-in", "Referral", "Google", "Instagram", "Zomato", "Swiggy", "Facebook", "WhatsApp"]
address_landmarks = ["Near City Mall", "Opp. Central Park", "Behind Metro Station", "Next to HDFC Bank",
                     "Near Railway Station", "Beside Apollo Hospital", "Near IT Park", "Opp. Phoenix Mall"]

# Generate customers
print("Creating 55 customers with all fields...")
customers = []
for i in range(55):
    gender = random.choice(["male", "female"]) if random.random() > 0.05 else "other"
    if gender == "male":
        first_name = random.choice(first_names_m)
    elif gender == "female":
        first_name = random.choice(first_names_f)
    else:
        first_name = random.choice(first_names_m + first_names_f)
    last_name = random.choice(last_names)
    name = f"{first_name} {last_name}"
    phone = f"98{random.randint(10000000, 99999999)}"
    total_spent = round(random.uniform(500, 50000), 2)
    total_points = int(total_spent * 0.1)
    total_visits = random.randint(1, 30)
    city = random.choice(cities)

    # Tier based on spend
    if total_spent < 5000:
        tier = "Bronze"
    elif total_spent < 15000:
        tier = "Silver"
    elif total_spent < 30000:
        tier = "Gold"
    else:
        tier = "Platinum"

    customer_type = "corporate" if random.random() > 0.85 else "normal"
    wallet_balance = random.randint(0, 2000) if random.random() > 0.7 else 0
    is_vip = random.random() > 0.85
    has_complaint = random.random() > 0.9
    is_blacklisted = random.random() > 0.95
    is_blocked = random.random() > 0.95

    customer = {
        "id": f"customer-demo-{i+1}",
        "user_id": demo_user_id,
        "pos_customer_id": 10000 + i if random.random() > 0.3 else None,
        # Basic
        "name": name,
        "phone": phone,
        "country_code": "+91",
        "email": f"{first_name.lower()}.{last_name.lower()}{i}@email.com",
        "gender": gender,
        "preferred_language": random.choice(languages),
        "dob": f"199{random.randint(0, 9)}-{str(random.randint(1, 12)).zfill(2)}-{str(random.randint(1, 28)).zfill(2)}" if random.random() > 0.3 else None,
        "anniversary": f"201{random.randint(0, 9)}-{str(random.randint(1, 12)).zfill(2)}-{str(random.randint(1, 28)).zfill(2)}" if random.random() > 0.6 else None,
        # Type
        "customer_type": customer_type,
        "gst_name": f"{last_name} Enterprises Pvt Ltd" if customer_type == "corporate" else None,
        "gst_number": f"27AABCU{random.randint(1000,9999)}R1Z{random.randint(1,9)}" if customer_type == "corporate" else None,
        "billing_address": f"Floor {random.randint(1,10)}, {random.choice(['Tech Tower','Business Hub','Corporate Plaza','Trade Center'])}, {city}" if customer_type == "corporate" else None,
        "credit_limit": random.choice([25000, 50000, 100000, 200000]) if customer_type == "corporate" else None,
        "payment_terms": random.choice(["Net 15", "Net 30", "Net 45", "Net 60"]) if customer_type == "corporate" else None,
        # Address
        "address": f"{random.randint(1,500)}, {random.choice(['MG Road','Link Road','Station Road','Park Street','Ring Road','Brigade Road'])}" if random.random() > 0.2 else None,
        "address_line_2": random.choice(address_landmarks) if random.random() > 0.4 else None,
        "city": city,
        "state": states[city],
        "pincode": f"{pincodes[city]}{str(random.randint(1, 99)).zfill(3)}",
        "country": "India",
        "delivery_instructions": random.choice(["Ring doorbell twice", "Call before delivery", "Leave at reception", "Gate code: 1234", "Don't ring bell, knock", None, None, None]),
        # Flags
        "vip_flag": is_vip,
        "complaint_flag": has_complaint,
        "blacklist_flag": is_blacklisted,
        "is_blocked": is_blocked,
        # Activity
        "total_spent": total_spent,
        "total_points": total_points,
        "total_visits": total_visits,
        "tier": tier,
        "wallet_balance": wallet_balance,
        "last_visit": random_date_ago(90),
        "avg_order_value": round(total_spent / max(total_visits, 1), 2),
        # Dining preferences
        "diet_preference": random.choice(diet_preferences) if random.random() > 0.2 else None,
        "preferred_dining_type": random.choice(dining_types) if random.random() > 0.3 else None,
        "preferred_time_slot": random.choice(time_slots) if random.random() > 0.3 else None,
        "spice_level": random.choice(spice_levels) if random.random() > 0.4 else None,
        "cuisine_preference": random.choice(cuisines) if random.random() > 0.3 else None,
        "avg_party_size": random.randint(1, 8) if random.random() > 0.4 else None,
        "preferred_payment_mode": random.choice(payment_modes) if random.random() > 0.3 else None,
        "allergies": random.sample(["Peanuts", "Dairy", "Gluten", "Shellfish", "Soy", "Eggs"], k=random.randint(1, 2)) if random.random() > 0.8 else None,
        # Engagement
        "whatsapp_opt_in": random.random() > 0.3,
        "lead_source": random.choice(lead_sources) if random.random() > 0.2 else None,
        "nps_score": random.randint(1, 10) if random.random() > 0.4 else None,
        "last_rating": random.randint(1, 5) if random.random() > 0.5 else None,
        "churn_risk_score": random.randint(0, 100) if random.random() > 0.5 else None,
        "price_sensitivity_score": random.choice(["Low", "Medium", "High"]) if random.random() > 0.6 else None,
        # Membership
        "membership_id": f"MEM-{random.randint(10000,99999)}" if random.random() > 0.7 else None,
        "referral_code": f"REF{first_name[:3].upper()}{random.randint(100,999)}" if random.random() > 0.6 else None,
        # Notes & custom
        "notes": random.choice(["Prefers window seating", "Regular weekend customer", "Always orders butter chicken",
                                 "Brings family of 4", "Allergic to nuts - always check", "Loves spicy food",
                                 None, None, None, None]),
        "custom_field_1": random.choice(["Dine-in Regular", "Takeaway Preferred", "Delivery Only", None]),
        "custom_field_2": None,
        "custom_field_3": None,
        "created_at": random_date_ago(365),
    }
    customers.append(customer)

db.customers.insert_many(customers)
print(f"  Created {len(customers)} customers")

# Menu items
MENU_ITEMS = [
    {"name": "Butter Chicken", "price": 380, "category": "North Indian", "notes": ["Extra gravy", "Less spicy", "No cream", None]},
    {"name": "Paneer Tikka", "price": 280, "category": "North Indian", "notes": ["Extra charred", "No onion", None, None]},
    {"name": "Dal Makhani", "price": 260, "category": "North Indian", "notes": ["Extra butter", None, None]},
    {"name": "Biryani", "price": 350, "category": "North Indian", "notes": ["Extra raita", "Less spicy", "No salan", None]},
    {"name": "Naan", "price": 60, "category": "Breads", "notes": ["Extra butter", "Well done", None, None]},
    {"name": "Garlic Naan", "price": 80, "category": "Breads", "notes": [None, None]},
    {"name": "Masala Dosa", "price": 180, "category": "South Indian", "notes": ["Extra chutney", "Crispy", None]},
    {"name": "Idli Sambar", "price": 120, "category": "South Indian", "notes": [None, None]},
    {"name": "Veg Fried Rice", "price": 220, "category": "Chinese", "notes": ["Extra spicy", "No MSG", None]},
    {"name": "Manchurian", "price": 240, "category": "Chinese", "notes": ["Dry", "Extra gravy", None]},
    {"name": "Pasta Alfredo", "price": 320, "category": "Continental", "notes": ["Extra cheese", "Gluten-free pasta", None]},
    {"name": "Caesar Salad", "price": 280, "category": "Continental", "notes": ["No croutons", "Dressing on side", None]},
    {"name": "Margherita Pizza", "price": 350, "category": "Continental", "notes": ["Thin crust", "Extra cheese", None]},
    {"name": "Gulab Jamun", "price": 120, "category": "Desserts", "notes": ["Warm", None]},
    {"name": "Rasmalai", "price": 150, "category": "Desserts", "notes": [None, None]},
    {"name": "Brownie Sundae", "price": 220, "category": "Desserts", "notes": ["Extra ice cream", None]},
    {"name": "Mango Lassi", "price": 120, "category": "Beverages", "notes": ["Less sugar", None]},
    {"name": "Masala Chai", "price": 60, "category": "Beverages", "notes": ["Extra ginger", "No sugar", None]},
    {"name": "Cold Coffee", "price": 180, "category": "Beverages", "notes": ["Extra shot", None]},
    {"name": "Fresh Lime Soda", "price": 90, "category": "Beverages", "notes": [None, None]},
]

ORDER_NOTES_LIST = [
    "Table 5 - Window seat", "Birthday celebration", "Takeaway order", "Corporate lunch",
    "Rush order", "Regular customer - preferred seating", "Allergic to peanuts - please check",
    "Party of 6", None, None, None, None, None,
]

# Generate orders and order_items
print("Creating orders and order items...")
orders_list = []
order_items_list = []

for customer in customers[:40]:
    num_orders = random.randint(3, 12)
    for j in range(num_orders):
        order_id = f"order-demo-{customer['id']}-{j}"
        order_date = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 180))
        order_hour = random.choice([9, 10, 12, 13, 14, 17, 18, 19, 20, 21])
        order_date = order_date.replace(hour=order_hour, minute=random.randint(0, 59))

        num_items = random.randint(2, 5)
        selected_items = random.sample(MENU_ITEMS, min(num_items, len(MENU_ITEMS)))

        items_embedded = []
        total = 0
        for menu_item in selected_items:
            qty = random.randint(1, 3)
            price = menu_item["price"]
            total += price * qty
            item_note = random.choice(menu_item["notes"])

            item_doc = {
                "item_name": menu_item["name"],
                "item_qty": qty,
                "item_price": price,
                "item_notes": item_note,
                "item_category": menu_item["category"],
            }
            items_embedded.append(item_doc)

            order_items_list.append({
                "id": str(uuid.uuid4()),
                "order_id": order_id,
                "customer_id": customer["id"],
                "user_id": demo_user_id,
                "item_name": menu_item["name"],
                "item_qty": qty,
                "item_price": price,
                "item_notes": item_note,
                "item_category": menu_item["category"],
                "created_at": order_date.isoformat(),
            })

        tax_amount = round(total * 0.05, 2)
        tip_amount = round(total * random.uniform(0, 0.1), 2) if random.random() > 0.5 else 0

        orders_list.append({
            "id": order_id,
            "user_id": demo_user_id,
            "customer_id": customer["id"],
            "pos_id": "mygenie",
            "pos_restaurant_id": demo_user_id,
            "pos_order_id": f"MG-{random.randint(10000, 99999)}",
            "order_amount": total,
            "tax_amount": tax_amount,
            "tip_amount": tip_amount,
            "wallet_used": 0,
            "coupon_code": None,
            "coupon_discount": 0,
            "order_discount": round(total * 0.1, 2) if random.random() > 0.8 else 0,
            "points_earned": int(total * 0.1),
            "off_peak_bonus": 0,
            "payment_method": random.choice(["cash", "upi", "card"]),
            "payment_status": "success",
            "order_type": random.choice(["pos", "dine_in", "takeaway", "delivery"]),
            "order_notes": random.choice(ORDER_NOTES_LIST),
            "table_id": f"T{random.randint(1, 20)}" if random.random() > 0.3 else None,
            "waiter_id": f"W{random.randint(1, 8)}" if random.random() > 0.3 else None,
            "items": items_embedded,
            "created_at": order_date.isoformat(),
        })

if orders_list:
    db.orders.insert_many(orders_list)
    print(f"  Created {len(orders_list)} orders")

if order_items_list:
    db.order_items.insert_many(order_items_list)
    print(f"  Created {len(order_items_list)} order items")

# Points transactions
print("Creating points transactions...")
points_transactions = []
transaction_types = ["earned", "redeemed", "bonus"]
reasons = {
    "earned": ["Bill payment", "Purchase", "Dine-in"],
    "redeemed": ["Discount redemption", "Reward claimed"],
    "bonus": ["Birthday bonus", "Anniversary bonus", "First visit bonus"]
}

for customer in customers[:30]:
    num_transactions = random.randint(5, 15)
    for j in range(num_transactions):
        trans_type = random.choice(transaction_types)
        points = -random.randint(100, 500) if trans_type == "redeemed" else random.randint(50, 500)
        transaction = {
            "id": f"points-{customer['id']}-{j}",
            "user_id": demo_user_id,
            "customer_id": customer["id"],
            "customer_name": customer["name"],
            "points": points,
            "type": trans_type,
            "reason": random.choice(reasons[trans_type]),
            "bill_amount": random.randint(500, 5000) if trans_type == "earned" else None,
            "created_at": random_date_ago(180)
        }
        points_transactions.append(transaction)

if points_transactions:
    db.points_transactions.insert_many(points_transactions)
    print(f"  Created {len(points_transactions)} points transactions")

# Wallet transactions
print("Creating wallet transactions...")
wallet_transactions = []
wallet_types = ["credit", "debit"]
wallet_reasons = {"credit": ["Wallet top-up", "Refund", "Bonus credit"], "debit": ["Bill payment", "Purchase"]}

for customer in customers[:20]:
    if customer["wallet_balance"] > 0 or random.random() > 0.5:
        num_transactions = random.randint(3, 10)
        for j in range(num_transactions):
            trans_type = random.choice(wallet_types)
            amount = -random.randint(100, 1000) if trans_type == "debit" else random.randint(500, 2000)
            transaction = {
                "id": f"wallet-{customer['id']}-{j}",
                "user_id": demo_user_id,
                "customer_id": customer["id"],
                "customer_name": customer["name"],
                "amount": amount,
                "type": trans_type,
                "reason": random.choice(wallet_reasons[trans_type]),
                "bonus_amount": int(amount * 0.1) if trans_type == "credit" and random.random() > 0.7 else None,
                "created_at": random_date_ago(120)
            }
            wallet_transactions.append(transaction)

if wallet_transactions:
    db.wallet_transactions.insert_many(wallet_transactions)
    print(f"  Created {len(wallet_transactions)} wallet transactions")

# Coupons
print("Creating coupons...")
now = datetime.now(timezone.utc)
coupons = [
    {
        "id": "coupon-demo-1", "user_id": demo_user_id, "code": "WELCOME20",
        "description": "Welcome offer - 20% off on first order", "discount_type": "percentage",
        "discount_value": 20, "min_order_value": 500, "max_discount": 200,
        "usage_limit": 100, "used_count": 45,
        "valid_from": (now - timedelta(days=30)).isoformat(), "valid_until": (now + timedelta(days=30)).isoformat(),
        "channels": ["dine-in", "delivery", "takeaway"], "is_active": True,
        "created_at": (now - timedelta(days=30)).isoformat()
    },
    {
        "id": "coupon-demo-2", "user_id": demo_user_id, "code": "GOLD50",
        "description": "Flat 50 off for Gold tier members", "discount_type": "fixed",
        "discount_value": 50, "min_order_value": 300, "max_discount": None,
        "usage_limit": 200, "used_count": 87,
        "valid_from": (now - timedelta(days=15)).isoformat(), "valid_until": (now + timedelta(days=45)).isoformat(),
        "channels": ["dine-in"], "tier_restriction": "Gold", "is_active": True,
        "created_at": (now - timedelta(days=15)).isoformat()
    },
    {
        "id": "coupon-demo-3", "user_id": demo_user_id, "code": "WEEKEND15",
        "description": "Weekend special - 15% off", "discount_type": "percentage",
        "discount_value": 15, "min_order_value": 800, "max_discount": 150,
        "usage_limit": 50, "used_count": 23,
        "valid_from": (now - timedelta(days=7)).isoformat(), "valid_until": (now + timedelta(days=7)).isoformat(),
        "channels": ["dine-in", "takeaway"], "is_active": True,
        "created_at": (now - timedelta(days=7)).isoformat()
    }
]
db.coupons.insert_many(coupons)
print(f"  Created {len(coupons)} coupons")

# Segments
print("Creating customer segments...")
segments = [
    {
        "id": "segment-demo-1", "user_id": demo_user_id, "name": "VIP Gold Members",
        "description": "Gold tier loyalty members", "filters": {"tier": "Gold"},
        "customer_count": len([c for c in customers if c["tier"] == "Gold"]),
        "created_at": (now - timedelta(days=45)).isoformat(), "updated_at": (now - timedelta(days=45)).isoformat()
    },
    {
        "id": "segment-demo-2", "user_id": demo_user_id, "name": "Inactive Customers (30+ days)",
        "description": "Customers who haven't visited in 30+ days", "filters": {"last_visit_days": "30"},
        "customer_count": 18,
        "created_at": (now - timedelta(days=30)).isoformat(), "updated_at": (now - timedelta(days=30)).isoformat()
    },
    {
        "id": "segment-demo-3", "user_id": demo_user_id, "name": "Corporate Clients",
        "description": "Business and corporate customers", "filters": {"customer_type": "corporate"},
        "customer_count": len([c for c in customers if c["customer_type"] == "corporate"]),
        "created_at": (now - timedelta(days=20)).isoformat(), "updated_at": (now - timedelta(days=20)).isoformat()
    },
    {
        "id": "segment-demo-4", "user_id": demo_user_id, "name": "High Spenders (10K+)",
        "description": "Customers who spent more than 10,000", "filters": {"total_spent": "10000+"},
        "customer_count": len([c for c in customers if c["total_spent"] > 10000]),
        "created_at": (now - timedelta(days=10)).isoformat(), "updated_at": (now - timedelta(days=10)).isoformat()
    }
]
db.segments.insert_many(segments)
print(f"  Created {len(segments)} segments")

# Feedback
print("Creating feedback entries...")
feedback_list = []
comments = [
    "Great food and service!", "Excellent ambiance, loved the experience",
    "Good food but service could be faster", "Amazing food quality, will visit again",
    "Nice place for family dining", "Delicious food, highly recommended",
    "Outstanding service and hospitality", "Best restaurant in the area!"
]

for i, customer in enumerate(customers[:25]):
    if random.random() > 0.3:
        feedback = {
            "id": f"feedback-demo-{i+1}", "user_id": demo_user_id,
            "customer_id": customer["id"], "customer_name": customer["name"],
            "customer_phone": customer["phone"], "rating": random.randint(3, 5),
            "comments": random.choice(comments), "created_at": random_date_ago(60)
        }
        feedback_list.append(feedback)

if feedback_list:
    db.feedback.insert_many(feedback_list)
    print(f"  Created {len(feedback_list)} feedback entries")

# WhatsApp templates
print("Creating WhatsApp templates...")
templates = [
    {"id": "template-demo-1", "user_id": demo_user_id, "name": "Welcome Message",
     "content": "Welcome to {{restaurant_name}}, {{customer_name}}! Thank you for joining our loyalty program.",
     "variables": ["restaurant_name", "customer_name"], "created_at": (now - timedelta(days=60)).isoformat()},
    {"id": "template-demo-2", "user_id": demo_user_id, "name": "Points Earned",
     "content": "Hi {{customer_name}}! You've earned {{points_earned}} points. Your balance: {{points_balance}} points.",
     "variables": ["customer_name", "points_earned", "points_balance"], "created_at": (now - timedelta(days=55)).isoformat()},
    {"id": "template-demo-3", "user_id": demo_user_id, "name": "Birthday Wishes",
     "content": "Happy Birthday {{customer_name}}! We've added {{points_earned}} bonus points to your account!",
     "variables": ["customer_name", "points_earned"], "created_at": (now - timedelta(days=50)).isoformat()},
]
db.whatsapp_templates.insert_many(templates)
print(f"  Created {len(templates)} WhatsApp templates")

# Automation rules
print("Creating automation rules...")
rules = [
    {"id": "rule-demo-1", "user_id": demo_user_id, "event": "points_earned",
     "template_id": "template-demo-2", "template_name": "Points Earned",
     "is_enabled": True, "delay_minutes": 5, "created_at": (now - timedelta(days=50)).isoformat()},
    {"id": "rule-demo-2", "user_id": demo_user_id, "event": "birthday",
     "template_id": "template-demo-3", "template_name": "Birthday Wishes",
     "is_enabled": True, "delay_minutes": 0, "created_at": (now - timedelta(days=45)).isoformat()},
]
db.automation_rules.insert_many(rules)
print(f"  Created {len(rules)} automation rules")

# Loyalty settings
print("Creating loyalty settings...")
loyalty_settings = {
    "id": f"settings-{demo_user_id}", "user_id": demo_user_id,
    "points_per_rupee": 1, "redemption_rate": 1, "min_points_to_redeem": 100,
    "points_expiry_days": 365, "birthday_bonus_points": 100, "anniversary_bonus_points": 150,
    "first_visit_bonus": 50,
    "bronze_earning_percentage": 100, "silver_earning_percentage": 110,
    "gold_earning_percentage": 125, "platinum_earning_percentage": 150,
    "bronze_threshold": 0, "silver_threshold": 5000,
    "gold_threshold": 15000, "platinum_threshold": 30000,
    "off_peak_hours_start": "14:00", "off_peak_hours_end": "17:00",
    "off_peak_bonus_percentage": 20, "updated_at": now.isoformat()
}
db.loyalty_settings.replace_one({"user_id": demo_user_id}, loyalty_settings, upsert=True)
print(f"  Created loyalty settings")

# Summary
print("\n" + "=" * 50)
print("DEMO DATA SEEDING COMPLETE!")
print("=" * 50)
print(f"\n  Credentials: demo@restaurant.com / demo123")
print(f"\n  {len(customers)} Customers (with gender, language, full address, flags, dining prefs, scores)")
print(f"  {len(orders_list)} Orders (with tax, tip, table, waiter)")
print(f"  {len(order_items_list)} Order Items")
print(f"  {len(points_transactions)} Points Transactions")
print(f"  {len(wallet_transactions)} Wallet Transactions")
print(f"  {len(coupons)} Coupons")
print(f"  {len(segments)} Customer Segments")
print(f"  {len(feedback_list)} Feedback Entries")
print(f"  {len(templates)} WhatsApp Templates")
print(f"  {len(rules)} Automation Rules")
print(f"  1 Loyalty Settings")
print("=" * 50)
