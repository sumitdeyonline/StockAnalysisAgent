import sys
from tools.finance import get_market_movers
import pprint

movers = get_market_movers()
pprint.pprint(movers)
