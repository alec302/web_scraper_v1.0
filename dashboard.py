import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Configuração da Página
st.set_page_config(page_title="Monitor KaBuM!", layout="wide")

# 1. CONEXÃO COM O MONGO (Com Cache de Recurso)
# O @st.cache_resource garante que a conexão só abra uma vez
@st.cache_resource
def init_connection():
    # Tenta pegar dos secrets do Streamlit (para nuvem) ou do .env (local)
    try:
        # Opção A: Streamlit Cloud
        return MongoClient(st.secrets["MONGO_URI"])
    except:
        # Opção B: Local (.env)
        load_dotenv()
        uri = os.getenv("MONGO_URI")
        return MongoClient(uri)

# 2. BUSCAR DADOS (Com Cache de Dados)
# O ttl=600 faz ele atualizar os dados do banco a cada 10 minutos
@st.cache_data(ttl=600)
def get_data():
    client = init_connection()
    db = client['kabum_tracker']      # Nome do seu Banco
    items = db['historico_precos'].find() # Nome da sua Coleção
    
    # Converte o cursor do Mongo (que é um gerador) para uma lista
    dados = list(items)
    
    # Se não tiver dados, retorna DataFrame vazio
    if not dados:
        return pd.DataFrame()

    # Cria o DataFrame e garante que a data é datetime
    df = pd.DataFrame(dados)
    
    # O Mongo às vezes traz a data como string, garantimos que seja data real
    if 'data_coleta' in df.columns:
        df['data_coleta'] = pd.to_datetime(df['data_coleta'])
        
    return df

# --- INTERFACE DO DASHBOARD ---

st.title("📊 Monitor de Preços: Memória RAM")
st.caption("Dados extraídos diretamente do MongoDB Atlas")

# Carrega os dados
df = get_data()

if df.empty:
    st.warning("⚠️ Nenhum dado encontrado no banco. Rode o 'main.py' para popular o MongoDB!")
else:
    # --- FILTROS LATERAIS ---
    st.sidebar.header("Filtros")
    
    # 1. Filtro de Data (Para ver o "Preço de Hoje")
    datas_disponiveis = df['data_coleta'].dt.date.unique()
    data_atual = st.sidebar.selectbox("Data de Análise:", 
                                      sorted(datas_disponiveis, reverse=True))
    
    # 2. Filtro de Capacidade
    capacidades = sorted(df['capacidade_gb'].unique())
    cap_selecionada = st.sidebar.multiselect("Capacidade (GB):", 
                                           capacidades, default=capacidades)

    # Aplica os filtros
    df_filtrado = df[
        (df['data_coleta'].dt.date == data_atual) & 
        (df['capacidade_gb'].isin(cap_selecionada))
    ]

    # --- KPIs (INDICADORES) ---
    col1, col2, col3 = st.columns(3)
    
    preco_medio = df_filtrado['preco'].mean()
    mais_barato = df_filtrado.nsmallest(1, 'preco').iloc[0] if not df_filtrado.empty else None
    
    col1.metric("Preço Médio (Hoje)", f"R$ {preco_medio:.2f}")
    if mais_barato is not None:
        col2.metric("Mais Barata", f"R$ {mais_barato['preco']:.2f}")
        col3.metric("Modelo", mais_barato['nome'][:30] + "...") # Corta o nome se for longo

    st.markdown("---")

    # --- GRÁFICO 1: COMPARAÇÃO DE PREÇOS (HOJE) ---
    st.subheader(f"Distribuição de Preços em {data_atual}")
    
    fig_bar = px.bar(df_filtrado.sort_values('preco'), 
                     x='preco', y='nome', 
                     color='ddr', # Colore por tipo de DDR
                     orientation='h',
                     title="Top Preços (Do menor para o maior)",
                     hover_data=['capacidade_gb', 'clock'])
    
    # Ajusta altura do gráfico dinamicamente
    fig_bar.update_layout(height=400 + (len(df_filtrado) * 10))
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- GRÁFICO 2: EVOLUÇÃO NO TEMPO (HISTÓRICO) ---
    st.markdown("---")
    st.subheader("📈 Evolução de Preço (Histórico)")
    
    # Dropdown para escolher UM produto e ver o histórico dele
    lista_produtos = df['nome'].unique()
    produto_escolhido = st.selectbox("Escolha uma memória para ver a variação:", lista_produtos)
    
    # Filtra só aquele produto em TODAS as datas
    df_historico = df[df['nome'] == produto_escolhido].sort_values('data_coleta')
    
    if len(df_historico) > 1:
        fig_linha = px.line(df_historico, x='data_coleta', y='preco', 
                            markers=True, title=f"Histórico: {produto_escolhido}")
        st.plotly_chart(fig_linha, use_container_width=True)
    else:
        st.info("Ainda não há histórico suficiente para gerar gráfico de linha (precisa de pelo menos 2 dias de coleta).")

    # --- TABELA DE DADOS BRUTOS ---
    with st.expander("Ver Dados Brutos"):
        # Removemos o _id do Mongo que é feio de ver na tabela
        cols_para_mostrar = [c for c in df_filtrado.columns if c != '_id']
        st.dataframe(df_filtrado[cols_para_mostrar])
