import streamlit as st
from src.services.rag_engine import get_chat_engine

def render_chat():
    st.header("Assistente de IA")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "chat_engine" not in st.session_state:
        with st.spinner("Inicializando IA..."):
            st.session_state.chat_engine = get_chat_engine()

    messages_container = st.container(height=500)

    with messages_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Pergunte sobre o dados..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with messages_container:
            st.chat_message("user").markdown(prompt)

        if st.session_state.chat_engine:
            with messages_container:
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""
                    try:
                        # Inject context if available
                        context_msg = ""
                        if "active_tab_context" in st.session_state:
                            context_msg = f"\n\n--- Contexto da Tela Atual ---\n{st.session_state['active_tab_context']}\n------------------------------\n\n"
                        
                        # We send the prompt combined with context to the engine, 
                        # but we only show the original prompt to the user (already done above).
                        # Ideally, we should not pollute the history with the context every time if it's huge,
                        # but for this simple implementation, it ensures the model sees it.
                        
                        final_prompt = f"{context_msg}{prompt}"
                        
                        with st.spinner("Thinking..."):
                            response = st.session_state.chat_engine.stream_chat(final_prompt)
                        
                        for token in response.response_gen:
                            full_response += token
                            message_placeholder.markdown(full_response + "▌")
                        
                        message_placeholder.markdown(full_response)
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                        
                    except Exception as e:
                        message_placeholder.error(f"Error during chat: {str(e)}")
        else:
            st.warning("IA não inicializada, checar chave de API")
