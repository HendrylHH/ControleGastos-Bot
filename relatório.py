import streamlit as st
import pandas as pd
import glob
import os

st.title("Dashboard de Gastos Mensais")

csv_files = glob.glob("relatorio_*.csv")

if not csv_files:
    st.write("Nenhum arquivo de relatório encontrado!")
else:
    df_list = []
    for file in csv_files:
        df = pd.read_csv(file)
        # Extrai o mês do nome do arquivo, assumindo o formato relatorio_YYYY-MM.csv
        month = os.path.basename(file).replace("relatorio_", "").replace(".csv", "")
        df["mês"] = month
        df_list.append(df)
    
    df_all = pd.concat(df_list, ignore_index=True)
    
    st.subheader("Dados Brutos")
    st.dataframe(df_all)
        
    meses = sorted(df_all["mês"].unique())
    selected_mes = st.selectbox("Selecione o mês", meses)
    
    df_mes = df_all[df_all["mês"] == selected_mes]
    
    st.subheader(f"Gastos para o mês: {selected_mes}")
    st.dataframe(df_mes)
        
    st.subheader("Gastos por Categoria")
    df_cat = df_mes.groupby("categoria")["valor"].sum().reset_index()
    df_cat = df_cat.set_index("categoria")
    st.bar_chart(df_cat)
    
    st.subheader("Comparação entre Meses")
    df_comparacao = df_all.groupby(["mês", "categoria"])["valor"].sum().reset_index()
    
    df_pivot = df_comparacao.pivot(index="categoria", columns="mês", values="valor").fillna(0)
    
    st.dataframe(df_pivot)
    st.bar_chart(df_pivot)
