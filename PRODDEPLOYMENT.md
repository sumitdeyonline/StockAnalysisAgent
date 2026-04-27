# Production Deployment Guide: Google Cloud Run

This guide outlines exactly how to deploy the **Claude Stock Analysis Agent** to the web using Google Cloud Run, strictly via the **Cloud Console Web Interface** (no command-line tools required). 

Google Cloud Run allows you to deploy containerized applications effortlessly, scaling automatically based on web traffic. Because this is a Streamlit application, Google Cloud Run is the optimal architecture.

---

## Pre-requisites

Before touching the Cloud Console, ensure your codebase is ready:

1. **Dockerized Environment**: Ensure you have a standard `Dockerfile` in the root of your project repository.
   *Because Cloud Run runs containers, a simple Streamlit Dockerfile is necessary.*
   ```dockerfile
   # Example minimal Dockerfile
   FROM python:3.12-slim
   WORKDIR /app
   COPY . /app
   # Using uv for lightning fast installation if applicable, or pip:
   RUN pip install uv && uv pip install --system -r requirements.txt
   EXPOSE 8501
   CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```
2. **Version Control**: Push your entire codebase (including the `Dockerfile`) to a **GitHub**, **GitLab**, or **Bitbucket** repository. Google Cloud Run natively integrates with these platforms to fetch your code!

---

## Step-by-Step Deployment (Web Interface)

### 1. Access Google Cloud Run
1. Log into your [Google Cloud Console](https://console.cloud.google.com/).
2. In the top search bar, search for **"Cloud Run"** and select it.
3. Click the blue **+ CREATE SERVICE** button at the top of the dashboard.

### 2. Connect Your Repository
1. Select **"Continuously deploy new revisions from a source repository"**.
2. Click **SET UP WITH CLOUD BUILD**.
3. **Repository Provider**: Select your host (e.g., GitHub). You may need to authorize Google Cloud to access your account temporarily.
4. **Repository**: Find and select your `ClaudeAgent` repository from the dropdown.
5. Check the box agreeing to the terms and click **NEXT**.

### 3. Build Configuration
1. **Branch**: Select the branch you want to deploy (usually `main` or `master`).
2. **Build Type**: Select **Dockerfile**.
3. **Source location**: Keep it as `/Dockerfile` (assuming it is in the root directory).
4. Click **SAVE**.

### 4. Service Configuration
You will now be returned to the main configuration page. Set the parameters as follows:
- **Service Name**: `claude-stock-agent` (or your preferred name).
- **Region**: Choose the region closest to you or your target user base (e.g., `us-central1`).
- **CPU Allocation**: Select "CPU is only allocated during request processing" (This ensures you are only billed when users are actively chatting).
- **Autoscaling**:
  - Minimum instances: `0` (Saves money, scales to zero when inactive).
  - Maximum instances: `5` (or whatever threshold guards your budget).
- **Ingress**: Select **"Allow all traffic"**.
- **Authentication**: Select **"Allow unauthenticated invocations"** (This makes your Streamlit app publicly accessible on the web framework).

### 5. Environment Variables & Secrets
Because this agent relies heavily on external APIs, you must pass your hidden variables safely!
1. Scroll down and expand the **Container, Volumes, Networking, Security** section.
2. Under the **Container** tab, locate **Container port**. Change this from `8080` to **`8501`** (This is Streamlit's required port default).
3. Scroll down slightly to **Environment Variables**.
4. Click **+ ADD VARIABLE** and copy/paste exactly what is within your local `.env` file:
   - Name: `ANTHROPIC_API_KEY` | Value: `your-actual-api-key`
   - Name: `TAVILY_API_KEY`     | Value: `your-actual-api-key`
   - Name: `DATABASE_URL`       | Value: `your-postgres-uri`

### 6. Deploy
1. Click the blue **CREATE** button at the very bottom.
2. A loading screen will appear showing the build logs in real-time. Google Cloud is automatically pulling your repository, building the Dockerfile, and deploying instances. (This normally takes 3–5 minutes).
3. Upon completion, a green checkmark will appear, and you will be provided with a **live public URL** directly beneath your service title.

---

## 🛠️ Post-Deployment Verification
- Click the provided Service URL to open your live application in the browser!
- Check the Streamlit Sidebar. If you configured your Environment Variables correctly in Step 5, the sidebar should generate green confirmation statuses `(e.g., "Tavily API initialized", "Claude 3.5 Sonnet connected")`. 
- **Continuous Deployment**: Anytime you `git push` new changes to your repository, Google Cloud Run will automatically orchestrate a seamless re-build and overwrite the existing server instance effortlessly.
