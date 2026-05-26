import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables to securely connect to the DB
load_dotenv()

SYSTEM_PROMPT = "You are a highly specialized financial AI assistant. You analyze stock market data, interpret technical indicators, and provide detailed, professional investment summaries without hallucinating."

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

def export_dataset(output_file="training_data.jsonl"):
    """
    Connects to the Supabase REST API, extracts historical user queries, 
    agent responses, and specialized knowledge, and formats them into a ChatML JSONL dataset.
    """
    url, headers = get_supabase_headers()
    dataset = []

    try:
        # 1. Extract Interaction History (Instruction Tuning)
        print("Extracting Search History...")
        interactions_res = requests.get(f"{url}/rest/v1/search_history?select=query,response", headers=headers)
        interactions_res.raise_for_status()
        interactions = interactions_res.json()
        
        for row in interactions:
            query = row.get('query', '')
            response = row.get('response', '')
            
            if not query or not response:
                continue
                
            query = query.strip()
            response = response.strip()
            
            # Discard broken or errored responses
            if len(response) < 20 or "Agent stream interrupted" in response or "Failed" in response:
                continue
                
            example = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                    {"role": "assistant", "content": response}
                ]
            }
            dataset.append(example)

        # 2. Extract Agent Knowledge (Domain Adaptation)
        print("Extracting Agent Knowledge Base...")
        knowledge_res = requests.get(f"{url}/rest/v1/agent_knowledge?select=topic,content", headers=headers)
        knowledge_res.raise_for_status()
        knowledge_rows = knowledge_res.json()
        
        for row in knowledge_rows:
            topic = row.get('topic', '')
            content = row.get('content', '')
            
            if not topic or not content:
                continue
                
            topic = topic.strip()
            content = content.strip()
            
            example = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Retrieve and summarize your deep knowledge regarding the following financial topic: {topic}"},
                    {"role": "assistant", "content": content}
                ]
            }
            dataset.append(example)

        # Write to JSONL
        with open(output_file, "w", encoding="utf-8") as f:
            for item in dataset:
                f.write(json.dumps(item) + "\n")

        print(f"Successfully exported {len(dataset)} perfectly formatted high-quality examples to {output_file}!")

    except Exception as e:
        print(f"Extraction failed: {e}")

if __name__ == "__main__":
    export_dataset()
