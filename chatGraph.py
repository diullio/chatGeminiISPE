import os
import fitz  # PyMuPDF
import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import plotly.express as px

GOOGLE_API_KEY = "SUA_KEY"
genai.configure(api_key=GOOGLE_API_KEY)

# Função para ler PDFs
def ler_pdf(uploaded_file):
    texto = ""
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    for pagina in doc:
        texto += pagina.get_text()
    return texto

# Prompt especialista em gráficos
PROMPT_GRAFICO = """
Você é um especialista em análise de dados e visualização. Ao receber documentos em texto, sua tarefa é identificar informações que possam ser representadas por gráficos. Sempre que possível, extraia e organize os dados em formato JSON estruturado, pronto para uso em bibliotecas de visualização (como Streamlit ou Plotly).

Regras:
- Sempre responda em formato JSON.
- Cada gráfico deve conter os campos: "titulo", "tipo", "dados", e "eixo_x" / "eixo_y" se aplicável.
- Tipos possíveis: "bar", "line", "pie", "scatter", "histogram", "box", "area".
- O campo "dados" deve ser um dicionário ou lista de pares chave/valor.
- Os valores devem ser extraídos diretamente dos documentos analisados ou inferidos com base em padrões claros nos textos.
- Se não houver dados suficientes para gerar um gráfico, retorne uma lista vazia: []


Exemplo de resposta JSON:

```json
[
  {
    "titulo": "Distribuição de Reclamações por Setor",
    "tipo": "bar",
    "dados": {
      "Financeiro": 15,
      "Produção": 22,
      "Qualidade": 9
    },
    "eixo_x": "Setor",
    "eixo_y": "Número de Reclamações"
  },
  {
    "titulo": "Proporção de Não Conformidades",
    "tipo": "pie",
    "dados": {
      "Crítica": 10,
      "Maior": 30,
      "Menor": 60
    }
  }
]
"""

# Inicia o chat com o contexto dos PDFs
def iniciar_chat(contexto):
    model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
    chat = model.start_chat(history=[])
    chat.send_message("Aqui estão dois documentos para análise:\n" + contexto + "\n\n" + PROMPT_GRAFICO)
    return chat

# Autenticação simples
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

# Função para exibir os gráficos JSON no Streamlit
def exibir_graficos(json_str):
    try:
        if json_str.strip().startswith("```json"):
            json_str = json_str.strip().removeprefix("```json").removesuffix("```").strip()

        graficos = json.loads(json_str)

    except json.JSONDecodeError:
        st.warning("⚠️ Resposta não é um JSON válido.")
        return

    if not graficos:
        st.info("Nenhum gráfico sugerido pela IA.")
        return

    for grafico in graficos:
        st.subheader(grafico.get("titulo", "Gráfico"))
        tipo = grafico.get("tipo", "bar")
        dados = grafico.get("dados", {})
        if isinstance(dados, dict):
            df = pd.DataFrame(list(dados.items()), columns=[grafico.get("eixo_x", "Categoria"), grafico.get("eixo_y", "Valor")])
        else:
            st.warning("Formato de dados não suportado.")
            continue

        try:
            if tipo == "bar":
                fig = px.bar(df, x=df.columns[0], y=df.columns[1])
            elif tipo == "line":
                fig = px.line(df, x=df.columns[0], y=df.columns[1])
            elif tipo == "pie":
                fig = px.pie(df, names=df.columns[0], values=df.columns[1])
            elif tipo == "scatter":
                fig = px.scatter(df, x=df.columns[0], y=df.columns[1])
            elif tipo == "area":
                fig = px.area(df, x=df.columns[0], y=df.columns[1])
            elif tipo == "histogram":
                fig = px.histogram(df, x=df.columns[0])
            elif tipo == "box":
                fig = px.box(df, y=df.columns[1])
            else:
                st.warning(f"Tipo de gráfico '{tipo}' não suportado.")
                continue

            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao gerar gráfico: {e}")

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
                st.markdown(f"**Gemini:**")
                st.code(resposta, language="json" if resposta.strip().startswith("[") else "markdown")

                # Se parecer um JSON com gráficos, tenta renderizar
                if resposta:
                    exibir_graficos(resposta)
    else:
        st.info("Faça upload de dois arquivos PDF para começar.")

# Lógica principal
if 'logado' not in st.session_state:
    st.session_state.logado = False

if st.session_state.logado:
    mostrar_app()
else:
    mostrar_login()
