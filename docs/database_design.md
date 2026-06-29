# SportsHub Database Design

## Overview

SportsHub is a Flask-based e-commerce platform for sports equipment. The database is designed using relational database principles and will be implemented using SQLAlchemy ORM with SQLite.

---

# Entity Relationship Design

## User

Stores information about registered users and administrators.

| Field         | Type     | Description           |
| ------------- | -------- | --------------------- |
| id            | Integer  | Primary Key           |
| name          | String   | User Full Name        |
| email         | String   | Unique Email Address  |
| password_hash | String   | Encrypted Password    |
| is_admin      | Boolean  | Admin Privileges      |
| created_at    | DateTime | Account Creation Date |

---

## Product

Stores all sports products available in the store.

| Field       | Type     | Description           |
| ----------- | -------- | --------------------- |
| id          | Integer  | Primary Key           |
| name        | String   | Product Name          |
| description | Text     | Product Description   |
| price       | Float    | Product Price         |
| stock       | Integer  | Available Quantity    |
| image       | String   | Product Image Path    |
| category    | String   | Product Category      |
| created_at  | DateTime | Product Creation Date |

---

## CartItem

Stores products added to a user's shopping cart.

| Field      | Type    | Description           |
| ---------- | ------- | --------------------- |
| id         | Integer | Primary Key           |
| user_id    | Integer | Foreign Key → User    |
| product_id | Integer | Foreign Key → Product |
| quantity   | Integer | Quantity Added        |

---

## Order

Stores order information after checkout.

| Field       | Type     | Description                 |
| ----------- | -------- | --------------------------- |
| id          | Integer  | Primary Key                 |
| user_id     | Integer  | Foreign Key → User          |
| total_price | Float    | Order Total                 |
| status      | String   | Pending, Shipped, Delivered |
| created_at  | DateTime | Order Date                  |

---

## OrderItem

Stores individual products inside an order.

| Field      | Type    | Description                    |
| ---------- | ------- | ------------------------------ |
| id         | Integer | Primary Key                    |
| order_id   | Integer | Foreign Key → Order            |
| product_id | Integer | Foreign Key → Product          |
| quantity   | Integer | Purchased Quantity             |
| price      | Float   | Product Price at Purchase Time |

---

# Relationships

## User Relationships

A User can have:

* Multiple Cart Items
* Multiple Orders

Relationship:

User (1) → (Many) CartItems

User (1) → (Many) Orders

---

## Product Relationships

A Product can appear in:

* Multiple Cart Items
* Multiple Order Items

Relationship:

Product (1) → (Many) CartItems

Product (1) → (Many) OrderItems

---

## Order Relationships

An Order can contain:

* Multiple Order Items

Relationship:

Order (1) → (Many) OrderItems

---

# ER Diagram

User
│
├── CartItems
│       │
│       └── Product
│
└── Orders
│
└── OrderItems
│
└── Product

---

# Foreign Key Summary

CartItem.user_id → User.id

CartItem.product_id → Product.id

Order.user_id → User.id

OrderItem.order_id → Order.id

OrderItem.product_id → Product.id

---

# Future Enhancements

The following entities can be added later:

* Category
* Wishlist
* Reviews & Ratings
* Coupons
* Payments
* Shipping Address
* Product Images
* Inventory Logs

These features are intentionally excluded from Version 1.0 to keep the project focused and beginner-friendly.

---

# Version

SportsHub Database Design v1.0
