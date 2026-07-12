# Docker Architecture Overview

This document outlines how Docker is architected and configured within the Agrovet application. The setup is highly optimized, secure, and production-ready.

---

## 1. The Services (`docker-compose.yml`)

The application is broken down into three separate, isolated containers that communicate with each other over a dedicated Docker network:

### `db` (MySQL)
- Runs a secure MySQL 8.0 database.
- It pulls your database passwords securely from the `.env` file (`MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}`).
- Data is stored in a persistent Docker volume (`mysql_data`), meaning your data is preserved even if the container crashes or is deleted.

### `backend` (Django)
- This is the core Python application.
- It waits for the `db` container to initialize using the `depends_on` directive.
- It shares its `/app/staticfiles` and `/app/media` folders with NGINX using Docker Volumes so NGINX can serve them directly.

### `nginx` (Web Server)
- Acts as the "front door" (Reverse Proxy) to the application, exposing port `8000` to the outside world.
- Any traffic coming from the host machine hits this container first.

---

## 2. The Backend Environment (`Dockerfile`)

The `Dockerfile` handles building the Python environment and implements several excellent industry best practices:

- **Security First**: It creates a non-root user (`appuser`) and switches to it before execution. This prevents attackers from gaining full root access to the host machine if the container is compromised.
- **System Dependencies**: It explicitly installs `libgl1` and `libglib2.0-0`. These are required C-libraries for OpenCV (used by the Soil Nutrition ML model) to function correctly on a minimal Linux OS.
- **Production Web Server**: Instead of using Django's slow, single-threaded development server (`manage.py runserver`), it executes **Gunicorn**. 
- **Timeouts**: The Gunicorn command uses `--timeout 300` (5 minutes). This is a critical configuration because heavy Machine Learning endpoints take significantly longer to process than standard API requests.

---

## 3. The Reverse Proxy (`nginx.conf`)

NGINX sits in front of the backend and handles three main responsibilities:

1. **Routing API Traffic**: When a user makes an API request, NGINX silently forwards it to the hidden `backend:8000` container via internal DNS mapping (`upstream web_app`).
2. **Serving Static/Media Files**: Django is notoriously slow at serving files. NGINX intercepts requests to `/media/` and `/static/` and serves the files directly from the shared Docker Volume, completely bypassing Python for maximum speed.
3. **Large Uploads**: It configures `client_max_body_size 100M`. By default, NGINX rejects uploads larger than 1MB. This configuration explicitly allows users to upload high-resolution images for the ML models without getting blocked by the proxy.
