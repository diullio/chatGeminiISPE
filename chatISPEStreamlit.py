import os
import fitz  # PyMuPDF
import streamlit as st
import google.generativeai as genai

GOOGLE_API_KEY="AIzaSyDbBCLmLG1pKnOI5FxA0IW_RduD0dbu3XY"

# Configurar API Key
genai.configure(api_key=GOOGLE_API_KEY)

def ler_pdf(uploaded_file):
    texto = ""
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    for pagina in doc:
        texto += pagina.get_text()
    return texto

def iniciar_chat(contexto):
    model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
    chat = model.start_chat(history=[])
    chat.send_message("Aqui estão dois documentos para análise:\n" + contexto)
    return chat

def autenticar(usuario, senha):
    return usuario == "admin" and senha == "1234"

# Interface de login
def mostrar_login():
    st.title("🔐 Login")
    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")
        if submit:
            if autenticar(usuario, senha):
                st.session_state.logado = True
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
                
# Interface principal do app
def mostrar_app():
    st.set_page_config(page_title="Chat com PDFs (Gemini)", layout="wide")
    st.title("📄 Chat com seus PDFs usando Gemini 2.5")

    pdf1 = st.file_uploader("Selecione o primeiro PDF", type="pdf")
    pdf2 = st.file_uploader("Selecione o segundo PDF", type="pdf")

    if pdf1 and pdf2:
        if 'chat' not in st.session_state:
            with st.spinner("Lendo PDFs e inicializando IA..."):
                texto1 = ler_pdf(pdf1)
                texto2 = ler_pdf(pdf2)
                contexto = f"Documento 1:\n{texto1}\n\nDocumento 2:\n{texto2}"
                st.session_state.chat = iniciar_chat(contexto)
                st.session_state.historico = []

        pergunta = st.text_input("Digite sua pergunta:", key="pergunta_input")
        if st.button("Enviar"):
            if pergunta.strip():
                with st.spinner("Aguarde..."):
                    resposta = st.session_state.chat.send_message(pergunta)
                    st.session_state.historico.append((pergunta, resposta.text))

        if st.session_state.get("historico"):
            st.subheader("🧠 Conversa")
            for pergunta, resposta in reversed(st.session_state.historico):
                st.markdown(f"**Você:** {pergunta}")
                st.markdown(f"**Gemini:** {resposta}")
    else:
        st.info("Faça upload de dois arquivos PDF para começar.")

# Lógica principal
if 'logado' not in st.session_state:
    st.session_state.logado = False

if st.session_state.logado:
    mostrar_app()
else:
    mostrar_login()