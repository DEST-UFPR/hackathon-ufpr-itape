import os
import google.generativeai as genai
import streamlit as st

def get_available_models():
    api_key = os.getenv("GOOGLE_API_KEY")
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
