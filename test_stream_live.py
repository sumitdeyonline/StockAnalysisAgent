import sys
import os
from agent import setup_agent
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()
agent = setup_agent()
msg = HumanMessage(content="What is AAPL's price?")

print("STARTING STREAM:")
try:
    for chunk, metadata in agent.stream({"messages": [msg]}, stream_mode="messages"):
        print(f"NODE: {metadata.get('langgraph_node')}, TYPE: {type(chunk).__name__}, CONTENT: {repr(chunk.content)[:50]}")
except Exception as e:
    print(f"Error: {e}")
print("DONE")
