import streamlit as st
import os
import asyncio
import nest_asyncio
import inspect
from src.services.rag_engine import get_chat_engine

nest_asyncio.apply()

async def run_agent_query(agent, prompt):
    """Executa o agente e lida com respostas síncronas ou assíncronas."""
    if hasattr(agent, "chat"):
        return agent.chat(prompt)
    
    response = await agent.run(user_msg=prompt)
    
    if inspect.isawaitable(response):
        return await response
    
    return response

def run_async(coro):
    """Helper para rodar corotinas em ambiente síncrono/Streamlit."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

def render_chat():
    st.header("Assistente de IA")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    chat_engine = None
    with st.spinner("Preparando assistente..."):
        try:
            chat_engine = get_chat_engine()
        except Exception as e:
            st.error(f"Erro ao inicializar: {str(e)}")

    messages_container = st.container(height=600)

    with messages_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    prompt = st.chat_input("Pergunte sobre os dados da avaliação...")
    
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with messages_container:
            st.chat_message("user").markdown(prompt)

        if chat_engine:
            with messages_container:
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""
                    
                    try:
                        context_msg = ""
                        if "active_tab_context" in st.session_state:
                            context = st.session_state['active_tab_context']
                            if len(context) > 8000:
                                context = context[:8000] + "\n\n[Contexto truncado devido ao tamanho...]"
                            context_msg = f"\n\n--- CONTEXTO DA TELA ATUAL (use se relevante) ---\n{context}\n-----------------------------------------\n\n"
                        
                        final_prompt = f"{context_msg}Pergunta do usuário: {prompt}"
                        
                        with st.spinner("Analisando e escolhendo ferramentas..."):
                            try:
                                response = run_async(run_agent_query(chat_engine, final_prompt))
                            except Exception as e:
                                from src.utils.key_manager import get_decrypted_key
                                api_key_2 = get_decrypted_key("APP_SECRET_TOKEN_2", "GOOGLE_API_KEY_2")
                                if api_key_2:
                                    try:
                                        new_chat_engine = get_chat_engine(api_key=api_key_2)
                                        if new_chat_engine:
                                            response = run_async(run_agent_query(new_chat_engine, final_prompt))
                                        else:
                                            raise e
                                    except Exception:
                                        raise e
                                else:
                                    raise e
                        
                        if response is None or str(response).strip() == "":
                            raise ValueError("O modelo retornou uma resposta vazia. Tente reformular sua pergunta.")
                        
                        full_response = str(response)
                        
                        # Remove artefato "undefined" que as vezes aparece
                        full_response = full_response.replace("```\nundefined\n```", "").replace("```undefined\n```", "")
                        
                        message_placeholder.markdown(full_response)
                        
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": full_response
                        })
                        
                    except Exception as e:
                        error_msg = f"Erro ao processar pergunta: {str(e)}"
                        message_placeholder.error(error_msg)
                        
                        st.info("""
                        **Dicas:**
                        - Para cálculos, seja específico: "média de X", "total de Y"
                        - Para rankings, especifique número: "top 10", "5 piores"
                        - Para conceitos, use: "o que é", "explique", "como funciona"
                        """)
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })
        else:
            with messages_container:
                st.error("IA não inicializada. Verifique a chave de API no .env")
    
    if st.session_state.messages:
        if st.button("Limpar conversa", type="secondary"):
            st.session_state.messages = []
            st.rerun()
