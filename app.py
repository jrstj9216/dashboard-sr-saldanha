import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Dashboard Sr. Saldanha", layout="wide")

# 🔐 Autenticação com Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(credentials)
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
uploaded_files = st.sidebar.file_uploader("Escolha os PDFs", type="pdf", accept_multiple_files=True)

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

        if st.button("🔗 Enviar dados para Google Sheets"):
            sheet.clear()
            sheet.update([df_final.columns.values.tolist()] + df_final.values.tolist())
            st.success("Dados enviados para Google Sheets com sucesso!")

# ===========================
# 📊 Dashboard de Faturamento
# ===========================

st.title("💈 Sr. Saldanha | Dashboard de Faturamento")

try:
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)

    df["Ano"] = df["Ano"].astype(str)
    df["Mês"] = df["Mês"].astype(str)

    # 🎯 Filtros ESPECÍFICOS para os Indicadores
    st.sidebar.header("🎯 Filtros dos Indicadores")
    ano_indicador = st.sidebar.selectbox("Ano", sorted(df["Ano"].unique()), index=0)
    mes_indicador = st.sidebar.selectbox("Mês", sorted(df["Mês"].unique()), index=0)

    df_indicador = df[(df["Ano"] == ano_indicador) & (df["Mês"] == mes_indicador)]

    # 🚥 Indicadores Filtrados
    st.subheader("📈 Indicadores")

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Faturamento", f'R$ {df_indicador["Faturamento"].sum():,.2f}')
    col2.metric("📋 Comandas", int(df_indicador["Comandas"].sum()))
    col3.metric("🎟️ Ticket Médio", f'R$ {df_indicador["Ticket Médio"].mean():,.2f}')

    st.markdown("---")

    # 🔥 Gráficos continuam sem filtro de mês/ano
    st.subheader("🚀 Evolução de Faturamento por Mês")
    graf1 = df.groupby(["Ano", "Mês"])["Faturamento"].sum().reset_index()
    st.line_chart(graf1.pivot(index="Mês", columns="Ano", values="Faturamento"))

    st.subheader("📊 Ticket Médio por Mês")
    graf2 = df.groupby(["Ano", "Mês"])["Ticket Médio"].mean().reset_index()
    st.line_chart(graf2.pivot(index="Mês", columns="Ano", values="Ticket Médio"))

    st.markdown("---")

    # 📑 Dados Detalhados (Todos)
    st.subheader("📑 Dados Detalhados")
    st.dataframe(df)

except Exception as e:
    st.warning("⚠️ Nenhum dado encontrado ou erro na conexão com o Google Sheets.")
    st.exception(e)
