# Project 3: Cloud-Native Stateful Database Migration (Kubernetes)

## 📋 Executive Summary
This project demonstrates the migration of a legacy, monolithic PostgreSQL database into a **High-Availability, Self-Healing Kubernetes Cluster**. Unlike stateless web applications, databases require strict guarantees regarding network identity and storage persistence.

This implementation utilizes **StatefulSets** rather than standard Deployments to ensure ordered deployment, stable network identifiers (`postgres-0`), and persistent volume attachment. Security is enforced via **Sealed Secrets** for credential management, and observability is provided via a sidecar **PgAdmin4** dashboard.

---

## 🏗 Architecture Overview

### 1. The Data Layer (StatefulSet)
* **Kind:** `StatefulSet` (Not Deployment)
* **Rationale:** Standard Deployments treat pods as ephemeral and interchangeable. Databases require a "Sticky Identity." The StatefulSet ensures the pod is always named `postgres-0`, allowing clients to reliably find the master node.
* **Storage:** Dynamic Volume Provisioning via **PersistentVolumeClaim (PVC)**.
    * **Mechanism:** Requests 1Gi of Block Storage from the underlying Cloud Provider (AWS EBS / Minikube HostPath).
    * **Persistence:** The volume lifecycle is decoupled from the Pod. If `postgres-0` crashes or is deleted, the volume automatically re-attaches to the replacement pod, preventing data loss.

### 2. The Network Layer (Headless Service)
* **Config:** `clusterIP: None`
* **Rationale:** A standard Service acts as a Load Balancer. For a primary database, we need direct access to the specific instance, not a round-robin distribution. The Headless Service creates a direct DNS record (`postgres.ha-db.svc.cluster.local`) that resolves directly to the Pod IP.

### 3. The Security Layer (Sealed Secrets)
* **Pattern:** GitOps-friendly Secret Management.
* **Implementation:** Credentials (`POSTGRES_USER`, `POSTGRES_PASSWORD`) are encrypted into a `SealedSecret` CRD. These are injected into the container as Environment Variables at runtime. This ensures no plain-text passwords exist in the YAML manifests.

### 4. The Management Layer (Stateless Web App)
* **Component:** PgAdmin4 Dashboard.
* **Kind:** `Deployment` (Stateless).
* **Exposure:** `NodePort` Service (Fixed Port `30080`) for external administrative access via AWS Security Group ingress or SSH Tunneling.

---

## 🛠️ Implementation & Manifests

### Deployment Order
The architecture enforces a strict startup order to prevent race conditions:
1.  **Secret Creation:** Encrypts credentials.
2.  **Database Initialization:** `postgres-0` mounts the volume and initializes the schema.
3.  **Dashboard Launch:** `pgadmin` starts and awaits database readiness.

### Key Components
* `db-sealed-secret.yaml`: Encrypted credentials.
* `db-statefulset.yaml`: The database engine definition.
* `admin-deployment.yaml`: The GUI dashboard.

---

## 🧪 Verification & Reliability Testing
This project was subjected to rigorous failure simulation to certify production readiness.

### Test 1: The "Crash Test" (Persistence Verification)
* **Objective:** Prove that data survives a catastrophic Pod failure.
* **Action:** Inserted critical business data (`id: 2`, `role: 'Senior DevOps Engineer'`) into the active database.
* **Simulation:** Forcefully deleted the pod: `kubectl delete pod postgres-0`.
* **Observation:** Kubernetes controller detected the state deviation and spun up a replacement pod.
* **Result:** The new pod successfully re-attached the existing PVC. A subsequent SQL query confirmed 100% data integrity.

### Test 2: Internal Service Discovery
* **Objective:** Verify internal DNS resolution between microservices.
* **Challenge:** The minimal Alpine image lacked debugging tools (`curl`).
* **Solution:** Deployed a temporary ephemeral "sniper" pod (`curlimages/curl`) to probe the internal network.
* **Command:** `kubectl run debug --image=curlimages/curl ...`
* **Result:** Confirmed HTTP 200 OK response from `pgadmin-service.ha-db.svc.cluster.local`, validating the internal service mesh.

### Test 3: External Access & Security Groups
* **Objective:** Securely expose the administrative dashboard.
* **Configuration:** Configured AWS Security Group to whitelist ingress on TCP Port 8080.
* **Tunneling:** Utilized `kubectl port-forward` to bridge the remote cluster network to the local development machine.
* **Result:** Successful login to PgAdmin4 via public IP, confirming the end-to-end network path.

---

## 🚀 How to Reproduce

### 1. Apply Configuration
```bash
# Create Namespace
kubectl create namespace ha-db

# Apply Secrets and StatefulSet
kubectl apply -f db-sealed-secret.yaml
kubectl apply -f db-statefulset.yaml
```
2. Verify Pod Status
```Bash
kubectl get pods -n ha-db -w
# Wait for 'Running' status on postgres-0
```
3. Access the Dashboard
```Bash
# Option A: Port Forwarding (Secure)
kubectl port-forward -n ha-db svc/pgadmin-service 8080:80 --address 0.0.0.0

# Option B: NodePort (Direct)
# Access http://<NODE_IP>:30080
```

Author Notes
Infrastructure: Deployed on AWS EC2 (Ubuntu 22.04 LTS).

Orchestrator: Minikube (v1.32.0).

Database: PostgreSQL 15-Alpine (Optimized for container footprint).

# Deploy Dashboard
kubectl apply -f admin-deployment.yaml
