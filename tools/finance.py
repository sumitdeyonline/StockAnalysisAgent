import yfinance as yf
from langchain_core.tools import tool
import pandas as pd
import numpy as np

@tool
def get_stock_price(ticker: str) -> str:
    """Fetch the current stock price and basic info for a given ticker."""
    try:
        ticker = ticker.replace('$', '').strip().upper()
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
        ticker = ticker.replace('$', '').strip().upper()
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
        ticker = ticker.replace('$', '').strip().upper()
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
        gainers_resp = yf.screener.screen(yf.screener.PREDEFINED_SCREENER_QUERIES['day_gainers']['query'])
        losers_resp = yf.screener.screen(yf.screener.PREDEFINED_SCREENER_QUERIES['day_losers']['query'])
        actives_resp = yf.screener.screen(yf.screener.PREDEFINED_SCREENER_QUERIES['most_actives']['query'])
        
        def parse(resp, sort_key, reverse):
            if not resp or 'quotes' not in resp: return []
            quotes = sorted(resp['quotes'], key=lambda x: x.get(sort_key, 0), reverse=reverse)
            return [{"symbol": q.get("symbol"), "price": q.get("regularMarketPrice"), "change": q.get("regularMarketChangePercent"), "volume": q.get("regularMarketVolume")} for q in quotes[:5]]
            
        return {
            "gainers": parse(gainers_resp, 'regularMarketChangePercent', True),
            "losers": parse(losers_resp, 'regularMarketChangePercent', False),
            "actives": parse(actives_resp, 'regularMarketVolume', True)
        }
    except Exception as e:
        return {"error": str(e)}

@tool
def get_stock_fundamentals(ticker: str) -> str:
    """Fetch fundamental financial metrics (P/E, EPS, Debt-to-Equity, FCF, ROE, margins) for a given stock ticker."""
    try:
        ticker = ticker.replace('$', '').strip().upper()
        stock = yf.Ticker(ticker)
        info = stock.info
        
        fundamentals = {
            "Trailing P/E": info.get("trailingPE", "N/A"),
            "Forward P/E": info.get("forwardPE", "N/A"),
            "Price-to-Book (P/B)": info.get("priceToBook", "N/A"),
            "Trailing EPS": info.get("trailingEps", "N/A"),
            "Forward EPS": info.get("forwardEps", "N/A"),
            "Debt-to-Equity": info.get("debtToEquity", "N/A"),
            "Return on Equity (ROE)": info.get("returnOnEquity", "N/A"),
            "Profit Margin": info.get("profitMargins", "N/A"),
            "Free Cash Flow": info.get("freeCashflow", "N/A"),
            "Revenue Growth": info.get("revenueGrowth", "N/A")
        }
        
        output = [f"Fundamental Analysis for {ticker}:"]
        for key, value in fundamentals.items():
            if isinstance(value, float):
                # Format large numbers or percentages
                if "Margin" in key or "Growth" in key or "ROE" in key:
                    output.append(f"- {key}: {value:.2%}")
                else:
                    output.append(f"- {key}: {value:.2f}")
            else:
                output.append(f"- {key}: {value}")
        
        return "\n".join(output)
    except Exception as e:
        return f"Error fetching fundamentals for {ticker}: {e}"

@tool
def get_technical_indicators(ticker: str) -> str:
    """Calculate and return key technical indicators (SMA-50, SMA-200, RSI, MACD) for a given stock ticker."""
    try:
        ticker = ticker.replace('$', '').strip().upper()
        stock = yf.Ticker(ticker)
        # Fetch 1 year of data to ensure enough history for 200-day SMA
        df = stock.history(period="1y")
        
        if df.empty or len(df) < 200:
            return f"Not enough historical data to calculate technicals for {ticker}. Need at least 200 days."

        # Calculate Simple Moving Averages (SMA)
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()

        # Calculate RSI (14-day)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['RSI_14'] = 100 - (100 / (1 + rs))

        # Calculate MACD (12-day EMA - 26-day EMA)
        ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema_12 - ema_26
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        # Get latest day values
        latest = df.iloc[-1]
        
        output = [
            f"Technical Analysis for {ticker} (as of {df.index[-1].strftime('%Y-%m-%d')}):",
            f"- Current Price: ${latest['Close']:.2f}",
            f"- 50-Day SMA: ${latest['SMA_50']:.2f}",
            f"- 200-Day SMA: ${latest['SMA_200']:.2f}",
            f"- 14-Day RSI: {latest['RSI_14']:.2f} (Overbought >70, Oversold <30)",
            f"- MACD: {latest['MACD']:.2f}",
            f"- MACD Signal: {latest['MACD_Signal']:.2f}",
            ""
        ]
        
        # Add basic momentum interpretation
        if latest['SMA_50'] > latest['SMA_200']:
            output.append("Trend: BULLISH (50-Day SMA is above 200-Day SMA)")
        else:
            output.append("Trend: BEARISH (50-Day SMA is below 200-Day SMA)")
            
        if latest['RSI_14'] > 70:
            output.append("Momentum: OVERBOUGHT (RSI > 70)")
        elif latest['RSI_14'] < 30:
            output.append("Momentum: OVERSOLD (RSI < 30)")
        else:
            output.append("Momentum: NEUTRAL (RSI between 30 and 70)")

        return "\n".join(output)
    except Exception as e:
        return f"Error calculating technical indicators for {ticker}: {e}"
