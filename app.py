import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 🎨 Configuração da página
st.set_page_config(page_title="Dashboard Sr. Saldanha", layout="wide")
st.title("💈 Sr. Saldanha | Dashboard de Faturamento")

# 🔐 Autenticação com Google Sheets
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(credentials)

# 📑 Conectando à planilha
spreadsheet = client.open("Automacao_Barbearia")
sheet = spreadsheet.worksheet("Dados_Faturamento")


# 📥 Função para extrair dados dos arquivos Excel
def extrair_dados_excel(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()  # Remove espaços extras nos nomes das colunas
    return df


# 🗂️ Upload dos arquivos
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

        # 🗑️ Limpar dados anteriores no Google Sheets
        sheet.clear()

        # 📅 Ajuste da coluna de data
        df_final['Data'] = pd.to_datetime(df_final['Data'], dayfirst=True, errors='coerce')
        df_final = df_final.dropna(subset=['Data'])  # Remove linhas com datas inválidas
        df_final['Data'] = df_final['Data'].dt.strftime('%d/%m/%Y')  # Formato como string

        # 🔼 Enviar os dados para o Google Sheets
        sheet.update([df_final.columns.values.tolist()] + df_final.values.tolist())

        st.success("✅ Dados enviados para Google Sheets com sucesso!")

        # 📊 Exibir dados carregados
        st.subheader("📊 Dados extraídos dos arquivos Excel:")
        st.dataframe(df_final)

        # 🔎 Processamento para KPIs
        df_final['Data'] = pd.to_datetime(df_final['Data'], dayfirst=True)
        df_final['Ano'] = df_final['Data'].dt.year
        df_final['Mês'] = df_final['Data'].dt.month

        df_2025 = df_final[df_final['Ano'] == 2025]

        faturamento_total = df_2025['Faturado'].sum()
        total_comandas = df_2025['Número de com.'].sum()
        ticket_medio = df_2025['Média Faturado'].mean()

        st.subheader("📊 Total 2025")
        col1, col2, col3 = st.columns(3)

        col1.metric("💰 Faturamento Total", f"R$ {faturamento_total:,.2f}")
        col2.metric("📄 Total de Comandas", int(total_comandas))
        col3.metric("💳 Ticket Médio", f"R$ {ticket_medio:,.2f}")

        # 📈 Gráfico de evolução de faturamento por mês
        st.subheader("📈 Evolução de Faturamento por Mês")
        graf = df_2025.groupby(['Ano', 'Mês'])['Faturado'].sum().reset_index()
        graf = graf.pivot(index='Mês', columns='Ano', values='Faturado')
        st.line_chart(graf)

    else:
        st.warning("⚠️ Nenhum arquivo Excel enviado.")

else:
    st.info("📥 Faça upload dos arquivos Excel para começar.")
