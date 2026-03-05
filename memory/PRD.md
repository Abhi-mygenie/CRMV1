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
- Repository cloned and set up
- Backend dependencies installed (FastAPI, MongoDB, APScheduler, etc.)
- Frontend dependencies installed (React 19, Tailwind, Shadcn/UI, Capacitor)
- Demo data seeded (55 customers, 292 orders, 1015 order items, etc.)
- Database imported from db_export (1967 customers, 280 points transactions)
- Added `customer_app_config` collection from separate git repo
- Services running (backend on port 8001, frontend on port 3000)
- Demo mode login verified working

**Field Rename (March 5, 2026)**
- Renamed `mygenie_customer_id` to `pos_customer_id`
- Updated 2146 existing customers in database
- Added new "Migration" tab in Settings (FIRST tab now)
- Tab order: Migration -> Profile -> WhatsApp -> Loyalty -> Coupons
- 3-step migration flow UI
- Backend endpoints: GET /api/migration/status, POST /api/migration/confirm, POST /api/migration/revert, POST /api/migration/revert-customers, POST /api/migration/revert-orders, POST /api/migration/sync-orders (placeholder)

**Order Webhook & Data Model Expansion (March 5, 2026)**
- Expanded POST /api/pos/orders webhook to accept ~40 new fields
- Updated Pydantic schemas (POSOrderWebhook, OrderItem)
- Seeded 100 realistic orders for "18march" restaurant

**UI Refactoring - Add New Customer Form (March 5, 2026)**
- Removed/reinstated "Coming Soon" overlays per user request
- AI-driven read-only fields for Dining Preferences and Special Occasions
- Reorganized form layout with "Other Information" section
- Implemented inline Corporate Customer fields with radio buttons (replacing button-style and separate accordion)
- "Coming Soon" overlays on: Contact Preferences, Membership, Source & Journey, Custom Fields & Notes

**Inline Corporate Fields (March 5, 2026)**
- Replaced button-style Customer Type selection with radio buttons (Normal/Corporate)
- When Corporate is selected, corporate fields (GST Name, GST Number, Billing Address, Credit Limit, Payment Terms) appear inline with orange-tinted background
- Removed separate "Corporate Info" accordion section
- Tested: 10/10 test cases passed (100% frontend)

**Coming Soon Sections (March 5, 2026) - Already Complete**
- Contact Preferences (blue) - WhatsApp Opt-in, Promo SMS switches
- Membership (purple) - Membership ID, Referral Code fields
- Source & Journey (amber) - Lead Source, Campaign Source fields
- Custom Fields & Notes (gray) - Custom Field 1, Notes fields
- All wrapped with ComingSoonOverlay component with rocket icon

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

**Phase 1 Bug Fix — Add Customer Data Loss (March 5, 2026)**
- Fixed `handleAddCustomer` to send ALL user-filled fields (was only sending 9 basic fields)
- Now sends: corporate fields (GST, billing, credit limit, payment terms), full address (6 fields), flags (VIP, complaint, blacklist)
- Verified via curl: all 17+ fields saved correctly to MongoDB

## Next Action Items
- Phase 2: Align Edit Customer form with Add form (add missing fields, match UI patterns)
- Phase 3: Add high-impact segment filters (gender, total_spent, is_blocked)
- Implement Sync Orders when MyGenie Order API endpoint is provided

## Backlog / Future Enhancements
- P1: Activate "Sync Orders" from MyGenie (blocked on API endpoint from user)
- P2: Clarify business logic for MyGenie fields (self_discount, paid_room, room_id, address_id)
- P2: Full E2E testing of MyGenie order webhook
- P2: Full E2E testing of Sync Orders feature
- P3: Refactor CustomersPage.jsx into smaller components
- P3: Push notification integration for mobile apps
