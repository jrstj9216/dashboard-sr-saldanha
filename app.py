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

# 🌐 Conectando à planilha
spreadsheet = client.open("Automacao_Barbearia")
sheet = spreadsheet.worksheet("Dados_Faturamento")

# 📥 Upload dos arquivos Excel
st.sidebar.header("📄 Enviar Arquivos Excel de Faturamento")
uploaded_file = st.sidebar.file_uploader(
    "Escolha seu arquivo Excel", 
    type=["xlsx"]
)

if uploaded_file:
    try:
        st.success(f"Arquivo {uploaded_file.name} carregado com sucesso!")

        # 🔍 Leitura do Excel
        df = pd.read_excel(uploaded_file, sheet_name="Sheet1")

        # 🔧 Limpeza de dados
        df.columns = df.columns.str.strip()
        df = df.rename(columns={
            "Data Comanda": "Data",
            "Valor": "Faturado",
            "Comanda": "Comandas"
        })

        df = df[["Data", "Faturado", "Comandas"]]

        df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")
        df = df.dropna(subset=["Data"])

        df["Faturado"] = pd.to_numeric(df["Faturado"], errors="coerce").fillna(0)
        df["Comandas"] = pd.to_numeric(df["Comandas"], errors="coerce").fillna(0)

        # 💾 Atualizando Google Sheets (apaga tudo antes)
        sheet.clear()

        # ✅ Enviando dados
        sheet.update(
            [df.columns.values.tolist()] + df.values.tolist()
        )
        st.success("Dados enviados para o Google Sheets com sucesso!")

    except Exception as e:
        st.error(f"Erro no processamento do arquivo: {e}")

# 🚦 Leitura dos dados do Google Sheets
try:
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)

    if not df.empty:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        df["Faturado"] = pd.to_numeric(df["Faturado"], errors="coerce")
        df["Comandas"] = pd.to_numeric(df["Comandas"], errors="coerce")

        # 🎯 Cálculo dos indicadores
        faturamento_total = df["Faturado"].sum()
        total_comandas = df["Comandas"].sum()
        ticket_medio = faturamento_total / total_comandas if total_comandas > 0 else 0

        # 📊 Layout dos Indicadores
        st.title("📊 Faturado Este Mês")
        col1, col2, col3 = st.columns(3)

        col1.metric("💰 Faturamento Total", f"R$ {faturamento_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col2.metric("🧾 Total de Comandas", int(total_comandas))
        col3.metric("🎯 Ticket Médio", f"R$ {ticket_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        # 📈 Gráfico de Faturamento por Dia
        st.subheader("📅 Evolução de Faturamento por Dia")
        graf = df.groupby("Data")["Faturado"].sum().reset_index()

        st.line_chart(graf.set_index("Data"))

        # 🗒️ Tabela de Dados
        st.subheader("📄 Dados Carregados")
        st.dataframe(df)

    else:
        st.warning("Nenhum dado encontrado no Google Sheets.")

except Exception as e:
    st.error(f"Erro na leitura dos dados: {e}")
