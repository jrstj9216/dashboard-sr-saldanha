import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 🎨 Configuração da página
st.set_page_config(page_title="Dashboard Sr. Saldanha", layout="wide")

# 🔑 Autenticação com Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(credentials)

# 🗂️ Conectando à planilha
spreadsheet = client.open("Automacao_Barbearia")
sheet = spreadsheet.worksheet("Dados_Faturamento")

# 🚀 Função para extrair dados dos arquivos Excel
def extrair_dados_excel(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()  # Remover espaços extras nos nomes das colunas
    return df

# ⬆️ Upload dos arquivos Excel
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

        # 🟢 Convertendo a coluna 'Data' para datetime e extraindo o Ano e Mês
        df_final['Data'] = pd.to_datetime(df_final['Data'], format='%m/%Y')
        df_final['Ano'] = df_final['Data'].dt.year
        df_final['Mês'] = df_final['Data'].dt.month

        # 🔄 Enviando para Google Sheets
        sheet.clear()
        sheet.update([df_final.columns.values.tolist()] + df_final.values.tolist())

        st.success("✅ Dados enviados para Google Sheets com sucesso!")

        # Mostrar dados
        st.subheader("📊 Dados extraídos dos arquivos Excel:")
        st.dataframe(df_final)

# 🔽 Leitura dos dados do Google Sheets
try:
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)

    if not df.empty:
        df['Data'] = pd.to_datetime(df['Data'], format='%m/%Y')
        df['Ano'] = df['Data'].dt.year
        df['Mês'] = df['Data'].dt.month

        df['Faturado'] = pd.to_numeric(df['Faturado'], errors='coerce')
        df['Número de comandas'] = pd.to_numeric(df['Número de comandas'], errors='coerce')
        df['Média Faturado'] = pd.to_numeric(df['Média Faturado'], errors='coerce')

        # 🎯 Filtrar dados de 2025
        df_2025 = df[df['Ano'] == 2025]

        # 💡 Indicadores principais
        st.title("📊 Total 2025")

        col1, col2, col3 = st.columns(3)

        col1.metric("💰 Faturamento Total", f"R$ {df_2025['Faturado'].sum():,.2f}")
        col2.metric("📑 Total de Comandas", int(df_2025['Número de comandas'].sum()))
        col3.metric("🧾 Ticket Médio", f"R$ {df_2025['Média Faturado'].mean():,.2f}")

        st.markdown("---")

        # 📈 Evolução de Faturamento por Mês
        st.subheader("📈 Evolução de Faturamento por Mês")

        graf = df_2025.groupby(['Ano', 'Mês'])['Faturado'].sum().reset_index()
        graf = graf.pivot(index='Mês', columns='Ano', values='Faturado')

        st.line_chart(graf)

except Exception as e:
    st.warning("⚠️ Nenhum dado encontrado ou erro na conexão com o Google Sheets.")
    st.error(f"{e}")
