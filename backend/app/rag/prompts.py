from typing import List, Dict
from app.rag.contracts import RetrievedChunk

REFUSAL_MESSAGE = "I couldn't find the answer to your question in the provided context. Please try asking something else or provide more information."

def build_qa_prompt(context_chunks: List[RetrievedChunk], question: str) -> str:
    """
    Build a grounded QA prompt for RAG.

    The LLM is strictly instructed to:
    - Use ONLY the provided context
    - Refuse if the answer is not found
    """
    # 1. build context block
    if not context_chunks:
        context_text = "NO RELEVANT CONTEXT WAS RETRIEVED."
    else:
        context_text = "n\n".join(
            f"[Context chunk {i+1}]\n{chunk.text}"
            for i, chunk in enumerate(context_chunks)
        )
        
    # 2. build final prompt
    prompt = f"""
    You are a careful and factual question-answering assistant.
    
    RULES (MANDATORY):
    - You must answer using the ONLY the information provided in the CONTEXT section.
    - You must NOT use any external knowledge or make assumptions.
    - If the answer is not found in the context, you MUST respond with: 
    "{REFUSAL_MESSAGE}"
    - Do NOT guess, infer, or add information that is not explicitly stated in the context.
    
    CONTEXT:
    {context_text}
    
    QUESTION:
    {question}
    
    ANSWER:
    """.strip()
    
    return prompt