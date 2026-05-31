import logging
from typing import Dict
import google.generativeai as genai
from utils.gemini_config import api_key, selected_text_model
from prompts.templates import (
    SHORT_SUMMARY_PROMPT,
    DETAILED_SUMMARY_PROMPT,
    KEY_CONCEPTS_PROMPT,
    IMPORTANT_TOPICS_PROMPT
)

logger = logging.getLogger(__name__)

def generate_summaries(text: str) -> Dict[str, str]:
    """
    Calls Gemini 1.5/2.5 Flash to analyze the extracted study content and generate
    four customized revision sections: Short Summary, Detailed Summary (HTML), 
    Key Concepts (HTML), and Important Topics (HTML).

    Args:
        text: The merged raw PDF text content.

    Returns:
        Dict[str, str]: {
            "short_summary": str,
            "detailed_summary": str,
            "key_concepts": str,
            "important_topics": str
        }
    """
    logger.info("Initializing Summarization pipeline using Gemini Generative Client...")
    
    # Pre-configure empty schemas
    empty_result = {
        "short_summary": "No summary generated. Upload your study resources and check your GEMINI_API_KEY connection.",
        "detailed_summary": "<p>Waiting for study content parsing. Please ensure your Gemini credentials are configured successfully.</p>",
        "key_concepts": "<ul><li><strong>Connection Pending:</strong> Upload materials to generate key terms.</li></ul>",
        "important_topics": "<ol><li><strong>Workspace Inactive:</strong> Add learning resources to unlock study focus paths.</li></ol>"
    }

    if not text or not text.strip():
        logger.warning("Summarizer received empty text input.")
        return empty_result

    if not api_key:
        logger.error("GEMINI_API_KEY is missing! Summarizer operating in fallback error display mode.")
        return {
            "short_summary": "⚠️ [ERROR] GEMINI_API_KEY is missing. Please set the GEMINI_API_KEY environment variable locally or configure Streamlit Secrets to activate active summaries.",
            "detailed_summary": "<p style='color: #EF4444; font-weight: 700;'>⚠️ Summarization API Key Missing</p><p>Please configure your Google Gemini API key to generate detailed study guides.</p>",
            "key_concepts": "<ul><li style='color: #EF4444;'><strong>Error:</strong> Missing API credentials.</li></ul>",
            "important_topics": "<ol><li style='color: #EF4444;'><strong>Error:</strong> Missing API credentials.</li></ol>"
        }

    try:
        # Initialize the model client gracefully
        try:
            model = genai.GenerativeModel(selected_text_model)
        except Exception as model_init_err:
            logger.warning(f"Failed to initialize model '{selected_text_model}': {str(model_init_err)}. Swapping to standard fallback.")
            model = genai.GenerativeModel("gemini-2.5-flash")

        # 1. Generate Executive Short Summary
        logger.info("Generating Short Summary...")
        short_resp = model.generate_content(SHORT_SUMMARY_PROMPT.format(text=text))
        short_summary = short_resp.text.strip() if short_resp.text else "Failed to generate short summary."

        # 2. Generate Detailed Summary Notes (HTML)
        logger.info("Generating Detailed Summary...")
        det_resp = model.generate_content(DETAILED_SUMMARY_PROMPT.format(text=text))
        detailed_summary = det_resp.text.strip() if det_resp.text else "<p>Failed to generate detailed summary.</p>"

        # 3. Generate Key Concepts Bulleted Card (HTML)
        logger.info("Generating Key Concepts...")
        con_resp = model.generate_content(KEY_CONCEPTS_PROMPT.format(text=text))
        key_concepts = con_resp.text.strip() if con_resp.text else "<ul><li>Failed to extract concepts.</li></ul>"

        # 4. Generate Important Focus Topics Card (HTML)
        logger.info("Generating Focus Topics...")
        top_resp = model.generate_content(IMPORTANT_TOPICS_PROMPT.format(text=text))
        important_topics = top_resp.text.strip() if top_resp.text else "<ol><li>Failed to parse focus topics.</li></ol>"

        # Remove accidental markdown wrap if Gemini adds it (e.g. ```html ... ```)
        def clean_html(html_str: str) -> str:
            cleaned = html_str.replace("```html", "").replace("```", "").strip()
            return cleaned

        detailed_summary = clean_html(detailed_summary)
        key_concepts = clean_html(key_concepts)
        important_topics = clean_html(important_topics)

        logger.info("Successfully compiled all four study guides.")
        return {
            "short_summary": short_summary,
            "detailed_summary": detailed_summary,
            "key_concepts": key_concepts,
            "important_topics": important_topics
        }

    except Exception as e:
        logger.error(f"Critical error during summarizer pipeline: {str(e)}")
        # Graceful recovery
        return {
            "short_summary": f"⚠️ [API ERROR] Generative AI call failed: {str(e)}",
            "detailed_summary": f"<p style='color: #EF4444;'>⚠️ API Call Failed</p><p>{str(e)}</p>",
            "key_concepts": f"<ul><li style='color: #EF4444;'>Failed to extract concepts due to API exception.</li></ul>",
            "important_topics": f"<ol><li style='color: #EF4444;'>Failed to extract focus topics due to API exception.</li></ol>"
        }
