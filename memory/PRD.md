# DinePoints CRM V1 - Product Requirements Document

## Original Problem Statement
Pull and build CRMV1 from GitHub: https://github.com/Abhi-mygenie/CRMV1.git with MongoDB database import script

## Architecture
- **Frontend**: React 19 + Tailwind CSS + shadcn/ui + Capacitor (mobile-ready)
- **Backend**: FastAPI (Python) with Motor (async MongoDB driver)
- **Database**: MongoDB with 15+ collections
- **Scheduler**: APScheduler for loyalty cron jobs

## User Personas
1. **Restaurant Owners** - Manage customers, loyalty programs, send WhatsApp campaigns
2. **Demo Users** - Explore features with pre-loaded test data

## Core Requirements (Static)
- Customer management with loyalty tiers
- Points earning/redemption system
- Wallet deposits and transactions
- Coupon generation and tracking
- WhatsApp template messaging
- Feedback collection and analytics
- MyGenie POS data migration

## What's Been Implemented (March 7, 2026)
- ✅ GitHub repository cloned and built
- ✅ Backend dependencies installed (apscheduler, qrcode, pillow)
- ✅ Frontend dependencies installed via yarn
- ✅ MongoDB seeded with 4,409 documents
- ✅ Demo login mode functional
- ✅ All pages working: Dashboard, Customers, Templates, Feedback, Settings

## Collections Seeded
- users: 3 documents
- loyalty_settings: 3 documents  
- customers: 85 documents
- segments: 4 documents
- coupons: 3 documents
- orders: 794 documents
- order_items: 2,560 documents
- points_transactions: 826 documents
- wallet_transactions: 61 documents
- feedback: 20 documents
- automation_rules: 22 documents
- whatsapp_templates: 23 documents

## Prioritized Backlog
### P0 (Critical)
- None - core functionality working

### P1 (High Priority)
- Configure WhatsApp API key for messaging
- Enable loyalty/coupon/wallet features (disabled by default)

### P2 (Medium Priority)
- Analytics dashboard with charts
- Customer retention reports
- Export functionality

## Next Tasks
1. WhatsApp API integration setup
2. Enable feature toggles in Settings
3. Test customer sync with MyGenie POS
