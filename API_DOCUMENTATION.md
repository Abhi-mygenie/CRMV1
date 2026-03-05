# MyGenie POS Integration API Documentation

**Base URL:** `https://hybrid-pos-system-3.preview.emergentagent.com/api`

**Authentication:** All POS endpoints require `X-API-Key` header. All CRM endpoints require `Authorization: Bearer <token>` header.

---

## Authentication

### POS API Authentication
All POS API endpoints require authentication via API Key in the request header:
```
X-API-Key: your_api_key_here
```

### CRM API Authentication
CRM endpoints (customers, insights, settings) require JWT token:
```
Authorization: Bearer <jwt_token>
```

Obtain a token via `POST /api/auth/login` or `POST /api/auth/demo-login`.

---

## CRM Endpoints

### Login
```
POST /api/auth/login
```
**Request Body:**
```json
{"email": "owner@18march.com", "password": "Qplazm@10"}
```
**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {"id": "...", "email": "...", "restaurant_name": "..."},
  "is_demo": false
}
```

### Demo Login
```
POST /api/auth/demo-login
```
No body required. Returns token with `is_demo: true`.

---

### AI Insights

Get AI-powered customer insights aggregated from order history.

```
GET /api/customers/{customer_id}/insights
```

**Headers:**
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes | `Bearer <jwt_token>` |

**Response (200 OK):**
```json
{
  "top_items": [
    {"name": "Butter Chicken", "count": 12},
    {"name": "Naan", "count": 8}
  ],
  "top_categories": [
    {"name": "North Indian", "count": 20, "percent": 55},
    {"name": "Beverages", "count": 10, "percent": 28}
  ],
  "avg_frequency_days": 12,
  "preferred_day": "Saturday",
  "preferred_time": "Dinner (7-11 PM)",
  "spending_trend": {"change_percent": 15, "direction": "up"},
  "common_notes": [
    {"note": "Extra gravy", "count": 5},
    {"note": "Less spicy", "count": 3}
  ],
  "avg_order_value": 1250.50
}
```

**Data Sources:**
- `top_items` and `top_categories`: Aggregated from `order_items` collection
- `avg_frequency_days`, `preferred_day`, `preferred_time`, `spending_trend`: Calculated from `orders` collection
- `common_notes`: Aggregated from `item_notes` in `order_items`
- `avg_order_value`: Stored on customer document, recalculated on each order

---

## POS Endpoints

### 1. Create Customer

```
POST /api/pos/customers
```

**Headers:**
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `X-API-Key` | string | Yes | API key for authentication |
| `Content-Type` | string | Yes | `application/json` |

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pos_id` | string | **Yes** | POS system identifier (e.g., "mygenie") |
| `restaurant_id` | string | **Yes** | Restaurant ID in the POS system |
| `name` | string | **Yes** | Customer's full name |
| `phone` | string | **Yes** | Phone number (10 digits, without country code) |
| `country_code` | string | No | Country code (default: "+91") |
| `email` | string | No | Email address |
| `dob` | string | No | Date of birth (YYYY-MM-DD) |
| `anniversary` | string | No | Anniversary date (YYYY-MM-DD) |
| `customer_type` | string | No | "normal" or "corporate" (default: "normal") |
| `gst_name` | string | No | GST registered name |
| `gst_number` | string | No | GST number |
| `address` | string | No | Street address |
| `city` | string | No | City |
| `pincode` | string | No | PIN/ZIP code |
| `allergies` | array | No | List of allergies |
| `favorites` | array | No | List of favorite items |
| `custom_field_1` | string | No | Custom field 1 |
| `custom_field_2` | string | No | Custom field 2 |
| `custom_field_3` | string | No | Custom field 3 |
| `notes` | string | No | Additional notes |

**Example:**
```bash
curl -X POST "https://hybrid-pos-system-3.preview.emergentagent.com/api/pos/customers" \
  -H "X-API-Key: dp_live_u-AFJd9rSTjej07ENWfbXT3XaK9OuoxdAJ70BWSylb4" \
  -H "Content-Type: application/json" \
  -d '{
    "pos_id": "mygenie",
    "restaurant_id": "rest_12345",
    "name": "John Doe",
    "phone": "9876543210",
    "email": "john@example.com",
    "city": "Mumbai",
    "allergies": ["Gluten", "Peanuts"]
  }'
```

---

### 2. Update Customer

```
PUT /api/pos/customers/{customer_id}
```

Updates an existing customer's information. Same fields as Create Customer (all optional except `pos_id`, `restaurant_id`, `phone`).

---

### 3. Customer Lookup

```
POST /api/pos/customer-lookup
```

Look up a customer by phone number to get loyalty info before processing a transaction.

**Request Body:**
```json
{"phone": "9876543210"}
```

**Success Response:**
```json
{
  "success": true,
  "message": "Customer found",
  "data": {
    "registered": true,
    "customer_id": "...",
    "name": "John Doe",
    "phone": "9876543210",
    "tier": "Gold",
    "total_points": 1500,
    "points_value": 375.00,
    "wallet_balance": 250.00,
    "total_visits": 25,
    "total_spent": 15000.00,
    "allergies": ["Gluten"],
    "favorites": ["Butter Chicken"],
    "last_visit": "2026-02-20T18:30:00.000000+00:00"
  }
}
```

---

### 4. Max Redeemable Points

```
POST /api/pos/max-redeemable
```

Calculate maximum redeemable loyalty points for a given bill amount.

**Request Body:**
```json
{
  "pos_id": "mygenie",
  "restaurant_id": "478",
  "cust_mobile": "9876543210",
  "bill_amount": 1000
}
```

**Response:**
```json
{
  "success": true,
  "message": "Max redeemable calculated",
  "data": {
    "max_points_redeemable": 400,
    "max_discount_value": 100.00
  }
}
```

**Calculation considers:** Customer's available points, minimum points threshold, max redemption percent of bill, and absolute redemption cap.

---

### 5. Order Webhook

Webhook for POS systems to send order data on every completed order. Automatically calculates loyalty points and stores items for AI analytics.

```
POST /api/pos/orders
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pos_id` | string | **Yes** | POS system identifier |
| `restaurant_id` | string | **Yes** | Restaurant ID |
| `order_id` | string | **Yes** | Unique order ID from POS |
| `cust_mobile` | string | **Yes** | Customer phone (10 digits) |
| `cust_name` | string | No | Customer name (required for new customers) |
| `order_amount` | float | **Yes** | Total order amount |
| `wallet_used` | float | No | Wallet amount used (default: 0) |
| `coupon_code` | string | No | Coupon code applied |
| `coupon_discount` | float | No | Discount amount (default: 0) |
| `payment_method` | string | No | "cash", "upi", "card", "TAB" |
| `payment_status` | string | **Yes** | Must be "success" to process |
| `order_type` | string | No | "pos", "dine_in", "takeaway", "delivery" |
| `order_notes` | string | No | Order-level notes |
| `items` | array | No | Line items (see below) |

#### Items Array Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `item_name` | string | **Yes** | Menu item name |
| `item_qty` | integer | No | Quantity (default: 1) |
| `item_price` | float | No | Price per unit (default: 0) |
| `item_notes` | string | No | Food-level notes (e.g., "extra gravy") |
| `item_category` | string | No | Food category (e.g., "North Indian", "Beverages") |

**Example:**
```bash
curl -X POST "https://hybrid-pos-system-3.preview.emergentagent.com/api/pos/orders" \
  -H "X-API-Key: dp_live_u-AFJd9rSTjej07ENWfbXT3XaK9OuoxdAJ70BWSylb4" \
  -H "Content-Type: application/json" \
  -d '{
    "pos_id": "mygenie",
    "restaurant_id": "478",
    "order_id": "ORD-2026-001234",
    "cust_mobile": "9653078025",
    "cust_name": "Piyush",
    "order_amount": 1850.0,
    "payment_method": "TAB",
    "payment_status": "success",
    "order_type": "dine_in",
    "order_notes": "Anniversary dinner, corner table",
    "items": [
      {"item_name": "Butter Chicken", "item_qty": 2, "item_price": 450.0, "item_notes": "Extra gravy, less spicy", "item_category": "North Indian"},
      {"item_name": "Garlic Naan", "item_qty": 4, "item_price": 80.0, "item_category": "Breads"},
      {"item_name": "Gulab Jamun", "item_qty": 1, "item_price": 180.0, "item_notes": "Warm", "item_category": "Desserts"}
    ]
  }'
```

**Dual Storage:** When `items` are provided:
1. **Embedded in order doc** (`orders` collection) - for fast order display
2. **Separate `order_items` collection** - indexed by `customer_id`, `item_name`, `order_id` for AI analytics

Both `order_notes` and `item_notes` are persisted. Orders without items are backward compatible.

**Success Response:**
```json
{
  "success": true,
  "message": "Order processed successfully",
  "data": {
    "order_id": "e4252338-...",
    "pos_order_id": "ORD-2026-001234",
    "customer_id": "f95ce018-...",
    "customer_name": "Piyush",
    "is_new_customer": false,
    "order_amount": 1850.0,
    "points_earned": 185,
    "total_points": 1685,
    "tier": "Gold",
    "wallet_used": 0.0,
    "wallet_balance_after": 500.0,
    "coupon_applied": "",
    "coupon_discount": 0.0
  }
}
```

---

## Response Schema

All POS API responses follow this standard format:

```json
{
  "success": boolean,
  "message": string,
  "data": object | null
}
```

## Error Codes

| HTTP Status | Description |
|-------------|-------------|
| 200 | Success (check `success` field) |
| 401 | Unauthorized - Missing or invalid API key / JWT token |
| 404 | Resource not found |
| 500 | Internal Server Error |

## Points Calculation

Points are earned based on tier and configurable loyalty settings:

| Tier | Default Earning Rate | Threshold |
|------|---------------------|-----------|
| Bronze | 100% of base rate | 0+ spent |
| Silver | 110% of base rate | 5,000+ spent |
| Gold | 125% of base rate | 15,000+ spent |
| Platinum | 150% of base rate | 30,000+ spent |

Off-peak bonus hours and birthday/anniversary bonuses are configurable via the Loyalty Settings.

## Notes for Integration

1. **Phone Numbers**: Send as 10-digit strings without country code
2. **Customer Auto-Creation**: Orders for unknown customers auto-create using `cust_mobile` + `cust_name`
3. **Duplicate Prevention**: Same `pos_id` + `order_id` combination is rejected
4. **Payment Status**: Only `payment_status: "success"` orders are processed
5. **avg_order_value**: Automatically recalculated on customer record with each new order
6. **pos_customer_id**: Customer ID from POS system, stored in our DB for sync/mapping between systems

## Customer Data Fields

When syncing customers from MyGenie POS API, the following key fields are stored:

| Field | Description |
|-------|-------------|
| `id` | Our internal UUID (primary key) |
| `pos_customer_id` | Customer ID from POS API (bridge between systems) |
| `mygenie_synced` | Boolean flag indicating if customer was synced from POS |
| `last_synced_at` | Timestamp of last sync |

## File References
- **Backend Entry**: `/app/backend/server.py`
- **POS Router**: `/app/backend/routers/pos.py`
- **Customers Router**: `/app/backend/routers/customers.py`
- **Auth Router**: `/app/backend/routers/auth.py`
- **Frontend Routing**: `/app/frontend/src/App.js`

---

**Last Updated**: March 5, 2026
