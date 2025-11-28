import os
import google.generativeai as genai
import streamlit as st

def get_available_models():
    """
    Fetches available Gemini models that support content generation.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return []

    try:
        genai.configure(api_key=api_key)
        models = []
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                # Filter for models that are likely free/standard (optional, but requested to keep in mind)
                # For now, we list all content generation models as requested by the user's snippet logic.
                models.append(m.name)
        return models
    except Exception as e:
        st.error(f"Error fetching models: {str(e)}")
        return []
