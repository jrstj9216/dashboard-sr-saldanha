import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ✅ Autenticação com Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(credentials)

# ✅ Conectando ao Google Sheets
spreadsheet = client.open("Automacao_Barbearia")
sheet = spreadsheet.worksheet("Dados_Faturamento")  # Nome da aba no Google Sheets

# ✅ Função para extrair dados do Excel
def extrair_dados_excel(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name="Sheet1")
    df.columns = df.columns.str.strip()  # Remove espaços extras
    return df

# ✅ Upload dos arquivos Excel
st.sidebar.header("📥 Enviar Arquivos Excel de Faturamento")
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

        # ✅ Ajuste de datas
        df_final['Data Comanda'] = pd.to_datetime(df_final['Data Comanda'], dayfirst=True, errors='coerce')

        # ⚠️ Remove linhas com data inválida
        df_final = df_final.dropna(subset=['Data Comanda'])

        # ✅ Envia os dados para o Google Sheets
        sheet.clear()  # Limpa dados anteriores
        sheet.update([df_final.columns.values.tolist()] + df_final.values.tolist())

        st.success("✅ Dados enviados com sucesso para Google Sheets!")

        # ✅ KPIs
        faturamento_total = df_final['Valor'].sum()
        total_comandas = df_final['Comanda'].sum()
        ticket_medio = faturamento_total / total_comandas if total_comandas != 0 else 0

        # ✅ Bloco de indicadores
        st.title("📊 Faturado Este Mês")
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Faturamento Total", f"R$ {faturamento_total:,.2f}".replace(",", "."))
        col2.metric("🧾 Total de Comandas", int(total_comandas))
        col3.metric("🎯 Ticket Médio", f"R$ {ticket_medio:,.2f}".replace(",", "."))

        # ✅ Gráfico
        st.subheader("📅 Evolução de Faturamento por Dia")
        graf = df_final.groupby('Data Comanda')['Valor'].sum().reset_index()
        st.line_chart(graf.rename(columns={"Data Comanda": "index"}).set_index('index'))

else:
    st.warning("⚠️ Faça upload dos arquivos Excel para gerar o dashboard.")
