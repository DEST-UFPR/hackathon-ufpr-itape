import os
import streamlit as st
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding

@st.cache_resource(show_spinner="Loading and indexing data...")
def get_index():
    """
    Loads data and creates the VectorStoreIndex. Cached to avoid reloading on every run.
    Persists the index to disk to speed up future runs.
    """
    from llama_index.core import Document, VectorStoreIndex, StorageContext, load_index_from_storage
    import pandas as pd
    
    STORAGE_DIR = "./storage"
    DATA_DIR = "data"

    if not os.path.exists(DATA_DIR) or not os.listdir(DATA_DIR):
        return None

    # Check if storage already exists
    if os.path.exists(STORAGE_DIR):
        try:
            storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
            index = load_index_from_storage(storage_context)
            return index
        except Exception as e:
            st.warning(f"Failed to load from storage: {e}. Re-indexing...")
    
    # If not, create new index
    st.info("Creating new index (this may take a while)...")
    
    documents = []
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(('.xlsx', '.xls', '.csv'))]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, file in enumerate(files):
        file_path = os.path.join(DATA_DIR, file)
        status_text.text(f"Processing {file}...")
        try:
            if file.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Convert DataFrame to string representation for the LLM
            # We use to_string() or to_json() or just iterate. 
            # A simple way is to convert each row to a text chunk, or the whole df if small.
            # For RAG, row-based or chunk-based is usually better.
            # Let's try converting the whole dataframe to a text summary first if it's "small".
            # Or better: "Column: Value, Column: Value..." format for each row.
            
            text_content = df.to_string(index=False)
            doc = Document(text=text_content, metadata={"filename": file})
            documents.append(doc)
            
        except Exception as e:
            st.error(f"Error reading {file}: {e}")
        
        progress_bar.progress((i + 1) / len(files))
    
    status_text.text("Generating Embeddings and Index...")
    index = VectorStoreIndex.from_documents(documents)
    
    # Persist to disk
    index.storage_context.persist(persist_dir=STORAGE_DIR)
    status_text.empty()
    progress_bar.empty()
    
    return index

def get_chat_engine(model_name="models/gemini-pro"):
    """
    Initializes and returns the chat engine using Gemini.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("GOOGLE_API_KEY not found in environment variables. Please set it in .env file.")
        return None

    try:
        # Configure Gemini
        Settings.llm = Gemini(api_key=api_key, model_name=model_name)
        Settings.embed_model = GeminiEmbedding(api_key=api_key, model_name="models/text-embedding-004")

        index = get_index()
        
        if index is None:
             st.warning("Data directory is empty. Please add documents to 'data/' for RAG.")
             return None
        
        # Use condense_plus_context mode for better handling of follow-up questions and context
        return index.as_chat_engine(chat_mode="condense_plus_context", verbose=True)
    except Exception as e:
        st.error(f"Error initializing RAG engine: {str(e)}")
        return None
