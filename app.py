import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import gspread
from google.oauth2.service_account import Credentials
import io

# 🚩 Configuração da Página
st.set_page_config(page_title="Dashboard Sr. Saldanha", layout="wide")

# 🎨 CSS Personalizado
st.markdown(
    """
    <style>
        .main {
            background-color: #000000;
            color: white;
        }
        .stApp {
            background-color: #000000;
        }
        h1, h2, h3, h4 {
            color: white;
        }
        .css-18e3th9 {
            background-color: #000000;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# 🔐 Autenticação com Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(credentials)

# 🔗 Ler dados da planilha
spreadsheet = client.open("Automacao_Barbearia")
sheet = spreadsheet.worksheet("Dados_Faturamento")
dados = sheet.get_all_records()

df = pd.DataFrame(dados)

# 🔧 Limpeza e ajustes
df.columns = df.columns.str.strip()

df["Ano"] = df["Ano"].astype(str)
df["Mês"] = df["Mês"].astype(str)

df["Faturamento"] = pd.to_numeric(df["Faturamento"], errors='coerce').fillna(0)
df["Comandas"] = pd.to_numeric(df["Comandas"], errors='coerce').fillna(0)
df["Ticket Médio"] = pd.to_numeric(df["Ticket Médio"], errors='coerce').fillna(0)

# ===========================================
# 🔥 Bloco Total 2025
# ===========================================

df_2025 = df[df["Ano"] == "2025"]

faturamento_2025 = df_2025["Faturamento"].sum()
comandas_2025 = df_2025["Comandas"].sum()
ticket_medio_2025 = df_2025["Ticket Médio"].mean()

st.title("💈 Sr. Saldanha | Dashboard de Faturamento")

st.subheader("📊 Total 2025 (Acumulado até Agora)")

col1, col2, col3 = st.columns(3)
col1.metric("💰 Faturamento Total", f'R$ {faturamento_2025:,.2f}')
col2.metric("📋 Total de Comandas", int(comandas_2025))
col3.metric("🎟️ Ticket Médio", f'R$ {ticket_medio_2025:,.2f}')

st.markdown("---")

# ===========================================
# 🎛️ Filtros para Gráficos e Tabela
# ===========================================

st.sidebar.header("🎯 Filtros para Análise")

ano_selecionado = st.sidebar.selectbox("Selecione o Ano", sorted(df["Ano"].unique()))
mes_selecionado = st.sidebar.selectbox("Selecione o Mês", sorted(df["Mês"].unique()))

df_filtrado = df[(df["Ano"] == ano_selecionado) & (df["Mês"] == mes_selecionado)]

# ===========================================
# 📅 Comparação de Períodos
# ===========================================

st.subheader("📅 Comparação de Períodos")

col4, col5 = st.columns(2)
with col4:
    ano1 = st.selectbox("Período 1 - Ano", sorted(df["Ano"].unique()))
    mes1 = st.selectbox("Período 1 - Mês", sorted(df["Mês"].unique()))

with col5:
    ano2 = st.selectbox("Período 2 - Ano", sorted(df["Ano"].unique()))
    mes2 = st.selectbox("Período 2 - Mês", sorted(df["Mês"].unique()))

filtro1 = (df["Ano"] == ano1) & (df["Mês"] == mes1)
filtro2 = (df["Ano"] == ano2) & (df["Mês"] == mes2)

fat1 = df.loc[filtro1, "Faturamento"].sum()
fat2 = df.loc[filtro2, "Faturamento"].sum()
dif = fat2 - fat1
perc = (dif / fat1) * 100 if fat1 != 0 else 0

st.write(f"**Período 1:** {mes1}/{ano1} → **R$ {fat1:,.2f}**")
st.write(f"**Período 2:** {mes2}/{ano2} → **R$ {fat2:,.2f}**")
st.write(f"**Variação:** {'🔺' if perc > 0 else '🔻'} {perc:.2f}%")

st.markdown("---")

# ===========================================
# 📈 Gráficos Dinâmicos
# ===========================================

st.subheader("🚀 Evolução de Faturamento por Mês")
graf1 = df.groupby(["Ano", "Mês"])["Faturamento"].sum().reset_index()
st.line_chart(graf1.pivot(index="Mês", columns="Ano", values="Faturamento"))

st.subheader("🎯 Ticket Médio por Mês")
graf2 = df.groupby(["Ano", "Mês"])["Ticket Médio"].mean().reset_index()
st.line_chart(graf2.pivot(index="Mês", columns="Ano", values="Ticket Médio"))

st.markdown("---")

# ===========================================
# 📑 Tabela Detalhada
# ===========================================

st.subheader("📑 Dados Detalhados")
st.dataframe(df)

# ===========================================
# 📥 Upload de PDFs e Atualização
# ===========================================

st.sidebar.header("📑 Upload de PDFs de Faturamento")
uploaded_files = st.sidebar.file_uploader("Escolha os PDFs", type="pdf", accept_multiple_files=True)

# 🚀 Função de extração dos PDFs
def extrair_dados_pdf(uploaded_file):
    texto = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            texto += page.get_text()

    linhas = texto.split("\n")
    dados = []

    for linha in linhas:
        if "/" in linha and any(c.isdigit() for c in linha):
            partes = linha.split()
            if len(partes) >= 4:
                data = partes[0]
                faturamento = partes[1].replace(".", "").replace(",", ".")
                comandas = partes[2]
                ticket = partes[3].replace(",", ".")
                ano, mes = data.split("/")

                dados.append({
                    "Ano": ano,
                    "Mês": mes,
                    "Faturamento": float(faturamento),
                    "Comandas": int(comandas),
                    "Ticket Médio": float(ticket)
                })

    return pd.DataFrame(dados)

# 🚩 Atualização do Google Sheets
dfs = []

if uploaded_files:
    for file in uploaded_files:
        st.info(f"Lendo arquivo: {file.name}")
        df_pdf = extrair_dados_pdf(file)
        dfs.append(df_pdf)

    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)
        st.subheader("📄 Dados extraídos dos PDFs:")
        st.dataframe(df_final)

        if st.button("🔗 Enviar dados para Google Sheets"):
            sheet.clear()
            sheet.update([df_final.columns.values.tolist()] + df_final.values.tolist())
            st.success("Dados enviados para Google Sheets com sucesso!")
