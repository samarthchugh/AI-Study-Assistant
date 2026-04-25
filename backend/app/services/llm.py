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
DEFAULT_SYSTEM_PROMPT = "You are a careful and factual study assistant. You must answer ONLY from the provided context."

# -----------------------------
# Public API
# -----------------------------

def generate_completion(
    prompt: str,
    system_prompt: str = None
    # max_tokens: int = MAX_NEW_TOKENS,
    # temperature: float = TEMPERATURE
) -> str:
    """
    Generate a text completion via Groq. Retries up to MAX_RETRIES times for robustness.
    Returns an empty string if all attempts fail.
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
                        'content': DEFAULT_SYSTEM_PROMPT or system_prompt
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
        
def generate_completion_stream(prompt: str, system_prompt: str = None):
    """Yield text delta chunks from Groq streaming API."""
    try:
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt or DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
    except Exception as e:
        logger.exception("Groq streaming failed")
        return


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
    Generate an LLM completion and parse the output as JSON.
    Raises ValueError if the output is empty or cannot be parsed.
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
