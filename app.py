import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import gspread
from google.oauth2.service_account import Credentials

# 🎯 Autenticação com Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope)

client = gspread.authorize(credentials)

# 🔗 Conectando ao Google Sheets
spreadsheet = client.open("Automacao_Barbearia")
sheet = spreadsheet.worksheet("Dados_Faturamento")


# 🧠 Função para extrair texto do PDF
def extrair_texto_pdf(pdf):
    texto = ""
    for page in pdf:
        texto += page.get_text()
    return texto


# 📤 Upload do PDF
st.sidebar.subheader("📤 Enviar PDF de Faturamento")
uploaded_file = st.sidebar.file_uploader("Escolha o PDF", type="pdf")

if uploaded_file:
    pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    texto = extrair_texto_pdf(pdf)

    st.subheader("📝 Texto extraído do PDF:")
    st.write(texto)

    # 🔍 Você pode aqui fazer o parser do texto para gerar dataframe
    # ⚠️ Exemplo abaixo é fictício, ajuste conforme seu PDF
    data = {
        "Ano": ["2024", "2024"],
        "Mês": ["Janeiro", "Fevereiro"],
        "Faturamento": [16200, 15200],
        "Comandas": [104, 121],
        "Ticket Médio": [156, 150]
    }

    df_pdf = pd.DataFrame(data)
    st.subheader("📊 Dados extraídos:")
    st.dataframe(df_pdf)

    # 🔄 Enviando para Google Sheets
    sheet.clear()
    sheet.update([df_pdf.columns.values.tolist()] + df_pdf.values.tolist())
    st.success("✅ Dados enviados para o Google Sheets com sucesso!")

st.markdown("---")

# 🔄 Lendo dados do Sheets
data = sheet.get_all_records()
df = pd.DataFrame(data)

# 🖥️ Layout do Dashboard
st.set_page_config(page_title="Dashboard Sr. Saldanha", layout="wide")
st.title("💈 Sr. Saldanha | Dashboard de Faturamento")

# 🚦 KPIs
col1, col2, col3 = st.columns(3)
col1.metric("💰 Faturamento Total", f'R$ {df["Faturamento"].sum():,.2f}')
col2.metric("📋 Total de Comandas", int(df["Comandas"].sum()))
col3.metric("🎟️ Ticket Médio", f'R$ {df["Ticket Médio"].mean():,.2f}')

st.markdown("---")

# 🎯 Filtros
st.sidebar.header("Filtros")
ano = st.sidebar.selectbox("Ano", df["Ano"].unique())
mes = st.sidebar.selectbox("Mês", df["Mês"].unique())

df_filtrado = df[(df["Ano"] == ano) & (df["Mês"] == mes)]

# 📈 Gráficos
st.subheader("🚀 Faturamento por Mês")
graf1 = df.groupby(["Ano", "Mês"])["Faturamento"].sum().reset_index()
st.line_chart(graf1.pivot(index="Mês", columns="Ano", values="Faturamento"))

st.subheader("📊 Ticket Médio por Mês")
graf2 = df.groupby(["Ano", "Mês"])["Ticket Médio"].mean().reset_index()
st.line_chart(graf2.pivot(index="Mês", columns="Ano", values="Ticket Médio"))

# 📑 Tabela Detalhada
st.subheader("📑 Dados Detalhados")
st.dataframe(df)
df_filtrado = df[(df["Ano"] == ano) & (df["Mês"] == mes)]

# 📈 Gráficos
st.subheader("🚀 Evolução de Faturamento por Mês")
graf1 = df.groupby(["Ano", "Mês"])["Faturamento"].sum().reset_index()
st.line_chart(graf1.pivot(index="Mês", columns="Ano", values="Faturamento"))

st.subheader("📊 Ticket Médio por Mês")
graf2 = df.groupby(["Ano", "Mês"])["Ticket Médio"].mean().reset_index()
st.line_chart(graf2.pivot(index="Mês", columns="Ano", values="Ticket Médio"))

# 📅 Comparativo de Períodos
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

st.write(f"**Período 1:** {mes1}/{ano1} → **R$ {fat1:,.2f}**")
st.write(f"**Período 2:** {mes2}/{ano2} → **R$ {fat2:,.2f}**")
st.write(f"**Variação:** {'🔺' if perc > 0 else '🔻'} {perc:.2f}%")

st.markdown("---")

# 📑 Tabela Detalhada
st.subheader("📑 Dados Detalhados")
st.dataframe(df)
