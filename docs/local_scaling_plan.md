# Local Scaling Plan (Docker Compose)

This plan outlines how to scale your Agrovet backend into a local cluster on a **single, powerful server** (e.g., a 32GB RAM EC2 instance or DigitalOcean Droplet) using Docker Compose.

Because your ML models require significant computing power, running multiple backend replicas allows different users to process image predictions simultaneously without waiting in a queue.

---

## 1. How It Works

Your current architecture already uses NGINX as a reverse proxy:
```nginx
upstream web_app {
    server backend:8000;
}
```
When we tell Docker Compose to spin up multiple replicas of the `backend` service (e.g., 3 replicas), Docker's internal DNS resolver will automatically load-balance incoming NGINX traffic evenly across all 3 backend containers using a round-robin strategy!

---

## 2. Changes Required

To implement this, we only need to make a minor change to your `docker-compose.yml` file. 

### Current Setup (docker-compose.yml)
```yaml
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    env_file:
      - .env
    # ...
```

### New Setup (docker-compose.yml)
We add a `deploy` block to specify the number of replicas:
```yaml
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    env_file:
      - .env
    deploy:
      mode: replicated
      replicas: 3  # Scale to 3 workers
    # ...
```
*Note: Because your `backend` container does not expose host ports (e.g., you don't have `ports: ["8000:8000"]`), there will be no port collisions. Nginx is the only service that needs to map to a host port.*

---

## 3. Running the Cluster

Once the YAML file is updated, you simply run:
```bash
docker-compose -p agrovetapp up --build -d
```
Docker will automatically spin up 1 Database container, 1 Nginx container, and **3 Backend containers**.

If traffic spikes and you need even more workers temporarily, you can dynamically scale up without stopping the server:
```bash
docker-compose -p agrovetapp up --scale backend=5 -d
```

---

## 4. Hardware Requirements & Constraints

While this is extremely easy to set up, there are two constraints to keep in mind:

1. **RAM Usage**: Every backend replica will load its own copy of the ML models into RAM. If one backend container uses 2GB of RAM, running 4 replicas will use 8GB of RAM. You must ensure your server has enough memory.
2. **Local Storage**: Currently, images are saved in a local Docker volume (`media_data`). Since all 3 replicas run on the *same* physical machine, they can all share this volume perfectly. (This is why Local Scaling is so much easier than Kubernetes!).
