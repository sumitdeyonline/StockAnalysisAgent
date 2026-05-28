import streamlit as st
import os
from dotenv import load_dotenv
from agent import setup_agent, is_financial_query
from langchain_core.messages import HumanMessage, AIMessage
from tools.db_tools import init_db, save_search_query, get_recent_searches, delete_search_history, delete_single_search, update_search_response
from authlib.integrations.requests_client import OAuth2Session
import secrets
import requests

# Load environment variables from .env
load_dotenv()

# Initialize PostgreSQL Database Table if it doesn't exist
init_db()

#st.set_page_config(page_title="Claude Stock Agent", page_icon="📈", layout="wide")
st.set_page_config(page_title="Stock Agent", page_icon="📈", layout="wide")

st.markdown("""
<style>
/* Compact UI for Sidebar Search History */
[data-testid="stSidebar"] div[data-testid="stButton"] button {
    padding: 0.1rem 0.5rem !important;
    min-height: 1.5rem !important;
    height: auto !important;
}
[data-testid="stSidebar"] div[data-testid="stButton"] button p {
    font-size: 0.75rem !important;
    line-height: 1.2 !important;
}
[data-testid="stSidebar"] div[data-testid="column"] {
    padding: 0 !important;
    gap: 0 !important;
}
</style>
""", unsafe_allow_html=True)
st.title("📈 Stock Analysis Agent")
#st.markdown("This agent has access to real-time market data (yfinance), recent news (Tavily), a Postgres database for memory, and a ChromaDB vector store for semantic context.")
st.markdown("This agent has access to real-time market data , recent news, and semantic context.")

if "email" not in st.session_state:
    st.session_state.email = None

# Load Auth0 credentials safely
try:
    AUTH0_DOMAIN = st.secrets.get("AUTH0_DOMAIN", os.getenv("AUTH0_DOMAIN"))
    CLIENT_ID = st.secrets.get("AUTH0_CLIENT_ID", os.getenv("AUTH0_CLIENT_ID"))
    CLIENT_SECRET = st.secrets.get("AUTH0_CLIENT_SECRET", os.getenv("AUTH0_CLIENT_SECRET"))
    REDIRECT_URI = st.secrets.get("AUTH0_REDIRECT_URI", os.getenv("AUTH0_REDIRECT_URI", "http://localhost:8501/"))
except Exception:
    AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
    CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
    CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
    REDIRECT_URI = os.getenv("AUTH0_REDIRECT_URI", "http://localhost:8501/")

if not AUTH0_DOMAIN or not CLIENT_ID:
    st.error("⚠️ **Auth0 Configuration Missing**\nPlease configure `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID`, and `AUTH0_CLIENT_SECRET` in `.streamlit/secrets.toml` or as environment variables.")
    st.stop()

# Fetch Auth0 endpoints manually
@st.cache_data
def get_auth0_endpoints(domain):
    try:
        resp = requests.get(f'https://{domain}/.well-known/openid-configuration')
        data = resp.json()
        return data['authorization_endpoint'], data['token_endpoint'], data['userinfo_endpoint']
    except Exception:
        return None, None, None

auth_url, token_url, userinfo_url = get_auth0_endpoints(AUTH0_DOMAIN)
if not auth_url:
    st.error("Failed to fetch Auth0 configuration. Please check your AUTH0_DOMAIN.")
    st.stop()

# Check if user is returning from Auth0 with an authorization code
query_params = st.query_params
if "code" in query_params and not st.session_state.email:
    code = query_params["code"]
    client = OAuth2Session(CLIENT_ID, CLIENT_SECRET, redirect_uri=REDIRECT_URI)
    
    try:
        from urllib.parse import urlencode
        callback_url = f"{REDIRECT_URI}?{urlencode(dict(st.query_params))}"
        token = client.fetch_token(token_url, authorization_response=callback_url)
        
        # Fetch user info using the access token
        resp = client.get(userinfo_url)
        user_info = resp.json()
        
        # Map Auth0 email to the app's internal email state
        st.session_state.email = user_info.get("email")
        st.query_params.clear() # Clean up the URL
        st.rerun()
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        st.stop()

# Force Login if no email is set in session
if not st.session_state.email:
    st.markdown("### 🔒 Secure Login Required")
    st.write("Please authenticate via Auth0 to access the Stock Analysis Agent.")
    
    if st.button("Login with Auth0"):
        nonce = secrets.token_urlsafe(16)
        st.session_state['nonce'] = nonce
        
        client = OAuth2Session(CLIENT_ID, CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope="openid profile email")
        
        uri, state = client.create_authorization_url(auth_url, nonce=nonce)
        st.markdown(f'<meta http-equiv="refresh" content="0; url={uri}">', unsafe_allow_html=True)
        
    st.stop()
    
col_user, col_logout = st.columns([8, 1])
with col_user:
    st.markdown(f"**Logged in securely as:** `{st.session_state.email}`")
with col_logout:
    if st.button("Logout"):
        st.session_state.clear()
        logout_url = f"https://{AUTH0_DOMAIN}/v2/logout?client_id={CLIENT_ID}&returnTo={REDIRECT_URI}"
        st.markdown(f'<meta http-equiv="refresh" content="0; url={logout_url}">', unsafe_allow_html=True)
        st.stop()

# Initialize session state for messages and the agent
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = setup_agent()

if "current_search_id" not in st.session_state:
    st.session_state.current_search_id = None

def show_comparison_dialog():
    with st.container(border=True):
        st.markdown("### 🔍 Historical Analysis Review")
        data = st.session_state.confirming_comparison
    st.markdown(f"**Past Query:** `{data['query']}`")
    st.info(data['response'])
    
    st.markdown("What would you like to do with this historical analysis?")
    col1, col2, col3 = st.columns(3)
    if col1.button("Update Live Analysis", type="primary", help="Query the AI directly to check for updates."):
        st.session_state.pending_comparison = data
        del st.session_state["confirming_comparison"]
        st.rerun()
    if col2.button("Load to Chat", help="Load this past result into the main chat screen."):
        response_text = data['response'] or ""
        
        # Check if the DB response is a modern serialized multi-turn transcript
        if "**HUMAN**:" in response_text or "**AI**:" in response_text:
            parsed_messages = []
            import re
            # Split the string by the role tags, keeping the roles in the resulting array
            chunks = re.split(r'\*\*(HUMAN|AI)\*\*:', response_text)
            for i in range(1, len(chunks), 2):
                role = chunks[i]
                content = chunks[i+1].strip()
                if role == "HUMAN":
                    parsed_messages.append(HumanMessage(content=content))
                elif role == "AI":
                    parsed_messages.append(AIMessage(content=content))
            st.session_state.messages = parsed_messages
        else:
            # Legacy fallback for old single-shot searches
            st.session_state.messages = [
                HumanMessage(content=data['query']),
                AIMessage(content=response_text)
            ]
        
        st.session_state.current_search_id = data['search_id']
        del st.session_state["confirming_comparison"]
        st.rerun()
    if col3.button("Cancel"):
        del st.session_state["confirming_comparison"]
        st.rerun()

if "confirming_comparison" in st.session_state:
    show_comparison_dialog()

# Display chat messages from history
for idx, msg in enumerate(st.session_state.messages):
    # Filter out langgraph's intermediate tool messages from the UI simple history
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(msg.content)
            # Defer PDF generation to prevent blocking the main render loop
            col1, col2 = st.columns([1, 4])
            
            # Dynamically formulate the filename based on the preceding user query
            dl_filename = "claude_analysis_report.pdf"
            if idx > 0 and isinstance(st.session_state.messages[idx-1], HumanMessage):
                raw_q = st.session_state.messages[idx-1].content
                import re
                # Strip non-alphanumeric chars, lowercase it, and grab first few words
                clean_q = re.sub(r'[^\w\s]', '', raw_q).strip().lower()
                short_q = "_".join(clean_q.split()[:5])[:30]
                if short_q:
                    dl_filename = f"{short_q}_analysis.pdf"
            
            with col1:
                if st.button("📄 Prepare PDF", key=f"prep_hist_{idx}"):
                    with st.spinner("Compiling..."):
                        try:
                            from tools.export_tools import generate_pdf
                            st.session_state[f"pdf_bytes_{idx}_{hash(msg.content)}"] = generate_pdf(msg.content)
                        except Exception as e:
                            st.error(f"Failed: {e}")
            
            with col2:
                if f"pdf_bytes_{idx}_{hash(msg.content)}" in st.session_state:
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=st.session_state[f"pdf_bytes_{idx}_{hash(msg.content)}"],
                        file_name=dl_filename,
                        mime="application/pdf",
                        key=f"dl_hist_{idx}"
                    )

prompt_to_run = None
active_search_id = st.session_state.current_search_id
active_query = None

# Accept user input
if prompt := st.chat_input("Enter your request (e.g., 'Analyze NVDA stock and recent news'):"):
    prompt_to_run = prompt

# Check for pending comparisons triggered by the sidebar
if "pending_comparison" in st.session_state and st.session_state.pending_comparison:
    prompt_to_run = st.session_state.pending_comparison["prompt"]
    active_search_id = st.session_state.pending_comparison["search_id"]
    st.session_state.current_search_id = active_search_id
    active_query = st.session_state.pending_comparison["query"]
    st.session_state.pending_comparison = None

def __stream_agent_response(user_message, status_placeholder):
    """A generator that plucks raw text fragments from the LangGraph message stream natively."""
    try:
        for chunk, metadata in st.session_state.agent.stream(
            {"messages": st.session_state.messages}, 
            stream_mode="messages"
        ):
            # Only intercept string chunks returned from the main Language Model
            if metadata.get("langgraph_node") == "agent":
                # Handle old-style string chunks natively
                if isinstance(chunk.content, str) and chunk.content:
                    status_placeholder.empty() # Clear the spinner when text generation explicitly starts
                    yield chunk.content
                # Handle new-style list chunk arrays generated distinctly by langchain-anthropic pipelines
                elif isinstance(chunk.content, list):
                    for block in chunk.content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            status_placeholder.empty()
                            yield block.get("text", "")
    except Exception as e:
        yield f"\n\n*Agent stream interrupted: {e}*"

@st.fragment
def execute_agent_search(user_message, prompt_str, search_id):
    # Run the streaming agent loop
    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        with status_placeholder.spinner("Thinking and interacting with tools..."):
            try:
                # Streamlit parses the generator securely and types the output visually in real-time.
                # It evaluates exactly to the full string once completion is done.
                final_ai_content = st.write_stream(__stream_agent_response(user_message, status_placeholder))
                
                if final_ai_content:
                    # Store to UI state map natively before database save
                    st.session_state.messages.append(AIMessage(content=final_ai_content))
                    
                    # Serialize the entire conversation for DB persistence
                    full_convo = "\n\n".join([f"**{m.type.upper()}**: {m.content}" for m in st.session_state.messages if isinstance(m, AIMessage) or isinstance(m, HumanMessage)])
                    
                    if search_id:
                        update_search_response(st.session_state.email, search_id, full_convo)
                    else:
                        new_id = save_search_query(st.session_state.email, prompt_str, full_convo)
                        if new_id:
                            st.session_state.current_search_id = new_id
                    
                    # Force a full app rerun to elegantly sync the fragment state back into the main history loop
                    st.rerun()
            except Exception as e:
                st.error(f"An error occurred: {e}")

if prompt_to_run:
    actual_input_msg = HumanMessage(content=prompt_to_run)
    
    if active_query:
        display_text = f"🔄 *Re-evaluating historical query against live systems:* **{active_query}**"
        st.session_state.messages.append(HumanMessage(content=display_text))
        with st.chat_message("user"):
            st.markdown(display_text)
        execute_agent_search(actual_input_msg, prompt_to_run, active_search_id)
    else:
        # Enforce Guardrail on natively typed queries
        with st.spinner("Validating request..."):
            is_valid = is_financial_query(prompt_to_run)
            
        st.session_state.messages.append(actual_input_msg)
        with st.chat_message("user"):
            st.markdown(prompt_to_run)
            
        if not is_valid:
            warning_msg = "⚠️ **Guardrail Alert:** I am a specialized financial assistant. Your query does not appear to relate to stocks, markets, companies, or investing. Please adjust your request."
            st.session_state.messages.append(AIMessage(content=warning_msg))
            with st.chat_message("assistant"):
                st.warning(warning_msg)
        else:
            execute_agent_search(actual_input_msg, prompt_to_run, active_search_id)

st.sidebar.markdown("### Chat Controls")
if st.sidebar.button("➕ New Chat", use_container_width=True, help="Clear the current chat window"):
    st.session_state.messages = []
    st.rerun()

#st.sidebar.markdown("---")
st.sidebar.markdown("### Search History")
past_searches = get_recent_searches(st.session_state.email)
if past_searches:
    for search in past_searches:
        search_id = search["id"]
        query = search["query"]
        snippet = query[:30] + "..." if len(query) > 30 else query
        
        col1, col2 = st.sidebar.columns([5, 1])
        if col1.button(snippet, key=f"load_{search_id}", help="Review and compare against live data"):
            st.session_state.messages = []
            compare_prompt = (
                f"I previously asked you: '{query}'\n\n"
                f"Your previous analysis was:\n<past_analysis>\n{search.get('response') or 'No past response recorded.'}\n</past_analysis>\n\n"
                f"Please explicitly perform this task again using real-time data, and provide a detailed comparison highlighting exactly what has changed (prices, news, developments) since that past analysis was generated."
            )
            st.session_state.confirming_comparison = {
                "prompt": compare_prompt, 
                "search_id": search_id,
                "query": query,
                "response": search.get('response') or 'No past response recorded.'
            }
            st.rerun()
            
        if col2.button("✖", key=f"del_{search_id}", help="Delete this search"):
            delete_single_search(st.session_state.email, search_id)
            st.rerun()
            
    #st.sidebar.markdown("---")
    if st.sidebar.button("Clear All History", type="primary"):
        delete_search_history(st.session_state.email)
        st.rerun()
else:
    st.sidebar.info("No searches yet.")

@st.cache_data(ttl=300)
def load_market_movers():
    from tools.finance import get_market_movers
    return get_market_movers()

st.sidebar.markdown("---")
st.sidebar.markdown("### Market Movers")
movers = load_market_movers()
if "error" not in movers:
    tab1, tab2, tab3 = st.sidebar.tabs(["📈 Gainers", "📉 Losers", "🔥 Active"])
    
    def render_mover_list(container, items, show_volume=False):
        if not items:
            container.info("Data unavailable")
            return
        for item in items:
            sym = item['symbol']
            price = f"${item['price']:.2f}" if item['price'] else "N/A"
            if show_volume:
                vol = item.get('volume', 0)
                if not vol: vol_str = "N/A"
                elif vol >= 1e9: vol_str = f"{vol/1e9:.2f}B"
                elif vol >= 1e6: vol_str = f"{vol/1e6:.2f}M"
                else: vol_str = f"{vol/1e3:.1f}k"
                container.markdown(f"**{sym}**: {price} *(Vol: {vol_str})*")
            else:
                chg = item['change']
                color = "green" if chg and chg > 0 else "red"
                chg_str = f"{chg:.2f}%" if chg else "N/A"
                container.markdown(f"**{sym}**: {price} (:{color}[{chg_str}])")
            
    render_mover_list(tab1, movers.get("gainers", []))
    render_mover_list(tab2, movers.get("losers", []))
    render_mover_list(tab3, movers.get("actives", []), show_volume=True)
else:
    st.sidebar.warning("Failed to load generic market movers.")

# st.sidebar.markdown("---")
# st.sidebar.markdown("### Status")
# st.sidebar.success("Database tools initialized")
# st.sidebar.success("ChromaDB vector store connected")
# if os.environ.get("TAVILY_API_KEY"):
#     st.sidebar.success("Tavily API initialized")
# else:
#     st.sidebar.warning("Tavily API Key missing")
    
# if os.environ.get("ANTHROPIC_API_KEY"):
#     st.sidebar.success("Claude 3.5 Sonnet connected")
# else:
#     st.sidebar.warning("Anthropic API Key missing")
