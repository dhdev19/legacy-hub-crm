# Legacy Hub CRM

A full-featured CRM for Legacy Hub built with FastAPI + Jinja2 + MySQL.

## Tech Stack
- **Backend:** FastAPI (Python)
- **Templates:** Jinja2 + Tailwind CSS (CDN) + Vanilla JS
- **Database:** MySQL
- **Auth:** JWT (HTTP-only cookies)
- **ORM:** SQLAlchemy
- **Migrations:** Alembic

## Setup & Installation

### 1. Prerequisites
- Python 3.10+
- MySQL 8.0+

### 2. Clone & Install
```bash
cd crm
pip install -r requirements.txt
```

### 3. Configure Environment
Edit `.env` file:
```
DATABASE_URL=mysql+pymysql://YOUR_USER:YOUR_PASSWORD@localhost:3306/legacy_hub_crm
SECRET_KEY=change-this-to-a-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

### 4. Create Database
```sql
CREATE DATABASE legacy_hub_crm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Run the App
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The app will auto-create all tables and seed:
- Superadmin account
- Default sources (Website, WhatsApp, Meta, Referral, Walk-in, Phone, Email)
- Default statuses (New, Contacted, Interested, Not Interested, Follow Up, Converted, Lost)

## Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Super Admin | `superadmin` | `legacyhubsuperadmin@123` |

## Roles & Access

### Super Admin (`/superadmin/`)
- Create / edit / delete admins
- View all activity logs

### Admin (`/admin/`)
- Manage projects (with NanoID webhook URLs)
- Manage sales persons
- View & manage all queries
- Add/edit/delete queries
- Assign queries to sales persons
- Manage global Sources & Statuses
- Add follow-ups to any query

### Sales Person (`/sales/`)
- View only their assigned queries
- Update query status
- Add follow-ups to their queries
- Add new queries (auto-assigned to themselves)
- View projects they are attached to

## Webhook Integration
Each project has a unique NanoID. Send POST requests to:
```
POST /webhook/{project_nanoid}/query
Content-Type: application/json

{
  "query_name": "Lead from Meta Ad",
  "client_name": "Rahul Sharma",
  "phone": "+91 98765 43210",
  "email": "rahul@example.com",
  "source": "Meta"
}
```
Query is auto-assigned to the sales person on that project with the fewest queries.

## FCM Integration (Future)
The `firebase-admin` SDK can be added to `requirements.txt`. Add FCM token to the `users` table and trigger notifications from `services/log_service.py` or router endpoints.

## Project Structure
```
crm/
├── main.py                 # App entry, startup seed
├── requirements.txt
├── .env
├── alembic.ini
├── alembic/
├── app/
│   ├── database.py
│   ├── dependencies.py     # Auth guards
│   ├── models/             # SQLAlchemy models
│   ├── routers/            # FastAPI route handlers
│   ├── services/           # Business logic
│   └── templates/          # Jinja2 HTML templates
```
