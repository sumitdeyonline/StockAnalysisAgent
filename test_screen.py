import yfinance as yf

print("Screener testing...")
try:
    s = yf.Screen()
    s.set_predefined_screener('day_gainers')
    resp = s.calculate()
    print(resp.keys())
    print(resp['quotes'][0]['symbol'])
except Exception as e:
    print(e)
    try:
        data = yf.screener.get_predefined_screener('day_gainers')
        print(data)
    except Exception as e2:
        print(f"Error 2: {e2}")
