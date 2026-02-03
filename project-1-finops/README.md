High-Availability PostgreSQL Cluster (Hardened)
Project Status: ✅ Deployed & Verified 
Role: Site Reliability Engineer (SRE) 
Tech Stack: Docker Swarm, HAProxy, PostgreSQL, Docker Secrets, Bash Infrastructure: AWS EC2 (Ubuntu Linux)

📖 Executive Summary
This project demonstrates a production-grade database architecture designed to survive infrastructure failures and supply chain attacks.

Moving beyond basic containerization, this deployment focuses on Zero-Trust Security and Immutable Infrastructure. It features a self-healing PostgreSQL cluster fronted by an auto-scaling HAProxy load balancer, using Docker Secrets for credential management and SHA256 image pinning to prevent upstream dependency attacks.

🏗️ Architecture
The stack consists of three decoupled services running on an encrypted overlay network:

Load Balancer (HAProxy):

Deployment Strategy: mode: global (Auto-scales to every node in the Swarm).

Function: Performs Layer 4 (TCP) health checks and routes traffic to available DB nodes.

Security: Configuration mounted as Read-Only (:ro) to prevent runtime tampering.

Primary Database (PostgreSQL):

Security: Credentials injected via Docker Secrets (encrypted at rest and in transit).

Stability: Image version pinned by SHA256 Digest to guarantee 100% immutability.

Placement: Pinned to Manager nodes for stability using constraints.

Replica Database (PostgreSQL):

Redundancy: Asynchronous replication from Primary.

Self-Healing: Automatic restart policy (condition: on-failure) ensures zero-touch recovery.

🛡️ Key Engineering Decisions
1. Zero-Trust Credential Management (Docker Secrets)
The Problem: Storing passwords in docker-compose.yml or Environment Variables (ENV) exposes credentials to anyone with read access to the repo or container inspection rights.

The Solution: Implemented Docker Secrets.

Passwords are stored in the Swarm's encrypted Raft log.

Secrets are mounted as temporary files in /run/secrets/ only for the specific container lifecycle.

Impact: Credentials are never visible in plain text in the codebase, git history, or process tree.

2. Supply Chain Security (Immutable Tags)
The Problem: Using image: postgres:latest is dangerous. Upstream changes can introduce breaking bugs or vulnerabilities without warning.

The Solution: Pinned images by SHA256 Digest.

Used: bitnami/postgresql@sha256:8c7f26a8ba4257fcbf4445bd50e156cbc7d8114942fb3d6523320c7732781b54

Impact: Guarantees that the code running in Production today is mathematically identical to the code tested in Staging, regardless of upstream tag updates.

3. Auto-Scaling & Global Mode
The Strategy: Deployed HAProxy in mode: global.

Impact: If the cluster scales from 3 nodes to 100 nodes, a load balancer instance automatically spawns on every new node without manual intervention. This provides infinite horizontal scalability for the ingress layer.

🛠️ Verification & Evidence
1. Service Status
Proof of Global and Replicated services running in a stable state.

Bash
ID             NAME               MODE         REPLICAS   IMAGE
o1ip7ltp749o   ha_db_haproxy      global       1/1        haproxy:2.8
ylwq5uslcod4   ha_db_pg-primary   replicated   1/1        bitnami/postgresql@sha256:8c7f...
vq4k6rax708w   ha_db_pg-replica   replicated   1/1        bitnami/postgresql@sha256:8c7f...
2. Network Integration (Health Checks)
HAProxy stats page confirming Layer 4 connectivity (L4OK) to both backend nodes.

Plaintext
postgres_back/primary   UP   L4OK in 0ms
postgres_back/replica   UP   L4OK in 0ms
💻 How to Reproduce
Prerequisites:

Docker Swarm initialized (docker swarm init).

Linux Environment.

Step 1: Clone & Navigate
Bash
git clone https://github.com/adriandenisofficial/senior-devops-portfolio.git
cd senior-devops-portfolio/project-2-ha-cluster
Step 2: Create Encrypted Secrets
We do not use .env files. We inject secrets directly into the Swarm Vault.

Bash
printf "my_secure_password" | sudo docker secret create postgres_password -
printf "my_secure_user" | sudo docker secret create postgres_user -
printf "my_repl_password" | sudo docker secret create replication_password -
Step 3: Deploy the Stack
Bash
sudo docker stack deploy -c docker-stack.yml ha_db --resolve-image never
Step 4: Verify Load Balancer
Bash
curl -s http://localhost:8080/stats | grep "postgres_back"
📂 Repository File Structure
docker-stack.yml: The Swarm manifest defining services, networks, volumes, and secrets.

config/haproxy.cfg: The Layer 4 Load Balancing configuration and health check logic.

README.md: System documentation (You are here).
