# SportsHub 🏀⚽🏏

SportsHub is a Flask-based sports equipment e-commerce platform.

## Features

- User Authentication & Authorization
- Comprehensive Product Catalog
- Shopping Cart & Checkout System
- **Payment Integration**: Razorpay Online Payments & Cash on Delivery (COD)
- **Email Notifications**: Centralized `Flask-Mail` integration with customizable Jinja2 HTML templates for Registration, Orders, Payments, and Admin Status Updates.
- **Promotions**: Discount Coupons & Flash Sales
- Order Management with Automated Email Confirmations
- PDF Invoice Generation
- Advanced Admin Dashboard
- Responsive & Modern UI built with Bootstrap 5

## Tech Stack

- Python
- Flask
- SQLAlchemy
- SQLite
- Bootstrap
- Flask-Login
- Flask-Mail
- Flask-Migrate

## 📧 Email Notification System

SportsHub uses `Flask-Mail` for transactional emails. The application is resilient: if email credentials are not set, it logs a warning but **never crashes** and preserves core functionality (e.g., placing an order still works).

### Supported Notifications
- Registration Welcome Email
- Password Change Security Alert
- Order Confirmation (Razorpay / Online)
- Cash on Delivery (COD) Order Placed
- Payment Success (Razorpay verification)
- Order Status Updates (Placed, Confirmed, Packed, Out for Delivery)
- Order Shipped
- Order Delivered
- Order Cancelled
- Contact Us Confirmation

### Configuration (Environment Variables)
Create a `.env` file in the project root with the following:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=your_email@gmail.com
```

> **Note on Gmail:** You must generate an [App Password](https://myaccount.google.com/apppasswords) for `MAIL_PASSWORD`. Do not use your regular Gmail password.

## Installation

```bash
git clone https://github.com/nikhilghotankar-8881/SportsHub.git

cd SportsHub

python -m venv venv

pip install -r requirements.txt

python run.py