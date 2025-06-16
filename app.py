import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import gspread
from google.oauth2.service_account import Credentials
import io

# ⚙️ Configuração da página (PRIMEIRA LINHA SEMPRE)
st.set_page_config(
    page_title="Dashboard Sr. Saldanha",
    layout="wide",
    page_icon="💈"
)

# 🌑 Estilo Dark
st.markdown(
    """
    <style>
    body {
        background-color: #000000;
        color: white;
    }
    .stApp {
        background-color: #000000;
    }
    div[data-testid="stMetricValue"] {
        color: white;
        font-size: 40px;
    }
    .css-1d391kg {
        background-color: #111111;
    }
    </style>
    """,
    unsafe_allow_html=True,
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
    "Escolha os PDFs", type="pdf", accept_multiple_files=True
)

dfs = []

if uploaded_files:
    for file in uploaded_files:
        st.info(f"📥 Lendo arquivo: {file.name}")
        df = extrair_dados_pdf(file)
        dfs.append(df)

    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)

        st.subheader("📄 Dados extraídos:")
        st.dataframe(df_final)

        if st.button("🔗 Enviar dados para Google Sheets"):
            sheet.clear()
            sheet.update([df_final.columns.values.tolist()] + df_final.values.tolist())
            st.success("✅ Dados enviados para Google Sheets com sucesso!")

# 🎯 Dashboard Principal
st.markdown("<h1 style='text-align: center;'>💈 Dados de Faturamento</h1>", unsafe_allow_html=True)

try:
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)

    df["Ano"] = df["Ano"].astype(str)
    df["Mês"] = df["Mês"].astype(str)

    # 🚥 KPIs principais
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Faturamento", f'{df["Faturamento"].sum():,.0f}'.replace(",", "."))
    col2.metric("🧾 Comandas", f'{int(df["Comandas"].sum()):,}'.replace(",", "."))
    col3.metric("🎟️ Ticket Médio", f'{df["Ticket Médio"].mean():,.0f}'.replace(",", "."))

    st.markdown("---")

    # 🎛️ Filtros
    colA, colB, colC = st.columns([1, 1, 2])
    with colA:
        ano = st.selectbox("Ano", sorted(df["Ano"].unique()))
    with colB:
        mes = st.selectbox("Mês", sorted(df["Mês"].unique()))
    with colC:
        st.write("")

    df_filtrado = df[(df["Ano"] == ano) & (df["Mês"] == mes)]

    # 📈 Gráfico Faturamento
    st.subheader("📈 Faturamento por Mês")
    graf1 = df.groupby(["Ano", "Mês"])["Faturamento"].sum().reset_index()
    graf1 = graf1.sort_values(by="Mês")
    st.line_chart(graf1.pivot(index="Mês", columns="Ano", values="Faturamento"))

    # 📊 Gráfico Ticket Médio
    st.subheader("📊 Ticket Médio por Mês")
    graf2 = df.groupby(["Ano", "Mês"])["Ticket Médio"].mean().reset_index()
    graf2 = graf2.sort_values(by="Mês")
    st.line_chart(graf2.pivot(index="Mês", columns="Ano", values="Ticket Médio"))

    st.markdown("---")

    # 📅 Comparativo
    st.subheader("📅 Comparativo de Períodos")

    col4, col5 = st.columns(2)
    with col4:
        ano1 = st.selectbox("Período 1 - Ano", df["Ano"].unique())
        mes1 = st.selectbox("Período 1 - Mês", df["Mês"].unique())

    with col5:
        ano2 = st.selectbox("Período 2 - Ano", df["Ano"].unique(), key="ano2")
        mes2 = st.selectbox("Período 2 - Mês", df["Mês"].unique(), key="mes2")

    filtro1 = (df["Ano"] == ano1) & (df["Mês"] == mes1)
    filtro2 = (df["Ano"] == ano2) & (df["Mês"] == mes2)

    fat1 = df.loc[filtro1, "Faturamento"].sum()
    fat2 = df.loc[filtro2, "Faturamento"].sum()
    dif = fat2 - fat1
    perc = (dif / fat1) * 100 if fat1 != 0 else 0

    col6, col7 = st.columns(2)
    col6.metric(f"Período {mes1}/{ano1}", f'R$ {fat1:,.0f}'.replace(",", "."), f"{perc:.2f}%")
    col7.metric(f"Período {mes2}/{ano2}", f'R$ {fat2:,.0f}'.replace(",", "."), f"{perc:.2f}%")

    st.markdown("---")

    # 🗒️ Tabela Detalhada
    st.subheader("📑 Dados Detalhados")
    st.dataframe(df)

except Exception as e:
    st.warning("Nenhum dado encontrado ou erro na conexão com o Google Sheets.")
    st.exception(e)
