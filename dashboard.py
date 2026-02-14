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
    uri = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")
    return MongoClient(uri)

@st.cache_data(ttl=600)
def get_data():
    client = init_connection()
    db = client['kabum_tracker']
    colecao = db['historico_precos']
    
    df = pd.DataFrame(list(colecao.find({}, {'_id': 0})))
    
    if not df.empty:
        # Converte para datetime e remove os segundos para ficar mais limpo no filtro
        df['data_coleta'] = pd.to_datetime(df['data_coleta'])
    return df

st.title("📊 Monitor de Memórias RAM - KaBuM!")

df_completo = get_data()

if df_completo.empty:
    st.warning("O banco de dados está vazio. Certifique-se de que o robô rodou.")
else:
# --- NOVO: LÓGICA DE FILTRO POR HORA EXATA ---
    st.sidebar.header("Filtros")
    
    # 1. Pegamos os carimbos de hora exatos (Timestamp), não só a data
    # Ordenamos do mais recente para o mais antigo
    datas_disponiveis = sorted(df_completo['data_coleta'].unique(), reverse=True)
    
    # 2. Selectbox agora escolhe uma COLETA ESPECÍFICA
    # Usamos format_func para mostrar a hora bonita na caixinha
    data_escolhida = st.sidebar.selectbox(
        "Escolha a coleta (Data/Hora):", 
        datas_disponiveis,
        format_func=lambda x: pd.to_datetime(x).strftime("%d/%m/%Y às %H:%M:%S")
    )
    
    # 3. Filtra EXATAMENTE por aquele carimbo de tempo
    # Agora ele vai pegar só os 20 itens daquela execução específica
    df_hoje = df_completo[df_completo['data_coleta'] == data_escolhida].copy()
    
    # Filtro de Geração (continua igual)
    geracao = st.sidebar.multiselect(
        "Geração:", 
        options=df_hoje['ddr'].unique(), 
        default=df_hoje['ddr'].unique()
    )
    
    df_filtrado = df_hoje[df_hoje['ddr'].isin(geracao)]

    # --- INDICADORES ---
    col1, col2 = st.columns(2)
    # Mostra a data escolhida no indicador
    col1.metric("Data Visualizada", data_escolhida.strftime("%d/%m/%Y"))
    col2.metric("Produtos Encontrados", len(df_filtrado))

    # --- GRÁFICO ---
    st.subheader(f"Comparativo de Preços em {data_escolhida.strftime('%d/%m/%Y')}")
    
    if not df_filtrado.empty:
        fig = px.bar(
            df_filtrado.sort_values('preco', ascending=True),
            x='preco',
            y='nome',
            color='ddr',
            orientation='h',
            text='preco',
            labels={'preco': 'Preço (R$)', 'nome': 'Modelo', 'ddr': 'Tipo'},
            color_discrete_map={'DDR4': '#1f77b4', 'DDR5': '#ff7f0e'}
        )

        fig.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
        fig.update_layout(
            yaxis={'categoryorder':'total ascending'},
            height=max(500, len(df_filtrado) * 30), # Altura dinâmica baseada na qtd de itens
            margin=dict(l=0, r=50, t=30, b=0)
        )

        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Ver lista completa de preços"):
            st.dataframe(df_filtrado.sort_values('preco'))
    else:
        st.info("Nenhum produto encontrado para os filtros selecionados.")
