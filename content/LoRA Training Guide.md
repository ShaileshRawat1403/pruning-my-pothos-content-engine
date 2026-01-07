# LoRA Training Guide (Concise)

## What this covers
- What LoRA is and when to use it
- Minimal, GPU-light pipeline for text generation models
- Data prep rules that avoid overfitting and junk outputs

## When LoRA makes sense
- You want to adapt a base model’s tone or domain without full fine-tuning.
- You have <10k training pairs and a single prosumer GPU (or Colab).
- You need a reversible, small adapter instead of a new checkpoint.

## Prerequisites
- Base model pulled locally (e.g., `llama-3` family) and a LoRA-capable trainer (PEFT, TRL).
- 4–12 GB VRAM for small adapters; mixed precision (fp16/bf16) enabled.
- Clean instruction/output pairs in JSONL: `{"instruction": "...", "output": "..."}`.

## Data prep (golden rules)
- 1 task per record; keep outputs concise and specific.
- Strip disclaimers, “As an AI...” boilerplate, and long rambling sentences.
- Keep sentences short (≤28 words); prefer bullet structure in outputs when applicable.
- Balance examples across personas/tones to avoid collapse.
- Deduplicate near-identical records; remove URLs that aren’t needed as text.

## Training recipe (PEFT/TRL sketch)
1) Tokenize with the base model tokenizer; cap sequence length to the model’s context (e.g., 4k).
2) Use LoRA rank 16–64; alpha 16–64; dropout 0.05 as a safe default.
3) Optimizer: AdamW; lr 1e-4 to 2e-4; weight decay 0.01; batch size 4–16 (with grad accumulation).
4) Train 1–3 epochs; watch validation loss to stop early. Overfitting shows up as verbatim copying.
5) Merge and export adapter weights; test via generation prompts that mirror your production tasks.

## Eval checklist
- Fluency: no broken sentences or hallucinated scaffolding.
- Faithfulness: matches provided facts and style guide.
- Length control: respects desired output length bands (short/medium/long).
- Safety: no PII leakage, no policy violations.

## Inference tips
- Start with temperature 0.2–0.4; top_p 0.9; top_k 40.
- If outputs drift to base-model voice, lower temperature or increase LoRA alpha during training.
- Keep adapters versioned; document base model, rank, alpha, epochs, and dataset hash.

## References
- PEFT: https://github.com/huggingface/peft
- TRL: https://github.com/huggingface/trl
- LoRA paper: https://arxiv.org/abs/2106.09685
