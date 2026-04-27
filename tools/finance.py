import yfinance as yf
from langchain_core.tools import tool

@tool
def get_stock_price(ticker: str) -> str:
    """Fetch the current stock price and basic info for a given ticker."""
    try:
        stock = yf.Ticker(ticker)
        current_price = stock.history(period='1d')['Close'].iloc[-1]
        info = stock.info
        name = info.get('longName', ticker)
        return f"The current price for {name} ({ticker}) is ${current_price:.2f}."
    except Exception as e:
        return f"Error fetching price for {ticker}: {e}"

@tool
def get_stock_historical_data(ticker: str, period: str = '1mo') -> str:
    """
    Fetch historical stock data for a given ticker. 
    Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            return f"No historical data found for {ticker} over period {period}."
        
        # Convert the pandas dataframe to a string representation for the LLM
        return hist[['Open', 'High', 'Low', 'Close', 'Volume']].to_string()
    except Exception as e:
        return f"Error fetching historical data for {ticker}: {e}"

@tool
def get_company_news(ticker: str) -> str:
    """Fetch the latest news specifically tied to the company's ticker via yfinance."""
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        if not news:
            return f"No recent news found on Yahoo Finance for {ticker}."
        
        news_summaries = []
        for n in news[:5]:
            title = n.get('title', 'No Title')
            publisher = n.get('publisher', 'Unknown')
            link = n.get('link', '')
            news_summaries.append(f"- {title} (Publisher: {publisher})\n  {link}")
        return "\n".join(news_summaries)
    except Exception as e:
        return f"Error fetching company news for {ticker}: {e}"

def get_market_movers() -> dict:
    """Fetch Top Gainers, Losers, and Most Actives from yfinance."""
    try:
        gainers = yf.screener.screen(yf.screener.PREDEFINED_SCREENER_QUERIES['day_gainers']['query'])
        losers = yf.screener.screen(yf.screener.PREDEFINED_SCREENER_QUERIES['day_losers']['query'])
        actives = yf.screener.screen(yf.screener.PREDEFINED_SCREENER_QUERIES['most_actives']['query'])
        
        def parse(resp):
            if not resp or 'quotes' not in resp: return []
            return [{"symbol": q.get("symbol"), "price": q.get("regularMarketPrice"), "change": q.get("regularMarketChangePercent")} for q in resp['quotes'][:5]]
            
        return {
            "gainers": parse(gainers),
            "losers": parse(losers),
            "actives": parse(actives)
        }
    except Exception as e:
        return {"error": str(e)}
