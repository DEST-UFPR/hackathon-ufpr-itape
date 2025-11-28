import streamlit as st
from src.components.dashboard import render_dashboard
from src.components.chat import render_chat
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    st.set_page_config(
        page_title="Data Dashboard & Chat",
        page_icon="📈",
        layout="wide"
    )

    st.sidebar.title("Navigation")
    # For now, we can just have a simple layout where both are visible, 
    # or use the sidebar to toggle, but the request asked for "dashboard and on the right side a chat".
    # So we will use columns.

    col1, col2 = st.columns([2, 1])

    with col1:
        render_dashboard()

    with col2:
        render_chat()

if __name__ == "__main__":
    main()
