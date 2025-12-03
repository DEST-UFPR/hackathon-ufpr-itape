import os
import google.generativeai as genai
import streamlit as st

from src.utils.key_manager import get_decrypted_key

def get_available_models():
    api_key = get_decrypted_key()
    if not api_key:
        return []

    try:
        genai.configure(api_key=api_key)
        models = []
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                models.append(m.name)
        return models
    except Exception as e:
        st.error(f"Error fetching models: {str(e)}")
        return []
