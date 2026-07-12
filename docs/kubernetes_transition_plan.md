# Kubernetes Transition Plan (1,000+ Daily Users)

Since Agrovet expects 1,000+ daily users—and specifically because those users will be hitting **heavy Machine Learning endpoints**—a multi-node Kubernetes cluster is the correct architectural choice. Single servers will quickly run out of RAM and CPU when processing dozens of simultaneous image predictions.

Here is the high-level plan for how we can transition your current Docker setup into a production-ready Kubernetes (K8s) cluster.

---

## 1. Architectural Changes Required for K8s

Moving from a single machine to a distributed cluster means your containers will be running on entirely different physical servers. This introduces a few new requirements:

### Centralized Database
Currently, MySQL runs in a container with a local volume (`mysql_data`).
- **The Change**: You should migrate to a managed cloud database (like AWS RDS or Google Cloud SQL). If a Kubernetes node crashes, you don't want to lose your database volume.

### Shared Media Storage (AWS S3 / GCP Storage)
Currently, uploaded prediction images are saved to a local folder `/app/media/`. 
- **The Problem**: If User A uploads an image, it might go to Server 1. If User A then requests that image, the load balancer might route them to Server 2 (which doesn't have the image).
- **The Change**: We need to configure `django-storages` to save uploaded media and ML model files to an S3 bucket so all servers in the cluster share the exact same files.

### Container Registry
- **The Change**: You will need to build your Docker image, tag it, and push it to a cloud registry (like Docker Hub or AWS ECR) so your Kubernetes nodes can pull the image.

---

## 2. Kubernetes Manifests (YAML Files)

We will need to translate your `docker-compose.yml` into Kubernetes manifests. Here is what we would create:

1. **Deployment (`backend-deployment.yaml`)**:
   - Instructs Kubernetes to run `X` replicas of your Django backend.
   - We will configure **Horizontal Pod Autoscaling (HPA)**. If CPU/RAM usage spikes because 50 people uploaded images at once, Kubernetes will automatically spin up more backend containers. When traffic drops, it will delete them to save you money.

2. **Service (`backend-service.yaml`)**:
   - Acts as the internal load balancer. It keeps track of all your backend replicas and distributes traffic evenly among them.

3. **Ingress (`ingress.yaml`)**:
   - Replaces your NGINX container. The Ingress controller will act as the gateway to the internet, handling SSL/HTTPS certificates and routing `/api/` traffic to the backend Service.

4. **Secrets (`secrets.yaml`)**:
   - Securely stores your `.env` variables (Database passwords, JWT secret keys, etc.) encoded in base64.

---

## Next Steps

Getting to Kubernetes is a multi-step journey. We should tackle it in this order:

1. **Phase 1: Cloud Storage**: Configure Django to use Amazon S3 (or similar) for media uploads so your app becomes "stateless."
2. **Phase 2: External Database**: Point your Django settings to a managed database URL instead of a local Docker container.
3. **Phase 3: Manifest Generation**: Generate the Kubernetes YAML files (Deployments, Services, Ingress) for you to apply to your cloud provider (EKS, GKE, DigitalOcean).
