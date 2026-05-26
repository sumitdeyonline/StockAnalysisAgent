import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
# 1. Load the original generic model
base_model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2",
    device_map="cpu", # Note: CPU will be extremely slow
    torch_dtype=torch.float16,
)
# 2. "Load" your saved model (this applies your safetensors weights!)
# This is the modern equivalent of `pickle.load()`
model = PeftModel.from_pretrained(base_model, "./scripts/fin_model_lora")
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
# 3. Use it to generate text
inputs = tokenizer("What is the current stock price of NVDA?", return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=50)
print(tokenizer.decode(outputs[0]))