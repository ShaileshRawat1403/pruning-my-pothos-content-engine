.PHONY: up up-engine up-ollama pull pull-model pull-local install index run logs stop clean reset-history clean-artifacts reset-vdb fresh-run venv install-local index-local run-local run-example run-example-local run-fast-local run-quality-local run-blog run-social run-all help repair ingest ingest-enrich ingest-yaml test-ollama ui lora-dataset ingest-url lint-artifact open-preview show-artifacts models qdrant-start-native qdrant-stop-native qdrant-status-native run-agentic-cms api

# Defaults
INGEST_URLS ?= sources/urls.txt
INGEST_YAML ?= sources/sources.yaml
MODEL ?= llama3.2:3b

QDRANT_NATIVE_BIN ?= $(HOME)/.local/bin/qdrant
QDRANT_NATIVE_CONFIG ?= $(HOME)/.config/qdrant/config.yaml
QDRANT_PID_FILE ?= artifacts/_runtime/qdrant.pid
QDRANT_LOG_FILE ?= artifacts/_runtime/qdrant.log

# Start both services (ollama + engine) — only needed if you want the bundled ollama
up:
	docker compose -f infra/docker-compose.yml up -d

# Start just the engine (recommended when using host Ollama on 11435)
up-engine:
	docker compose -f infra/docker-compose.yml up -d engine

up-ollama:
	docker compose -f infra/docker-compose.yml up -d ollama

up-qdrant:
	docker compose -f infra/docker-compose.yml up -d qdrant

check-qdrant:
	@echo "Checking Qdrant at http://localhost:6333...";
	@curl -s http://localhost:6333/readyz || true; echo;

# Hybrid dev helper: start Qdrant, index locally, run locally (skip publish)
dev-hybrid:
	$(MAKE) up-qdrant
	$(MAKE) check-qdrant
	$(MAKE) install-local
	$(MAKE) index-local
	SKIP_PUBLISH=1 .venv/bin/python -m engine.run $(brief)

# macOS convenience: open preview index for a slug
open-preview:
	open artifacts/$(slug)/index.html

# Pull LLMs into the bundled ollama container (optional; skip if using host Ollama)
pull:
	docker exec -it $$(docker ps -qf name=ollama) ollama pull llama3.2:3b || true
	docker exec -it $$(docker ps -qf name=ollama) ollama pull phi3:mini-128k || true
	docker exec -it $$(docker ps -qf name=ollama) ollama pull nomic-embed-text:latest || true

pull-model:
	docker exec -it $$(docker ps -qf name=ollama) ollama pull $(MODEL) || true

pull-local:
	ollama pull $(MODEL)

# Install Python deps inside the engine container
install:
	docker compose -f infra/docker-compose.yml exec engine pip install -r requirements.txt

# Build the index from content/*.md (Qdrant)
index:
	docker compose -f infra/docker-compose.yml exec engine python -m engine.rag.build_index

# Usage: make run brief=briefs/example.yaml
run:
	docker compose -f infra/docker-compose.yml exec \
		-e GEN_MODEL=$${GEN_MODEL} \
		engine python -m engine.run $(brief)

# Tail container logs
logs:
	docker compose -f infra/docker-compose.yml logs -f

# Stop all services
stop:
	docker compose -f infra/docker-compose.yml down

# Clean local artifacts
clean:
	rm -rf artifacts/*

# Remove only history used for duplicate detection
reset-history:
	rm -f artifacts/_history/embeddings.jsonl || true

# Clean artifacts, history, and snapshots
clean-artifacts:
	rm -rf artifacts/* snapshots/* || true

# Reset local vector DB (Chroma default)
reset-vdb:
	rm -rf engine/.chroma || true

# Fresh run: purge artifacts + history + vdb, rebuild index, then generate (skip publish)
fresh-run:
	$(MAKE) clean-artifacts reset-history reset-vdb
	.venv/bin/python -m engine.rag.build_index
	SKIP_PUBLISH=1 .venv/bin/python -m engine.run $(brief)

# --- Local (non-Docker) convenience targets ---

help:
	@echo "make venv               # Create .venv and install deps"
	@echo "make install-local      # Install deps into existing .venv"
	@echo "make index-local        # Build index locally (Qdrant)"
	@echo "make run-local brief=...# Run engine locally with a brief"
	@echo "make run-local-draft    # Run with SKIP_PUBLISH=1 (uses brief=...)"
	@echo "make regen-section brief=... section=H2  # Regenerate a single section deterministically"
	@echo "make prune-index sources=path1.md[,path2.md]  # Remove sources from vector index"
	@echo "make repair             # Wipe local DB + reinstall deps"
	@echo "make ingest             # Ingest URLs from sources/urls.txt"
	@echo "make ingest urls=FILE   # Ingest URLs from FILE"
	@echo "make ingest-enrich      # Ingest with LLM enrichment (summary/tags)"
	@echo "make ingest-yaml        # Ingest from sources/sources.yaml"
	@echo "make up-ollama          # Start only Ollama via Docker"
	@echo "make pull               # Pull default models in Docker Ollama"
	@echo "make pull-model MODEL=..# Pull a specific model in Docker Ollama"
	@echo "make pull-local MODEL=..# Pull a model with your local Ollama"
	@echo "make test-ollama        # Check Ollama API availability"
	@echo "make run-example        # Run example brief (Docker)"
	@echo "make run-example-local  # Run example brief (local)"
	@echo "make run-example-dry    # Run example brief (skip publish)"
	@echo "make show-artifacts slug=<slug>  # List + preview artifacts for a slug"
	@echo "make lora-dataset          # Build LoRA SFT dataset from artifacts"
	@echo "make ui                    # Launch the new React Admin UI"
	@echo "make api                 # Launch FastAPI backend"
	@echo "make ingest-url url=...  # Ingest a single URL and re-index"
	@echo "make lint-artifact slug=.. [allow=domain1,domain2] [no_external=1] # Lint governance on an artifact"
	@echo "make run-local-lowmem   # Local run with strict low-memory caps"
	@echo "make run-local-small    # Local run with small model (phi3:mini-128k)"
	@echo "make run-blog brief=... # Generate blog/html only (uses OUTPUTS override)"
	@echo "make run-social brief=...# Generate LinkedIn + Instagram only"
	@echo "make run-all brief=...  # Generate blog + social + GitHub Doc"
	@echo "make qdrant-start-native [QDRANT_NATIVE_BIN=...] # Start local qdrant in background"
	@echo "make qdrant-status-native   # Check local qdrant process"
	@echo "make qdrant-stop-native    # Stop local qdrant process"
	@echo "make batch-previews       # Clean index, run both briefs, open previews"

venv:
	python3 -m venv .venv && .venv/bin/pip install -U pip && .venv/bin/pip install -r requirements.txt

install-local:
	.venv/bin/pip install -r requirements.txt

index-local:
	.venv/bin/python -m engine.rag.build_index

run-local:
	.venv/bin/python -m engine.run $(brief)

# Convenience: local run skipping publish
run-local-draft:
	SKIP_PUBLISH=1 .venv/bin/python -m engine.run $(brief)

# Convenience: run agentic CMS brief locally with publish disabled
run-agentic-cms:
	SKIP_PUBLISH=1 .venv/bin/python -m engine.run briefs/agentic-cms.yaml

# Convenience: local low-memory run (clamps ctx/predict)
run-local-lowmem:
	GEN_MAX_CTX=768 GEN_MAX_PREDICT=300 .venv/bin/python -m engine.run $(brief)

# Convenience: local small-model run
run-local-small:
	GEN_MODEL=phi3:mini-128k .venv/bin/python -m engine.run $(brief)

run-blog:
	@test -n "$(brief)" || { echo "Provide brief=..."; exit 2; }
	OUTPUTS=blog SKIP_PUBLISH=$${SKIP_PUBLISH:-1} .venv/bin/python -m engine.run $(brief)

run-social:
	@test -n "$(brief)" || { echo "Provide brief=..."; exit 2; }
	OUTPUTS=linkedin,instagram SKIP_PUBLISH=$${SKIP_PUBLISH:-1} .venv/bin/python -m engine.run $(brief)

run-all:
	@test -n "$(brief)" || { echo "Provide brief=..."; exit 2; }
	OUTPUTS=blog,linkedin,instagram,github_doc SKIP_PUBLISH=$${SKIP_PUBLISH:-1} .venv/bin/python -m engine.run $(brief)

run-example:
	docker compose -f infra/docker-compose.yml exec engine \
		python -m engine.run briefs/example-multiplatform.yaml

run-example-local:
	.venv/bin/python -m engine.run briefs/example-multiplatform.yaml

# Convenience: choose model per run (local)
run-fast-local:
	GEN_MODEL=phi3:mini-128k .venv/bin/python -m engine.run $(brief)

run-quality-local:
	GEN_MODEL=llama3.2:3b .venv/bin/python -m engine.run $(brief)

# Dry run (skip publish)
run-dry:
	SKIP_PUBLISH=1 .venv/bin/python -m engine.run $(brief)

run-example-dry:
	SKIP_PUBLISH=1 .venv/bin/python -m engine.run briefs/example-multiplatform.yaml

# Remove specific sources from index (comma-separated list or single glob)
prune-index:
	@test -n "$(sources)" || { echo "Provide sources=content/..md[,content/..md] or a glob"; exit 2; }
	.venv/bin/python -m engine.rag.prune_sources $(sources)

# Deterministic single-section regeneration (requires brief and section)
regen-section:
	@test -n "$(brief)" || { echo "Provide brief=..."; exit 2; }
	@test -n "$(section)" || { echo "Provide section=... (e.g., Steps)"; exit 2; }
	GEN_ONLY_SECTION="$(section)" SKIP_PUBLISH=1 GEN_TEMPERATURE=0.0 GEN_SEED=42 .venv/bin/python -m engine.run $(brief)

# One command: clean index → generate two briefs → open previews (macOS)
batch-previews:
	$(MAKE) clean-artifacts reset-history reset-vdb
	.venv/bin/python -m engine.rag.build_index
	SKIP_PUBLISH=1 .venv/bin/python -m engine.run briefs/ai-content-governance-smbs-focused.yaml
	SKIP_PUBLISH=1 .venv/bin/python -m engine.run briefs/smbs-rag-starter.yaml
	open artifacts/ai-content-governance-smbs-focused/index.html || true
	open artifacts/smbs-rag-starter/index.html || true

repair:
	rm -rf artifacts/*
	.venv/bin/pip install -U pip
	.venv/bin/pip install -r requirements.txt

ingest:
	.venv/bin/python -m engine.ingest --urls $(or $(urls),$(INGEST_URLS))

ingest-enrich:
	.venv/bin/python -m engine.ingest --urls $(or $(urls),$(INGEST_URLS)) --enrich

ingest-yaml:
	.venv/bin/python -m engine.ingest --yaml $(or $(yaml),$(INGEST_YAML))

test-ollama:
	@echo "Checking Ollama at $${OLLAMA_URL:-http://localhost:11434}...";
	@curl -s $${OLLAMA_URL:-http://localhost:11434}/api/version || true; echo;
	@echo "Try: 'make pull-local MODEL=$(MODEL)' or 'make pull-model MODEL=$(MODEL)'"

models:
	@echo "Installed models on $${OLLAMA_URL:-http://localhost:11434}:";
	@curl -s $${OLLAMA_URL:-http://localhost:11434}/api/tags | jq -r '.models[].name' || true

# Show categorized artifacts for a slug
show-artifacts:
	@echo "Artifacts for $(slug):";
	@ls -R artifacts/$(slug) || true;
	@echo "\n--- Blog draft (head) ---";
	@sed -n '1,80p' artifacts/$(slug)/blog/draft.md 2>/dev/null || true;
	@echo "\n--- LinkedIn ---";
	@sed -n '1,60p' artifacts/$(slug)/social/linkedin.md 2>/dev/null || true;

# Build LoRA dataset from artifacts
lora-dataset:
	python tools/lora/build_dataset.py

# Split LoRA dataset into train/val
lora-split:
	python tools/lora/split_dataset.py

# Launch React UI
ui:
	@echo "Launching React UI... (make sure to run 'make api' in another terminal)"
	@cd frontend && npm install && npm run dev

api:
	@echo "Starting FastAPI backend on http://localhost:8000 ..."
	@.venv/bin/uvicorn engine.api:app --reload --port 8000

api-stop:
	@echo "Stopping FastAPI backend on port 8000 (if running)..."
	@-if command -v lsof >/dev/null 2>&1; then \
		pids=$$(lsof -ti tcp:8000); \
		if [ -n "$$pids" ]; then \
			echo "Killing $$pids"; \
			kill $$pids || true; \
		else \
			echo "No process on port 8000"; \
		fi; \
	else \
		echo "lsof not available; please stop uvicorn manually."; \
	fi

# Convenience: ingest a single URL and rebuild index
ingest-url:
	@echo "URL=$(url)";
	@if [ -z "$(url)" ]; then echo "Provide url=..."; exit 2; fi
	@echo "$(url)" > /tmp/ingest_url.txt
	.venv/bin/python -m engine.ingest --urls /tmp/ingest_url.txt
	.venv/bin/python -m engine.rag.build_index

# Lint governance rules on an artifact's blog markdown

qdrant-start-native:
	@command -v $(QDRANT_NATIVE_BIN) >/dev/null 2>&1 || { echo "qdrant binary not found at $(QDRANT_NATIVE_BIN). Override QDRANT_NATIVE_BIN=..."; exit 2; }
	@mkdir -p $(dir $(QDRANT_PID_FILE))
	@if [ -f $(QDRANT_PID_FILE) ] && ps -p $$(cat $(QDRANT_PID_FILE)) >/dev/null 2>&1; then \
		echo "qdrant already running (PID $$(cat $(QDRANT_PID_FILE)))"; \
	else \
		echo "Starting qdrant -> $(QDRANT_NATIVE_BIN) --config-path $(QDRANT_NATIVE_CONFIG)"; \
		nohup $(QDRANT_NATIVE_BIN) --config-path $(QDRANT_NATIVE_CONFIG) > $(QDRANT_LOG_FILE) 2>&1 & echo $$! > $(QDRANT_PID_FILE); \
		echo "qdrant started (PID $$(cat $(QDRANT_PID_FILE)))"; \
	fi

qdrant-status-native:
	@if [ -f $(QDRANT_PID_FILE) ] && ps -p $$(cat $(QDRANT_PID_FILE)) >/dev/null 2>&1; then \
		echo "qdrant running (PID $$(cat $(QDRANT_PID_FILE)))"; \
	else \
		echo "qdrant not running (pid file missing or stale)."; \
	fi; \
	(if command -v lsof >/dev/null 2>&1; then echo -n "Port 6333: "; lsof -i :6333 -sTCP:LISTEN -n || true; fi)

qdrant-stop-native:
	@if [ -f $(QDRANT_PID_FILE) ]; then \
		pid=$$(cat $(QDRANT_PID_FILE)); \
		if ps -p $$pid >/dev/null 2>&1; then \
			echo "Stopping qdrant (PID $$pid)"; kill $$pid; \
			wait $$pid 2>/dev/null || true; \
		else \
			echo "No running qdrant found for PID $$pid"; \
		fi; \
		rm -f $(QDRANT_PID_FILE); \
	else \
		echo "No qdrant PID file at $(QDRANT_PID_FILE)"; \
	fi; \
	if command -v pkill >/dev/null 2>&1; then pkill -f "$(QDRANT_NATIVE_BIN)" 2>/dev/null || true; fi

# Convenience subset runs (require prior indexing)
lint-artifact:
	@if [ -z "$(slug)" ]; then echo "Provide slug=..."; exit 2; fi
	ALLOW_ARG=""; \
	if [ -n "$(allow)" ]; then \
	  IFS=',' read -ra DOMS <<< "$(allow)"; \
	  for d in "$${DOMS[@]}"; do ALLOW_ARG="$$ALLOW_ARG --allow $$d"; done; \
	fi; \
	NOEXT_ARG=""; \
	if [ "$(no_external)" = "1" ]; then NOEXT_ARG="--no-external"; fi; \
	.venv/bin/python tools/ci/check_post.py --file artifacts/$(slug)/blog/draft.md $$ALLOW_ARG $$NOEXT_ARG
	@echo "\n--- Instagram ---";
	@sed -n '1,60p' artifacts/$(slug)/social/instagram.md 2>/dev/null || true;
	@echo "\n--- GitHub README (head) ---";
	@sed -n '1,60p' artifacts/$(slug)/github/README.md 2>/dev/null || true;
	@echo "\n--- Meta files ---";
	@ls artifacts/$(slug)/meta 2>/dev/null || true;

# Regenerate all briefs locally (skip publish) with deterministic defaults
regen-all-local:
	@for b in briefs/*.yaml; do \
	  echo "===> $$b"; \
	  GEN_TEMPERATURE=0.0 GEN_SEED=42 SKIP_PUBLISH=1 .venv/bin/python -m engine.run $$b || exit 1; \
	done
