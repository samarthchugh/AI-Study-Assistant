from typing import Dict, Generator, List
from app.services.llm import generate_completion, generate_completion_stream
from app.rag.retriever import Retriever
from app.rag.prompts import build_qa_prompt, REFUSAL_MESSAGE
from app.rag.contracts import RetrievedChunk
from app.utils.logging import get_logger

logger = get_logger(__name__)
DEBUG = False  # Set to True to enable debug prints

def expand_with_neighbors(chunks: List[RetrievedChunk], window_size: int = 3) :
    """
    Expand retrieved chunks with their nearby chunks using chunk_index to provide more context.
    """
    try:
        expanded = []
        seen = set()
        for chunk in chunks:
            idx = chunk.metadata.get("chunk_index")
            
            if idx is None:
                expanded.append(chunk)
                continue
            
            for offset in range(-window_size, window_size + 1):
                neighbor_idx = idx + offset
                if neighbor_idx < 0:
                    continue
                
                neighbor_metadata = chunk.metadata.copy()
                neighbor_metadata["chunk_index"] = neighbor_idx
                
                neighbor_chunk = RetrievedChunk(
                    text=chunk.text,  # In real implementation, fetch actual text for neighbor_idx
                    score=chunk.score,
                    metadata=neighbor_metadata
                )
                
                if neighbor_chunk.text not in seen:
                    expanded.append(neighbor_chunk)
                    seen.add(neighbor_chunk.text)
            
        return expanded
    except Exception as e:
        logger.error(f"Error during context expansion: {e}")
        return chunks  # Fallback to original chunks if expansion fails

class QueryAnswerPipeline:
    """
    Orchestrates:
    Question -> Retrievel -> Prompt -> LLM -> Safe Answer
    """
    
    def __init__(self, retriever: Retriever):
        self.retriever = retriever
        
    def answer_query(self, question: str, user_id: int) -> Dict:
        """
        Main entry point for answering a user question.
        Can be reused by:
        - FastAPI endpoint
        - Quiz Engine
        - Agents
        """
        try:
            if DEBUG:
                print("\n==============RAG DEBUG START==============\n")
                print(f"Question: {question}")
                print(f"User ID: {user_id}")
                
            # 0. Basic Validation
            if not question or not question.strip():
                return self._empty_answer("Question is empty.")
            
            logger.info("Answering Query", extra={"question": question})
            
            # 1. Retrieve relevant context chunks
            queries = [
                question,
                f"{question} explaination",
                f"{question} concept",
                f"{question} detailed"
            ]
            
            all_chunks = []
            
            for q in queries:
                chunks = self.retriever.retrieve(q, filters={"user_id": user_id})
                all_chunks.extend(chunks)
            # deduplicate chunks by text
            unique_chunks = {}
            for c in all_chunks:
                unique_chunks[c.text] = c
            context_chunks = list(unique_chunks.values())
            context_chunks = expand_with_neighbors(context_chunks, window_size=2)
            

            if DEBUG:
                print("==============RAG DEBUG: Retrieved Context==============\n")
                print(f"Total Chunks {len(context_chunks)}")
                for i, chunk in enumerate(context_chunks[:3]):  # Show top 3 chunks
                    print(f"\nChunk {i+1}:")
                    print(f"Text Preview: {chunk.text[:200]}...")  # Print first 200 chars
                    print(f"Metadata: {chunk.metadata}")
                    print(f"Score: {chunk.score}")
                    print("-" * 50)
            
            if not context_chunks:
                logger.warning("No relevant context retrieved for the question.")
                return self._refusal_answer()
            
            logger.info(
                "Retrieved context chunks",
                extra={"num_chunks": len(context_chunks)}
            )
            
            # 2. Build the QA prompt
            prompt = build_qa_prompt(context_chunks=context_chunks, question=question)
            if DEBUG:
                print("\n==============RAG DEBUG: Prompt Sent to LLM==============\n")
                print(prompt)
            
            # 3. Generate LLM completion
            answer = generate_completion(prompt)
            
            if DEBUG:
                print("\n==============RAG DEBUG: LLM Raw Answer==============\n")
                print(answer)
            if not answer or not answer.strip():
                logger.warning("LLM returned an empty answer.")
                return self._refusal_answer()
            
            # 4. Post LLM guardrail
            if REFUSAL_MESSAGE in answer:
                logger.info("LLM explicitly refused.")
                return self._refusal_answer()
            
            if DEBUG:
                print("\n==============RAG DEBUG: Final Answer==============\n")
                print(f"Answer: {answer.strip()}")
                print(f"Sources: {self._extract_sources(context_chunks)}")
                print(f"Confidence: {self._estimate_confidence(context_chunks)}")
                print("\n==============RAG DEBUG END==============\n")
                
            
            # 5. Return the final answer
            return {
                'answer': answer.strip(),
                'sources': self._extract_sources(context_chunks),
                "confidence": self._estimate_confidence(context_chunks)           
            }
        except Exception as e:
            logger.error(f"Error during query answering: {e}")
            return self._refusal_answer()
        
    
    def stream_query(self, question: str, user_id: int, history: list = None) -> Generator:
        """Stream LLM output as text chunks, then yield a final dict with source passages."""
        try:
            if not question or not question.strip():
                yield "Question is empty."
                return

            queries = [question, f"{question} explanation", f"{question} concept", f"{question} detailed"]
            all_chunks = []
            for q in queries:
                chunks = self.retriever.retrieve(q, filters={"user_id": user_id})
                all_chunks.extend(chunks)

            unique_chunks: Dict[str, RetrievedChunk] = {}
            for c in all_chunks:
                unique_chunks[c.text] = c
            context_chunks = list(unique_chunks.values())
            context_chunks = expand_with_neighbors(context_chunks, window_size=2)

            if not context_chunks:
                yield REFUSAL_MESSAGE
                return

            prompt = build_qa_prompt(context_chunks=context_chunks, question=question, history=history)

            for chunk in generate_completion_stream(prompt):
                yield chunk

            # After text stream, yield source metadata so UI can show retrieved passages.
            # Only include chunks above a relevance threshold so unrelated passages are excluded.
            RELEVANCE_THRESHOLD = 0.35
            relevant = [c for c in context_chunks if c.score >= RELEVANCE_THRESHOLD]
            if not relevant:
                # Fallback: show the single best chunk even if below threshold
                relevant = sorted(context_chunks, key=lambda c: c.score, reverse=True)[:1]

            # One entry per document — keep the highest-scoring chunk per doc_id
            best_per_doc: Dict[str, RetrievedChunk] = {}
            for c in sorted(relevant, key=lambda c: c.score, reverse=True):
                doc_id = c.metadata.get("doc_id", "unknown")
                if doc_id not in best_per_doc:
                    best_per_doc[doc_id] = c

            source_chunks = list(best_per_doc.values())[:3]
            confidence = round(sum(c.score for c in source_chunks) / len(source_chunks), 3) if source_chunks else 0.0

            yield {
                "sources": [
                    {
                        "text": c.text[:280].strip(),
                        "doc_id": c.metadata.get("doc_id", ""),
                        "score": round(c.score, 3),
                    }
                    for c in source_chunks
                ],
                "confidence": confidence,
            }
        except Exception as e:
            logger.error(f"Error during streaming query: {e}")
            yield REFUSAL_MESSAGE

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