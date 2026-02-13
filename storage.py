import pandas as pd
import re
from datetime import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# --- CONFIGURAÇÃO ---
# Cole sua string do MongoDB Atlas aqui
load_dotenv()


def processar_e_salvar(lista_bruta):
    if not lista_bruta:
        print("Nenhum dado para salvar.")
        return

    # 1. Cria o DataFrame e processa com Regex
    df = pd.DataFrame(lista_bruta)

    # Extrai GB
    df['capacidade_gb'] = df['nome'].str.extract(r'(\d+)\s*GB', flags=re.IGNORECASE, expand=False)
    df['capacidade_gb'] = df['capacidade_gb'].fillna(0).astype(int)

    # Extrai MHz ou MT/s
    df['clock'] = df['nome'].str.extract(r'(\d+)\s*(?:MHZ|MT)', flags=re.IGNORECASE, expand=False)
    df['clock'] = df['clock'].fillna(0).astype(int)

    # Extrai DDR
    df['ddr'] = df['nome'].str.extract(r'DDR\s*(\d+)', flags=re.IGNORECASE, expand=False)
    df['ddr'] = df['ddr'].fillna(0).astype(int)

    # 2. Adiciona a data de hoje (Importante para o histórico!)
    df['data_coleta'] = datetime.now()

    # 2. Pega a URI e verifica se ela existe
    uri = os.getenv("MONGO_URI")
    
    if not uri:
        print("❌ ERRO: A variável MONGO_URI está vazia ou não foi carregada do .env!")
        return

    try:
        # 3. Conecta usando a URI do Atlas
        client = MongoClient(uri)
        
        # Testa a conexão imediatamente com um ping
        client.admin.command('ping')
        
        db = client['kabum_tracker']
        col = db['historico_precos']
        
        dados_finais = df.to_dict('records')
        col.insert_many(dados_finais)
        
        # Mova o print de sucesso para DENTRO do try
        print(f"--- ✅ Sucesso: {len(dados_finais)} dados salvos no MongoDB Atlas ---")
        
    except Exception as e:
        print(f"❌ Erro ao salvar no banco: {e}")
