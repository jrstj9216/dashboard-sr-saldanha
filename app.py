import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import gspread
from google.oauth2.service_account import Credentials
import re

# 🎯 Autenticação com Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope)

client = gspread.authorize(credentials)

# 🔗 Conectando ao Google Sheets
spreadsheet = client.open("Automacao_Barbearia")
sheet = spreadsheet.worksheet("Dados_Faturamento")


# 🔍 Função para extrair dados do PDF
def extrair_dados_pdf(file, ano_pdf):
    texto = ""
    pdf = fitz.open(stream=file.read(), filetype="pdf")
    for page in pdf:
        texto += page.get_text()

    # Regex para capturar linhas tipo: 01/2024   45.000,00   900   50,00
    linhas = re.findall(r'(\d{2}/\d{4})\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)', texto)

    dados = []
    for linha in linhas:
        mes_ano = linha[0]
        mes, ano = mes_ano.split('/')

        faturamento = float(linha[1].replace('.', '').replace(',', '.'))
        comandas = int(linha[2].replace('.', '').replace(',', ''))
        ticket_medio = float(linha[3].replace('.', '').replace(',', '.'))

        dados.append({
            "Ano": ano,
            "Mês": mes,
            "Faturamento": faturamento,
            "Comandas": comandas,
            "Ticket Médio": ticket_medio
        })

    return pd.DataFrame(dados)


# 🗂️ Upload de múltiplos PDFs
st.sidebar.subheader("📤 Enviar PDFs de Faturamento")
uploaded_files = st.sidebar.file_uploader(
    "Escolha os PDFs (pode selecionar múltiplos)", type="pdf", accept_multiple_files=True)

if uploaded_files:
    df_total = pd.DataFrame()

    for uploaded_file in uploaded_files:
        # Pegando o nome do arquivo para extrair o ano (ex.: 2024.pdf → 2024)
        nome_arquivo = uploaded_file.name
        ano_arquivo = re.findall(r'\d{4}', nome_arquivo)
        ano_pdf = ano_arquivo[0] if ano_arquivo else "Desconhecido"

        st.success(f"🗂️ Lendo arquivo: {nome_arquivo}")

        df_pdf = extrair_dados_pdf(uploaded_file, ano_pdf)
        df_total = pd.concat([df_total, df_pdf], ignore_index=True)

    st.subheader("📊 Dados extraídos:")
    st.dataframe(df_total)

    # 🔄 Atualizando Google Sheets
    sheet.clear()
    sheet.update([df_total.columns.values.tolist()] + df_total.values.tolist())
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
