import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 🎨 Configuração da página
st.set_page_config(page_title="Sr. Saldanha | Dashboard", layout="wide")
st.title("💈 Sr. Saldanha | Dashboard de Faturamento")

# 🔑 Autenticação com Google Sheets
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)
client = gspread.authorize(credentials)

# 📊 Conectar na planilha
spreadsheet = client.open("Automacao_Barbearia")
sheet = spreadsheet.worksheet("Dados_Faturamento")

# 📥 Função para extrair dados do Excel
def extrair_dados_excel(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name="Sheet1")
    df.columns = df.columns.str.strip()
    return df

# ⬆️ Upload dos arquivos
st.sidebar.header("📄 Enviar Arquivos Excel de Faturamento")
uploaded_files = st.sidebar.file_uploader(
    "Escolha os arquivos Excel",
    type=["xlsx"],
    accept_multiple_files=True
)

dfs = []
if uploaded_files:
    for file in uploaded_files:
        st.info(f"📑 Lendo arquivo: {file.name}")
        df = extrair_dados_excel(file)
        dfs.append(df)

    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)

        # 🔄 Limpar planilha antes de enviar os dados
        sheet.clear()

        # 🚀 Enviar para Google Sheets
        sheet.update([df_final.columns.values.tolist()] + df_final.values.tolist())

        st.success("✅ Dados enviados para Google Sheets com sucesso!")

# 🗂️ Carregar dados do Google Sheets
try:
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)

    if not df.empty:
        df["Data Comanda"] = pd.to_datetime(df["Data Comanda"], dayfirst=True, errors='coerce')
        df["Comanda"] = pd.to_numeric(df["Comanda"], errors='coerce')
        df["Valor"] = pd.to_numeric(df["Valor"], errors='coerce')

        # 🔢 Bloco Faturamento do mês
        st.subheader("📊 Faturado Este Mês")
        total_faturamento = df["Valor"].sum()
        total_comandas = df["Comanda"].sum()
        ticket_medio = total_faturamento / total_comandas if total_comandas != 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Faturamento Total", f"R$ {total_faturamento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col2.metric("🧾 Total de Comandas", int(total_comandas))
        col3.metric("🎟️ Ticket Médio", f"R$ {ticket_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        # 📅 Mostrar tabela dos dados
        st.subheader("📅 Dados de Faturamento")
        st.dataframe(df)

    else:
        st.warning("⚠️ Nenhum dado encontrado no Google Sheets.")

except Exception as e:
    st.warning("⚠️ Erro na conexão ou na leitura dos dados.")
    st.error(e)
