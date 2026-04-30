# StockPilot — Inventory Management System

> A production-ready, containerized inventory management web application with a full CI/CD pipeline deployed on AWS EC2.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Jenkins](https://img.shields.io/badge/Jenkins-CI%2FCD-D24939?logo=jenkins&logoColor=white)](https://www.jenkins.io/)
[![AWS](https://img.shields.io/badge/AWS-EC2-FF9900?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)

---

## 📌 Overview

**StockPilot** is a full-stack inventory management system built to demonstrate end-to-end software engineering — from backend development and relational database design to containerization and automated cloud deployment.

The application lets businesses track products, manage stock levels, monitor low-stock alerts, and view a real-time activity log — all through a clean, responsive web interface.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📊 **Dashboard** | Real-time KPIs — total products, low-stock count, total inventory value, and recent stock activity |
| 📦 **Product Management** | Full CRUD — add, edit, delete products with category assignment and pricing |
| 🔍 **Search & Filter** | Filter products by category and search by name |
| ⚠️ **Low Stock Alerts** | Dedicated view listing all products below their restock threshold |
| 📋 **Stock Activity Log** | Tracks every stock change with reason and timestamp |
| 🏥 **Health Check Endpoint** | `/health` endpoint used by Docker and Jenkins for liveness checks |

---

## 🛠️ Tech Stack

### Backend
- **Python 3.11** — Core language
- **Flask 3.0.3** — Lightweight WSGI web framework
- **MySQL Connector/Python 8.4.0** — Database driver

### Database
- **MySQL 8.0** — Relational database with normalized schema (products, categories, stock_logs)
- Auto-initialized schema on first run with seeded category data

### DevOps & Infrastructure
- **Docker** — Containerized Flask app using a `python:3.11-slim` base image
- **Docker Compose** — Orchestrates Flask + MySQL as networked services with health checks and persistent volumes
- **Jenkins** — CI/CD pipeline (4 stages: Clone → Build → Deploy → Health Check)
- **AWS EC2** — Cloud deployment target; Jenkins runs on the EC2 instance and pulls from GitHub on every pipeline trigger

---

## 🏗️ Architecture

```
GitHub Repository
       │
       │  git pull (Jenkins pipeline trigger)
       ▼
  ┌─────────────────────────────────┐
  │         AWS EC2 Instance        │
  │                                 │
  │  ┌──────────┐  ┌─────────────┐  │
  │  │ Jenkins  │─▶│  Docker     │  │
  │  │ (CI/CD)  │  │  Compose    │  │
  │  └──────────┘  └──────┬──────┘  │
  │                        │        │
  │          ┌─────────────┴──────────────┐
  │          │                            │
  │  ┌───────▼──────┐        ┌────────────▼────┐
  │  │  Flask App   │        │   MySQL 8.0      │
  │  │ (Port 5000)  │◀──────▶│  (Port 3306)     │
  │  └──────────────┘        └─────────────────┘
  │          inventory-net (Docker bridge network)
  └─────────────────────────────────┘
```

---

## ⚙️ CI/CD Pipeline (Jenkins)

The `Jenkinsfile` defines a 4-stage declarative pipeline:

```
Stage 1: Clone Code      → Pulls latest code from GitHub (main branch)
Stage 2: Build Image     → Builds the Flask Docker image
Stage 3: Deploy          → Tears down old containers, starts fresh via docker-compose up
Stage 4: Health Check    → Hits /health endpoint to verify successful deployment
```

On **success**: app is live at `http://<EC2-IP>:5000`  
On **failure**: pipeline dumps the last 50 lines of container logs for debugging

---

## 🗄️ Database Schema

```sql
categories        products                    stock_logs
──────────────    ──────────────────────────  ──────────────────────────────
id   (PK)         id          (PK)            id          (PK)
name              name                        product_id  (FK → products.id)
                  category_id (FK)            change_amount
                  quantity                    reason
                  threshold                   logged_at
                  price
                  created_at
```

- **Foreign keys** enforce referential integrity between tables
- **`ON DELETE CASCADE`** on `stock_logs` automatically cleans up logs when a product is deleted
- Schema auto-creates on application startup — no manual migration needed

---

## 🚀 Running Locally

### Prerequisites
- [Docker](https://www.docker.com/get-started) & Docker Compose installed

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/vedantp3/inventory-management.git
cd inventory-management

# 2. Create your environment file
cp .env.example .env   # Update values as needed

# 3. Start all services
docker-compose up -d --build

# 4. Open the app
# Visit http://localhost:5000
```

> The MySQL container has a health check configured. The Flask app will only start once MySQL is ready — no manual waiting required.

### Stopping the App

```bash
docker-compose down          # Stop containers
docker-compose down -v       # Stop and remove volumes (wipes DB data)
```

---

## 🔧 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MYSQL_HOST` | `mysql` | MySQL container hostname |
| `MYSQL_USER` | `root` | MySQL username |
| `MYSQL_PASSWORD` | `root` | MySQL password |
| `MYSQL_DB` | `inventory` | Database name |
| `SECRET_KEY` | `inventory-secret-2024` | Flask session secret key |

> ⚠️ **Always override `SECRET_KEY` and `MYSQL_PASSWORD` in production.**

---

## 📁 Project Structure

```
inventory-app/
├── app.py                  # Flask application — routes & DB logic
├── requirements.txt        # Python dependencies
├── Dockerfile              # Flask container image definition
├── docker-compose.yml      # Multi-service orchestration (Flask + MySQL)
├── Jenkinsfile             # Declarative CI/CD pipeline
├── templates/              # Jinja2 HTML templates
│   ├── dashboard.html
│   ├── products.html
│   ├── add_product.html
│   ├── edit_product.html
│   └── low_stock.html
└── .gitignore
```

---

## 🔑 Key Engineering Decisions

- **`python:3.11-slim` base image** — Minimizes Docker image size while keeping a production-safe runtime
- **`depends_on` with `condition: service_healthy`** — Prevents Flask from starting before MySQL is actually ready, eliminating race conditions
- **Parameterized SQL queries** — All database queries use `%s` placeholders to prevent SQL injection
- **`restart: always`** on both services — Ensures containers auto-recover from crashes without manual intervention
- **`/health` endpoint** — Enables automated liveness checks from both Docker Compose and the Jenkins pipeline post-deploy stage

---

## 👤 Author

**Vedant** — [@vedantp3](https://github.com/vedantp3)
