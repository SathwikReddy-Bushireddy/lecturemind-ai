import os
import logging
from typing import List, Dict, Any
import google.generativeai as genai
from utils.gemini_config import api_key, selected_text_model
from prompts.templates import QA_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

def format_retrieved_context(chunks: List[Dict[str, Any]]) -> str:
    """
    Format vector store matched chunks into a clean, labeled context block.
    """
    formatted_blocks = []
    for idx, chunk in enumerate(chunks):
        doc_name = chunk.get("doc_name", "Unknown Source")
        page_num = chunk.get("page_num", 1)
        text = chunk.get("text", "").strip()
        
        block = f"[Chunk {idx + 1} - Source: {doc_name}, Page {page_num}]\n{text}"
        formatted_blocks.append(block)
        
    return "\n\n".join(formatted_blocks)

def format_chat_history(chat_history: List[Dict[str, str]]) -> str:
    """
    Formats the conversation logs into a clean text block for model context.
    """
    history_blocks = []
    # Avoid first system welcome message to prevent redundant noise
    for msg in chat_history[1:]:
        role = "Student" if msg["role"] == "user" else "LectureMind AI"
        history_blocks.append(f"{role}: {msg['content']}")
        
    return "\n".join(history_blocks)

def answer_question(query: str, chat_history: List[Dict[str, str]], vector_store: Any) -> str:
    """
    Answers a student's question about uploaded PDFs by searching vector embeddings
    for matching pages, assembling history contexts, and calling Gemini 1.5 Flash.

    Args:
        query: The student's text query/question.
        chat_history: Active conversation logs list.
        vector_store: The custom in-memory Cosine Similarity Vector database instance.

    Returns:
        str: Context-aware cited answer.
    """
    logger.info(f"Initializing RAG Retrieval query for: '{query[:45]}...'")

    if not vector_store:
        logger.warning("RAG requested but vector store is empty.")
        return "⚠️ Vector database is not initialized. Please upload and process study content first!"

    # 1. Retrieve the top k = 4 most semantically similar context chunks
    matched_chunks = vector_store.similarity_search(query, k=4)
    
    if not matched_chunks:
        return "I couldn't locate any matching passages in your uploaded documents. Could you please refine your question?"

    # 2. Format chunks and chat history for the prompt context
    context_str = format_retrieved_context(matched_chunks)
    history_str = format_chat_history(chat_history)

    if not api_key:
        logger.error("GEMINI_API_KEY is missing! QA chain running in fallback mode.")
        # Provide simulated RAG answer using the retrieved context to keep system highly usable offline!
        best_chunk = matched_chunks[0]
        doc_name = best_chunk.get("doc_name", "document.pdf")
        page_num = best_chunk.get("page_num", 1)
        text = best_chunk.get("text", "")
        
        return (
            f"⚠️ **[API Key Missing]** Here is a matching passage directly retrieved from your upload "
            f"**[{doc_name} Page {page_num}]**:\n\n"
            f"> \"{text}\"\n\n"
            f"*Please set your `GEMINI_API_KEY` credential in Streamlit Secrets or environment variables to enable generative AI RAG answers.*"
        )

    try:
        # Initialize generative client gracefully
        try:
            model = genai.GenerativeModel(selected_text_model)
        except Exception as model_init_err:
            logger.warning(f"Failed to initialize model '{selected_text_model}': {str(model_init_err)}. Swapping to standard fallback.")
            model = genai.GenerativeModel("gemini-2.5-flash")
        
        # 3. Assemble the prompt stack
        system_rules = QA_SYSTEM_PROMPT.format(context=context_str)
        
        prompt_stack = f"{system_rules}\n\n"
        if history_str:
            prompt_stack += f"Recent Dialogue History:\n{history_str}\n\n"
            
        prompt_stack += f"Current Question from Student:\n{query}\n\nAnswer:"
        
        logger.info("Calling Gemini 1.5 Flash for RAG synthesis...")
        response = model.generate_content(prompt_stack)
        
        answer_text = response.text.strip() if response.text else "Failed to generate answer context."
        logger.info("RAG answer compiled successfully!")
        return answer_text

    except Exception as e:
        logger.error(f"Critical error during RAG QA API call: {str(e)}")
        # Graceful fallback utilizing raw context citations so the user always receives information
        best_chunk = matched_chunks[0]
        return (
            f"⚠️ **[API Request Failed]** I encountered an exception calling the Gemini API: `{str(e)}`.\n\n"
            f"However, here is a highly relevant passage located directly in your document "
            f"**[{best_chunk.get('doc_name', 'Source')} Page {best_chunk.get('page_num', 1)}]**:\n\n"
            f"\"{best_chunk.get('text', '')}\""
        )
