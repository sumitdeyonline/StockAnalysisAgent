from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.tools import tool
import json

@tool
def dummy_tool(x: str) -> str:
    """A dummy tool."""
    return "Dummy response"

# Create a fake model that returns a streamable response
fake = FakeMessagesListChatModel(responses=[HumanMessage(content="This is a streamed fake response.")])
agent = create_react_agent(fake, [dummy_tool])

for chunk, metadata in agent.stream({"messages": [HumanMessage(content="hi")]}, stream_mode="messages"):
    print(f"CHUNK: {chunk.content}, METADATA: {metadata}")
