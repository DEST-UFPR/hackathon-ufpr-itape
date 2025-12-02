
import os
from llama_index.llms.google_genai import GoogleGenAI
from dotenv import load_dotenv

load_dotenv()

def test_llm_connection():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("GOOGLE_API_KEY not found.")
        return

    print(f"Testing model: models/gemini-2.5-flash-live")
    try:
        llm = GoogleGenAI(api_key=api_key, model_name="models/gemini-2.5-flash-live")
        response = llm.complete("Hello, are you working?")
        print(f"Response received: {response}")
    except Exception as e:
        print(f"Error connecting to LLM: {e}")

if __name__ == "__main__":
    test_llm_connection()
