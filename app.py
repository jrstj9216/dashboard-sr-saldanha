import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 🧠 Autenticação com Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(credentials)

# 🔗 Conectando à Planilha
spreadsheet = client.open("Automacao_Barbearia")
sheet = spreadsheet.worksheet("Dados_Faturamento")
data = sheet.get_all_records()

# 📊 Criando DataFrame
df = pd.DataFrame(data)

# 🧽 Tratamento de dados
df["Ano"] = df["Ano"].astype(str)
df["Mês"] = df["Mês"].astype(str)

# 🖥️ Layout
st.set_page_config(page_title="Dashboard Sr. Saldanha", layout="wide")
st.title("💈 Sr. Saldanha | Dashboard de Faturamento")

# 🚥 KPIs principais
st.subheader("📈 Indicadores")

col1, col2, col3 = st.columns(3)
col1.metric("💰 Faturamento Total", f'R$ {df["Faturamento"].sum():,.2f}')
col2.metric("📋 Total de Comandas", int(df["Comandas"].sum()))
col3.metric("🎟️ Ticket Médio", f'R$ {df["Ticket Médio"].mean():,.2f}')

st.markdown("---")

# 🎛️ Filtros
st.sidebar.header("Filtros")
ano = st.sidebar.selectbox("Ano", df["Ano"].unique())
mes = st.sidebar.selectbox("Mês", df["Mês"].unique())

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
