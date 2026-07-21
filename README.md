# SportsHub 🏀⚽🏏

SportsHub is a Flask-based sports equipment e-commerce platform with full payment integration, email notifications, and an admin dashboard.

## Features

- User Authentication & Authorization
- Comprehensive Product Catalog with Search, Filters & Pagination
- Shopping Cart & Checkout System
- **Payment Integration**: Razorpay Online Payments & Cash on Delivery (COD)
- **Email Notifications**: Centralized `Flask-Mail` integration with HTML templates
- **Promotions**: Discount Coupons & Flash Sales
- Order Management with Status Tracking & History
- PDF Invoice Generation
- Wishlist & Product Reviews
- Advanced Admin Dashboard with Analytics
- Inventory Management
- Responsive UI built with Bootstrap 5

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask 3.x |
| Database (Local) | SQLite |
| Database (Production) | PostgreSQL |
| ORM | SQLAlchemy 2.x + Flask-Migrate |
| Auth | Flask-Login + Werkzeug |
| Email | Flask-Mail |
| Payments | Razorpay |
| PDF | ReportLab |
| WSGI | Gunicorn |
| Hosting | Render |

---

## Local Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/nikhilghotankar-8881/SportsHub.git
cd SportsHub
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements-prod.txt
```

### 4. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with your real values (see Environment Variables section below)
```

### 5. Run Database Migrations
```bash
flask db upgrade
```

### 6. Running the Application

**Local Flask development (Windows/Mac/Linux):**
```bash
python run.py
```
*(Runs on http://127.0.0.1:5000)*

**Windows production-like testing (using Waitress):**
```bash
waitress-serve --listen=127.0.0.1:8000 run:app
```
*(Runs on http://127.0.0.1:8000)*

**Render/Linux production (using Gunicorn):**
```bash
gunicorn run:app
```
*(Used internally by Render during deployment)*

---

## Environment Variables

Create a `.env` file in the project root (never commit this file):

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ Yes | Strong random string for Flask sessions |
| `DATABASE_URL` | Production only | PostgreSQL URL (Render sets this automatically) |
| `RAZORPAY_KEY_ID` | For payments | Razorpay Key ID (test or live) |
| `RAZORPAY_KEY_SECRET` | For payments | Razorpay Key Secret |
| `MAIL_SERVER` | For emails | SMTP server (default: `smtp.gmail.com`) |
| `MAIL_PORT` | For emails | SMTP port (default: `587`) |
| `MAIL_USE_TLS` | For emails | Use TLS (default: `true`) |
| `MAIL_USERNAME` | For emails | Your email address |
| `MAIL_PASSWORD` | For emails | Gmail App Password (not your regular password) |
| `MAIL_DEFAULT_SENDER` | For emails | From address for outgoing emails |

> **Local Development**: `DATABASE_URL` is not needed locally. The app automatically uses SQLite.
>
> **Gmail App Password**: Generate one at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

See `.env.example` for a template with placeholder values.

---

## Database Migrations

```bash
# Check current migration state
flask db current

# Show all available migration heads
flask db heads

# Apply all pending migrations (run this on first deploy and after schema changes)
flask db upgrade

# Generate a new migration after changing models.py
flask db migrate -m "describe your change"
```

---

## Health Check

The application exposes a health check endpoint:

```
GET /health
→ {"status": "ok"}
```

This is used by Render to verify the service is running.

---

## 📧 Email Notification System

SportsHub uses `Flask-Mail` for transactional emails. If email credentials are not configured, the app logs a warning but **never crashes**.

### Supported Notifications
- Registration Welcome Email
- Password Change Security Alert
- Order Confirmation (Razorpay / Online)
- Cash on Delivery (COD) Order Placed
- Payment Success (Razorpay verification)
- Order Status Updates (Confirmed, Packed, Out for Delivery)
- Order Shipped
- Order Delivered
- Order Cancelled
- Contact Us Confirmation

---

## 🚀 Render Deployment

### Step 1 — Push to GitHub
Ensure your code is pushed to GitHub. The `.env` file must **not** be committed (already excluded in `.gitignore`).

### Step 2 — Create a PostgreSQL Database on Render
1. Go to [render.com](https://render.com) → **New** → **PostgreSQL**
2. Give it a name (e.g., `sportshub-db`)
3. Copy the **Internal Database URL** (you'll need it in Step 4)

### Step 3 — Create a Web Service on Render
1. Go to **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:

| Setting | Value |
|---|---|
| **Name** | `sportshub` |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements-prod.txt` |
| **Start Command** | `gunicorn run:app` |

### Step 4 — Set Environment Variables on Render
In your Web Service → **Environment** tab, add:

```
SECRET_KEY=<generate a strong random key>
DATABASE_URL=<paste the Internal Database URL from Step 2>
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxx
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### Step 5 — Run Migrations on First Deploy
After the first deploy, open the Render **Shell** tab and run:
```bash
flask db upgrade
```

Or add it to the Build Command:
```
pip install -r requirements-prod.txt && flask db upgrade
```

### Step 6 — Verify
Visit `https://your-app.onrender.com/health` — you should see `{"status": "ok"}`.

---

## Project Structure

```
SportsHub/
├── app/
│   ├── __init__.py          # App factory, extensions
│   ├── config.py            # Configuration (SQLite local / PostgreSQL prod)
│   ├── models.py            # SQLAlchemy models
│   ├── forms.py             # WTForms
│   ├── helpers/
│   │   └── email_helper.py  # Flask-Mail email senders
│   └── routes/              # Blueprint route handlers
├── templates/               # Jinja2 HTML templates
│   └── emails/              # Transactional email templates
├── static/                  # CSS, JS, images
├── migrations/              # Flask-Migrate Alembic migrations
├── run.py                   # App entry point (gunicorn run:app)
├── requirements-prod.txt    # Production dependencies (for Render)
├── requirements.txt         # Full local dev dependencies
└── .env.example             # Environment variable template
```