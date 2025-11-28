import streamlit as st
from src.services.rag_engine import get_chat_engine

from src.utils.models import get_available_models

def render_chat():
    st.header("💬 Assistente de IA")

    # Model selection
    available_models = get_available_models()
    if available_models:
        selected_model = st.selectbox("Escolha o Modelo:", available_models, index=0)
    else:
        selected_model = "models/gemini-pro"
        st.warning("Could not fetch models. Defaulting to gemini-pro.")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Initialize chat engine if not already done or if model changed
    if "chat_engine" not in st.session_state or st.session_state.get("current_model") != selected_model:
        with st.spinner(f"Initializing AI with {selected_model}... This might take a while for large files."):
            st.session_state.chat_engine = get_chat_engine(model_name=selected_model)
            st.session_state.current_model = selected_model

    # Chat container with fixed height for scrolling
    messages_container = st.container(height=600)

    # Display chat messages from history inside the container
    with messages_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Ask something about your data..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message in container
        with messages_container:
            st.chat_message("user").markdown(prompt)

        if st.session_state.chat_engine:
            try:
                with st.spinner("Thinking..."):
                    response = st.session_state.chat_engine.chat(prompt)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response.response})
                
                # Display assistant response in container
                with messages_container:
                    with st.chat_message("assistant"):
                        st.markdown(response.response)
            except Exception as e:
                st.error(f"Error during chat: {str(e)}")
        else:
            st.warning("Chat engine is not initialized. Check API Key.")
