import os
import logging
import json
from typing import Dict, Any
import google.generativeai as genai
from utils.gemini_config import api_key, selected_text_model
from prompts.templates import QUIZ_GENERATOR_PROMPT

logger = logging.getLogger(__name__)

# Standard fallback quiz schema if API key is missing or parsing fails
FALLBACK_QUIZ = {
    "mcqs": [
        {
            "question": "What does the gradient vector mathematically represent in optimization landscapes?",
            "options": [
                "A) The direction of absolute steepest descent.",
                "B) The direction of absolute steepest ascent.",
                "C) A static scalar bias parameter.",
                "D) The learning rate scaling threshold."
            ],
            "correct_key": "B",
            "explanation": "The gradient vector points in the direction of steepest ascent. Subtracted gradients move weights in the steepest descent direction."
        },
        {
            "question": "Why is Stochastic Gradient Descent (SGD) noisy compared to batch gradient descent?",
            "options": [
                "A) It uses multiple GPU hardware threads simultaneously.",
                "B) It utilizes only a single random dataset sample per update.",
                "C) It completely eliminates the learning rate scalar.",
                "D) It locks the optimization landscape dimensions."
            ],
            "correct_key": "B",
            "explanation": "Because SGD calculates slopes on individual randomized samples instead of compiling the entire dataset, updates fluctuate jumps, which helps escape saddle zones."
        },
        {
            "question": "Which optimizer utilizes running momentum values alongside RMSProp adaptive weights updates?",
            "options": [
                "A) Vanilla Gradient Descent.",
                "B) SGD with zero momentum.",
                "C) Adam Optimizer.",
                "D) Exponential decay optimizer."
            ],
            "correct_key": "C",
            "explanation": "The Adam optimizer tracks both the first raw momentum gradients (mean) and the second raw square gradients (variance) to dynamically adjust parameters epoch-by-epoch."
        }
    ],
    "interview_questions": [
        {
            "question": "Explain how backpropagation uses gradients.",
            "answer": "Backpropagation applies the calculus chain rule backwards from the network loss nodes, calculating gradients per parameter layer to update weights and resolve structural losses."
        },
        {
            "question": "Why are saddle points problematic in massive deep learning models?",
            "options": [],
            "answer": "In multi-million dimensional weight landscapes, parameters trap regions are typically flat valleys of zero slope (saddle points) where vanilla updates vanish, rather than local minima."
        },
        {
            "question": "What is the role of a learning rate scheduler?",
            "options": [],
            "answer": "A learning rate decay scheduler dynamically decreases steps size (e.g., using cosine annealing or steps-decay) in later epochs, stabilizing convergence and preventing validation divergence."
        }
    ],
    "revision_cards": [
        {
            "title": "Learning Rate Calibration",
            "content": "A high learning rate causes divergence (overshooting valleys), while an under-calibrated rate results in extremely slow optimization loops."
        },
        {
            "title": "Adam Optimizer Momentum",
            "content": "Adam couples momentum velocities and variance-based adaptive scaling, resolving structural saddle point barriers."
        }
    ]
}

def generate_quiz(text: str) -> Dict[str, Any]:
    """
    Calls Gemini 1.5 Flash to generate a structured JSON quiz matching the student's
    uploaded content, parsing it into MCQs, interview expanders, and revision tags.

    Args:
        text: The merged raw PDF text content.

    Returns:
        Dict[str, Any]: A quiz structure:
            {
                "mcqs": [...],
                "interview_questions": [...],
                "revision_cards": [...]
            }
    """
    logger.info("Initializing Quiz Generation pipeline using Gemini 1.5 Flash...")
    
    if not text or not text.strip():
        logger.warning("Quiz generator received empty text input. Returning fallback quiz.")
        return FALLBACK_QUIZ

    if not api_key:
        logger.error("GEMINI_API_KEY is missing! Returning pre-packaged high-fidelity quiz dataset.")
        return FALLBACK_QUIZ

    try:
        # Initialize generative client gracefully
        try:
            model = genai.GenerativeModel(selected_text_model)
        except Exception as model_init_err:
            logger.warning(f"Failed to initialize model '{selected_text_model}': {str(model_init_err)}. Swapping to standard fallback.")
            model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Request a clean JSON response
        logger.info("Calling Gemini 1.5 Flash API for structured Quiz dataset...")
        response = model.generate_content(
            QUIZ_GENERATOR_PROMPT.format(text=text),
            generation_config={"response_mime_type": "application/json"}
        )
        
        raw_text = response.text.strip() if response.text else ""
        
        if not raw_text:
            logger.warning("API returned empty quiz content. Falling back to default quiz.")
            return FALLBACK_QUIZ

        # Parse JSON
        quiz_data = json.loads(raw_text)
        
        # Verify JSON keys presence
        required_keys = ["mcqs", "interview_questions", "revision_cards"]
        if all(key in quiz_data for key in required_keys):
            logger.info("Successfully generated and parsed dynamic quiz dataset!")
            return quiz_data
        else:
            logger.warning(f"Generated JSON was missing keys. Keys found: {list(quiz_data.keys())}. Swapping to fallback.")
            return FALLBACK_QUIZ

    except Exception as e:
        logger.error(f"Failed to compile dynamic Quiz from PDF text: {str(e)}. Falling back to standard dataset.")
        return FALLBACK_QUIZ
