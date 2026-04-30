import requests
from dotenv import load_dotenv
load_dotenv()
from tools.db_tools import get_supabase_headers

url, headers = get_supabase_headers()
update_url = f"{url}/rest/v1/search_history?email=eq.sumitdey@yahoo.com&id=eq.21"
payload = {"response": "TESTING"}
res = requests.patch(update_url, headers=headers, json=payload)
print(res.status_code, res.text)
