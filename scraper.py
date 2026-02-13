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
            
            # Navegando no JSON da Kabum
            raw_data = json.loads(script_tag.string)
            lista_json = raw_data['props']['pageProps']['data']['catalogServer']['data']

            for item in lista_json:
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
