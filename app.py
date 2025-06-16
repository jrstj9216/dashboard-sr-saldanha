import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 🚩 Configuração da Página
st.set_page_config(page_title="Dashboard Sr. Saldanha", layout="wide")

# 🔐 Conectar ao Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)
client = gspread.authorize(credentials)

# 🔗 Ler a planilha
spreadsheet = client.open("Automacao_Barbearia")
sheet = spreadsheet.worksheet("Dados_Faturamento")
dados = sheet.get_all_records()

df = pd.DataFrame(dados)

# 🧽 Tratamento de Dados
df["Ano"] = df["Ano"].astype(str)
df["Mês"] = df["Mês"].astype(str)

# 🎯 Filtros apenas para os Indicadores
st.sidebar.header("🎯 Filtros para Indicadores")
filtro_ano = st.sidebar.selectbox("Ano", sorted(df["Ano"].unique()))
filtro_mes = st.sidebar.selectbox("Mês", sorted(df["Mês"].unique()))

df_filtrado = df[(df["Ano"] == filtro_ano) & (df["Mês"] == filtro_mes)]

# 🏆 Indicadores Filtrados
st.title("💈 Sr. Saldanha | Dashboard de Faturamento")

st.subheader("📊 Indicadores do Mês Selecionado")

col1, col2, col3 = st.columns(3)
col1.metric("💰 Faturamento", f'R$ {df_filtrado["Faturamento"].sum():,.2f}')
col2.metric("📋 Comandas", int(df_filtrado["Comandas"].sum()))
col3.metric("🎟️ Ticket Médio", f'R$ {df_filtrado["Ticket Médio"].mean():,.2f}')

st.markdown("---")

# 🚀 Gráficos Gerais (Sem Filtro)
st.subheader("🚀 Evolução de Faturamento por Mês")
graf1 = df.groupby(["Ano", "Mês"])["Faturamento"].sum().reset_index()
st.line_chart(graf1.pivot(index="Mês", columns="Ano", values="Faturamento"))

st.subheader("🎯 Ticket Médio por Mês")
graf2 = df.groupby(["Ano", "Mês"])["Ticket Médio"].mean().reset_index()
st.line_chart(graf2.pivot(index="Mês", columns="Ano", values="Ticket Médio"))

st.markdown("---")

# 📑 Tabela Geral (Sem Filtro)
st.subheader("📑 Dados Detalhados")
st.dataframe(df)
