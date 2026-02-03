# Project 1: FinOps Observability Pipeline

**Role:** Cloud Engineer & FinOps Practitioner

**Status:** ✅ Deployed & Verified

**Focus:** Cost Intelligence, Monitoring, & Automation

---

## 📖 Executive Summary
This project bridges the gap between **Engineering Health** (Latency/Errors) and **Business Impact** (AWS Spend/Revenue).

In standard DevOps environments, "Cost" is often a lagging indicator—a bill received at the end of the month. I engineered a solution to make cost a **leading indicator**, allowing teams to see the financial impact of their infrastructure changes in real-time alongside system performance metrics.

---

## 🏗️ Architecture
The system follows a **Scrape-Based Architecture**:

1.  **Application Layer:** A Flask Microservice instrumented with `prometheus_client` to expose business metrics (Revenue per Second).
2.  **Infrastructure Layer:** A custom Python exporter using `boto3` to fetch real-time billing data from AWS Cost Explorer.
3.  **Aggregation Layer:** Prometheus scrapes both the App and the Cost Exporter every 15 seconds.
4.  **Visualization Layer:** Grafana correlates these metrics on a unified dashboard.

---

## 🛠 Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Orchestration** | Docker Compose | Managing the multi-container stack. |
| **App Logic** | Python (Flask) | Simulating high-traffic e-commerce transactions. |
| **Cloud SDK** | AWS Boto3 | Programmatic access to AWS Cost Explorer API. |
| **Metric Storage** | Prometheus | Time-series database for storing cost & latency data. |
| **Visualization** | Grafana | Dashboarding "Cost per Request" vs. "Latency". |
| **Security** | AWS IAM | Least Privilege Roles (Read-Only access to Billing). |

---

## 🛡️ Key Engineering Decisions

### 1. The "Sidecar" Pattern for Cost Injection
* **Challenge:** Standard tools like `node-exporter` only measure CPU/RAM, not money.
* **Solution:** I wrote a custom **Python Sidecar Container**. It runs alongside the application, independently authenticating with AWS to fetch billing data and formatting it into OpenMetrics standards.
* **Benefit:** Decouples cost monitoring from application logic. The app doesn't need to know about AWS credentials.

### 2. Custom Prometheus Instrumentation
* **Challenge:** Measuring "HTTP 200 OK" is not enough to understand business health.
* **Solution:** I instrumented the application code to expose **Business Metrics**:
    * `app_revenue_total`: Counter metric tracking real-time dollars generated.
    * `app_requests_processing_seconds`: Histogram metric tracking 99th percentile latency.
* **Result:** We can now alert if *Revenue drops* even if *Server Health is green* (logic error detection).

### 3. Least-Privilege IAM Security
* **Challenge:** Giving a container access to AWS Billing is risky.
* **Solution:** Instead of using Admin keys, I created a restricted IAM Policy allowing **only** `ce:GetCostAndUsage`.
* **Benefit:** Even if the container is compromised, the attacker cannot provision resources or read sensitive S3 data.

---

## 📸 Evidence & Dashboards

### The "Single Pane of Glass"
This Grafana dashboard correlates three critical dimensions:
1.  **System Health:** (Top Right) Latency and Error Rates.
2.  **Financial Health:** (Top Left) Real-time AWS Daily Spend.
3.  **Business Health:** (Bottom Left) Revenue generated per second.

<img width="1905" height="815" alt="final-dashboard-evidence" src="https://github.com/user-attachments/assets/05aa1142-75c5-4294-91cd-8fe38a69b32a" />



---

## 💻 How to Run This Project

### Prerequisites
* **Docker Desktop** installed.
* **AWS Account** with `Cost Explorer` enabled.
* **AWS Credentials** (`~/.aws/credentials`) or IAM Role attached to the host.

### Step-by-Step Deployment

**1. Clone the Repository**
```bash
git clone [https://github.com/adriandenisofficial/senior-devops-portfolio.git](https://github.com/adriandenisofficial/senior-devops-portfolio.git)
cd senior-devops-portfolio/project-1-finops
```
2. Configure Permissions Prometheus needs permission to write metric data to the local volume.

```bash
chmod -R 777 prom_metrics
```
3. Inject AWS Credentials (Local Mode) Note: In production, use IAM Roles. For local testing, mount your credentials.

```YAML
# Inside docker-compose.yml (already configured)
volumes:
  - ~/.aws:/root/.aws:ro
```
4. Launch the Stack

```Bash
docker-compose up -d --build
```
5. Generate Traffic I included a traffic simulator script to populate the graphs.

```Bash
python3 traffic_generator.py
```
6. Access the Dashboard

Grafana: http://localhost:3000

Login: admin / admin

Prometheus: http://localhost:9090

🧹 Tear Down
To stop the stack and remove volumes:

```Bash
docker-compose down -v
```
