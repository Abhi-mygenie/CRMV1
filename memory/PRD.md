# CRM V1 Project - PRD

## Original Problem Statement
Pull https://github.com/Abhi-mygenie/CRMV1.git and build this project, import DB data, list users.

## Architecture
- **Backend**: FastAPI (Python) on port 8001
- **Frontend**: React with Tailwind CSS on port 3000
- **Database**: MongoDB (local instance)

## What's Been Implemented (March 7, 2026)
- [x] Cloned CRM repository from GitHub
- [x] Set up environment files (.env for backend and frontend)
- [x] Installed all dependencies (Python + Node.js)
- [x] Imported 15 database collections (4,406 documents)
- [x] Services running and healthy

## Core Features (from codebase)
- User authentication (JWT)
- Customer management with QR codes
- Points/loyalty system
- Digital wallet
- Coupons management
- Feedback system
- WhatsApp integration
- POS integration

## Database Collections
- users (3)
- customers (85)
- orders (794)
- order_items (2,560)
- points_transactions (826)
- wallet_transactions (61)
- automation_rules (22)
- whatsapp_templates (23)
- segments (4)
- loyalty_settings (3)
- coupons (3)
- feedback (20)

## Users in System
1. demo@restaurant.com - Demo Restaurant & Cafe
2. owner@18march.com - 18march
3. owner@youngmonk.com - Young Monk Cafe

## Next Tasks
- P0: Test full user flow (login, dashboard)
- P1: Test customer management features
- P2: Test WhatsApp integration
