import requests
from bs4 import BeautifulSoup
import json

def pegar_dados_kabum():
    url = "https://www.kabum.com.br/hardware/memoria-ram"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.google.com/',
    }
    
    produtos = []

    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tag = soup.find('script', id='__NEXT_DATA__')
            
        # 1. Transforma o texto da tag <script> em um dicionário Python
            raw_data = json.loads(script_tag.string)
            
            # 2. O campo 'data' da KaBuM geralmente é uma STRING que contém outro JSON.
            # Precisamos extrair essa string e dar um novo loads() nela.
            string_interna_json = raw_data['props']['pageProps']['data']
            
            # 3. Agora sim, transformamos a string interna em dicionário
            dados_internos = json.loads(string_interna_json)
            
            # 4. Navegamos até a lista final de produtos
            lista_final = dados_internos['catalogServer']['data']

            for item in lista_final:
                produtos.append({
                    'nome': item.get('name', 'Sem Nome'),
                    'preco': float(item.get('price', 0)),
                    'link': 'kabum.com.br/produto/' + str(item.get('code'))
                })
            print(f"Scraper: Encontrei {len(produtos)} produtos.")
            return produtos
            
        else:
            print("Erro ao acessar o site.")
            return []

    except Exception as e:
        print(f"Erro no scraper: {e}")
        return []
