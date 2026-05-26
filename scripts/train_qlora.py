import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import LoraConfig, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.2" # Excellent base model for logic and reasoning
DATASET_PATH = "training_data.jsonl"
OUTPUT_DIR = "./fin_model_lora"

def train():
    print(f"Loading {MODEL_ID} in 4-bit precision via QLoRA...")
    
    # 1. Load Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 2. Configure 4-bit Quantization to fit 7B model on a single 16GB GPU (like Google Colab T4)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float32,
        bnb_4bit_use_double_quant=True,
    )

    # 3. Load the Model
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
    )
    
    # Prepare model for gradient checkpointing and parameter efficient fine-tuning
    model = prepare_model_for_kbit_training(model)

    # 4. LoRA Adapter Configuration (The "brain" we are actually training)
    peft_config = LoraConfig(
        lora_alpha=16,
        lora_dropout=0.1,
        r=64,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    )

    # 5. Load our Custom Financial Dataset
    print(f"Loading custom database interactions from {DATASET_PATH}...")
    dataset = load_dataset("json", data_files=DATASET_PATH, split="train")
    
    # Apply ChatML formatting
    def format_chatml(example):
        text = tokenizer.apply_chat_template(example["messages"], tokenize=False, add_generation_prompt=False)
        return {"text": text}
        
    dataset = dataset.map(format_chatml)

    # 6. Setup Training Loop
    training_args = SFTConfig(
        output_dir=OUTPUT_DIR,
        dataset_text_field="text",
        max_length=2048,
        packing=False,
        num_train_epochs=3,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        optim="paged_adamw_32bit",
        save_steps=50,
        logging_steps=10,
        learning_rate=2e-4,
        weight_decay=0.001,
        fp16=False,
        bf16=False,
        max_grad_norm=0.3,
        max_steps=-1,
        warmup_steps=10,
        group_by_length=True,
        lr_scheduler_type="cosine",
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        processing_class=tokenizer,
        args=training_args,
    )

    # 7. Start Fine-Tuning!
    print("Initiating HuggingFace SFTTrainer Loop...")
    trainer.train()

    # 8. Save the Adapter Weights
    print(f"Training complete! Saving LoRA adapter to {OUTPUT_DIR}")
    trainer.model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

if __name__ == "__main__":
    train()
