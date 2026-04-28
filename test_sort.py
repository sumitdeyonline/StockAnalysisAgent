import yfinance as yf
s = yf.screener.screen(yf.screener.PREDEFINED_SCREENER_QUERIES['day_gainers']['query'])
quotes = s.get('quotes', [])
print("Alpha slice 5:", [q['symbol'] for q in quotes[:5]])

# Sort manually by percent change
sorted_quotes = sorted(quotes, key=lambda x: x.get('regularMarketChangePercent', 0), reverse=True)
print("Sorted slice 5:", [q['symbol'] for q in sorted_quotes[:5]])
print("Sorted changes:", [q['regularMarketChangePercent'] for q in sorted_quotes[:5]])
