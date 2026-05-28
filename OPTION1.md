# Option 1: Google Cloud Identity-Aware Proxy (IAP)

This is the **Enterprise Standard** approach. Because your application is deployed on Google Cloud Run, you can secure it at the network edge before a user's request even reaches your Python code.

## Architecture
1. **Google Cloud Load Balancer:** Sits in front of your Cloud Run service.
2. **Identity-Aware Proxy (IAP):** Intercepts all traffic at the Load Balancer.
3. **Cloud Identity / Okta Federation:** Authenticates the user via Google (which can be linked to your Okta tenant via SAML).

## Implementation Steps (Zero Code)

### 1. Set up a Load Balancer
Cloud Run services are publicly accessible by default. You must restrict ingress to "Internal and Cloud Load Balancing" only.
1. Go to **Network Services -> Load balancing** in GCP.
2. Create a global HTTP(S) load balancer.
3. Create a **Serverless Network Endpoint Group (NEG)** pointing to your Cloud Run service.
4. Set the backend service to use this NEG.

### 2. Configure OAuth & IAP
1. Go to **Security -> Identity-Aware Proxy**.
2. Enable IAP on the backend service you just created.
3. You will be prompted to configure an OAuth consent screen.
4. Grant the `IAP-secured Web App User` IAM role to the specific users or groups (e.g., your Okta group) who should have access.

### 3. Federate Okta (If required)
If your organization requires users to explicitly type their credentials into Okta rather than using Google Workspace:
1. Go to Google Cloud Identity admin console.
2. Set up **Third-party IdP integration** using SAML.
3. Point it to your Okta tenant.

## Pros & Cons
- **Pros:** 100% zero-code. Incredibly secure (impossible to bypass the Python app). Handles scaling and DDoS protection natively.
- **Cons:** Requires networking knowledge in GCP. The Load Balancer incurs a small monthly infrastructure cost (~$15-20/mo).
