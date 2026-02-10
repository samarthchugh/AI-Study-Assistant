# backend/tests/test_rag.py

from app.rag.retriever import Retriever
from app.services.vector_store import FAISSVectorStore
from app.rag.embeddings import embed_text


def run_retriever_test():
    """
    CLI-style retriever validation.
    Assumes FAISS index + metadata already exist on disk.
    """

    # 1️⃣ Infer embedding dimension safely (SOURCE OF TRUTH = data)
    dummy_embedding = embed_text(["embedding_dim_probe"])
    embedding_dim = dummy_embedding.shape[1]

    # 2️⃣ Load FAISS vector store (auto-loads index + metadata)
    vector_store = FAISSVectorStore(
        embedding_dim=embedding_dim
    )

    # 3️⃣ Initialize retriever
    retriever = Retriever(
        vector_store=vector_store,
        top_k=5,
        score_threshold=0.1,
        max_context_chars=4000
    )

    print("\nRetriever test started. Type 'exit' to quit.")

    # 4️⃣ Interactive CLI loop
    while True:
        query = input("\nAsk a question: ").strip()
        if query.lower() == "exit":
            break

        results = retriever.retrieve(query)

        print(f"\nRetrieved {len(results)} chunks\n")

        for i, chunk in enumerate(results, start=1):
            print(f"#{i}")
            print(f"Score   : {chunk['score']:.3f}")
            print(f"Source  : {chunk['metadata'].get('source')}")
            print("Text    :")
            print(chunk["text"][:300])
            print("-" * 70)


if __name__ == "__main__":
    run_retriever_test()
