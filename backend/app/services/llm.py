# backend/app/services/llm.py

# from llama_cpp import Llama
# import requests
from groq import Groq
import json
import re
import os
# import multiprocessing
from app.utils.logging import get_logger
from app.config import settings

logger = get_logger(__name__)
# CPU_THREADS = min(4,multiprocessing.cpu_count())

# MODEL CONFIG
client = Groq(api_key=settings.GROQ_API_KEY)
MODEL_NAME = settings.GROQ_MODEL_NAME

MAX_RETRIES = 3

# -----------------------------
# Public API
# -----------------------------

def generate_completion(
    prompt: str,
    # max_tokens: int = MAX_NEW_TOKENS,
    # temperature: float = TEMPERATURE
) -> str:
    """
    Generate response using OLLAMA (Mistral).
    Includes retry for ribustness
    """

    if not prompt or not prompt.strip():
        logger.warning("Empty prompt passed to LLM")
        return ""

    # _load_model()

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model = MODEL_NAME,
                messages = [
                    {
                        'role': 'system',
                        'content': "You are a careful and factual study assistant. You must answer ONLY from the provided context."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature = 0.2,
                
            )
            
            text = response.choices[0].message.content.strip()
            
            if text:
                logger.info(
                    "Groq completion successful",
                    extra={"prompt_len": len(prompt), "output_len": len(text), "attempt":attempt + 1}  # log only first
                )
                return text
        except Exception as e:
            logger.exception(f"Groq generation failed (attempt {attempt + 1})")
    logger.error(f"LLM failed after retries")
    return ""
        
def _extract_json(text:str):
    """
    Robust JSON extraction from LLM output.
    Handles:
    - clean JSON
    - JSON with extra text
    - multiple JSON blocks 
    """
    # 1. Direct parse attempt
    try:
        return json.loads(text)
    except:
        pass
    
    # 2. Extract largest JSON block
    matches = re.findall(r"\{.*?\}", text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match)
        except:
            continue
        
    # 3. Fallback: try full greedy match
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass
    raise ValueError("No Valid JSON found in LLM output")

def generate_json_completion(prompt: str) -> dict:
    """
    Gennerate LLM Output and safely parse json.
    Raises ValueError if parsing fails.
    """
        
    raw_output = generate_completion(prompt)
    
    if not raw_output:
        raise ValueError("LLM returned empty output")
    try:
        return _extract_json(raw_output)
    except json.JSONDecodeError:
        # Attempt to extract JSON from the messy output using regex
        
        logger.error("Invalid JSON from LLM", extra={"raw_output": raw_output})
        raise ValueError("LLM did not return valid JSON")
