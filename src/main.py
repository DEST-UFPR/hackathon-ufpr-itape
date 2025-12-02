import streamlit as st
from src.components.dashboard import render_dashboard
from src.components.chat import render_chat
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_password():

    def password_entered():
        if st.session_state["username"] == "admin" and st.session_state["password"] == "admin":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Usuário", key="username")
        st.text_input("Senha", type="password", on_change=password_entered, key="password")
        st.button("Login", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Usuário", key="username")
        st.text_input("Senha", type="password", on_change=password_entered, key="password")
        st.button("Login", on_click=password_entered)
        st.error("Usuário ou senha incorretos")
        return False
    else:
        return True

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
