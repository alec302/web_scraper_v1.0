import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Configuração da página
st.set_page_config(page_title="Monitor de Preços KaBuM!", layout="wide")

@st.cache_resource
def init_connection():
    load_dotenv()
    # Tenta pegar a URI do Streamlit Secrets ou do .env local
    uri = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
    return MongoClient(uri)

@st.cache_data(ttl=600)
def get_data():
    client = init_connection()
    db = client['kabum_tracker']
    colecao = db['historico_precos']
    
    # Busca os dados e converte para DataFrame
    df = pd.DataFrame(list(colecao.find({}, {'_id': 0})))
    
    if not df.empty:
        # Garante que a data está no formato correto
        df['data_coleta'] = pd.to_datetime(df['data_coleta'])
    return df

# --- INTERFACE ---
st.title("📊 Monitor de Memórias RAM - KaBuM!")

df_completo = get_data()

if df_completo.empty:
    st.warning("O banco de dados está vazio. Certifique-se de que o robô (main.py) rodou com sucesso.")
else:
    # 1. PEGAR APENAS A COLETA MAIS RECENTE (Evita somar preços históricos)
    ultima_data = df_completo['data_coleta'].max()
    df_hoje = df_completo[df_completo['data_coleta'] == ultima_data].copy()

    # 2. LIMPEZA DOS DADOS PARA O GRÁFICO
    # Transforma DDR em texto para a legenda não virar uma barra de gradiente
    df_hoje['ddr'] = "DDR" + df_hoje['ddr'].astype(str)
    
    # --- FILTROS LATERAIS ---
    st.sidebar.header("Filtros de Hoje")
    geracao = st.sidebar.multiselect("Geração:", options=df_hoje['ddr'].unique(), default=df_hoje['ddr'].unique())
    
    df_filtrado = df_hoje[df_hoje['ddr'].isin(geracao)]

    # --- INDICADORES ---
    col1, col2 = st.columns(2)
    col1.metric("Última Atualização", ultima_data.strftime("%d/%m/%Y %H:%M"))
    col2.metric("Produtos Encontrados", len(df_filtrado))

    # --- GRÁFICO DE BARRAS (CORRIGIDO) ---
    st.subheader("Comparativo de Preços Atuais")
    
    fig = px.bar(
        df_filtrado.sort_values('preco', ascending=True),
        x='preco',
        y='nome',
        color='ddr', # Agora as cores serão categorias fixas
        orientation='h',
        text='preco',
        labels={'preco': 'Preço (R$)', 'nome': 'Modelo', 'ddr': 'Tipo'},
        # Cores específicas para facilitar a batida de olho
        color_discrete_map={'DDR4': '#1f77b4', 'DDR5': '#ff7f0e'}
    )

    # Ajustes finos no visual
    fig.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
    fig.update_layout(
        yaxis={'categoryorder':'total ascending'},
        height=600,
        margin=dict(l=0, r=50, t=30, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- TABELA DETALHADA ---
    with st.expander("Ver lista completa de preços"):
        st.dataframe(df_filtrado.sort_values('preco'))
