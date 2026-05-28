# Option 2: Supabase Auth (Native UI Integration)

This approach leverages your existing Supabase project to handle the heavy lifting of OAuth/SAML securely, while providing a login screen directly inside your Streamlit interface.

## Architecture
1. **Streamlit UI:** Checks for an active session state. If none, renders a login screen.
2. **Supabase Auth:** Handles the actual redirect to Okta and stores the secure JWT token.
3. **Okta:** Acts as the Identity Provider (IdP).

## Implementation Steps (Code-Based)

### 1. Configure Supabase Dashboard
1. Go to your Supabase Project -> **Authentication** -> **Providers**.
2. Find **Okta** (or standard SAML/OIDC) and enable it.
3. You will need to input your Okta Domain, Client ID, and Client Secret.
4. Supabase will generate a Callback URL. Paste this into your Okta Developer Console.

### 2. Update Python Dependencies
We must add the official Supabase Python client to `pyproject.toml` and `requirements.txt`:
```toml
"supabase>=2.4.5"
```

### 3. Modify `app.py`
We will wrap the entire application in an authentication check.

```python
import streamlit as st
from supabase import create_client, Client

# Initialize Supabase Client
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
supabase: Client = create_client(url, key)

# Check Session State
if "user" not in st.session_state:
    st.title("🔒 Login Required")
    st.write("Please authenticate to access the Stock Analysis Agent.")
    
    if st.button("Login with Okta"):
        # Trigger Supabase OAuth flow
        data = supabase.auth.sign_in_with_oauth({
            "provider": "okta",
            "options": {"redirect_to": "https://your-cloud-run-url.com"}
        })
        st.markdown(f"[Click here to continue]({data.url})")
    
    st.stop() # Halts execution of the rest of the app

# ... (Rest of your app code runs normally here) ...
```

## Pros & Cons
- **Pros:** No extra infrastructure costs. Keeps users inside your app's visual experience. Ties authentication directly to your existing database if you want to implement user-specific row-level security (RLS) later.
- **Cons:** Requires modifying Python code and handling session state edge cases in Streamlit.
