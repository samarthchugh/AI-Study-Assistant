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
    - You must NOT use any external knowledge.
    - Do NOT hallucinate or invent facts.
    - However, the answer may not be explicitly written as a direct sentence.
    - You are allowed to infer and extract relevant information from the context, but you must NOT add any information that is not supported by the context.
    - The answer may be spread across multiple context chunks. Combine information from all relevant chunks.
    - Some information may reference other parts of the document. Use the metadata to understand relationships between chunks.
    
    ANSWERING GUIDELINES:
    - If the answer is clearly present -> answer completely.
    - If the question has multiple parts, -> answer all using the context.
    - If the answer is partially available -> answer what you can and clearly mention missing parts.
    - Only respond with "{REFUSAL_MESSAGE}" if NO relevant information is found in the context to answer ANY part of the question.
    
    STYLE:
    - Be clear and explanatory.
    - Do NOT just copy-paste from the context. Always use your own words to explain.
    - If multiple context chunks are relevant, synthesize the information together in a coherent way.
    
    CONTEXT:
    {context_text}
    
    QUESTION:
    {question}
    
    ANSWER:
    """.strip()
    
    return prompt