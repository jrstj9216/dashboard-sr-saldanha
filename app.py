import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import gspread
from google.oauth2.service_account import Credentials
import io

# ⚙️ Configuração da página
st.set_page_config(page_title="Dashboard Sr. Saldanha", layout="wide")

# 🎨 CSS personalizado
st.markdown(
    """
    <style>
    .stApp {
        background-color: #000000;
        color: white;
    }
    h1 {
        color: white;
        text-align: center;
        font-size: 50px;
    }
    h2, h3, h4 {
        color: white;
        text-align: center;
    }
    div[data-testid="metric-container"] {
        background-color: #111;
        border-radius: 15px;
        padding: 15px;
        margin: 5px;
        border: 1px solid #333;
        color: white;
    }
    .st-emotion-cache-1d391kg {
        background-color: #111;
        color: white;
    }
    .stButton>button {
        background-color: #444;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 8px 20px;
    }
    .stButton>button:hover {
        background-color: #666;
        color: white;
    }
    .stDataFrame {
        background-color: #111;
        color: white;
    }
    ::-webkit-scrollbar {
        width: 10px;
    }
    ::-webkit-scrollbar-track {
        background: #222;
    }
    ::-webkit-scrollbar-thumb {
        background: #555;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #888;
    }
    .element-container {
        background-color: #111;
        border-radius: 15px;
        padding: 15px;
        border: 1px solid #333;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 🔐 Autenticação com Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(credentials)

# 🔗 Conectando à planilha
spreadsheet = client.open("Automacao_Barbearia")
sheet = spreadsheet.worksheet("Dados_Faturamento")

# 🚀 Função para extrair dados do PDF
def extrair_dados_pdf(uploaded_file):
    texto = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            texto += page.get_text()

    linhas = texto.split("\n")
    dados = []

    for linha in linhas:
        if "/" in linha and any(c.isdigit() for c in linha):
            partes = linha.split()
            if len(partes) >= 4:
                data = partes[0]
                faturamento = partes[1].replace(".", "").replace(",", ".")
                comandas = partes[2]
                ticket = partes[3].replace(",", ".")
                ano, mes = data.split("/")

                dados.append({
                    "Ano": ano,
                    "Mês": mes,
                    "Faturamento": float(faturamento),
                    "Comandas": int(comandas),
                    "Ticket Médio": float(ticket)
                })

    return pd.DataFrame(dados)

# 📤 Upload dos PDFs
st.sidebar.header("📑 Enviar PDFs de Faturamento")
uploaded_files = st.sidebar.file_uploader(
    "Escolha os PDFs", type="pdf", accept_multiple_files=True)

dfs = []

if uploaded_files:
    for file in uploaded_files:
        st.info(f"Lendo arquivo: {file.name}")
        df = extrair_dados_pdf(file)
        dfs.append(df)

    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)

        st.subheader("📄 Dados extraídos:")
        st.dataframe(df_final)

        # 🔄 Atualiza o Google Sheets
        if st.button("🔗 Enviar dados para Google Sheets"):
            sheet.clear()  # ⚠️ Limpa antes de atualizar
            sheet.update([df_final.columns.values.tolist()] +
                         df_final.values.tolist())
            st.success("Dados enviados para Google Sheets com sucesso!")

# 📊 Dashboard de Faturamento
st.title("💈 Sr. Saldanha | Dashboard de Faturamento")

try:
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)

    # 🧽 Tratamento
    df["Ano"] = df["Ano"].astype(str)
    df["Mês"] = df["Mês"].astype(str)

    # 🚥 KPIs principais
    st.subheader("📈 Indicadores")

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Faturamento Total",
                f'R$ {df["Faturamento"].sum():,.2f}')
    col2.metric("📋 Total de Comandas", int(df["Comandas"].sum()))
    col3.metric("🎟️ Ticket Médio",
                f'R$ {df["Ticket Médio"].mean():,.2f}')

    st.markdown("---")

    # 🎛️ Filtros
    st.sidebar.header("Filtros")
    ano = st.sidebar.selectbox("Ano", df["Ano"].unique())
    mes = st.sidebar.selectbox("Mês", df["Mês"].unique())

    df_filtrado = df[(df["Ano"] == ano) & (df["Mês"] == mes)]

    # 📈 Gráficos
    st.subheader("🚀 Evolução de Faturamento por Mês")
    graf1 = df.groupby(["Ano", "Mês"])["Faturamento"].sum().reset_index()
    st.line_chart(graf1.pivot(index="Mês",
                 columns="Ano", values="Faturamento"))

    st.subheader("📊 Ticket Médio por Mês")
    graf2 = df.groupby(["Ano", "Mês"])["Ticket Médio"].mean().reset_index()
    st.line_chart(graf2.pivot(index="Mês",
                 columns="Ano", values="Ticket Médio"))

    # 📅 Comparativo de Períodos
    st.subheader("📅 Comparativo de Períodos")

    col4, col5 = st.columns(2)
    with col4:
        ano1 = st.selectbox("Período 1 - Ano", df["Ano"].unique())
        mes1 = st.selectbox("Período 1 - Mês", df["Mês"].unique())

    with col5:
        ano2 = st.selectbox(
            "Período 2 - Ano", df["Ano"].unique(), key="ano2")
        mes2 = st.selectbox(
            "Período 2 - Mês", df["Mês"].unique(), key="mes2")

    filtro1 = (df["Ano"] == ano1) & (df["Mês"] == mes1)
    filtro2 = (df["Ano"] == ano2) & (df["Mês"] == mes2)

    fat1 = df.loc[filtro1, "Faturamento"].sum()
    fat2 = df.loc[filtro2, "Faturamento"].sum()
    dif = fat2 - fat1
    perc = (dif / fat1) * 100 if fat1 != 0 else 0

    st.write(f"**Período 1:** {mes1}/{ano1} → **R$ {fat1:,.2f}**")
    st.write(f"**Período 2:** {mes2}/{ano2} → **R$ {fat2:,.2f}**")
    st.write(
        f"**Variação:** {'🔺' if perc > 0 else '🔻'} {perc:.2f}%")

    st.markdown("---")

    # 📑 Tabela Detalhada
    st.subheader("📑 Dados Detalhados")
    st.dataframe(df)

except Exception as e:
    st.warning("Nenhum dado encontrado ou erro na conexão com o Google Sheets.")
    st.exception(e)
