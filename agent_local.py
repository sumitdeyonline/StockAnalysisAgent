import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from peft import PeftModel
from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate

from tools.finance import (
    get_stock_price, 
    get_stock_historical_data, 
    get_company_news,
    get_stock_fundamentals,
    get_technical_indicators
)

MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.2"
ADAPTER_PATH = "scripts/fin_model_lora"

_local_llm = None

def get_local_llm():
    global _local_llm
    if _local_llm is not None:
        return _local_llm

    print(f"Loading local base model {MODEL_ID} on Mac...")
    
    # Check if MPS (Metal Performance Shaders) is available for Apple Silicon
    if torch.backends.mps.is_available():
        device = "mps"
    elif torch.cuda.is_available():
        device = "cuda"
    else:
        device = "cpu"
        
    print(f"Using device: {device}")

    # Load base model
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        device_map=device,
        torch_dtype=torch.float16,
    )
    
    print(f"Applying QLoRA adapter from {ADAPTER_PATH}...")
    model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    
    print("Initializing HuggingFace Pipeline for LangGraph...")
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=512,
        temperature=0.1,
        return_full_text=False
    )
    
    hf = HuggingFacePipeline(pipeline=pipe)
    _local_llm = ChatHuggingFace(llm=hf)
    return _local_llm

def is_financial_query(query: str) -> bool:
    """Explicitly protect the system by bouncing generic chat payloads using a cheap classifier boundary."""
    try:
        llm = get_local_llm()
        prompt = PromptTemplate.from_template(
            "You are a strict query classifier. Does the following user query explicitly ask about stocks, trading, financial markets, investing, companies, business news, or political news that could affect the economy/markets? Respond with exactly one word: 'YES' or 'NO'.\n\nQuery: {query}"
        )
        chain = prompt | llm
        response = chain.invoke({"query": query})
        return "yes" in response.content.lower()
    except Exception as e:
        print(f"Guardrail failed: {e}")
        # If the guardrail itself fails (API error), default to allowing it through to avoid app crashing
        return True

def setup_agent():
    llm = get_local_llm()
    
    tools = [
        get_stock_price,
        get_stock_historical_data,
        get_company_news,
        get_stock_fundamentals,
        get_technical_indicators,
        web_search_tavily,
        save_analysis_to_db,
        get_past_analyses,
        store_in_vector_db,
        search_vector_db
    ]
    
    # Define the powerful system prompt that guides the AI's behavior
    SYSTEM_PROMPT = """You are an elite financial advisor, quantitative analyst, and stock market AI.
Your primary directive is to provide highly accurate, data-driven stock predictions and recommendations. 

CRITICAL INSTRUCTIONS:
1. When asked for stock recommendations (e.g., short-term 7-15 days, or long-term), you MUST use your tools to research both Quantitative and Qualitative data.
2. For short-term predictions (momentum), you MUST use `get_technical_indicators` to analyze RSI and MACD, and `web_search_tavily` for immediate political/market news catalysts.
3. For long-term predictions (value), you MUST use `get_stock_fundamentals` to analyze P/E, EPS, Debt, and Free Cash Flow, along with broad macroeconomic news.
4. Synthesize all political, financial, and technical data to justify your stock picks with mathematical backing.
5. STRICT GUARDRAIL: You must absolutely refuse to answer any query that is not related to finance, stocks, investing, business, or economic/political market impacts. If a user asks a general knowledge, coding, or unrelated question, politely decline and state you are strictly a financial AI."""

    # Construct the LangGraph React Agent with our toolset and system prompt
    agent_executor = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)
    return agent_executor
