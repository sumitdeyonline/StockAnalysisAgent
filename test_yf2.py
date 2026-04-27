import yfinance as yf

try:
    s = yf.screener.screen(yf.screener.PREDEFINED_SCREENER_QUERIES['day_gainers']['query'])
    print(s)
except Exception as e:
    print(e)
