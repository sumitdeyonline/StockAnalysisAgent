import os
import datetime
import psycopg2
from psycopg2.extras import DictCursor
from langchain_core.tools import tool

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise Exception("DATABASE_URL environment variable is not set.")
    return psycopg2.connect(db_url)

# Setup function to create the table if it's missing
def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_knowledge (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                topic VARCHAR(255),
                content TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                email VARCHAR(255),
                query TEXT,
                response TEXT
            )
        """)
        # Make sure the email column exists if the table was created previously
        # try:
        #     cur.execute("ALTER TABLE search_history ADD COLUMN email VARCHAR(255);")
        # except psycopg2.Error:
        #     conn.rollback() # It already exists
        # else:
        #     conn.commit()

        # # Add response column for caching AI results
        # try:
        #     cur.execute("ALTER TABLE search_history ADD COLUMN response TEXT;")
        # except psycopg2.Error:
        #     conn.rollback() # It already exists
        # else:
        #     conn.commit()
            
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"PostgreSQL init error (ensure DB is running and URL is correct): {e}")

@tool
def save_analysis_to_db(topic: str, content: str) -> str:
    """
    Saves a summary or key finding of an analysis to the PostgreSQL database for future reference.
    Useful when saving long term knowledge or tracking conclusions.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO agent_knowledge (topic, content) VALUES (%s, %s)",
            (topic, content)
        )
        conn.commit()
        cur.close()
        conn.close()
        return f"Successfully saved analysis on '{topic}' to the database."
    except Exception as e:
        return f"Failed to save to database: {e}"

@tool
def get_past_analyses(topic: str, limit: int = 5) -> str:
    """
    Retrieves past analyses or knowledge stored in the PostgreSQL database matching a specific topic.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        search_topic = f"%{topic}%"
        cur.execute(
            "SELECT timestamp, topic, content FROM agent_knowledge WHERE topic ILIKE %s ORDER BY timestamp DESC LIMIT %s",
            (search_topic, limit)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        if not rows:
            return f"No past analyses found in the database for topic: {topic}"
            
        result_lines = []
        for row in rows:
            result_lines.append(f"[{row['timestamp']}] Topic: {row['topic']}\nContent: {row['content']}")
            
        return "\n\n---\n\n".join(result_lines)
    except Exception as e:
        return f"Failed to retrieve from database: {e}"

def save_search_query(email: str, query: str, response: str):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO search_history (email, query, response) VALUES (%s, %s, %s)", (email, query, response))
        
        # Enforce maximum 15 search history limit per email
        cur.execute("""
            DELETE FROM search_history 
            WHERE id IN (
                SELECT id FROM search_history 
                WHERE email = %s 
                ORDER BY timestamp DESC 
                OFFSET 15
            )
        """, (email,))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Failed to save search query: {e}")

def get_recent_searches(email: str, limit: int = 15):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute("SELECT id, query, response FROM search_history WHERE email = %s ORDER BY timestamp DESC LIMIT %s", (email, limit))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [{"id": row['id'], "query": row['query'], "response": row.get('response')} for row in rows]
    except Exception as e:
        print(f"Failed to retrieve recent searches: {e}")
        return []

def delete_search_history(email: str):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM search_history WHERE email = %s", (email,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Failed to delete search history: {e}")

def delete_single_search(email: str, search_id: int):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM search_history WHERE email = %s AND id = %s", (email, search_id))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Failed to delete single search: {e}")

def update_search_response(email: str, search_id: int, new_response: str):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE search_history SET response = %s WHERE id = %s AND email = %s", (new_response, search_id, email))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Failed to update search response: {e}")
