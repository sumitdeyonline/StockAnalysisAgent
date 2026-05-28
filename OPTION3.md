# Option 3: Direct Okta Integration (Authlib)

This approach connects your Streamlit app directly to Okta using raw OAuth2/OIDC protocols via the Python `authlib` package. 

## Architecture
1. **Streamlit App:** Acts as the OAuth Client.
2. **Okta:** Acts as the Authorization Server.
3. **Flow:** User clicks login -> Redirects to Okta -> Authenticates -> Redirects back to Streamlit with a query parameter `?code=123` -> Streamlit trades code for JWT token.

## Implementation Steps (Code-Based)

### 1. Configure Okta Developer Console
1. Create a new "Web Application" in Okta.
2. Note down your `Client ID`, `Client Secret`, and `Issuer URI`.
3. Set the **Sign-in Redirect URI** to your deployed Streamlit URL (e.g., `https://my-app-xyz.a.run.app/`).

### 2. Update Python Dependencies
Add `authlib` to your `pyproject.toml` and `requirements.txt`:
```toml
"authlib>=1.3.0",
"httpx>=0.27.0"
```

### 3. Modify `app.py`
We will use Streamlit's query parameter parsing to handle the OAuth callback natively.

```python
import streamlit as st
from authlib.integrations.requests_client import OAuth2Session

# Okta Configuration
client_id = st.secrets["OKTA_CLIENT_ID"]
client_secret = st.secrets["OKTA_CLIENT_SECRET"]
authorization_endpoint = "https://your-domain.okta.com/oauth2/v1/authorize"
token_endpoint = "https://your-domain.okta.com/oauth2/v1/token"
redirect_uri = "https://your-cloud-run-url.com/"

# Check if user is returning from Okta with an auth code
query_params = st.query_params
if "code" in query_params and "user" not in st.session_state:
    code = query_params["code"]
    client = OAuth2Session(client_id, client_secret, redirect_uri=redirect_uri)
    token = client.fetch_token(token_endpoint, authorization_response=st.request.url)
    st.session_state.user = token
    st.query_params.clear() # Clean up the URL

# Check Session State
if "user" not in st.session_state:
    st.title("🔒 Login Required")
    
    if st.button("Login with Okta"):
        client = OAuth2Session(client_id, client_secret, redirect_uri=redirect_uri)
        uri, state = client.create_authorization_url(authorization_endpoint)
        st.markdown(f"[Click here to continue]({uri})")
        
    st.stop() # Halts execution

# ... (Rest of your app code runs normally here) ...
```

## Pros & Cons
- **Pros:** Direct connection to Okta. Total control over the OAuth flow and token storage.
- **Cons:** Streamlit's stateless, rerun-heavy architecture makes handling OAuth callbacks notoriously tricky. If the user refreshes the page incorrectly, they might lose their session state and have to log in again.
