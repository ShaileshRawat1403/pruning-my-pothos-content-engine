import os
import json
import requests

# Shared LLM helpers for Ollama

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
GEN_MODEL  = os.getenv("GEN_MODEL", "phi3:mini-128k")


def _predict_tokens_for_length(length: str) -> int:
    return {
        "short": 700,
        "medium": 1400,
        "long": 2200,
    }.get((length or "medium").lower(), 1400)


def build_ollama_options(*, length: str = "medium") -> dict:
    """Build Ollama options from environment. Only include keys that are set."""
    opts = {
        "num_ctx": int(os.getenv("GEN_NUM_CTX", "120000")),
        "num_predict": int(os.getenv("GEN_NUM_PREDICT", str(_predict_tokens_for_length(length)))),
        "temperature": float(os.getenv("GEN_TEMPERATURE", "0.3")),
    }
    # Optional performance/tuning knobs
    if os.getenv("GEN_NUM_THREAD"):    opts["num_thread"]      = int(os.getenv("GEN_NUM_THREAD"))
    if os.getenv("GEN_NUM_BATCH"):     opts["num_batch"]       = int(os.getenv("GEN_NUM_BATCH"))
    if os.getenv("GEN_TOP_K"):         opts["top_k"]           = int(os.getenv("GEN_TOP_K"))
    if os.getenv("GEN_TOP_P"):         opts["top_p"]           = float(os.getenv("GEN_TOP_P"))
    if os.getenv("GEN_REPEAT_PENALTY"):opts["repeat_penalty"]  = float(os.getenv("GEN_REPEAT_PENALTY"))
    if os.getenv("GEN_PRESENCE_PENALTY"):opts["presence_penalty"] = float(os.getenv("GEN_PRESENCE_PENALTY"))
    if os.getenv("GEN_FREQUENCY_PENALTY"):opts["frequency_penalty"] = float(os.getenv("GEN_FREQUENCY_PENALTY"))
    if os.getenv("GEN_MIROSTAT"):      opts["mirostat"]        = int(os.getenv("GEN_MIROSTAT"))
    if os.getenv("GEN_MIROSTAT_TAU"):  opts["mirostat_tau"]    = float(os.getenv("GEN_MIROSTAT_TAU"))
    if os.getenv("GEN_MIROSTAT_ETA"):  opts["mirostat_eta"]    = float(os.getenv("GEN_MIROSTAT_ETA"))
    return opts


def assert_ollama_up():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/version", timeout=5)
        r.raise_for_status()
    except Exception as e:
        raise RuntimeError(
            f"Cannot reach Ollama at {OLLAMA_URL}. Ensure it's running.\n"
            "Options:\n"
            "- Local: install ollama, then run 'ollama serve' and 'ollama pull <model>'\n"
            "- Docker: 'make up' then 'make pull' and use 'make run brief=...'\n"
            "You can change OLLAMA_URL in .env if needed."
        ) from e


def ollama_complete(prompt: str, *, length: str = "medium", timeout_s: int | None = None) -> str:
    options = build_ollama_options(length=length)
    timeout_s = timeout_s or int(os.getenv("GEN_HTTP_TIMEOUT", "1200"))
    payload = {"model": GEN_MODEL, "prompt": prompt, "stream": False, "options": options}

    try:
        r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=timeout_s)
        r.raise_for_status()
        return r.json().get("response", "")
    except (requests.Timeout, requests.HTTPError):
        # Retry once with smaller cap
        smaller = max(400, int(options.get("num_predict", 900) * 0.6))
        payload["options"]["num_predict"] = int(os.getenv("GEN_NUM_PREDICT_RETRY", str(smaller)))
        try:
            r2 = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=timeout_s)
            r2.raise_for_status()
            return r2.json().get("response", "")
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            if status == 404:
                raise RuntimeError(
                    f"Ollama endpoint not found at {OLLAMA_URL}/api/generate.\n"
                    "Start Ollama locally (ollama serve) or run Docker (make up).\n"
                    f"Then pull a model, e.g.: 'ollama pull {GEN_MODEL}'."
                ) from e
            raise
