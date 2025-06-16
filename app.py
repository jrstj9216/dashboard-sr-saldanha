import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 🎨 Configuração da página
st.set_page_config(page_title="Dashboard Sr. Saldanha", layout="wide")

# 🔑 Autenticação com Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(credentials)

# 🗒️ Conectar à planilha
spreadsheet = client.open("Automacao_Barbearia")
sheet = spreadsheet.worksheet("Dados_Faturamento")

# 🧠 Função para extrair dados dos arquivos Excel
def extrair_dados_excel(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()  # Remove espaços nos nomes das colunas
    return df


# ☁️ Upload dos arquivos
st.sidebar.header("📄 Enviar Arquivos Excel de Faturamento")
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

        # Limpa e formata a coluna de data
        df_final["Data Comanda"] = pd.to_datetime(df_final["Data Comanda"], format="%d/%m/%Y")

        # ✨ Envia dados para o Google Sheets (substitui tudo pelo novo)
        sheet.clear()
        sheet.update([df_final.columns.values.tolist()] + df_final.values.tolist())

        st.success("✅ Dados enviados para o Google Sheets com sucesso!")

        st.subheader("📊 Dados extraídos dos arquivos Excel:")
        st.dataframe(df_final)

# 🧠 Leitura dos dados do Google Sheets
try:
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)

    if not df.empty:
        df["Data Comanda"] = pd.to_datetime(df["Data Comanda"], format="%d/%m/%Y")

        # 🎯 KPIs
        faturamento_total = df["Valor"].sum()
        total_comandas = df.shape[0]
        ticket_medio = faturamento_total / total_comandas if total_comandas != 0 else 0

        st.subheader("📊 Faturado Este Mês")

        col1, col2, col3 = st.columns(3)

        col1.metric("💰 Faturamento Total", f"R$ {faturamento_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col2.metric("📑 Total de Comandas", total_comandas)
        col3.metric("📈 Ticket Médio", f"R$ {ticket_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    else:
        st.warning("⚠️ Nenhum dado encontrado no Google Sheets.")

except Exception as e:
    st.error(f"❌ Erro na leitura dos dados: {e}")
