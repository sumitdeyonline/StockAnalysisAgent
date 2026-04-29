# Agentic Financial Model Fine-Tuning Guide (QLoRA Architecture)

This document provides a comprehensive technical overview of the architecture, data extraction pipeline, and execution strategy for fine-tuning a foundational HuggingFace model using your PostgreSQL agent knowledge base.

---

## 1. System Architecture
We utilize **Parameter-Efficient Fine-Tuning (PEFT)** combined with **QLoRA (Quantized Low-Rank Adaptation)**. 

### Why QLoRA?
Training a 7 Billion parameter model (like Mistral-7B or Llama-3-8B) in full precision (FP32) requires over 100GB of VRAM, which costs thousands of dollars in cloud compute. 
QLoRA radically compresses this requirement:
1. **4-Bit Quantization**: The foundational model is loaded in `NF4` (NormalFloat4) precision using the `bitsandbytes` library. This shrinks the model's footprint from 28GB to roughly 5GB, allowing it to easily fit on a standard 16GB Nvidia T4 GPU (free on Google Colab).
2. **LoRA Adapters**: Instead of modifying the billions of base weights, we freeze them completely. We inject a tiny, trainable "Adapter" network (usually ~1% of the model's size) consisting of low-rank matrices into the attention layers (`q_proj`, `v_proj`). During training, *only* these tiny adapters learn your financial behavior.

---

## 2. Dataset Extraction Pipeline
Before training, the model needs high-quality examples. We built `scripts/export_dataset.py` to handle this.

### Process
1. **Database Connection**: The script connects to your production PostgreSQL database (`DATABASE_URL`).
2. **Extraction**: It pulls rows from `search_history` (raw queries and agent responses) and `agent_knowledge` (expert topic summaries).
3. **Cleaning**: It aggressively filters out short responses, network errors, and hallucinated failures.
4. **ChatML Formatting**: It maps the data into a strict JSONL format required by the HuggingFace `SFTTrainer`.

**Format Example (`training_data.jsonl`)**:
```json
{
  "messages": [
    {"role": "system", "content": "You are a highly specialized financial AI assistant..."},
    {"role": "user", "content": "Analyze NVDA stock over the last 30 days."},
    {"role": "assistant", "content": "Based on the technicals, NVDA has shown strong MACD divergence..."}
  ]
}
```

---

## 3. Step-by-Step Training Execution
Because training strictly requires Nvidia GPU acceleration (CUDA), you cannot run this on your local Mac. You must execute this on **Google Colab**, **RunPod**, or **Google Cloud Vertex AI**.

### Step 1: Environment Setup
Spin up a cloud Jupyter Notebook with an **Nvidia T4, L4, or A100 GPU**. Upload both `training_data.jsonl` and `scripts/train_qlora.py` to the cloud server.

### Step 2: Install HuggingFace Toolchain
Run the following bash command in the cloud environment to install the PyTorch ML stack:
```bash
pip install torch transformers datasets peft trl bitsandbytes accelerate
```

### Step 3: Execute the Training Engine
Run the training script:
```bash
python train_qlora.py
```
**What happens under the hood?**
- `AutoModelForCausalLM` downloads the `Mistral-7B-Instruct-v0.2` base weights from HuggingFace.
- `BitsAndBytesConfig` instantly crushes the weights into 4-bit precision.
- `LoraConfig` attaches the trainable matrices to the attention heads.
- `SFTTrainer` (Supervised Fine-Tuning Trainer) feeds your `training_data.jsonl` into the model in batches, calculating the loss and updating the LoRA weights using the `paged_adamw_32bit` optimizer.

---

## 4. Saving the Model
Once `train_qlora.py` finishes (usually 1-3 hours depending on dataset size), it executes:
```python
trainer.model.save_pretrained("./fin_model_lora")
tokenizer.save_pretrained("./fin_model_lora")
```
This generates a folder (`fin_model_lora`) containing the **Adapter Weights** (`adapter_model.safetensors` or `adapter_model.bin`). 

**Note**: This folder does *not* contain the massive 7B base model—it only contains the ~200MB "brain upgrade" that learned your specific financial data. You must download this folder back to your local machine!

---

## 5. How to Use the Trained Model (Integration)
To replace the paid Anthropic/Claude API with your custom model, we will use **Ollama** or **vLLM** to serve the model locally.

### Step 1: Merging (Optional but Recommended)
To run the model easily in Ollama, you merge your tiny adapter weights back into the massive Mistral base model. You can do this in Python:
```python
from peft import AutoPeftModelForCausalLM
model = AutoPeftModelForCausalLM.from_pretrained("./fin_model_lora")
merged_model = model.merge_and_unload()
merged_model.save_pretrained("./final_financial_model")
```

### Step 2: Convert to GGUF
Using the `llama.cpp` toolkit, convert the `./final_financial_model` into a `.gguf` file.

### Step 3: Run via Ollama
Create an Ollama `Modelfile`:
```dockerfile
FROM ./final_financial_model.gguf
SYSTEM "You are a highly specialized financial AI assistant..."
```
Run it: `ollama create FinModel -f Modelfile`

### Step 4: Hook into LangGraph
Finally, update your `agent.py` to point to your new local endpoint!
```python
# Old implementation:
# from langchain_anthropic import ChatAnthropic
# llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")

# New custom implementation!
from langchain_community.chat_models import ChatOllama
llm = ChatOllama(model="FinModel", temperature=0.2)
```
Your Streamlit application will now route all traffic, tool executions, and analytical reasoning through your completely free, custom-trained financial model!
