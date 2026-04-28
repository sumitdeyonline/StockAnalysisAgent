import sys
import os
from agent import setup_agent
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()
agent = setup_agent()
msg = HumanMessage(content="What is AAPL's price?")

print("STARTING STREAM:")
for chunk, metadata in agent.stream({"messages": [msg]}, stream_mode="messages"):
    if metadata.get("langgraph_node") == "agent":
        if isinstance(chunk.content, str) and chunk.content:
            print(f"STRING YIELD: {chunk.content}")
        elif isinstance(chunk.content, list):
            for block in chunk.content:
                if isinstance(block, dict) and block.get("type") == "text":
                    print(f"TEXT BLOCK: {block.get('text', '')}", end="")
print("\nDONE")
