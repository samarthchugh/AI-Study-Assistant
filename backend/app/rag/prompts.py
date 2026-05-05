from typing import List, Optional
from app.rag.contracts import RetrievedChunk

REFUSAL_MESSAGE = "I couldn't find the answer to your question in the provided context. Please try asking something else or provide more information."

def build_qa_prompt(context_chunks: List[RetrievedChunk], question: str, history: Optional[list] = None) -> str:
    """Build a grounded QA prompt, optionally including conversation history for follow-up context."""

    # Build history section (last 8 messages = 4 turns)
    history_section = ""
    follow_up_rule = ""
    if history:
        recent = history[-8:]
        lines = [
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in recent
        ]
        history_section = "\nCONVERSATION HISTORY:\n" + "\n".join(lines) + "\n"
        follow_up_rule = "\n    - Use the CONVERSATION HISTORY to understand what the user is referring to if the question is a follow-up."

    # Build context block
    if not context_chunks:
        context_text = "NO RELEVANT CONTEXT WAS RETRIEVED."
    else:
        context_text = "\n\n".join(
            f"[Context chunk {i+1}]\n{chunk.text}"
            for i, chunk in enumerate(context_chunks)
        )

    prompt = f"""You are a careful and factual question-answering assistant.
{history_section}
RULES (MANDATORY):
    - You must answer using ONLY the information provided in the CONTEXT section.
    - You must NOT use any external knowledge.
    - Do NOT hallucinate or invent facts.
    - You are allowed to infer and extract relevant information from the context, but must NOT add unsupported information.
    - The answer may be spread across multiple context chunks — combine information from all relevant chunks.{follow_up_rule}

ANSWERING GUIDELINES:
    - If the answer is clearly present -> answer completely.
    - If the question has multiple parts -> answer all using the context.
    - If the answer is partially available -> answer what you can and clearly mention missing parts.
    - Only respond with "{REFUSAL_MESSAGE}" if NO relevant information is found in the context.

STYLE:
    - Be clear and explanatory.
    - Do NOT just copy-paste from the context. Use your own words.
    - If multiple context chunks are relevant, synthesize them into a coherent answer.

CONTEXT:
{context_text}

QUESTION:
{question}

ANSWER:""".strip()

    return prompt
