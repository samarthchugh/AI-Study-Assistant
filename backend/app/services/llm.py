# backend/app/services/llm.py

from llama_cpp import Llama
import os
import multiprocessing
from app.utils.logging import get_logger
from app.config import settings

logger = get_logger(__name__)
CPU_THREADS = min(4,multiprocessing.cpu_count())

# MODEL CONFIG

MODEL_PATH = settings.LLM_MODEL_PATH
MAX_NEW_TOKENS = 512
TEMPERATURE = 0.0   # deterministic for study assistant

_llm = None

def _load_model():
    global _llm
    if MODEL_PATH is None:
        raise ValueError("LLM_MODEL_PATH is not set")
    
    if _llm is not None:
        return

    logger.info(f"Loading Phi-3 Mini (quantized) via llama.cpp from {MODEL_PATH}...")

    _llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=3072,
        n_threads=CPU_THREADS,
        verbose=False,
        n_batch=256,
        use_mlock=False,
        use_mmap=True
    )

    logger.info("LLM loaded successfully")
    
def _format_prompt(prompt: str) -> str:
    """
    Format prompt for Phi-3 Mini chat-style models.
    """
    return (
        "<|system|>\n"
        "You are a careful and factual study assistant. "
        "You must answer ONLY from the provided context.\n"
        "<|end|>\n"
        "<|user|>\n"
        f"{prompt}\n"
        "<|end|>\n"
        "<|assistant|>\n"
    )



# -----------------------------
# Public API
# -----------------------------

def generate_completion(
    prompt: str,
    max_tokens: int = MAX_NEW_TOKENS,
    temperature: float = TEMPERATURE
) -> str:
    """
    Generate a completion using an open-source LLM.

    This function is:
    - Stateless
    - Deterministic (by default)
    - RAG-safe (prompt-controlled)
    """

    if not prompt or not prompt.strip():
        logger.warning("Empty prompt passed to LLM")
        return ""

    _load_model()

    try:
        formatted_prompt = _format_prompt(prompt)
        
        output = _llm(
            formatted_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["<|end|>"]
        )
        
        text = output["choices"][0]["text"].strip()

        logger.info(
            "LLM completion generated",
            extra={
                "prompt_len": len(formatted_prompt),
                "output_len": len(text),
            }
        )

        return text
       

    except Exception as e:
        logger.exception("LLM generation failed")
        return ""
