import os
import logging
import streamlit as st
import google.generativeai as genai

logger = logging.getLogger(__name__)

# --- 1. SDK VERSION CHECK (Task 1) ---
SDK_VERSION = getattr(genai, "__version__", "0.8.6")

# --- 2. AUTHENTICATION KEY CHECK (Task 4) ---
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

# Configure client SDK globally
if api_key:
    try:
        genai.configure(api_key=api_key)
    except Exception as configure_err:
        logger.error(f"Error configuring Google Generative AI SDK: {str(configure_err)}")

# --- 3. DYNAMIC MODEL SELECTION & FALLBACKS (Task 2, 3, 6) ---
DEFAULT_TEXT_MODEL = "gemini-2.5-flash"
DEFAULT_EMBED_MODEL = "models/gemini-embedding-001"

# Ordered preference list of active text models
SUPPORTED_TEXT_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-3.5-flash",
    "gemini-flash-latest",
    "gemini-pro-latest"
]

def validate_and_select_models() -> tuple[str, str, list[str]]:
    """
    Scans the API endpoint to select the best available supported model.
    Implements graceful fallback error handlers if model names are invalid or deprecated.

    Returns:
        tuple[str, str, list[str]]: (selected_text_model, selected_embed_model, all_available_models)
    """
    selected_text = DEFAULT_TEXT_MODEL
    selected_embed = DEFAULT_EMBED_MODEL
    all_available = []

    if not api_key:
        logger.warning("Generative AI Key is missing. Using local defaults.")
        return selected_text, selected_embed, ["(API Key Missing - Defaults Active)"]

    try:
        # Fetch actual model listings from Google Generative AI API
        models_list = list(genai.list_models())
        all_available = [m.name for m in models_list]

        # Verify Text Model presence (Task 6)
        prefixed_default = f"models/{DEFAULT_TEXT_MODEL}"
        if prefixed_default in all_available:
            selected_text = DEFAULT_TEXT_MODEL
        else:
            # Loop through text preference list
            matched = False
            for text_candidate in SUPPORTED_TEXT_MODELS:
                if f"models/{text_candidate}" in all_available:
                    selected_text = text_candidate
                    matched = True
                    logger.info(f"Target model deprecated. Gracefully swiped to candidate: '{text_candidate}'")
                    break

            if not matched:
                # Find any available model with 'flash' in its name that isn't an embedding
                flash_candidates = [
                    m.replace("models/", "") 
                    for m in all_available 
                    if "flash" in m and "embedding" not in m
                ]
                if flash_candidates:
                    selected_text = flash_candidates[0]
                    logger.warning(f"Using auto-selected flash model fallback: '{selected_text}'")
                else:
                    selected_text = "gemini-flash-latest"

        # Verify Embedding Model presence
        if "models/gemini-embedding-001" in all_available:
            selected_embed = "models/gemini-embedding-001"
        elif "models/gemini-embedding-2" in all_available:
            selected_embed = "models/gemini-embedding-2"
        else:
            # Fallback to any model with 'embedding' in its identifier
            embedding_candidates = [m for m in all_available if "embedding" in m]
            if embedding_candidates:
                selected_embed = embedding_candidates[0]
                logger.info(f"Using custom embedding fallback: '{selected_embed}'")

    except Exception as api_err:
        logger.error(f"Failed to query generative models from Google endpoint: {str(api_err)}")
        # Default back to standard pointer configs
        selected_text = DEFAULT_TEXT_MODEL
        selected_embed = DEFAULT_EMBED_MODEL

    return selected_text, selected_embed, all_available

# --- 4. EXPORT AND RUN STARTUP VALIDATION LOG (Task 5) ---
selected_text_model, selected_embed_model, available_models = validate_and_select_models()

print("=" * 60)
print("             LOCKED GEMINI SDK CONFIGURATION REPORT")
print("=" * 60)
print(f"SDK Version:         {SDK_VERSION}")
print(f"API Key Present:     {api_key is not None}")
print(f"Selected Text Model: {selected_text_model}")
print(f"Selected Embed Model:{selected_embed_model}")
print("Available Gemini Endpoint Models:")
if available_models:
    for m in available_models[:12]:
        print(f"  - {m}")
    if len(available_models) > 12:
        print(f"  ... and {len(available_models) - 12} other models.")
else:
    print("  - None")
print("=" * 60)
