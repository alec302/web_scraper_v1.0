import pandas as pd
import re
from datetime import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# --- CONFIGURAÇÃO ---
# Cole sua string do MongoDB Atlas aqui
load_dotenv()
uri = os.getenv("MONGO_KEY")


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

    # 3. Conecta no Mongo e Salva
    try:
        client = MongoClient(uri)
        db = client['kabum_tracker']     # Nome do Banco
        col = db['historico_precos']     # Nome da Coleção
        
        # Converte para lista de dicionários (O Mongo precisa disso)
        dados_finais = df.to_dict('records')
        
        col.insert_many(dados_finais)
        print(f"Sucesso! {len(dados_finais)} registros salvos no MongoDB.")
        
    except Exception as e:
        print(f"Erro ao salvar no banco: {e}")
