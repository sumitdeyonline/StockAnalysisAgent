# Claude Stock Analysis Agent 📈

An advanced, interactive generative AI assistant built exactly for domain-specific market analysis. It functions not just as a typical chatbot, but as an autonomous LangGraph agent equipped with independent reasoning logic and customized external tooling, complete with a persistent user interface and generative memory.

## Key Features

- **Live Data Extractor:** Leverages `yfinance` plugins and the advanced Tavily Search API to execute native queries on current stock prices, historical datasets, company news, and breaking macroeconomic developments.
- **Autonomous Reasoning:** Operates on ReAct architecture powered by Anthropic's Claude 3.5 Sonnet. It evaluates ambiguous inquiries, loops through external API integrations until it retrieves actionable context, and synthesizes financial conclusions automatically.
- **Persistent Memory & Comparative Generation:** Includes an email-gated session logic tied to heavily structured PostgreSQL databases. The agent not only remembers past analyses but allows you to natively pull up old saved logs and explicitly trigger real-time "comparisons" to contrast them against live data seamlessly.
- **Intent Classifier Guardrails:** Secures API limits and tool thresholds by strictly vetting early inputs via edge-layer LLM intent classifiers, cleanly bouncing any prompt that strays from core financial market themes.
- **Asynchronicity:** Outfitted natively with Streamlit's fragment (`@st.fragment`) mechanics for total UI decoupling, handling ultra-heavy LLM wait states without freezing main Streamlit rendering canvases!
- **Dynamic Live Sidebar:** Actively caches real-time analytical stock screeners via `yfinance`, continuously updating "Top Gainers," "Top Losers," and "Most Active" equities into a space-efficient side-panel layout.

## Environment & Run Configuration

Requires Python 3.12 managed structurally via `uv`.

1. **Install Dependencies:**
```bash
uv pip install -r requirements.txt
```

2. **Supply Global Environmental Variables (`.env`):**
```env
ANTHROPIC_API_KEY=your_key
TAVILY_API_KEY=your_key
DATABASE_URL=postgres_connection_uri
```

3. **Spin Up the Interactive Frontend:**
```bash
uv run streamlit run app.py
```
