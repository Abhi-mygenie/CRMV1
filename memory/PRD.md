# DinePoints (MyGenie CRM) - PRD

## Original Problem Statement
Clone and set up the repository: https://github.com/Abhi-mygenie/CMV2.git

## Architecture
- **Frontend**: React 18 + Tailwind CSS + Shadcn/UI + Capacitor 6 (iOS/Android)
- **Backend**: Python FastAPI
- **Database**: MongoDB
- **Auth**: JWT-based + Demo Mode

## What's Been Implemented
**Date: March 5, 2026**
- ✅ Repository cloned and set up
- ✅ Backend dependencies installed (FastAPI, MongoDB, APScheduler, etc.)
- ✅ Frontend dependencies installed (React 19, Tailwind, Shadcn/UI, Capacitor)
- ✅ Demo data seeded (55 customers, 292 orders, 1015 order items, etc.)
- ✅ Database imported from db_export (1967 customers, 280 points transactions)
- ✅ Added `customer_app_config` collection from separate git repo
- ✅ Services running (backend on port 8001, frontend on port 3000)
- ✅ Demo mode login verified working

**Field Rename (March 5, 2026)**
- ✅ Renamed `mygenie_customer_id` → `pos_customer_id`
- This field stores the customer ID from POS API
- Acts as the bridge/link between our DB and POS system
- Updated 2146 existing customers in database
- ✅ Added new "Migration" tab in Settings (FIRST tab now)
- ✅ Tab order: Migration → Profile → WhatsApp → Loyalty → Coupons
- ✅ 3-step migration flow UI:
  - Step 1: Sync Customers (with individual Revert button when synced)
  - Step 2: Sync Orders (with individual Revert button when synced) - placeholder awaiting API
  - Step 3: Confirm Migration button
- ✅ Backend endpoints:
  - GET /api/migration/status
  - POST /api/migration/confirm
  - POST /api/migration/revert (all data)
  - POST /api/migration/revert-customers (only customers)
  - POST /api/migration/revert-orders (only orders)
  - POST /api/migration/sync-orders (placeholder)
- ✅ After confirmation, shows "Migration Complete" state
- ✅ Individual revert buttons appear after each sync completes

## Core Features (Existing)
- Customer Management with 75+ fields
- AI Insights (top items, cuisine preferences, visit patterns)
- Loyalty Program (Bronze/Silver/Gold/Platinum tiers)
- POS Order Webhook integration
- Coupon Management
- WhatsApp Automation templates
- Feedback Collection
- QR Code Registration
- Customer Segments

## Demo Credentials
- **Demo Mode**: Click "Try Demo Mode" on login page
- **Demo Account**: demo@restaurant.com / demo123

## Database Collections (15 total)
- customers, orders, order_items, points_transactions, wallet_transactions
- coupons, loyalty_settings, feedback, whatsapp_templates, automation_rules
- segments, users, customer_app_config, cron_job_logs, whatsapp_event_template_map

## Next Action Items
- Implement Sync Orders when MyGenie Order API endpoint is provided

## Backlog / Future Enhancements
- P1: MyGenie Order API integration for order sync
- P2: Add more analytics dashboards
- P3: Push notification integration for mobile apps
