import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 🎨 Configuração da Página
st.set_page_config(page_title="Dashboard Sr. Saldanha", layout="wide")

# 🔐 Autenticação com Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(credentials)

# 📑 Nome do arquivo e da aba no Google Sheets
spreadsheet = client.open("Automacao_Barbearia")
sheet = spreadsheet.worksheet("Dados_Faturamento")


# 📤 Upload do Arquivo Excel
st.sidebar.header("📄 Enviar Arquivo Excel de Faturamento")
uploaded_file = st.sidebar.file_uploader(
    "Escolha o arquivo Excel",
    type=["xlsx"]
)

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()  # Remove espaços extras dos nomes das colunas

    required_columns = {'Data', 'Faturado', 'Número de com.', 'Média Faturado'}
    if required_columns.issubset(df.columns):

        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')

        # 🔥 Atualiza Google Sheets (sobrescreve tudo)
        try:
            sheet.clear()  # Limpa os dados existentes
            sheet.update(
                [df.columns.values.tolist()] + df.values.tolist()
            )
            st.success("✅ Dados enviados para Google Sheets com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao enviar dados para Google Sheets: {e}")

        # 🔥 Bloco - Faturado Este Mês
        st.subheader("📊 Faturado Este Mês")

        faturamento_total = df["Faturado"].sum()
        total_comandas = df["Número de com."].sum()
        ticket_medio = df["Média Faturado"].mean()

        col1, col2, col3 = st.columns(3)

        col1.metric("💰 Faturamento Total", f"R$ {faturamento_total:,.2f}".replace(",", ".").replace(".", ",", 1))
        col2.metric("🧾 Total de Comandas", int(total_comandas))
        col3.metric("🎯 Ticket Médio", f"R$ {ticket_medio:,.2f}".replace(",", ".").replace(".", ",", 1))

        with st.expander("🔍 Visualizar Dados Carregados"):
            st.dataframe(df)

    else:
        st.error("❌ A planilha deve conter as colunas: Data, Faturado, Número de com., Média Faturado")
else:
    st.warning("📤 Faça o upload de um arquivo Excel para visualizar o dashboard.")
