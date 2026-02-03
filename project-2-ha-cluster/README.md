# Project 2: High-Availability PostgreSQL Cluster (Hardened)

**Role:** Site Reliability Engineer (SRE)

**Status:** ✅ Deployed & Verified

**Focus:** Infrastructure hardening, Fault Tolerance, & Zero-Trust Security

---

## 📖 Executive Summary
Standard database deployments (using `docker-compose up`) represent a **Single Point of Failure**. In a real production environment, a single crashed container or a corrupted upstream image update can cause significant downtime and data loss.

I engineered a **Self-Healing, Fault-Tolerant Database Architecture** using Docker Swarm. Moving beyond basic containerization, this project implements "Senior-Grade" patterns including **Immutable Infrastructure** (SHA pinning), **Zero-Trust Credential Management** (Secrets), and **Global Load Balancing**.

---

## 🏗️ Architecture


The system runs on an encrypted Overlay Network and consists of three decoupled layers:

1.  **Ingress Layer (HAProxy):**
    * Deployed in `global` mode (automatically scales to every node in the cluster).
    * Performs Layer 4 (TCP) health checks on the backend databases.
2.  **Primary Data Layer (PostgreSQL):**
    * Accepts Writes.
    * Pinned to specific nodes using Placement Constraints.
3.  **Replica Data Layer (PostgreSQL):**
    * Asynchronous replication from Primary.
    * Auto-restarts (`condition: on-failure`) to ensure high availability.

---

## 🛠 Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Orchestration** | Docker Swarm | Native clustering and service management. |
| **Networking** | Overlay Driver | Encrypted mesh networking between containers. |
| **Load Balancing** | HAProxy 2.8 | TCP (Layer 4) Routing and Health Checking. |
| **Database** | PostgreSQL 16 (Bitnami) | Primary-Replica Architecture. |
| **Security** | Docker Secrets | Encrypted credential storage (No plain text). |
| **Supply Chain** | SHA256 Digests | Immutable image versioning. |

---

## 🛡️ Key Engineering Decisions

### 1. Zero-Trust Credential Management
* **The Problem:** Storing passwords in `docker-compose.yml` or `.env` files exposes sensitive credentials to anyone with read access to the repo or the server process tree (`ps aux`).
* **The Solution:** I implemented **Docker Secrets**.
    * Passwords are encrypted in the Swarm Manager's Raft log.
    * Secrets are mounted as temporary files in `/run/secrets/` *only* during the container's lifecycle.
    * **Result:** Credentials are never visible in plain text in the codebase, environment variables, or Git history.

### 2. Supply Chain Security (Immutable Infrastructure)
* **The Problem:** Using tags like `image: postgres:latest` is dangerous. If the upstream provider pushes a broken update or introduces a vulnerability, the production system pulls it automatically, causing a crash.
* **The Solution:** I pinned all images by their **SHA256 Digest** (e.g., `bitnami/postgresql@sha256:8c7f...`).
    * **Result:** This guarantees that the code running in production today is **mathematically identical** to the code tested in staging, eliminating "drift" and unexpected upstream breakages.

### 3. Auto-Scaling & Self-Healing
* **The Problem:** In a traditional setup, adding a new server requires manually configuring a new load balancer.
* **The Solution:** I deployed HAProxy in `mode: global`.
    * Docker Swarm automatically schedules a Load Balancer instance on *every* new node that joins the cluster.
    * If the Database crashes, the `restart_policy` automatically provisions a fresh container in <5 seconds.

---

## 📸 Evidence & Verification

### 1. Network Integration (Health Checks)
The HAProxy Stats Dashboard confirms that the Load Balancer has successfully discovered both the **Primary** and **Replica** nodes and marked them as `L4OK` (Layer 4 Healthy).

<img width="1888" height="738" alt="HAProxy stats page confirming successful Layer 4 health checks and active connections to both Primary and Replica database nodes" src="https://github.com/user-attachments/assets/8df148e1-ba73-48e2-8cb3-e65ee1cbd762" />


### 2. Service Status
Command line verification showing the stack running in a stable state with `1/1` replicas and SHA256 pinned images.

<img width="1462" height="137" alt="service deployed on cluster" src="https://github.com/user-attachments/assets/a1bfea39-0459-49cb-bb28-35cf268f57db" />

### 3. Self-Healing in Action
Console logs demonstrating the cluster's fault tolerance.
* **Event:** I manually simulated a crash (Exit Code 137).
* **Result:** Docker Swarm detected the failure and automatically provisioned a replacement container in <10 seconds.

<img width="1805" height="272" alt="old container died and swarm manager started new one auto" src="https://github.com/user-attachments/assets/2d941405-7b7e-443b-bf78-3fc83d8abf6e" />

---

## 💻 How to Run This Project

### Prerequisites
* **Docker Engine** installed on Linux (Ubuntu/Debian recommended).
* **Swarm Mode** initialized:
    ```bash
    docker swarm init
    ```

### Step-by-Step Deployment

**1. Clone the Repository**
```bash
git clone [https://github.com/adriandenisofficial/senior-devops-portfolio.git](https://github.com/adriandenisofficial/senior-devops-portfolio.git)
cd senior-devops-portfolio/project-2-ha-cluster
```
2. Create Encrypted Secrets We manually inject secrets into the Swarm Vault. These will never be shown again.

```Bash
printf "my_secure_password" | sudo docker secret create postgres_password -
printf "my_secure_user" | sudo docker secret create postgres_user -
printf "my_repl_password" | sudo docker secret create replication_password -
```
3. Deploy the Hardened Stack

```Bash
sudo docker stack deploy -c docker-stack.yml ha_db
```
4. Verify Deployment Check that all services have converged to 1/1:

```Bash
watch sudo docker service ls
```
5. Access the Load Balancer Stats

URL: http://localhost:8080/stats

What to look for: Locate the postgres_back section and verify UP status.

🧹 Tear Down
To destroy the cluster and remove secrets:

```Bash
sudo docker stack rm ha_db
sudo docker secret rm postgres_password postgres_user replication_password
```
