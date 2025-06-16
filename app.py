import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 🔧 Configuração da página
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

# 📥 Função para extrair dados dos arquivos Excel
def extrair_dados_excel(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # 👉 Extrai Ano e Mês da coluna 'Data'
    df['Ano'] = df['Data'].astype(str).str.split('/').str[1]
    df['Mês'] = df['Data'].astype(str).str.split('/').str[0]
    return df

# 🚀 Upload dos arquivos
st.sidebar.header("📑 Enviar Arquivos Excel de Faturamento")
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

        st.subheader("📄 Dados extraídos dos arquivos Excel:")
        st.dataframe(df_final)

        # 🔄 Enviar para Google Sheets
        if st.button("📤 Enviar dados para Google Sheets"):
            sheet.clear()
            sheet.update([df_final.columns.values.tolist()] + df_final.values.tolist())
            st.success("Dados enviados para Google Sheets com sucesso!")

# 📊 Dashboard
st.title("💈 Sr. Saldanha | Dashboard de Faturamento")

try:
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)

    # 🔧 Ajustes de tipos e dados
    df["Ano"] = df["Data"].astype(str).str.split("/").str[1]
    df["Mês"] = df["Data"].astype(str).str.split("/").str[0]

    # 🔢 KPIs principais
    st.subheader("📊 Indicadores")

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Faturamento Total", f'R$ {df["Faturado"].sum():,.2f}')
    col2.metric("📋 Total de Comandas", int(df["Número de comandas"].sum()))
    col3.metric("🎟️ Ticket Médio", f'R$ {df["Média Faturado"].mean():,.2f}')

    # 📈 Gráfico de faturamento por mês
    st.subheader("📈 Evolução de Faturamento por Mês")
    graf = df.groupby(["Ano", "Mês"])["Faturado"].sum().reset_index()
    graf = graf.pivot(index="Mês", columns="Ano", values="Faturado")
    st.line_chart(graf)

except Exception as e:
    st.warning("⚠️ Erro na conexão ou na leitura dos dados.")
    st.error(e)
