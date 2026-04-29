import os
import json
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

# Load environment variables to securely connect to the DB
load_dotenv()

SYSTEM_PROMPT = "You are a highly specialized financial AI assistant. You analyze stock market data, interpret technical indicators, and provide detailed, professional investment summaries without hallucinating."

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise Exception("DATABASE_URL missing. Check your .env file.")
    return psycopg2.connect(db_url)

def export_dataset(output_file="training_data.jsonl"):
    """
    Connects to the PostgreSQL database, extracts historical user queries, 
    agent responses, and specialized knowledge, and formats them into a ChatML JSONL dataset.
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    dataset = []

    try:
        # 1. Extract Interaction History (Instruction Tuning)
        print("Extracting Search History...")
        cur.execute("SELECT query, response FROM search_history WHERE query IS NOT NULL AND response IS NOT NULL")
        interactions = cur.fetchall()
        for row in interactions:
            query = row['query'].strip()
            response = row['response'].strip()
            
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
        cur.execute("SELECT topic, content FROM agent_knowledge WHERE topic IS NOT NULL AND content IS NOT NULL")
        knowledge_rows = cur.fetchall()
        for row in knowledge_rows:
            topic = row['topic'].strip()
            content = row['content'].strip()
            
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
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    export_dataset()
