import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 🎨 Configuração da página
st.set_page_config(page_title="Dashboard Sr. Saldanha", layout="wide")
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
spreadsheet = client.open("Automacao_Barbearia")
sheet = spreadsheet.worksheet("Dados_Faturamento")

# 🚀 Upload dos arquivos Excel
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
        df = pd.read_excel(file)
        df.columns = df.columns.str.strip()
        dfs.append(df)

    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)

        # 🔧 Tratamento da coluna 'Data'
        df_final['Data'] = pd.to_datetime(df_final['Data'], dayfirst=True, errors='coerce')
        df_final['Ano'] = df_final['Data'].dt.year
        df_final['Mês'] = df_final['Data'].dt.month

        # ✅ Botão para enviar dados ao Google Sheets
        if st.button("🚀 Enviar dados para Google Sheets"):
            sheet.clear()  # Limpa a planilha antes de enviar
            sheet.update([df_final.columns.values.tolist()] + df_final.values.tolist())
            st.success("✅ Dados enviados para Google Sheets com sucesso!")

        st.subheader("📊 Dados extraídos dos arquivos Excel:")
        st.dataframe(df_final)

# 🗂️ Leitura dos dados do Google Sheets
try:
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)

    if not df.empty:
        # 🔧 Tratamento da coluna 'Data'
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df['Ano'] = df['Data'].dt.year
        df['Mês'] = df['Data'].dt.month

        # 🎯 Filtro por Ano
        ano_selecionado = st.sidebar.selectbox(
            "Selecione o ano:",
            options=sorted(df['Ano'].dropna().unique())
        )

        df_ano = df[df['Ano'] == ano_selecionado]

        # 📊 KPIs principais
        st.subheader("📊 Total " + str(ano_selecionado))

        col1, col2, col3 = st.columns(3)

        faturamento_total = df_ano['Faturado'].sum()
        total_comandas = df_ano['Número de com'].sum()
        ticket_medio = df_ano['Média Faturado'].mean()

        col1.metric("🪙 Faturamento Total", f"R$ {faturamento_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col2.metric("🧾 Total de Comandas", int(total_comandas))
        col3.metric("💳 Ticket Médio", f"R$ {ticket_medio:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        # 📈 Gráfico de Faturamento por Mês
        st.subheader("📈 Evolução de Faturamento por Mês")
        graf = df_ano.groupby('Mês')['Faturado'].sum().reset_index()

        st.line_chart(
            data=graf,
            x="Mês",
            y="Faturado"
        )

        # 📉 Gráfico de Ticket Médio por Mês
        st.subheader("📉 Evolução do Ticket Médio por Mês")
        graf_ticket = df_ano.groupby('Mês')['Média Faturado'].mean().reset_index()

        st.line_chart(
            data=graf_ticket,
            x="Mês",
            y="Média Faturado"
        )

        # 📅 Tabela detalhada
        st.subheader("📑 Tabela de Faturamento")
        st.dataframe(df_ano)

    else:
        st.warning("⚠️ Nenhum dado encontrado no Google Sheets.")

except Exception as e:
    st.warning("⚠️ Nenhum dado encontrado ou erro na conexão com o Google Sheets.")
    st.error(e)
