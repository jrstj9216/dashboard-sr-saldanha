import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 🎨 Configuração da página
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

# 🚀 Função para extrair dados dos arquivos Excel
def extrair_dados_excel(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()  # Remove espaços extras nos nomes das colunas
    return df

# 📤 Upload dos arquivos
st.sidebar.header("📑 Enviar Arquivos de Faturamento")
uploaded_files = st.sidebar.file_uploader(
    "Escolha os arquivos Excel", type=["xlsx"], accept_multiple_files=True
)

dfs = []

if uploaded_files:
    for file in uploaded_files:
        st.info(f"Lendo arquivo: {file.name}")
        df = extrair_dados_excel(file)
        dfs.append(df)

    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)

        st.subheader("📄 Dados extraídos:")
        st.dataframe(df_final)

        # 🔄 Atualiza o Google Sheets
        if st.button("🔗 Enviar dados para Google Sheets"):
            sheet.clear()  # ⚠️ Limpa antes de atualizar
            sheet.update([df_final.columns.values.tolist()] + df_final.values.tolist())
            st.success("Dados enviados para Google Sheets com sucesso!")

# 📊 Dashboard de Faturamento
st.title("💈 Sr. Saldanha | Dashboard de Faturamento")

try:
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)

    df["Ano"] = df["Ano"].astype(str)
    df["Mês"] = df["Mês"].astype(str)

    # 🚥 KPIs principais → Total 2025
    st.subheader("📈 Total 2025")

    df_2025 = df[df["Ano"] == "2025"]

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Faturamento Total", f'R$ {df_2025["Faturamento"].sum():,.2f}')
    col2.metric("📋 Total de Comandas", int(df_2025["Comandas"].sum()))
    col3.metric("🎟️ Ticket Médio", f'R$ {df_2025["Ticket Médio"].mean():,.2f}')

    st.markdown("---")

    # 📈 Evolução de Faturamento
    st.subheader("🚀 Evolução de Faturamento por Mês")
    graf1 = df.groupby(["Ano", "Mês"])["Faturamento"].sum().reset_index()
    st.line_chart(graf1.pivot(index="Mês", columns="Ano", values="Faturamento"))

    # 📊 Ticket Médio por Mês
    st.subheader("📊 Ticket Médio por Mês")
    graf2 = df.groupby(["Ano", "Mês"])["Ticket Médio"].mean().reset_index()
    st.line_chart(graf2.pivot(index="Mês", columns="Ano", values="Ticket Médio"))

    # 📑 Dados Detalhados
    st.subheader("📑 Dados Detalhados")
    st.dataframe(df)

except Exception as e:
    st.warning("Nenhum dado encontrado ou erro na conexão com o Google Sheets.")
    st.exception(e)
