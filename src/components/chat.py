import streamlit as st
from src.services.rag_engine import get_chat_engine

def render_chat():
    st.header("💬 Assistente de IA")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Initialize chat engine if not already done
    if "chat_engine" not in st.session_state:
        with st.spinner("Initializing AI..."):
            st.session_state.chat_engine = get_chat_engine()

    # Chat container with fixed height for scrolling
    # Reduced height slightly to fit better on smaller screens
    messages_container = st.container(height=500)

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
