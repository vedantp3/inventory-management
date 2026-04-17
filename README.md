# StockPilot — Inventory Management System

A two-tier web application built with Flask + MySQL, containerized with Docker, and deployed via Jenkins CI/CD on AWS EC2.

## Tech Stack
- **Backend:** Python / Flask
- **Database:** MySQL 8.0
- **Containerization:** Docker + Docker Compose
- **CI/CD:** Jenkins (Pipeline as Code)
- **Cloud:** AWS EC2 (Ubuntu 22.04)

## Features
- Add, edit, delete products with category + pricing
- Real-time stock update modal (+ restock / − reduce)
- Low stock alerts with threshold per product
- Full stock change log with reasons + timestamps
- Dashboard with inventory value, alerts summary
- Category filter + search on products page

## Project Structure
```
inventory-management/
├── app.py                  # Flask routes + DB logic
├── requirements.txt        # Python dependencies
├── Dockerfile              # Flask container definition
├── docker-compose.yml      # Multi-container orchestration
├── Jenkinsfile             # CI/CD pipeline definition
└── templates/
    ├── base.html           # Shared layout + sidebar
    ├── dashboard.html      # Overview + stats
    ├── products.html       # Products list + stock modal
    ├── add_product.html    # Add new product form
    ├── edit_product.html   # Edit product form
    └── low_stock.html      # Low stock alert view
```

## Run Locally

```bash
git clone https://github.com/YOUR-USERNAME/inventory-management.git
cd inventory-management
docker compose up --build
```

Visit: http://localhost:5000

## CI/CD Pipeline Stages
1. **Clone Code** — pulls latest from GitHub main branch
2. **Build Docker Image** — builds Flask app image
3. **Deploy** — `docker compose down` → `docker compose up -d`
4. **Health Check** — hits `/health` endpoint to verify deployment

## AWS EC2 Deployment
See full setup guide in the project walkthrough.

After Jenkins pipeline runs:
- App: `http://<EC2-PUBLIC-IP>:5000`
- Jenkins: `http://<EC2-PUBLIC-IP>:8080`
