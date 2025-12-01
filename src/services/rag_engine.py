import os
import shutil
import streamlit as st
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

@st.cache_resource(show_spinner=False)
def get_index():
    from llama_index.core import Document, VectorStoreIndex, StorageContext, load_index_from_storage, SimpleDirectoryReader
    import pandas as pd
    import gc
    
    STORAGE_DIR = "./storage"
    DATA_DIR = "data"

    if not os.path.exists(DATA_DIR) or not os.listdir(DATA_DIR):
        return None

    if os.path.exists(STORAGE_DIR):
        try:
            storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
            index = load_index_from_storage(storage_context)
            gc.collect() 
            return index
        except Exception as e:
            st.warning(f"Failed to load from storage: {e}. Re-indexing...")
            if os.path.exists(STORAGE_DIR):
                shutil.rmtree(STORAGE_DIR)
        
    index = VectorStoreIndex([])
    
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(('.xlsx', '.xls', '.csv', '.pdf'))]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, file in enumerate(files):
        file_path = os.path.join(DATA_DIR, file)
        status_text.text(f"Processing {file}...")
        try:
            documents = []
            if file.endswith('.csv'):
                try:
                    df = pd.read_csv(file_path, sep=None, engine='python', dtype=str)
                except:
                    df = pd.read_csv(file_path, sep=';', dtype=str)
            
                df.columns = df.columns.str.replace('\ufeff', '').str.strip()
                df = df.fillna("")
                
                text = df.to_csv(index=False)
                documents = [Document(text=text, metadata={"filename": file})]
                
                del df
                gc.collect()
            else:
                documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
                for d in documents:
                    d.metadata["filename"] = file

            nodes = Settings.node_parser.get_nodes_from_documents(documents)
            
            index.insert_nodes(nodes)
            
            del documents
            del nodes
            gc.collect()
            
        except Exception as e:
            st.error(f"Error reading {file}: {e}")
        
        progress_bar.progress((i + 1) / len(files))
    
    status_text.text("Persisting index...")
    index.storage_context.persist(persist_dir=STORAGE_DIR)
    
    status_text.empty()
    progress_bar.empty()
    gc.collect()
    
    return index

def get_chat_engine():
    """
    Initializes and returns the chat engine using Gemini.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("GOOGLE_API_KEY not found in environment variables. Please set it in .env file.")
        return None

    try:
        Settings.llm = GoogleGenAI(api_key=api_key, model_name="models/gemini-2.5-flash")
        Settings.embed_model = GoogleGenAIEmbedding(api_key=api_key, model_name="models/text-embedding-004")

        index = get_index()
        
        if index is None:
             st.warning("Data directory is empty. Please add documents to 'data/' for RAG.")
             return None
        
        system_prompt = (
            "You are an AI assistant for analyzing UFPR data. "
            "You must ONLY answer questions based on the provided context from the documents. "
            "If the answer is not in the documents, state clearly that you do not know based on the available data. "
            "Do not hallucinate or use outside knowledge."
            "Do not quote the PDF or the CVS files directly when answering. But use it to generate the answer based on the csv, xlsx, xls files."
            "Always answer in portuguese brazil."
            "Always check all files you have acess before answer"
        )

        return index.as_chat_engine(
            chat_mode="condense_plus_context", 
            verbose=True,
            system_prompt=system_prompt
        )
    except Exception as e:
        st.error(f"Error initializing RAG engine: {str(e)}")
        return None
