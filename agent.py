import os
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic

# Import our custom tools
from tools.finance import get_stock_price, get_stock_historical_data, get_company_news
from tools.search import web_search_tavily
from tools.db_tools import save_analysis_to_db, get_past_analyses
from tools.vector_tools import store_in_vector_db, search_vector_db
from langchain_core.prompts import PromptTemplate

def is_financial_query(query: str) -> bool:
    """Explicitly protect the system by bouncing generic chat payloads using a cheap classifier boundary."""
    try:
        model_name = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        llm = ChatAnthropic(model=model_name, temperature=0, max_tokens=10)
        prompt = PromptTemplate.from_template(
            "You are a strict query classifier. Does the following user query explicitly ask about stocks, trading, financial markets, investing, companies, or business news? Respond with exactly one word: 'YES' or 'NO'.\n\nQuery: {query}"
        )
        chain = prompt | llm
        response = chain.invoke({"query": query})
        return "yes" in response.content.lower()
    except Exception:
        # If the guardrail itself fails (API error), default to allowing it through to avoid app crashing
        return True
def setup_agent():
    # We use Claude 3.5 Sonnet as the underlying LLM
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Warning: ANTHROPIC_API_KEY not set. The agent will fail if invoked.")
        
    llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)
    
    tools = [
        get_stock_price,
        get_stock_historical_data,
        get_company_news,
        web_search_tavily,
        save_analysis_to_db,
        get_past_analyses,
        store_in_vector_db,
        search_vector_db
    ]
    
    # Construct the LangGraph React Agent with our toolset
    agent_executor = create_react_agent(llm, tools)
    return agent_executor
