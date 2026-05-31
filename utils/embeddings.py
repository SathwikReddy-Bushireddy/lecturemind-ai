import logging
from typing import List
import google.generativeai as genai
from utils.gemini_config import api_key, selected_embed_model

logger = logging.getLogger(__name__)

def get_embedding(text: str, task_type: str = "retrieval_document") -> List[float]:
    """
    Fetches the 768-dimensional dense vector representing the text using Google's 
    selected embedding API model (configured via gemini_config).

    Args:
        text: The text string to embed.
        task_type: Purpose of embedding ('retrieval_document' or 'retrieval_query').

    Returns:
        List[float]: A 768-dimensional float vector.
    """
    # 768-dimensional zero vector fallback if API key is not active
    fallback_vector = [0.0] * 768

    if not api_key:
        return fallback_vector

    if not text or not text.strip():
        return fallback_vector

    try:
        response = genai.embed_content(
            model=selected_embed_model,
            content=text.strip(),
            task_type=task_type
        )
        if "embedding" in response:
            return response["embedding"]
        else:
            logger.warning("Generative AI API response did not contain 'embedding' key.")
            return fallback_vector
    except Exception as e:
        logger.error(f"Google Generative AI embeddings API failed: {str(e)}")
        return fallback_vector
