import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# 1. ZOOM E LAYOUT
st.set_page_config(page_title="KaBuM! Tracker", layout="wide")

# Injeta CSS para diminuir a escala e melhorar o aproveitamento de tela
st.markdown("""
    <style>
        html { zoom: 0.9; } /* Zoom padrão de entrada */
        .main { padding-top: 2rem; }
        div.stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def init_connection():
    load_dotenv()
    uri = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
    return MongoClient(uri)

@st.cache_data(ttl=600)
def get_data():
    client = init_connection()
    db = client['kabum_tracker']
    df = pd.DataFrame(list(db['historico_precos'].find({}, {'_id': 0})))
    if not df.empty:
        df['data_coleta'] = pd.to_datetime(df['data_coleta'])
    return df

st.title("📊 Monitor de Preços: Memória RAM")

df_raw = get_data()

if not df_raw.empty:
    # FILTRO DE DATA (Última coleta)
    ultima_data = df_raw['data_coleta'].max()
    df = df_raw[df_raw['data_coleta'] == ultima_data].copy()

    # --- TRATAMENTO PARA LIMPAR O VISUAL ---
    # 1. Encurta o nome para não ocupar metade da tela
    df['nome_exibicao'] = df['nome'].apply(lambda x: x[:45] + "..." if len(x) > 45 else x)
    # 2. DDR como categoria
    df['ddr'] = "DDR" + df['ddr'].astype(str)

    # --- FILTROS ---
    st.sidebar.header("Configurações")
    # Slider para limitar a quantidade de itens e o gráfico não ficar gigante
    top_n = st.sidebar.slider("Mostrar quantos produtos?", 5, 30, 15)
    
    df_plot = df.sort_values('preco').head(top_n)

    # --- GRÁFICO ---
    st.subheader(f"Top {top_n} Memórias mais baratas ({ultima_data.strftime('%d/%m %H:%M')})")

    fig = px.bar(
        df_plot,
        x='preco',
        y='nome_exibicao',
        color='ddr',
        orientation='h',
        text='preco',
        # Hover mostra o nome completo original
        hover_data={'nome': True, 'nome_exibicao': False, 'preco': ':.2f'},
        labels={'preco': 'Preço (R$)', 'nome_exibicao': 'Modelo', 'ddr': 'Tipo'},
        color_discrete_map={'DDR4': '#1f77b4', 'DDR5': '#ff7f0e', 'DDR3': '#d62728'}
    )

    fig.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
    
    fig.update_layout(
        margin=dict(l=200, r=100, t=20, b=20), # Aumenta margem esquerda para os nomes
        height=500 + (top_n * 10), # Altura dinâmica
        xaxis_title="Preço (R$)",
        yaxis_title="",
        showlegend=True,
        legend_title_text="Geração"
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Aguardando primeira coleta do robô...")
