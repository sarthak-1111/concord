import os
import pickle
import numpy as np
import torch  # noqa: F401  Concord: torch before faiss (see create_vector_store)
import faiss
from typing import Dict, Any, List

from concord.literature import QUERY_PROMPT, embedder

VECTOR_DIR = "papers/vector_store"
INDEX_FILE = os.path.join(VECTOR_DIR, "papers.faiss")
CHUNKS_FILE = os.path.join(VECTOR_DIR, "papers.chunks")  # updated extension


def _embed_query(query: str) -> List[float]:
    """Concord: local query embedding (same model as the index) instead of the OpenAI API."""
    return embedder().encode_query([query], prompt=QUERY_PROMPT, normalize_embeddings=True)[0].tolist()


def retrieve_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve relevant chunks for a given query from FAISS index.

    Expected Input (payload):
        {
          "query": "<user's natural language question>",
          "top_k": <number of chunks to retrieve, default = 5>
        }
    """
    print(">>> Retrieving data...")
    query = payload.get("query", "")
    top_k = payload.get("top_k", 5)

    if not os.path.exists(INDEX_FILE) or not os.path.exists(CHUNKS_FILE):
        return {"status": "error", "message": "Vector store not found. Run create_vector_store first."}

    # Load FAISS index
    index = faiss.read_index(INDEX_FILE)

    # Load PaperChunk objects
    with open(CHUNKS_FILE, "rb") as f:
        documents = pickle.load(f)

    # Embed query
    qvec = np.array([_embed_query(query)], dtype="float32")

    # Search
    D, I = index.search(qvec, top_k)
    results = []
    for idx, score in zip(I[0], D[0]):
        if 0 <= idx < len(documents):
            chunk = documents[idx]
            results.append({
                "text": chunk.text,
                "metadata": chunk.metadata,
                "score": float(score)
            })
    print(">>> Retrieved data:", results)
    return {
        "status": "ok",
        "query": query,
        "results": results
    }
