# Supabase Production Security Guide

Currently, your Streamlit application connects to Supabase using a raw PostgreSQL connection string (`DATABASE_URL`). This is perfectly fine for local development, but in a production environment (like Cloud Run), exposing the raw database port to the internet with the master password carries risks. 

Here are the 3 progressive steps to secure your Supabase architecture.

---

## 1. Implement Supabase Connection Pooling (Immediate Fix)

Direct connections map 1-to-1 with PostgreSQL processes. If your Streamlit app scales up, you will instantly run out of database connections and the app will crash.

**How to fix:**
In the Supabase Dashboard, go to **Database > Connection Pooling**.
Update your `.env` to use the pooler URL (notice the port `6543` instead of `5432`).
*This acts as a secure buffer, managing thousands of incoming requests efficiently without crashing the master database.*

---

## 2. Enforce IP Allowlisting (Network Security)
By default, your Supabase database allows connections from any IP address. 

**How to fix:**
Go to your **Supabase Dashboard** -> **Project Settings** -> **Network**. Under **IP Allowlisting**, restrict access exclusively to your local IP and your production server's Static IP.

### Configuring a Static IP for Google Cloud Run
By default, Cloud Run uses a constantly changing pool of dynamic IP addresses for outgoing traffic. To allowlist your Cloud Run app (`stockanalysisagent-351454544171.us-west2.run.app`) in Supabase, you must assign it a **Static Outbound IP (Cloud NAT)**.

Follow these exact steps in the Google Cloud Console:

1. **Create a Serverless VPC Access Connector**:
   - Go to **VPC Network** > **Serverless VPC access**.
   - Create a connector in `us-west2` (the same region as your app).
   
2. **Reserve a Static IP**:
   - Go to **VPC Network** > **IP addresses**.
   - Click "Reserve External Static IP" (Name it `supabase-db-ip`, Region `us-west2`).

3. **Setup Cloud NAT & Cloud Router**:
   - Go to **Network Services** > **Cloud NAT**.
   - Click "Get started". Create a new Cloud Router in `us-west2`.
   - Under "Cloud NAT IP Addresses", select **Manual** and choose the Static IP you reserved in Step 2.

4. **Route Cloud Run through the VPC**:
   - Go to **Cloud Run**, click on your `stockanalysisagent` service, and click **Edit & Deploy New Revision**.
   - Go to the **Connections** tab.
   - Under "VPC", select the **Serverless VPC Access connector** you created.
   - Under "Egress", select **Route all traffic to the VPC**.
   - Click **Deploy**.

**Result:** Now, every time your Cloud Run app queries Supabase, it will *always* use that exact Static IP you reserved! You can copy that IP address and paste it directly into your Supabase Allowlist!

---

## 3. Migrate to the Supabase REST API (Ultimate Security)
The most secure architecture possible is to completely shut off direct PostgreSQL access (Port 5432/6543) from the public internet.

Instead of using `psycopg2` and writing raw SQL `INSERT` commands, you would use the official `supabase-py` client library.
