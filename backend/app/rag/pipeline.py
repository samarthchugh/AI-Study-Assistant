from typing import Dict, List
from app.services.llm import generate_completion
from app.rag.retriever import Retriever
from app.rag.prompts import build_qa_prompt, REFUSAL_MESSAGE
from app.rag.contracts import RetrievedChunk
from app.utils.logging import get_logger

logger = get_logger(__name__)

class QueryAnswerPipeline:
    """
    Orchestrates:
    Question -> Retrievel -> Prompt -> LLM -> Safe Answer
    """
    
    def __init__(self, retriever: Retriever):
        self.retriever = retriever
        
    def answer_query(self, question: str) -> Dict:
        """
        Main entry point for answering a user question.
        Can be reused by:
        - FastAPI endpoint
        - Quiz Engine
        - Agents
        """
        # 0. Basic Validation
        if not question or not question.strip():
            return self._empty_answer("Question is empty.")
        
        logger.info("Answering Query", extra={"question": question})
        
        # 1. Retrieve relevant context chunks
        context_chunks = self.retriever.retrieve(question)
        if not context_chunks:
            logger.warning("No relevant context retrieved for the question.")
            return self._refusal_answer()
        
        logger.info(
            "Retrieved context chunks",
            extra={"num_chunks": len(context_chunks)}
        )
        
        # 2. Build the QA prompt
        prompt = build_qa_prompt(context_chunks=context_chunks, question=question)
        
        # 3. Generate LLM completion
        answer = generate_completion(prompt)
        if not answer or not answer.strip():
            logger.warning("LLM returned an empty answer.")
            return self._refusal_answer()
        
        # 4. Post LLM guardrail
        if REFUSAL_MESSAGE in answer:
            logger.info("LLM explicitly refused.")
            return self._refusal_answer()
        
        # 5. Return the final answer
        return {
            'answer': answer.strip(),
            'sources': self._extract_sources(context_chunks),
            "confidence": self._estimate_confidence(context_chunks)           
        }
        
    
    def _refusal_answer(self) -> Dict:
        return {
            'answer': REFUSAL_MESSAGE,
            'sources': [],
            "confidence": 0.0
        }
        
    def _empty_answer(self, reason: str) -> Dict:
        return {
            "answer": reason,
            "sources": [],
            "confidence": 0.0
        }
    
    def _extract_sources(self, context_chunks: List[RetrievedChunk]) -> List[str]:
        """
        Extract document identofiers from chunk metadata.
        """
        sources = set()
        for chunk in context_chunks:
            metadata = chunk.metadata
            if "doc_id" in metadata:
                sources.add(metadata["doc_id"])
        return list(sources)
    
    def _estimate_confidence(self, context_chunks: List[RetrievedChunk], user_id=None) -> float:
        """
        Simple confidence heuristic:
        average similarity score of retrieved chunks.
        
        v1: similarity-based
        v2: + recency
        v3: + quiz accuracy 
        """
        scores = [chunk.score for chunk in context_chunks]
        if not scores:
            return 0.0
        return round(sum(scores) / len(scores), 3)