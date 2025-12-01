import os
import shutil
import time
import pandas as pd
from dotenv import load_dotenv
from llama_index.core import Document, VectorStoreIndex, Settings, StorageContext
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

# Load environment variables
load_dotenv()

def generate_index_terminal():
    print("🚀 Starting Index Generation Process...")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY not found in environment variables.")
        return

    # Configure Settings
    Settings.llm = GoogleGenAI(api_key=api_key, model_name="models/gemini-2.5-flash")
    Settings.embed_model = GoogleGenAIEmbedding(api_key=api_key, model_name="models/text-embedding-004")

    STORAGE_DIR = "./storage"
    DATA_DIR = "data"

    if not os.path.exists(DATA_DIR) or not os.listdir(DATA_DIR):
        print("❌ Error: Data directory is empty or does not exist.")
        return

    # Clean existing storage if it exists to ensure a fresh start
    if os.path.exists(STORAGE_DIR):
        print(f"🧹 Removing existing storage at {STORAGE_DIR}...")
        shutil.rmtree(STORAGE_DIR)

    documents = []
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(('.xlsx', '.xls', '.csv', '.pdf'))]
    
    print(f"📂 Found {len(files)} files to process.")

    for i, file in enumerate(files):
        file_path = os.path.join(DATA_DIR, file)
        print(f"   📄 Processing {file} ({i+1}/{len(files)})...")
        try:
            if file.endswith('.csv'):
                try:
                    df = pd.read_csv(file_path, sep=None, engine='python', dtype=str)
                except:
                    df = pd.read_csv(file_path, sep=';', dtype=str)
            
                # Clean column names
                df.columns = df.columns.str.replace('\ufeff', '').str.strip()
                
                # Fill NaNs
                df = df.fillna("")
                df = df.astype(str)

                # Use CSV format for denser representation
                text = df.to_csv(index=False)
                file_docs = [Document(text=text, metadata={"filename": file})]
            else:
                from llama_index.core import SimpleDirectoryReader
                file_docs = SimpleDirectoryReader(input_files=[file_path]).load_data()
                for d in file_docs:
                    d.metadata["filename"] = file

            documents.extend(file_docs)
            
        except Exception as e:
            print(f"   ❌ Error reading {file}: {e}")

    print("🧩 Parsing documents into nodes...")
    nodes = Settings.node_parser.get_nodes_from_documents(documents)
    print(f"   ✅ Created {len(nodes)} nodes.")
    
    print("🧠 Generating Embeddings and Indexing...")
    
    # Create the index
    # We use a large batch size to speed up processing
    # show_progress=True uses tqdm automatically if available
    index = VectorStoreIndex(
        nodes, 
        show_progress=True,
    )
    
    print("💾 Persisting index to storage...")
    index.storage_context.persist(persist_dir=STORAGE_DIR)
    
    print("🎉 Index generation complete! Storage saved to ./storage")

if __name__ == "__main__":
    generate_index_terminal()
