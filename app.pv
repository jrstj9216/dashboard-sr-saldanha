import streamlit as st  
import pandas as pd  
import fitz  
import gspread  
from oauth2client.service_account import ServiceAccountCredentials  
import matplotlib.pyplot as plt  
import seaborn as sns  

st.set_page_config(page_title="Sr. Saldanha | Dashboard Faturamento", layout="wide")  

st.title("💈 Sr. Saldanha | Dashboard de Faturamento")  

# Conexão com Google Sheets  
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]  
creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)  
client = gspread.authorize(creds)  

spreadsheet = client.open("Automacao_Barbearia")  
sheet = spreadsheet.worksheet("Dados_Faturamento")  

# Upload PDFs  
st.subheader("📤 Upload dos PDFs")  
uploaded_files = st.file_uploader("Enviar PDFs", type="pdf", accept_multiple_files=True)  

data = []  

if uploaded_files:  
    for file in uploaded_files:  
        with fitz.open(stream=file.read(), filetype="pdf") as pdf:  
            text = "".join([page.get_text() for page in pdf])  

            ano = "2024" if "2024" in text else "2023"  
            meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",  
                     "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]  

            for mes in meses:  
                if mes in text:  
                    faturamento = 10000  # Substituir por sua extração real  
                    comandas = 200  
                    ticket = round(faturamento / comandas, 2)  

                    data.append([ano, mes, faturamento, comandas, ticket])  

    if data:  
        sheet.append_rows(data)  
        st.success("✅ Dados enviados ao Google Sheets!")  

# Ler dados existentes  
dados = sheet.get_all_records()  
df = pd.DataFrame(dados)  

if not df.empty:  
    st.subheader("🗂️ Filtros e Comparação")  
    col1, col2, col3, col4 = st.columns([1,1,1,1.5])  

    with col1:  
        anos = st.multiselect("Ano", df["Ano"].unique(), default=df["Ano"].unique())  
    with col2:  
        meses = st.multiselect("Mês", df["Mês"].unique(), default=df["Mês"].unique())  

    with col4:  
        comparar = st.checkbox("🔀 Comparar Período")  

    filtro = (df["Ano"].isin(anos)) & (df["Mês"].isin(meses))  
    df_filtrado = df[filtro]  

    st.subheader("📊 Indicadores")  
    col1, col2, col3 = st.columns(3)  
    col1.metric("Faturamento Total", f'R$ {df_filtrado["Faturamento"].sum():,.2f}')  
    col2.metric("Total de Comandas", f'{df_filtrado["Comandas"].sum()}')  
    col3.metric("Ticket Médio", f'R$ {df_filtrado["Ticket Médio"].mean():,.2f}')  

    st.subheader("📈 Gráficos")  
    col1, col2 = st.columns(2)  

    with col1:  
        st.markdown("**Faturamento Mensal**")  
        fig, ax = plt.subplots()  
        sns.barplot(data=df_filtrado, x="Mês", y="Faturamento", hue="Ano", ax=ax)  
        plt.xticks(rotation=45)  
        st.pyplot(fig)  

    with col2:  
        st.markdown("**Ticket Médio Mensal**")  
        fig, ax = plt.subplots()  
        sns.lineplot(data=df_filtrado, x="Mês", y="Ticket Médio", hue="Ano", marker="o", ax=ax)  
        plt.xticks(rotation=45)  
        st.pyplot(fig)  

    if comparar:  
        st.subheader("🔀 Comparar Períodos")  

        col1, col2 = st.columns(2)  
        with col1:  
            ano1 = st.selectbox("Ano Período 1", df["Ano"].unique())  
            mes1 = st.selectbox("Mês Período 1", df["Mês"].unique())  

        with col2:  
            ano2 = st.selectbox("Ano Período 2", df["Ano"].unique())  
            mes2 = st.selectbox("Mês Período 2", df["Mês"].unique())  

        df1 = df[(df["Ano"] == ano1) & (df["Mês"] == mes1)]  
        df2 = df[(df["Ano"] == ano2) & (df["Mês"] == mes2)]  

        st.write("### 📊 Comparativo de Períodos")  
        col1, col2, col3 = st.columns(3)  

        faturamento1 = df1["Faturamento"].sum()  
        faturamento2 = df2["Faturamento"].sum()  
        diff_fat = faturamento2 - faturamento1  
        perc_fat = (diff_fat / faturamento1) * 100 if faturamento1 != 0 else 0  

        col1.metric("Faturamento", f"R$ {faturamento1:,.2f}", f"{perc_fat:.2f}%")  
        col2.metric("Faturamento", f"R$ {faturamento2:,.2f}")  

        # Repetir para comandas e ticket médio se quiser  

# Dados detalhados  
st.subheader("📄 Dados Detalhados")  
st.dataframe(df_filtrado)  
