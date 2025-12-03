import streamlit as st
from src.components.dashboard import render_dashboard
from src.components.chat import render_chat
from dotenv import load_dotenv
import os

load_dotenv()

def check_password():
    if st.session_state.get("password_correct", False):
        return True


    with st.form("login_form"):
        st.text_input("Usuário", key="username")
        st.text_input("Senha", type="password", key="password")
        submitted = st.form_submit_button("Login")

    if submitted:

        username = st.session_state.get("username", "").strip()
        password = st.session_state.get("password", "").strip()
        
        if username == "admin" and password == "itape-ufpr":
            st.session_state["password_correct"] = True

            if "username" in st.session_state: del st.session_state["username"]
            if "password" in st.session_state: del st.session_state["password"]
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos")
            
    return False

def main():
    st.set_page_config(
        page_title="Hackathon Dados UFPR 2025 - Equipe ITAPE",
        page_icon="📊",
        layout="wide"
    )

    if os.getenv("prod") == "true":
        if not check_password():
            st.stop()

    col1, col2 = st.columns([2, 1])

    with col1:
        render_dashboard()

    with col2:
        render_chat()

if __name__ == "__main__":
    main()
