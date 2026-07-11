# Agrovet AI Assistance - Backend

Welcome to the **Agrovet Backend API**. This project is a modern, enterprise-grade Django REST Framework application providing user authentication and AI-powered animal disease prediction. 

It is fully containerized using **Docker Compose** and runs securely behind an **Nginx** reverse proxy, backed by a **MySQL** database.

---

## 🌟 Key Features
- **Dockerized Architecture**: Zero-config local development setup via Docker.
- **Enterprise User Models**: Custom user model with secure UUID primary keys, email-based authentication, soft-deletions, and activity tracking.
- **JWT Authentication**: Stateless and highly scalable bearer token authentication.
- **Swagger UI Documentation**: Automatically generated, interactive OpenAPI specifications.
- **AI Predictions**: Endpoints ready for YOLO/PyTorch integrations to predict agricultural and veterinary diseases.

---

## 🚀 Quickstart Guide

Follow these steps to get the entire API stack running locally in under a minute!

### 1️⃣ Prerequisites
Make sure you have the following installed on your machine:
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Git

### 2️⃣ Clone the Repository
```bash
git clone https://github.com/Shivam-Narayan/agrovet-ai-assistance-be.git
cd agrovet-ai-assistance-be
```

### 3️⃣ Environment Variables
Ensure you have a `.env` file in the root of the project with your MySQL and Django secrets. Example:
```env
DB_ENGINE=django.db.backends.mysql
DB_NAME=agrovet_be
DB_USER=root
DB_PASSWORD=root
DB_HOST=db
DB_PORT=3306
```

### 4️⃣ Build and Run the Stack
Run the following command to download the images, build the backend, and start the services:
```bash
docker-compose -p agrovetapp up --build -d
```
*(The `-d` flag runs the containers in the background).*

### 5️⃣ Database Migrations & Static Files
On your very first run, you need to apply the database migrations and collect the static files so Nginx can serve the Swagger UI:

```bash
docker-compose -p agrovetapp exec backend python manage.py migrate
docker-compose -p agrovetapp exec backend python manage.py collectstatic --noinput -c
```

### 6️⃣ Create an Admin User (Optional)
To access the Django Admin panel, create a superuser:
```bash
docker-compose -p agrovetapp exec backend python manage.py createsuperuser
```

---

## 📖 API Documentation

Once the containers are running, you can explore and interact with the API endpoints instantly via our built-in Swagger UI:

👉 **[Interactive API Explorer](http://localhost:8000/swagger/)**

---

## 🛠️ Architecture & Services

When you run `docker-compose up`, the following services are spun up:
1. **db (MySQL 8.0)**: The core relational database (port `3306`).
2. **backend (Django/Gunicorn)**: The core Python REST API.
3. **nginx**: The reverse proxy acting as the gateway (port `8000`). It routes `/api/` traffic to the backend and securely serves static assets for the Swagger UI.

---

## 🛑 Useful Commands

**Stop all containers:**
```bash
docker-compose -p agrovetapp down
```

**View logs for the backend:**
```bash
docker-compose -p agrovetapp logs -f backend
```

**Open a shell inside the backend container:**
```bash
docker-compose -p agrovetapp exec backend bash
```

**Wipe the database completely (DANGER):**
```bash
docker-compose -p agrovetapp down -v
```
