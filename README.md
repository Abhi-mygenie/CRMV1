# DinePoints CRM V1

Restaurant CRM system for customer management, loyalty points, coupons, wallet, and WhatsApp marketing integration with MyGenie POS.

## Tech Stack
- **Frontend**: React + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI (Python)
- **Database**: MongoDB

## Quick Start

### 1. Install Dependencies
```bash
# Backend
cd /app/backend
pip install -r requirements.txt

# Frontend
cd /app/frontend
yarn install
```

### 2. Seed Database
```bash
cd /app/db_export
python seed_database.py
```

### 3. Start Services
```bash
sudo supervisorctl restart backend frontend
```

## Default Users
| Email | Restaurant | Password |
|-------|------------|----------|
| owner@18march.com | 18march | test123 |
| owner@kunafamahal.com | Kunafa Mahal | (check db) |

## Feature Toggles

All features are **DISABLED by default**. Enable in Settings:

| Feature | Location |
|---------|----------|
| Loyalty Points | Settings > Loyalty |
| Coupons | Settings > Coupons |
| Wallet | Settings > Wallet |

## Migration from MyGenie POS

### Customer Sync
1. Go to Settings > Migration
2. Click "Sync Customers"
3. Progress shows: "Syncing customers... 100/1432"

### Order Sync
1. Sync customers first
2. Click "Sync Orders"
3. Progress shows: "Syncing orders... 1700/7000"
4. Handles pagination automatically (80+ pages)

## API Endpoints

### Customer Migration
```
POST /api/customers/sync-from-mygenie
GET /api/customers/sync-status
```

### Order Migration
```
POST /api/migration/sync-orders
GET /api/migration/sync-orders/status
```

### Revert Migration
```
POST /api/migration/revert-customers
POST /api/migration/revert-orders
```

## Project Structure
```
/app
├── backend/
│   ├── server.py           # FastAPI main app
│   ├── routers/            # API routes
│   │   ├── customers.py    # Customer + sync endpoints
│   │   ├── migration.py    # Order migration
│   │   ├── points.py       # Loyalty settings
│   │   └── ...
│   ├── models/schemas.py   # Pydantic models
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/          # React pages
│   │   │   ├── CustomersPage.jsx
│   │   │   ├── SettingsPage.jsx
│   │   │   └── ...
│   │   └── components/     # UI components
│   └── package.json
├── db_export/
│   ├── seed_database.py    # DB seed script
│   ├── *.json              # Seed data files
│   └── README.md
└── memory/
    └── PRD.md              # Product requirements
```

## Documentation
- `/app/memory/PRD.md` - Full product requirements
- `/app/db_export/README.md` - Database & migration docs

## License
Proprietary - MyGenie
