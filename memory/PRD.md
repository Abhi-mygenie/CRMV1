# CRM V1 Project - PRD

## Original Problem Statement
Pull https://github.com/Abhi-mygenie/CRMV1.git and build this project, import DB data, list users.

## Architecture
- **Backend**: FastAPI (Python) on port 8001
- **Frontend**: React with Tailwind CSS on port 3000
- **Database**: MongoDB (local instance)

## What's Been Implemented
- [x] Cloned CRM repository from GitHub
- [x] Set up environment files (.env for backend and frontend)
- [x] Installed all dependencies (Python + Node.js)
- [x] Imported 15 database collections (4,406 documents)
- [x] Demo Login for testing (demo@mygenie.com / demo123)
- [x] Dashboard with comprehensive metrics grid (conditional row visibility)
- [x] Customer management with filters, segments, add/edit
- [x] Data sync with transaction histories (points, wallet, coupons)
- [x] Filter drawer redesigned as compact slide-up modal
- [x] **Filter drawer reorganized into Basic & Advanced sections** (Feb 7, 2026)
  - Basic: Tier, Type, City, Inactive, Sort By
  - Advanced: Visits, Spent, Diet, Time Slot, Dining, Gender, Source, WhatsApp, VIP, Blocked, Blacklist, Complaint, Birthday, Anniversary
  - Z-index fix applied for proper layering above bottom nav

## Core Features (from codebase)
- User authentication (JWT + Demo Login)
- Customer management with QR codes
- Points/loyalty system
- Digital wallet
- Coupons management
- Feedback system
- WhatsApp integration
- POS integration

## Database Collections
- users (3), customers (85), orders (794), order_items (2,560)
- points_transactions (826), wallet_transactions (61)
- automation_rules (22), whatsapp_templates (23)
- segments (4), loyalty_settings (3), coupons (3), feedback (20)

## Key API Endpoints
- POST /api/auth/demo-login
- GET /api/feedback/dashboard-stats/{user_id}
- GET /api/customers/{user_id}
- POST /api/customers/segment/{user_id}
- POST /api/mygenie/sync-customers
- POST /api/mygenie/sync-orders

## Upcoming Tasks
- P1: Add `+ Add` button to Segments page/tab header

## Backlog
- Refactor CustomersPage.jsx into smaller components (FilterDrawer, SegmentsTab)
- Refactor feedback.py into smaller service modules
