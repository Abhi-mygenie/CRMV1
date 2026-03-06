# DinePoints - Restaurant CRM & Loyalty System PRD

## Original Problem Statement
Pull and build the DinePoints CRM app from https://github.com/Abhi-mygenie/CRMV1.git

## Architecture
- **Frontend**: React 18 + Tailwind CSS + Shadcn/UI + Capacitor 6 (iOS/Android)
- **Backend**: Python FastAPI
- **Database**: MongoDB
- **Auth**: JWT-based + Demo Mode

## User Personas
1. **Restaurant Owners** - Primary users managing customer loyalty programs
2. **Demo Users** - Exploring the platform with pre-loaded test data

## Core Requirements (Static)
- Customer Management with 75+ fields
- Loyalty Program (Bronze/Silver/Gold/Platinum tiers)
- Points & Wallet Management
- AI-powered Customer Insights
- POS Integration via webhooks
- WhatsApp Automation
- Coupon Management
- Feedback Collection
- QR Code Customer Registration

## What's Been Implemented (March 6, 2026)
- [x] Repository cloned from GitHub
- [x] Backend setup with FastAPI and all routers
- [x] Frontend setup with React 18 and Capacitor
- [x] MongoDB connection configured
- [x] Demo data seeded (55 customers, 294 orders, 1050+ order items)
- [x] Demo login functionality
- [x] Dashboard with analytics
- [x] Customers list with filters
- [x] Customer detail page with AI insights
- [x] Fixed PointsTransaction schema for flexible field mapping
- [x] Customer row click navigation enabled
- [x] React StrictMode disabled for smoother transitions

## Key Features
| Feature | Status |
|---------|--------|
| Customer CRUD | ✅ Working |
| Loyalty Tiers | ✅ Working |
| Points Transactions | ✅ Working |
| Wallet Transactions | ✅ Working |
| AI Insights | ✅ Working |
| Customer Segments | ✅ Working |
| Feedback | ✅ Working |
| Settings | ✅ Working |
| Demo Mode | ✅ Working |

## Prioritized Backlog
### P0 - Critical
- None currently blocking

### P1 - High Priority
- WhatsApp Integration (requires API keys)
- Production auth with MyGenie API

### P2 - Medium Priority
- Native mobile app builds (Capacitor)
- Email notifications
- SMS integration

## Next Tasks
1. Configure production environment variables
2. Set up WhatsApp Business API integration
3. Build native iOS/Android apps
4. Deploy to production
