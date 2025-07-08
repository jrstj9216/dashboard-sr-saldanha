import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 🎨 Configuração da página
st.set_page_config(page_title="Sr. Saldanha | Dashboard", layout="wide")
st.title("💈 Sr. Saldanha | Dashboard de Faturamento")

# 🔐 Autenticação com Google Sheets
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(credentials)

# Conectando ao Google Sheets
spreadsheet = client.open("dados_avec")
sheet = spreadsheet.worksheet("Dados_Faturamento")


# 📥 Função para extrair dados do Excel
def extrair_dados_excel(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name="Sheet1")
    df.columns = df.columns.str.strip()  # Remove espaços nas colunas
    return df


# 📤 Upload dos arquivos
st.sidebar.header("📄 Enviar Arquivos Excel de Faturamento")
uploaded_files = st.sidebar.file_uploader(
    "Escolha os arquivos Excel",
    type=["xlsx"],
    accept_multiple_files=True
)

dfs = []

if uploaded_files:
    for file in uploaded_files:
        st.info(f"Lendo arquivo: {file.name}")
        df = extrair_dados_excel(file)

        # 🛑 Verificar se as colunas estão corretas
        colunas_esperadas = ['Data Comanda', 'Comanda', 'Valor']
        if not all(coluna in df.columns for coluna in colunas_esperadas):
            st.error(f"⚠️ Colunas não conferem. Esperado: {colunas_esperadas}")
            st.stop()

        dfs.append(df)

    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)

        # Mostrar dados no app
        st.subheader("📑 Dados extraídos dos arquivos Excel:")
        st.dataframe(df_final)

        # 🔄 Enviar dados para Google Sheets
        if st.button("🚀 Enviar dados para Google Sheets"):
            try:
                # Limpa os dados atuais no Google Sheets
                sheet.clear()

                # Atualiza com os novos dados
                sheet.update(
                    [df_final.columns.values.tolist()] + df_final.values.tolist()
                )

                st.success("✅ Dados enviados para Google Sheets com sucesso!")

            except Exception as e:
                st.error(f"❌ Erro ao enviar dados para Google Sheets: {e}")

# 🔍 Leitura dos dados do Google Sheets
try:
    dados = sheet.get_all_records()
    df_google = pd.DataFrame(dados)

    if not df_google.empty:
        # Conversões necessárias
        df_google['Valor'] = pd.to_numeric(df_google['Valor'], errors='coerce')
        df_google['Comanda'] = pd.to_numeric(df_google['Comanda'], errors='coerce')

        # ✅ Bloco de indicadores
        st.subheader("📊 Faturado Este Mês")

        col1, col2, col3 = st.columns(3)

        faturamento_total = df_google['Valor'].sum()
        total_comandas = df_google['Comanda'].sum()
        ticket_medio = faturamento_total / total_comandas if total_comandas != 0 else 0

        col1.metric("💰 Faturamento Total", f"R$ {faturamento_total:,.2f}")
        col2.metric("🧾 Total de Comandas", int(total_comandas))
        col3.metric("🎟️ Ticket Médio", f"R$ {ticket_medio:,.2f}")

        # 📈 Exibir tabela
        st.subheader("📄 Dados do Google Sheets:")
        st.dataframe(df_google)

    else:
        st.warning("⚠️ Nenhum dado encontrado no Google Sheets.")

except Exception as e:
    st.error(f"❌ Erro na conexão ou leitura dos dados: {e}")
    Commit changes

