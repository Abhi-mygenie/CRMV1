# DinePoints CRM V1 - Product Requirements Document

## Overview
Restaurant CRM system for customer management, loyalty points, and WhatsApp marketing integration with MyGenie POS.

## Repository
- Source: https://github.com/Abhi-mygenie/CRMV1
- Stack: React (Frontend) + FastAPI (Backend) + MongoDB

---

## Migration API Endpoints (Updated March 2026)

### Customer Migration (Step 1)
```
POST /api/v1/vendoremployee/whatsappcrm/customer-migration
Authorization: Bearer {mygenie_token}
```

**Field Mappings:**
| API Field | CRM Field |
|-----------|-----------|
| `name` | `name` |
| `phone` | `phone` |
| `dob` | `dob` |
| `anniversary` | `anniversary` |
| `country_code` | `country_code` |
| `customer_type` | `customer_type` |
| `address` | `address` |
| `city` | `city` |
| `pincode` | `pincode` |
| `pos_id` | `pos_id` |
| `id` | `pos_customer_id` |

### Order Migration (Step 2)
```
POST /api/v1/vendoremployee/whatsappcrm/customer-order-migration?page=N
Authorization: Bearer {mygenie_token}
```

**Pagination:**
- 25 orders per page
- Response includes: `current_page`, `last_page`, `total_orders`

**Field Mappings:**
| API Field | CRM Field |
|-----------|-----------|
| `id` | `pos_order_id` |
| `restaurant_order_id` | `restaurant_order_id` |
| `user.phone` | `cust_mobile` |
| `user.f_name + l_name` | `cust_name` |
| `orderDetails` | `items` |
| `orderDetails[].food_details.name` | `items[].item_name` |
| `orderDetails[].price` | `items[].item_price` |
| `order_status` | `order_status` |

---

## Feature Toggles

All features are **DISABLED by default** during migration:

| Feature | Toggle Field | Tab Location |
|---------|--------------|--------------|
| Loyalty Points | `loyalty_enabled` | Settings > Loyalty |
| Coupons | `coupon_enabled` | Settings > Coupons |
| Wallet | `wallet_enabled` | Settings > Wallet |

When disabled:
- No points calculations during order migration
- No coupon/wallet features visible in UI
- Safe for data migration without side effects

---

## Database Collections

| Collection | Documents | Description |
|------------|-----------|-------------|
| users | 3 | Restaurant owner accounts |
| loyalty_settings | 3 | Points/coupon/wallet config |
| customers | 1,480+ | Customer profiles |
| segments | 4 | Marketing segments |
| coupons | 3 | Promotional codes |
| orders | 5,000+ | Order history |
| order_items | 5,000+ | Individual items for analytics |
| points_transactions | 826 | Points history |
| wallet_transactions | 61 | Wallet history |
| feedback | 20 | Customer reviews |
| automation_rules | 22 | WhatsApp automation |
| whatsapp_templates | 23 | Message templates |

---

## User Accounts (Seeded)

| Email | Restaurant | Password |
|-------|------------|----------|
| demo@restaurant.com | Demo Restaurant | (check db) |
| owner@18march.com | 18march | test123 |
| owner@youngmonk.com | Young Monk Cafe | (check db) |
| owner@kunafamahal.com | Kunafa Mahal | (check db) |

---

## Settings Tabs

1. **Migration** - Data sync from MyGenie POS
2. **Profile** - Restaurant profile settings
3. **WhatsApp** - Automation rules & templates
4. **Loyalty** - Points earning/redemption (toggle + settings)
5. **Coupons** - Coupon management (toggle + list)
6. **Wallet** - Wallet feature (toggle + coming soon)

---

## Customer Filters

### Basic Filters
- Tier (Bronze/Silver/Gold/Platinum)
- Customer Type
- City
- Inactive For (Win-back)
- Total Visits
- Total Spent

### Marketing Filters
- Lead Source
- Gender
- WhatsApp Opt-In

### Other Filters
- Dining Preferences
- Special Occasions
- Loyalty & Wallet

---

## Background Sync Features

### Customer Sync
- Runs in background
- Progress: "Syncing customers... 100/1432"
- Endpoint: `GET /api/customers/sync-status`

### Order Sync
- Runs in background with pagination
- Progress: "Syncing orders... 1700/7000"
- Endpoint: `GET /api/migration/sync-orders/status`

---

## What's Implemented (March 6, 2026)

- [x] Repository cloned and built
- [x] Seed script with toggle defaults
- [x] Customer migration with correct field mappings
- [x] Order migration with pagination (80+ pages)
- [x] Background sync with progress display
- [x] Customer stats update (total_visits, total_spent, last_visit)
- [x] Revert functionality with AlertDialog
- [x] Segments tab bug fix
- [x] Filter reorganization
- [x] Feature toggles (Loyalty/Coupon/Wallet) - all disabled by default
- [x] Separate tabs for each toggle

---

## Backlog

### P0 (Critical)
- None currently

### P1 (High)
- Wallet features implementation
- WhatsApp integration testing

### P2 (Medium)
- Migration summary dashboard
- Bulk customer actions
- Export functionality

### P3 (Low)
- Advanced analytics
- Multi-language support

---

## Running the Seed Script

```bash
cd /app/db_export

# Update/Upsert mode (default)
python seed_database.py

# Clear and fresh import
python seed_database.py --clear
```

**Note:** All feature toggles will be set to `false` (disabled) by default.
