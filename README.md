# SportsHub 🏀⚽🏏

**SportsHub** is a full-stack e-commerce web application designed for sports equipment. It features a complete shopping experience, from browsing products and applying discount coupons to processing payments, tracking orders, and generating PDF invoices.

---

## 🌟 Key Features
- **User Authentication:** Secure registration, login, and password management.
- **Product Catalog:** Comprehensive product browsing with category filtering, search, and pagination.
- **Shopping Cart & Checkout:** Persistent cart, dynamic tax calculation (GST), and shipping logic.
- **Payment Integration:** Razorpay Test Mode for online transactions & Cash on Delivery (COD).
- **Email Notifications:** Automated alerts for registration, order updates, and password changes.
- **Promotions:** Discount coupons and time-limited Flash Sales.
- **Order Management:** Tracking statuses (Placed, Packed, Shipped, Delivered), history, and PDF invoices.
- **User Engagement:** Wishlist functionality and product reviews/ratings.
- **Admin Dashboard:** Comprehensive dashboard for managing inventory, orders, products, and analytics.

---

## 📸 Screenshots
*(Add screenshots of your application here, e.g., Homepage, Product Catalog, Admin Dashboard, Checkout Flow)*

---

## 🛠️ Tech Stack
| Component | Technology |
|---|---|
| **Backend Framework** | Python 3, Flask 3.x |
| **Database (Local)** | SQLite |
| **Database (Production)** | PostgreSQL |
| **ORM & Migrations** | SQLAlchemy 2.x, Flask-Migrate (Alembic) |
| **Authentication** | Flask-Login, Werkzeug (Password Hashing) |
| **Email System** | Flask-Mail (Jinja2 HTML Templates) |
| **Payment Gateway** | Razorpay SDK |
| **PDF Generation** | ReportLab |
| **Frontend** | HTML5, CSS3, Bootstrap 5, Jinja2 Templates |
| **WSGI Server (Prod)** | Gunicorn (Linux/Render) |
| **WSGI Server (Test)** | Waitress (Windows) |
| **Deployment** | Render |

---

## 🏗️ Application Architecture
The application follows the **Flask Application Factory** pattern, separating concerns into distinct blueprints (e.g., `auth`, `main`, `admin`, `products`, `checkout`). 

### 🗄️ Database Relationships
- **User:** One-to-Many with Orders, Reviews, CartItems, and WishlistItems.
- **Product:** One-to-Many with OrderItems, Reviews, CartItems, and WishlistItems. Many-to-One with Category.
- **Order:** One-to-Many with OrderItems. Many-to-One with User.
- **Coupon & Promotion:** Independent entities modifying cart totals during checkout.

---

## 🚀 Local Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/nikhilghotankar-8881/SportsHub.git
cd SportsHub
```

### 2. Virtual Environment Setup
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Environment Variables
Create a `.env` file in the project root. DO NOT commit this file.

```env
SECRET_KEY=your-strong-random-secret-key

# Database
DATABASE_URL= # Leave blank for local SQLite. Use Postgres URL for Render.

# Razorpay Test Mode
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxx

# Email Configuration (Gmail App Password required)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```
*Note: For Gmail, generate an [App Password](https://myaccount.google.com/apppasswords) instead of using your standard password.*

---

## 🗃️ Database Migrations
Run these commands to apply the database schema locally:

```bash
# Verify current migration state
flask db current
flask db heads

# Apply all migrations to the database
flask db upgrade
```

---

## 🏃 Running the Application

### Option A: Local Flask Development (Windows/Mac/Linux)
```bash
python run.py
```
*Accessible at `http://127.0.0.1:5000`*

### Option B: Windows Production-like Testing
Uses `waitress` to test the WSGI configuration natively on Windows:
```bash
waitress-serve --listen=127.0.0.1:8000 run:app
```
*Accessible at `http://127.0.0.1:8000`*

### Option C: Production Deployment (Render / Linux)
Render uses `gunicorn` to serve the application:
```bash
gunicorn run:app
```
*(Render executes this automatically based on the Build Settings)*

---

## 🌐 Production Deployment (Render)
1. Push the repository to GitHub.
2. Create a new **PostgreSQL** database on Render and copy its Internal URL.
3. Create a **Web Service** on Render linked to your repository.
4. Set the **Build Command**: `pip install -r requirements-prod.txt && flask db upgrade`
5. Set the **Start Command**: `gunicorn run:app`
6. Add the environment variables from the `.env` section above in the Render dashboard.

---

## 📂 Project Structure
```text
SportsHub/
├── app/
│   ├── __init__.py           # Application Factory
│   ├── config.py             # SQLite/PostgreSQL Config logic
│   ├── models.py             # Database Schema
│   ├── forms.py              # WTForms classes
│   ├── routes/               # Blueprints (auth, main, admin, etc.)
│   └── helpers/              # Email, Invoice, and Discount logic
├── migrations/               # Alembic database migrations
├── templates/                # Jinja2 HTML Templates
├── static/                   # CSS, JS, and image assets
├── run.py                    # WSGI Entry Point
├── requirements.txt          # Local development packages
├── requirements-prod.txt     # Clean production packages for Render
└── .env.example              # Environment variable placeholders
```

---

## 🔒 Security Notes
- Passwords are cryptographically hashed using `Werkzeug.security`.
- CSRF protection is enforced on all forms using `Flask-WTF`.
- Route protection is implemented via `@login_required` and custom admin checks.
- Sensitive variables and database URIs are strictly loaded from `.env` (never hardcoded).

---

## 🔮 Future Improvements
- **Live Payments:** Transition Razorpay from Test Mode to Live Mode.
- **Automated Testing:** Implement `pytest` for unit and integration testing.
- **REST API:** Extract backend logic into a JSON API to support mobile applications.
- **OAuth:** Allow users to log in via Google or GitHub.