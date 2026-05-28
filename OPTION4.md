# Option 4: Direct Auth0 Integration (Authlib)

This approach connects your Streamlit app directly to Auth0 using standard OAuth2/OIDC protocols via the Python `authlib` package. Auth0 is widely considered one of the easiest Identity Providers to integrate into custom Python applications.

## Architecture
1. **Streamlit App:** Acts as the OAuth Client.
2. **Auth0:** Acts as the Authorization Server and User Identity Provider.
3. **Flow:** User clicks login -> Redirects to Auth0 Universal Login -> Authenticates -> Redirects back to Streamlit with an authorization code -> Streamlit trades code for JWT token.

## Implementation Steps (Code-Based)

### 1. Configure Auth0 Dashboard
1. Log in to your Auth0 Dashboard and go to **Applications -> Applications**.
2. Create a new **Regular Web Application**.
3. Go to the Settings tab and note down your `Domain`, `Client ID`, and `Client Secret`.
4. Set the **Allowed Callback URLs** to your deployed Streamlit URL (e.g., `https://my-app-xyz.a.run.app/`).
5. Set the **Allowed Logout URLs** to the same URL.

### 2. Update Python Dependencies
Add `authlib` to your `pyproject.toml` and `requirements.txt`:
```toml
"authlib>=1.3.0",
"httpx>=0.27.0" # Required by Authlib for async/modern HTTP requests
```

### 3. Modify `app.py`
We will use Streamlit's query parameter parsing to handle the OAuth callback natively. Because Auth0 supports OpenID Connect discovery, configuring the client is incredibly clean.

```python
import streamlit as st
from authlib.integrations.requests_client import OAuth2Session

# Auth0 Configuration
AUTH0_DOMAIN = st.secrets["AUTH0_DOMAIN"]
CLIENT_ID = st.secrets["AUTH0_CLIENT_ID"]
CLIENT_SECRET = st.secrets["AUTH0_CLIENT_SECRET"]
REDIRECT_URI = "https://your-cloud-run-url.com/"

# Auth0 Discovery URL
server_metadata_url = f'https://{AUTH0_DOMAIN}/.well-known/openid-configuration'

# Check if user is returning from Auth0 with an auth code
query_params = st.query_params
if "code" in query_params and "user" not in st.session_state:
    code = query_params["code"]
    client = OAuth2Session(CLIENT_ID, CLIENT_SECRET, redirect_uri=REDIRECT_URI)
    
    # Authlib automatically discovers endpoints from the metadata URL
    client.load_server_metadata(server_metadata_url)
    
    token = client.fetch_token(authorization_response=st.request.url)
    user_info = client.parse_id_token(token, nonce=st.session_state.get('nonce'))
    
    st.session_state.user = user_info
    st.query_params.clear() # Clean up the URL so the code isn't reused

# Check Session State
if "user" not in st.session_state:
    st.title("🔒 Login Required")
    st.write("Please authenticate via Auth0 to access the Stock Analysis Agent.")
    
    if st.button("Login with Auth0"):
        import secrets
        nonce = secrets.token_urlsafe(16)
        st.session_state['nonce'] = nonce
        
        client = OAuth2Session(CLIENT_ID, CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope="openid profile email")
        client.load_server_metadata(server_metadata_url)
        
        uri, state = client.create_authorization_url(nonce=nonce)
        st.markdown(f"[Click here to securely login via Auth0]({uri})")
        
    st.stop() # Halts execution

# ... (Rest of your app code runs normally here) ...
st.write(f"Welcome, {st.session_state.user.get('name')}!")
```

## Pros & Cons
- **Pros:** Direct connection to Auth0. Auth0's Universal Login page looks extremely professional out of the box. No intermediate services needed.
- **Cons:** Streamlit's stateless architecture means managing the redirect loop and `nonce` states requires strict session management. Like Option 3, if users navigate weirdly, they might drop their session state.
