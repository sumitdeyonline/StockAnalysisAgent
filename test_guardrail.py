from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()

def is_financial_query(query: str) -> bool:
    try:
        # User's model
        llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0, max_tokens=10)
        prompt = PromptTemplate.from_template(
            "You are a strict query classifier. Does the following user query explicitly ask about stocks, trading, financial markets, investing, companies, or business news? Respond with exactly one word: 'YES' or 'NO'.\n\nQuery: {query}"
        )
        chain = prompt | llm
        response = chain.invoke({"query": query})
        print(f"Query: '{query}' -> Response: {response.content}")
        return "yes" in response.content.lower()
    except Exception as e:
        print(e)
        return True # Fallback

is_financial_query("What is the capital of France?")
is_financial_query("How is NVDA doing today?")
