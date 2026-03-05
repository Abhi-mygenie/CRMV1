# Demo Mode Implementation Guide

## Overview
DinePoints includes a **Demo Mode** feature that allows users to explore the platform with comprehensive test data, including orders, AI insights, and all CRM features.

## Architecture

### Data Flow
```
LOGIN PAGE
  * Regular Login Form -> MyGenie API
  * "Try Demo Mode" Button -> Local DB

Demo Mode Path:
  POST /api/auth/demo-login
  -> No credentials needed
  -> Uses demo@restaurant.com
  -> Returns is_demo: true

Regular Login Path:
  POST /api/auth/login -> /api/auth/mygenie-login
  -> Requires email/password
  -> Returns is_demo: false
```

## Demo User Credentials
- **Email**: `demo@restaurant.com`
- **Password**: `demo123`
- **Database**: Local MongoDB
- **Data**: Populated via `backend/seed_demo_data.py`

## Seeded Demo Data

Running the seed script creates:

| Collection | Count | Details |
|------------|-------|---------|
| Customers | 55 | Bronze/Silver/Gold/Platinum tiers, with avg_order_value |
| Orders | ~305 | With embedded items, order_notes, item_notes, item_category |
| Order Items | ~1,080 | Flat documents for AI Insights aggregation |
| Points Transactions | ~311 | Earn/redeem/bonus types |
| Wallet Transactions | ~44 | Credit/debit types |
| Coupons | 3 | Active with usage tracking |
| Segments | 3 | VIP Gold, Inactive 30+, Corporate |
| Feedback | ~18 | Star ratings with comments |
| WhatsApp Templates | 3 | Welcome, Points Earned, Birthday |
| Automation Rules | 2 | Points earned, Birthday |
| Loyalty Settings | 1 | Full configuration |

### Menu Items in Demo Data
The seed script includes 20 realistic menu items across 6 categories:
- **North Indian**: Butter Chicken, Paneer Tikka, Dal Makhani, Biryani
- **Breads**: Naan, Garlic Naan
- **South Indian**: Masala Dosa, Idli Sambar
- **Chinese**: Veg Fried Rice, Manchurian
- **Continental**: Pasta Alfredo, Caesar Salad, Margherita Pizza
- **Desserts**: Gulab Jamun, Rasmalai, Brownie Sundae
- **Beverages**: Mango Lassi, Masala Chai, Cold Coffee, Fresh Lime Soda

Each item has realistic food-level notes (e.g., "Extra gravy", "Less spicy", "No cream").

## Backend Endpoints

| Endpoint | Purpose | Data Source |
|----------|---------|-------------|
| `POST /api/auth/demo-login` | Instant demo access | Local MongoDB |
| `POST /api/auth/mygenie-login` | Production auth | MyGenie API |
| `POST /api/auth/login` | Unified entry | Routes to mygenie-login |

## Frontend Implementation

### File Structure
```
frontend/src/
  pages/LoginPage.jsx             # Login form + Demo Mode button
  contexts/AuthContext.jsx         # isDemoMode state, demoLogin()
  components/shared/DemoModeBanner.jsx  # Purple banner component
  components/MobileLayout.jsx      # Includes DemoModeBanner
```

### AuthContext
- `isDemoMode` state persisted in localStorage
- `demoLogin()` function for one-click demo access

### DemoModeBanner
- Purple gradient banner at top of every page in demo mode
- Sticky positioning, clearly indicates demo status

## Usage

### Seeding Demo Data
```bash
cd /app/backend
python seed_demo_data.py
```

### API Testing
```bash
# Demo login
curl -X POST https://cmv2-crm-dev.preview.emergentagent.com/api/auth/demo-login

# Login with credentials
curl -X POST https://cmv2-crm-dev.preview.emergentagent.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@restaurant.com","password":"demo123"}'
```

## Quick Reference

| Feature | Demo Mode | Regular Mode |
|---------|-----------|--------------|
| Login Method | One-click button | Email + Password |
| Authentication | Local DB | MyGenie API |
| Banner Display | Yes (purple) | No |
| AI Insights | Fully populated | Depends on order data |
| `is_demo` flag | `true` | `false` |

---

**Status**: Fully Implemented and Working
**Last Updated**: March 3, 2026
