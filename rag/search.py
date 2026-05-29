"""
NexusFlow Agent — RAG Search Wrapper (Phase 3)
Connects the agent's search_knowledge_base tool to the real ChromaDB vector store.
"""

import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

# Paths — point to the copied ChromaDB and knowledge base
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
KB_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")
CRM_DATA = os.path.join(os.path.dirname(__file__), "..", "crm", "synthetic_data.json")


@lru_cache(maxsize=1)
def get_vector_store():
    """
    Load the ChromaDB vector store once and cache it.
    lru_cache means it only loads from disk on the first call —
    every subsequent call reuses the same instance in memory.
    """
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import Chroma

    print("[RAG] Loading vector store from disk...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings
    )
    count = vector_store._collection.count()
    print(f"[RAG] Vector store loaded — {count} vectors ready")
    return vector_store


def search(query: str, k: int = 4) -> list[dict]:
    """
    Search the ChromaDB vector store for chunks relevant to the query.
    Returns a list of results with content and source metadata.

    Args:
        query: Natural language search query
        k: Number of results to return (default 4)

    Returns:
        List of dicts with 'content', 'source', 'type', 'score'
    """
    try:
        vector_store = get_vector_store()
        results = vector_store.similarity_search_with_relevance_scores(query, k=k)

        formatted = []
        for doc, score in results:
            formatted.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "type": doc.metadata.get("type", "unknown"),
                "record_id": doc.metadata.get("record_id", ""),
                "relevance_score": round(score, 3)
            })

        return formatted

    except Exception as e:
        print(f"[RAG] Search error: {e}")
        return [{"content": f"RAG search unavailable: {e}", "source": "error", "score": 0}]