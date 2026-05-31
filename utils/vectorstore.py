import numpy as np
import logging
from typing import List, Dict, Any
from utils.embeddings import get_embedding

logger = logging.getLogger(__name__)

class MemoryVectorStore:
    """
    A lightweight, pure-Python in-memory vector store that uses numpy to perform
    extremely fast CPU Cosine Similarity search queries. Fits within Streamlit's 1GB memory limit.
    """
    def __init__(self):
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: List[List[float]] = []

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Generates dense vector embeddings for a list of text chunks and indexes them.

        Args:
            chunks: A list of text chunks with metadata:
                [{"text": str, "page_num": int, "doc_name": str}, ...]
        """
        if not chunks:
            logger.warning("add_chunks received an empty list of chunks.")
            return

        logger.info(f"Compiling vector store embeddings for {len(chunks)} document chunks...")
        
        for idx, chunk in enumerate(chunks):
            # Retrieve 768-d vector embedding via Gemini API
            vector = get_embedding(chunk["text"], task_type="retrieval_document")
            self.chunks.append(chunk)
            self.embeddings.append(vector)
            
            if (idx + 1) % 10 == 0 or (idx + 1) == len(chunks):
                logger.info(f"Indexed embeddings: {idx + 1}/{len(chunks)}")

        logger.info(f"Successfully compiled Vector DB. Total indexed chunks: {len(self.chunks)}.")

    def similarity_search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """
        Retrieves the top k most semantically relevant text chunks for a query using Cosine Similarity.

        Args:
            query: The student's text query/question.
            k: Total matches to retrieve.

        Returns:
            List[Dict[str, Any]]: Top k matching chunk dictionaries with metadata.
        """
        if not self.embeddings:
            logger.warning("Similarity search requested, but the vector database is empty.")
            return []

        # Get embedding vector representing the search query
        query_vector = get_embedding(query, task_type="retrieval_query")
        
        q_arr = np.array(query_vector)
        q_norm = np.linalg.norm(q_arr)
        
        if q_norm == 0:
            # Fallback to returning the first k chunks if query embedding failed (all zeros)
            return self.chunks[:k]

        scores_and_chunks = []
        for idx, emb_vector in enumerate(self.embeddings):
            e_arr = np.array(emb_vector)
            e_norm = np.linalg.norm(e_arr)
            
            if e_norm == 0:
                similarity = 0.0
            else:
                # Cosine Similarity: A . B / (||A|| * ||B||)
                similarity = float(np.dot(q_arr, e_arr) / (q_norm * e_norm))
            
            scores_and_chunks.append((similarity, self.chunks[idx]))

        # Sort candidates descending by similarity score
        scores_and_chunks.sort(key=lambda x: x[0], reverse=True)
        
        # Extract the top k results
        results = [item[1] for item in scores_and_chunks[:k]]
        logger.info(f"RAG retrieved {len(results)} context blocks for query: '{query[:40]}...'")
        return results
