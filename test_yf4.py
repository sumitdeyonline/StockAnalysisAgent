import yfinance as yf
s = yf.screener.screen(yf.screener.PREDEFINED_SCREENER_QUERIES['day_gainers']['query'])
print(s.keys())
print(s['quotes'][0]['symbol'])
