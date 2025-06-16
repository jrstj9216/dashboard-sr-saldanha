import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ⚙️ Configuração da página
st.set_page_config(page_title="Dashboard Sr. Saldanha", layout="wide")

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

# 🚀 Upload dos Arquivos Excel
st.sidebar.header("📑 Enviar Dados de Faturamento")
uploaded_files = st.sidebar.file_uploader("Escolha os arquivos Excel", type=["xls", "xlsx"], accept_multiple_files=True)

dfs = []

if uploaded_files:
    for file in uploaded_files:
        st.info(f"Lendo arquivo: {file.name}")
        df = pd.read_excel(file)
        dfs.append(df)

    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)

        st.subheader("📄 Dados extraídos:")
        st.dataframe(df_final)

        # 🔄 Atualiza o Google Sheets
        if st.button("🔗 Enviar dados para Google Sheets"):
            sheet.clear()
            sheet.update([df_final.columns.values.tolist()] + df_final.values.tolist())
            st.success("Dados enviados para Google Sheets com sucesso!")

# 📊 Dashboard de Faturamento
st.title("💈 Sr. Saldanha | Dashboard de Faturamento")

try:
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)

    df["Ano"] = df["Ano"].astype(str)
    df["Mês"] = df["Mês"].astype(str)

    df["Faturamento"] = pd.to_numeric(df["Faturamento"], errors='coerce').fillna(0)
    df["Comandas"] = pd.to_numeric(df["Comandas"], errors='coerce').fillna(0)
    df["Ticket Médio"] = pd.to_numeric(df["Ticket Médio"], errors='coerce').fillna(0)

    # 🎯 Dados apenas do ano de 2025
    df_2025 = df[df["Ano"] == "2025"]

    faturamento_2025 = df_2025["Faturamento"].sum()
    comandas_2025 = df_2025["Comandas"].sum()
    ticket_medio_2025 = faturamento_2025 / comandas_2025 if comandas_2025 != 0 else 0

    # 🚥 KPIs de 2025
    st.subheader("📊 Total 2025 (Acumulado até Agora)")

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Faturamento Total", f'R$ {faturamento_2025:,.2f}')
    col2.metric("📋 Total de Comandas", int(comandas_2025))
    col3.metric("🎟️ Ticket Médio", f'R$ {ticket_medio_2025:,.2f}')

    st.markdown("---")

    # 🔥 Gráfico de Faturamento por Mês (todos os anos)
    st.subheader("🚀 Evolução de Faturamento por Mês")
    graf1 = df.groupby(["Ano", "Mês"])["Faturamento"].sum().reset_index()
    st.line_chart(graf1.pivot(index="Mês", columns="Ano", values="Faturamento"))

    # 🔥 Gráfico de Ticket Médio
    st.subheader("📊 Ticket Médio por Mês")
    graf2 = df.groupby(["Ano", "Mês"])["Ticket Médio"].mean().reset_index()
    st.line_chart(graf2.pivot(index="Mês", columns="Ano", values="Ticket Médio"))

    # 🔥 Tabela Detalhada
    st.subheader("📑 Dados Detalhados")
    st.dataframe(df)

except Exception as e:
    st.warning("Nenhum dado encontrado ou erro na conexão com o Google Sheets.")
    st.exception(e)
