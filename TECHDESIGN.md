# Technical Design Document: Claude Stock Analysis Agent

## 1. System Overview
The **Claude Stock Analysis Agent** is a generative AI-powered application designed to autonomously analyze financial markets, retrieve real-time data, and build an ongoing knowledge base of its findings. It is built using a React (Reasoning and Acting) architecture powered by LangGraph, with Anthropic's Claude serving as the core reasoning engine.

The system is designed to provide users with an interactive chat interface to request analysis of specific ticker symbols, general market trends, and historical contexts. 

## 2. Architecture Architecture
The application consists of three main layers:

### 2.1 Frontend User Interface (Streamlit)
* **File:** `app.py`
* **Role:** Manages the visual interface, state-driven user interactions, and visual layouts.
* **Key Features:**
  - Enforces email-gated user sessions, ensuring any interactions natively scope persistent metrics.
  - Generates a compact, history-tracked sidebar loaded via centralized databases mapping older agentic payloads natively back into the frontend.
  - Natively manages "Generative Comparison Arrays": bypassing standard queries and allowing users to re-evaluate their archived queries immediately against the live state to synthesize dynamic deltas.
  - Dynamically runs `yfinance` screener logic and natively caches a "Market Movers" interface parsing exact Top Gainers, Losers, and Actives under streamlined UI tabs.
  - Utlizes advanced `@st.fragment` rendering architectures specifically built to disassociate LLM processing timeouts from the core DOM string, permanently bypassing visual interaction locking!

### 2.2 Agent Reasoning Layer (LangGraph & LangChain)
* **File:** `agent.py`
* **Role:** Acts as the brain of the application and the semantic filter.
* **Component Details:**
  - Utilizes a fast heuristic `is_financial_query()` Intent Classifier powered asynchronously before the graph compiles. This establishes strict boundary guardrails, rejecting off-topic commands instantly to reserve token quotas.
  - Uses `langgraph.prebuilt.create_react_agent` to construct a deterministic ReAct loop.
  - Specifically configured to use `ChatAnthropic` (Claude) as the core Large Language Model.
  - Receives the list of configured tools and determines when, how, and in what sequence to execute them autonomously based on complex contextual prompts.

### 2.3 Tools & Integrations Layer
The agent extends its capabilities beyond its training data through specialized, custom-built tools covering 4 domains:

#### A. Finance Integration (`tools/finance.py`)
Powered by `yfinance`, this toolset gives the agent real-time access to the stock market:
* `get_stock_price(ticker)`: Retrieves the latest closing price and company metadata.
* `get_stock_historical_data(ticker, period)`: Extracts Open/High/Low/Close/Volume metrics over intervals (e.g., '1mo', '1y') and formats the pandas dataframe as string output for LLM consumption.
* `get_company_news(ticker)`: Fetches the top 5 most recent news articles directly tied to a ticker.

#### B. Web Search (`tools/search.py`)
Powered by `TavilyClient`:
* `web_search_tavily(query)`: Executes real-time web searches. It bypasses ticker-specific silos and gives the agent broad macro-economic capability and market sentiment analysis via the Tavily advanced search endpoint.

#### C. Relational Memory & Session Logs (`tools/db_tools.py`)
Powered by `psycopg2` targeting a structured PostgreSQL instance, binding to the user's explicit email gateway:
* `init_db()`: Ensures the existence of the `search_history` tabular relational memory map.
* `save_search_query(email, query, response)`: Saves final user payloads and AI generations systematically into strict cached blocks.
* `get_recent_searches(email)`: Dynamically fetches histories into the Streamlit UI up to 15 nodes thick.
* `update_search_response(...)`: Synthesizes stateful changes when analyzing comparative modifications without bloating the data stack.

#### D. Semantic Vector Storage (`tools/vector_tools.py`)
Powered by local `chromadb`:
* `store_in_vector_db(text, source, document_id)`: Stores heavy unstructured text (like dense analyst reports) alongside metadata into a `stock_research` collection.
* `search_vector_db(query)`: Utilizes semantic embeddings to bypass token limits, allowing the agent to query concepts against stored archives and inject relevant snippets into its working context.

## 3. Data Flow
1. **Input:** The user inputs a query via Streamlit (`app.py`).
2. **Context:** The query, appended to the historical `HumanMessage`/`AIMessage` list, is passed to `agent.invoke()`.
3. **Execution Loop:**
   - Claude evaluates the prompt.
   - If a tool is needed (e.g., fetching a stock price), Claude generates a tool call.
   - LangGraph intercepts the call, executes the corresponding Python function in `tools/`, and feeds the raw string result back to Claude.
   - Claude evaluates the new context. It may call another tool (e.g., searching for news to contextualize the price drop) or conclude its reasoning.
4. **Resolution:** Once Claude has enough data, it generates a final natural-language response.
5. **Output:** The final response is appended to session state and rendered in Streamlit.

## 4. Dependencies
* **Core Frameworks:** `streamlit`, `langgraph`, `langchain-anthropic`
* **Integrations:** `yfinance`, `tavily-python`, `psycopg2-binary`, `chromadb`
* **Environment:** Python 3.12 managed via `uv` (`pyproject.toml`). Secrets loaded via `python-dotenv`.
