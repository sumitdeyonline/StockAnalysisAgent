import os
import requests
from langchain_core.tools import tool

def get_supabase_headers():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise Exception("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing from .env")
    return url, {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

def init_db():
    print("Database tables are now managed externally via Supabase Dashboard.")

@tool
def save_analysis_to_db(topic: str, content: str) -> str:
    """
    Saves a summary or key finding of an analysis to the Supabase database for future reference.
    Useful when saving long term knowledge or tracking conclusions.
    """
    try:
        url, headers = get_supabase_headers()
        payload = {"topic": topic, "content": content}
        res = requests.post(f"{url}/rest/v1/agent_knowledge", headers=headers, json=payload)
        res.raise_for_status()
        return f"Successfully saved analysis on '{topic}' to the database."
    except Exception as e:
        return f"Failed to save to database: {e}"

@tool
def get_past_analyses(topic: str, limit: int = 5) -> str:
    """
    Retrieves past analyses or knowledge stored in the Supabase database matching a specific topic.
    """
    try:
        url, headers = get_supabase_headers()
        search_topic = f"%{topic}%"
        query_url = f"{url}/rest/v1/agent_knowledge?topic=ilike.{search_topic}&select=timestamp,topic,content&order=timestamp.desc&limit={limit}"
        res = requests.get(query_url, headers=headers)
        res.raise_for_status()
        
        rows = res.json()
        if not rows:
            return f"No past analyses found in the database for topic: {topic}"
            
        result_lines = []
        for row in rows:
            result_lines.append(f"[{row['timestamp']}] Topic: {row['topic']}\nContent: {row['content']}")
            
        return "\n\n---\n\n".join(result_lines)
    except Exception as e:
        return f"Failed to retrieve from database: {e}"

def save_search_query(email: str, query: str, response_text: str) -> int:
    try:
        url, headers = get_supabase_headers()
        
        # Prefer: return=representation ensures the API returns the inserted row (including its auto-generated ID)
        post_headers = {**headers, "Prefer": "return=representation"}
        payload = {"email": email, "query": query, "response": response_text}
        
        insert_res = requests.post(f"{url}/rest/v1/search_history", headers=post_headers, json=payload)
        insert_res.raise_for_status()
        
        inserted_data = insert_res.json()
        if not inserted_data:
            raise Exception("No data returned from insert.")
            
        new_id = inserted_data[0]['id']
        
        # Enforce maximum 15 search history limit per email
        history_url = f"{url}/rest/v1/search_history?email=eq.{email}&select=id&order=timestamp.desc"
        history_res = requests.get(history_url, headers=headers)
        history_res.raise_for_status()
            
        history_ids = [row['id'] for row in history_res.json()]
        if len(history_ids) > 15:
            ids_to_delete = history_ids[15:]
            delete_url = f"{url}/rest/v1/search_history?id=in.({','.join(map(str, ids_to_delete))})"
            requests.delete(delete_url, headers=headers)
            
        return new_id
    except Exception as e:
        print(f"Failed to save search query: {e}")
        return None

def get_recent_searches(email: str, limit: int = 15):
    try:
        url, headers = get_supabase_headers()
        query_url = f"{url}/rest/v1/search_history?email=eq.{email}&select=id,query,response&order=timestamp.desc&limit={limit}"
        res = requests.get(query_url, headers=headers)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"Failed to retrieve recent searches: {e}")
        return []

def delete_search_history(email: str):
    try:
        url, headers = get_supabase_headers()
        delete_url = f"{url}/rest/v1/search_history?email=eq.{email}"
        requests.delete(delete_url, headers=headers)
    except Exception as e:
        print(f"Failed to delete search history: {e}")

def delete_single_search(email: str, search_id: int):
    try:
        url, headers = get_supabase_headers()
        delete_url = f"{url}/rest/v1/search_history?email=eq.{email}&id=eq.{search_id}"
        requests.delete(delete_url, headers=headers)
    except Exception as e:
        print(f"Failed to delete single search: {e}")

def update_search_response(email: str, search_id: int, new_response: str):
    try:
        url, headers = get_supabase_headers()
        update_url = f"{url}/rest/v1/search_history?email=eq.{email}&id=eq.{search_id}"
        payload = {"response": new_response}
        requests.patch(update_url, headers=headers, json=payload)
    except Exception as e:
        print(f"Failed to update search response: {e}")
