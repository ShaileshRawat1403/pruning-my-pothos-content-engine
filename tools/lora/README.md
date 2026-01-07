LoRA Style Adapter – Quick Guide
================================

Goal: train a small LoRA adapter to enforce your house style and structure, then run it via Ollama.

1) Build the dataset
- From repo root:
```
python tools/lora/build_dataset.py
```
Outputs:
- `data/lora/sections.jsonl` (preferred for stable section style)
- `data/lora/posts.jsonl` (full posts)

2) Train (GPU recommended)
- Create a new venv elsewhere and install: `pip install transformers peft datasets accelerate bitsandbytes trl`.
- Use TRL `SFTTrainer` with QLoRA. See `tools/lora/trl_sft_template.py` for a working starter.

Settings that work well:
- Base model: `mistralai/Mistral-7B-Instruct-v0.2` or `meta-llama/Meta-Llama-3-8B-Instruct`
- LoRA: r=16, alpha=32, dropout=0.05
- 4-bit quantization (bnb), seq_len 4096, effective batch 64 (via grad accumulation)
- 2–4 epochs to start

3) Export and serve via Ollama
- Option A (merge): merge LoRA → FP16, convert to GGUF (llama.cpp), quantize (Q4_K_M), then create an Ollama Modelfile.
- Option B (adapter): if your Ollama supports adapters, point the Modelfile to the base GGUF + LoRA adapter.

See `tools/lora/Modelfile.template` for a template Modelfile.

4) Use in this engine
- Set in `.env`: `GEN_MODEL=<your-model-name>`, `GEN_TEMPERATURE=0.0`, `GEN_SEED=42`.
- Run: `make run-local brief=...`

Notes
- Keep a small holdout set to verify improvements.
- The dataset builder removes meta artifacts and weird blocks automatically.
- Do not check your trained weights into this repo.

