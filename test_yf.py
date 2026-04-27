import yfinance as yf

print("Testing Screeners...")
try:
    print("Gainers:")
    print(yf.Sector('msft')) # just testing random things if screeners aren't exposed directly
except Exception as e:
    print(e)
