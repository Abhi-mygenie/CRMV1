# DinePoints CRM - Database Export & Seed Scripts

## Overview
This folder contains database seed scripts and JSON data files for initializing the DinePoints CRM MongoDB database.

## Files

### Scripts
- `seed_database.py` - Main import script (supports upsert and clear modes)
- `import_data.py` - Alternative import script

### Data Files (JSON)
| File | Description | Key Fields |
|------|-------------|------------|
| `users.json` | Restaurant owner accounts | id, email, password_hash, mygenie_token |
| `loyalty_settings.json` | Feature toggles & settings | loyalty_enabled, coupon_enabled, wallet_enabled |
| `customers.json` | Customer profiles | id, pos_customer_id, name, phone, dob |
| `segments.json` | Marketing segments | id, name, filter_criteria |
| `coupons.json` | Promotional codes | id, code, discount_type, discount_value |
| `orders.json` | Order history | id, pos_order_id, customer_id, items |
| `order_items.json` | Individual order items | id, order_id, item_name, item_price |
| `points_transactions.json` | Points history | id, customer_id, points, transaction_type |
| `wallet_transactions.json` | Wallet history | id, customer_id, amount, type |
| `feedback.json` | Customer reviews | id, customer_id, rating, comment |
| `automation_rules.json` | WhatsApp automation | id, event_type, template_id |
| `whatsapp_templates.json` | Message templates | id, name, template_body |

## Usage

### Standard Import (Upsert Mode)
```bash
cd /app/db_export
python seed_database.py
```

### Fresh Import (Clear First)
```bash
python seed_database.py --clear
```

### Environment Variables
```bash
export MONGO_URL="mongodb://localhost:27017"
export DB_NAME="test_database"
```

## Feature Toggles

All features are **DISABLED by default** in `loyalty_settings.json`:

```json
{
  "loyalty_enabled": false,
  "coupon_enabled": false,
  "wallet_enabled": false
}
```

This ensures:
- No points calculations during customer/order migration
- Features remain hidden until explicitly enabled
- Safe data migration without side effects

## Migration API Endpoints

### Customer Migration
```
POST https://preprod.mygenie.online/api/v1/vendoremployee/whatsappcrm/customer-migration
```

### Order Migration (Paginated)
```
POST https://preprod.mygenie.online/api/v1/vendoremployee/whatsappcrm/customer-order-migration?page=N
```

## Field Mappings

### Customer Fields
| MyGenie API | CRM Database | Type Conversion |
|-------------|--------------|-----------------|
| `id` | `pos_customer_id` | int |
| `pos_id` | `pos_id` | str |
| `restaurant_id` | `pos_restaurant_id` | str |
| `name` | `name` | str |
| `phone` | `phone` | str |
| `country_code` | `country_code` | str |
| `email` | `email` | str |
| `dob` | `dob` | str |
| `anniversary` | `anniversary` | str |
| `customer_type` | `customer_type` | str |
| `gst_name` | `gst_name` | str |
| `gst_number` | `gst_number` | str |
| `address` | `address` | str |
| `city` | `city` | str |
| `pincode` | `pincode` | str |
| `loyalty_point` | `total_points` | int |
| `total_points_earned` | `total_points_earned` | str → int |
| `total_points_redeemed` | `total_points_redeemed` | str → int |
| `wallet_balance` | `wallet_balance` | int → float |
| `total_wallet_received` | `total_wallet_received` | str → float |
| `total_wallet_used` | `total_wallet_used` | str → float |
| `total_coupon_used` | `total_coupon_used` | int |
| `created_time` | `created_at` | str |
| `updated_time` | `last_updated_at` | str |

### Calculated Fields (from Orders sync)
| CRM Field | Source |
|-----------|--------|
| `total_spent` | Sum of order amounts |
| `total_visits` | Count of orders |
| `last_visit` | Latest order date |
| `tier` | Calculated from total_points |

### Order Fields
| MyGenie API | CRM Database |
|-------------|--------------|
| `id` | `pos_order_id` |
| `user.phone` | `cust_mobile` |
| `user.f_name` | `cust_name` |
| `orderDetails` | `items` |
| `orderDetails[].food_details.name` | `items[].item_name` |
| `orderDetails[].price` | `items[].item_price` |

## Notes

1. The seed script automatically adds missing toggle fields to existing `loyalty_settings` documents
2. All documents use `id` field (not `_id`) for upsert operations
3. Order import preserves `pos_order_id` for duplicate detection
4. Customer import preserves `pos_customer_id` for MyGenie sync
