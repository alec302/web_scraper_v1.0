import os
from scraper import pegar_dados_kabum
from storage import processar_e_salvar
from dotenv import load_dotenv

def main():
    # 1. Tenta carregar o .env (funciona no Mac, é ignorado no GitHub)
    load_dotenv()
    
    # 2. Verifica se a senha do banco existe no sistema
    if not os.getenv("MONGO_URI"):
        print("❌ ERRO: Variável MONGO_URI não encontrada!")
        return

    print("--- 🤖 Iniciando Robô Diário ---")
    
    # Passo 1: Pega os dados
    dados = pegar_dados_kabum()
    
    if dados:
        # Passo 2: Processa e joga no banco
        processar_e_salvar(dados)
        print("--- ✅ Sucesso: Dados salvos no MongoDB ---")
    else:
        print("--- ⚠️ Aviso: Nenhum dado coletado hoje ---")

if __name__ == "__main__":
    main()
