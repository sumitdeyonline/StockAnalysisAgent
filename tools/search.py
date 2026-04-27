import os
from langchain_core.tools import tool
from tavily import TavilyClient

@tool
def web_search_tavily(query: str, max_results: int = 5) -> str:
    """
    Search the web for real-time news and market updates using the Tavily API.
    Use this to look for general financial trends or broader news unrelated to a single ticker,
    or real-time broad sentiment.
    """
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "Tavily API key not found in environment."
    
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query, 
            search_depth="advanced", 
            max_results=max_results
        )
        
        results = response.get('results', [])
        if not results:
            return f"No results found for query: {query}"
        
        formatted_results = []
        for r in results:
            title = r.get('title', 'No title')
            snippet = r.get('content', 'No snippet')
            url = r.get('url', '')
            formatted_results.append(f"Title: {title}\nSnippet: {snippet}\nURL: {url}\n")
        
        return "\n---\n".join(formatted_results)
    except Exception as e:
        return f"Error performing web search: {e}"
