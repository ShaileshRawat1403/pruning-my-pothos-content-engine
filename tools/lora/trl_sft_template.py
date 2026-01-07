#!/usr/bin/env python3
"""
Template TRL SFT training script for LoRA style tuning.
Run in a separate GPU environment. Adjust paths/models as needed.
"""
from dataclasses import dataclass
from typing import Dict
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, SFTConfig
import torch


@dataclass
class Paths:
    dataset_path: str = "data/lora/sections.jsonl"  # or posts.jsonl
    base_model: str = "mistralai/Mistral-7B-Instruct-v0.2"
    output_dir: str = "outputs/lora-mistral-sections"


def load_jsonl_dataset(path: str):
    return load_dataset("json", data_files=path, split="train")


def main():
    P = Paths()
    ds = load_jsonl_dataset(P.dataset_path)

    tok = AutoTokenizer.from_pretrained(P.base_model, use_fast=True)
    tok.padding_side = "right"
    tok.pad_token = tok.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        P.base_model,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
    )

    lcfg = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lcfg)

    cfg = SFTConfig(
        output_dir=P.output_dir,
        num_train_epochs=3,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=32,  # effective batch 32
        learning_rate=2e-4,
        logging_steps=20,
        save_steps=500,
        eval_strategy="no",
        max_seq_length=4096,
        packing=False,
    )

    def format_example(ex: Dict):
        # Simple instruction-following format
        return f"Instruction:\n{ex['instruction']}\n\nOutput:\n{ex['output']}"

    trainer = SFTTrainer(
        model=model,
        tokenizer=tok,
        train_dataset=ds,
        formatting_func=lambda batch: [format_example(ex) for ex in batch],
        args=cfg,
    )
    trainer.train()
    trainer.model.save_pretrained(P.output_dir)
    trainer.tokenizer.save_pretrained(P.output_dir)


if __name__ == "__main__":
    main()
