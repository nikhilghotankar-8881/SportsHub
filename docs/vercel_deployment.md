# 🚀 Deploying SportsHub to Vercel

This guide walks you through deploying **SportsHub** to **Vercel** serverless hosting with a cloud PostgreSQL database.

---

## 🏗️ Architecture Overview on Vercel

- **Frontend & Static Files:** Served directly from Vercel's global Edge CDN ([`/static/`](file:///c:/Users/NIKHIL/OneDrive/Desktop/Sports_hub/static)).
- **Backend:** Python 3.11/3.12/3.13 Serverless Functions executed via [`api/index.py`](file:///c:/Users/NIKHIL/OneDrive/Desktop/Sports_hub/api/index.py) configured in [`vercel.json`](file:///c:/Users/NIKHIL/OneDrive/Desktop/Sports_hub/vercel.json).
- **Database:** Serverless cloud PostgreSQL (Recommended: **[Neon.tech](https://neon.tech)** or **[Supabase](https://supabase.com)** — both offer generous 100% free tiers).

---

## 📋 Prerequisites

1. A **[Vercel](https://vercel.com)** account (free).
2. A free serverless PostgreSQL database from **[Neon](https://neon.tech)** (takes 30 seconds to create).
3. Your **Razorpay** test mode credentials (Key ID and Secret Key).

---

## ⚡ Step-by-Step Deployment Instructions

### Step 1: Create a Free Cloud PostgreSQL Database (Neon)
1. Go to **[Neon.tech](https://neon.tech)** and sign up / log in.
2. Click **Create Project** (Name: `sportshub-db`).
3. Under **Connection Details**, copy your `postgres://...` connection string.

### Step 2: Seed the Cloud Database
Before launching live or after connecting, seed your initial products and admin user into Neon:
```bash
# In your terminal, set DATABASE_URL temporarily to your Neon URL:
$env:DATABASE_URL="postgresql://user:password@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require"

# Run the seeding script:
python seed_db.py
```
This automatically creates all database tables, seeds the default admin user (`admin@sportshub.com` / `Admin@12345`), creates 12 sports products across all categories, and activates coupons and flash sales.

---

### Step 3: Push Repository to GitHub
```bash
git add .
git commit -m "feat: complete professional SportsHub upgrade with Vercel serverless support"
git push origin main
```

---

### Step 4: Import Project into Vercel
1. Log in to your **[Vercel Dashboard](https://vercel.com/dashboard)**.
2. Click **"Add New..."** → **"Project"**.
3. Import your **`SportsHub`** GitHub repository.
4. In **Project Settings**:
   - **Framework Preset:** Leave as *Other*.
   - **Root Directory:** `./`
5. Expand the **Environment Variables** section and add the following keys:

| Key | Example Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://user:pass@ep-xyz.aws.neon.tech/neondb?sslmode=require` | Cloud Postgres connection string |
| `SECRET_KEY` | `sportshub-prod-super-secure-key-2026-xyz` | 32+ character random secret string |
| `RAZORPAY_KEY_ID` | `rzp_test_TEocfg67ysVCVM` | Razorpay Test Key ID |
| `RAZORPAY_KEY_SECRET` | `cBrjWcQlgex31RvAF4I2DAS0` | Razorpay Test Key Secret |
| `MAIL_SERVER` | `smtp.gmail.com` | SMTP host |
| `MAIL_PORT` | `587` | SMTP port |
| `MAIL_USE_TLS` | `true` | TLS encryption flag |
| `MAIL_USERNAME` | `your-email@gmail.com` | Email account for notifications |
| `MAIL_PASSWORD` | `your-gmail-app-password` | Gmail 16-character App Password |
| `MAIL_DEFAULT_SENDER` | `your-email@gmail.com` | Default sender email |

6. Click **Deploy**!

---

## 🛡️ Vercel Specific Files Added to SportsHub

- [`vercel.json`](file:///c:/Users/NIKHIL/OneDrive/Desktop/Sports_hub/vercel.json): Tells Vercel how to route requests to the `@vercel/python` serverless lambda while serving static files with high-speed CDN caching.
- [`api/index.py`](file:///c:/Users/NIKHIL/OneDrive/Desktop/Sports_hub/api/index.py): WSGI entry point that initializes the Flask application inside the serverless execution environment.
- [`requirements.txt`](file:///c:/Users/NIKHIL/OneDrive/Desktop/Sports_hub/requirements.txt): Clean 22-package set adhering to Vercel's 250 MB lambda size limits.
- [`seed_db.py`](file:///c:/Users/NIKHIL/OneDrive/Desktop/Sports_hub/seed_db.py): Instant 1-click cloud database setup script.
