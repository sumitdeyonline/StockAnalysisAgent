import chromadb
from langchain_core.tools import tool

# Initialize ChromaDB client (local persistent storage)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="stock_research")

@tool
def store_in_vector_db(text: str, source: str, document_id: str) -> str:
    """
    Store long research reports or detailed news articles into the vector database.
    This allows semantic retrieval of relevant text later.
    """
    try:
        collection.add(
            documents=[text],
            metadatas=[{"source": source}],
            ids=[document_id]
        )
        return f"Successfully stored document '{document_id}' into ChromaDB."
    except Exception as e:
        return f"Error storing to vector DB: {e}"

@tool
def search_vector_db(query: str, n_results: int = 3) -> str:
    """
    Semantically search the vector database for previously stored research or news using a query.
    Useful when you need context about a topic that might be too large for the immediate context window.
    """
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        if not results['documents'] or not results['documents'][0]:
            return f"No relevant documents found for query: {query}"
            
        formatted_results = []
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            formatted_results.append(f"Source: {meta.get('source', 'Unknown')}\nSnippet:\n{doc}\n")
            
        return "\n---\n".join(formatted_results)
    except Exception as e:
        return f"Error searching vector DB: {e}"
