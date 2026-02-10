

from app.rag.pipeline import QueryAnswerPipeline
from app.rag.retriever import Retriever
from app.services.vector_store import FAISSVectorStore
from app.rag.embeddings import embed_text


def run_pipeline_cli():
    """
    CLI test for the Query → Answer pipeline.
    Run this BEFORE exposing FastAPI.
    """

    print("\nInitializing pipeline...\n")

    # 1️⃣ Infer embedding dimension safely
    dummy_embedding = embed_text(["embedding_dim_probe"])
    embedding_dim = dummy_embedding.shape[1]

    # 2️⃣ Load FAISS vector store (auto-loads index + metadata)
    vector_store = FAISSVectorStore(
        embedding_dim=embedding_dim
    )

    # 3️⃣ Initialize retriever (tuned values)
    retriever = Retriever(
        vector_store=vector_store,
        top_k=5,
        score_threshold=0.15,
        max_context_chars=4000,
    )

    # 4️⃣ Initialize pipeline
    pipeline = QueryAnswerPipeline(
        retriever=retriever
    )

    print("Pipeline ready.")
    print("Type 'exit' to quit.\n")

    # 5️⃣ Interactive CLI loop
    while True:
        question = input("Ask a question: ").strip()

        if question.lower() == "exit":
            print("Exiting.")
            break

        result = pipeline.answer_query(question)

        print("\n--- ANSWER ---")
        print(result["answer"])

        print("\n--- SOURCES ---")
        if result["sources"]:
            for src in result["sources"]:
                print("-", src)
        else:
            print("No sources")

        print("\n--- CONFIDENCE ---")
        print(result["confidence"])

        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    run_pipeline_cli()
