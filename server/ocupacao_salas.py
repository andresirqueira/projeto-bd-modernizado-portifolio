import time
import pandas as pd
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options

# Configurar o Edge WebDriver para modo headless
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')

service = Service('C:\\WebDriver\\msedgedriver.exe')
driver = webdriver.Edge(service=service, options=options)

# Carregar o JSON dos andares
with open('audio-e-video.json', encoding='utf-8') as f:
    andares_json = json.load(f)

# Extrair sensores do JSON
# Extrair sensores do JSON
sensores = []
for andar in andares_json['andares'].values():
    for sala in andar.get('salas', []):
        nome_sala = sala.get('nome', '')
        for eq in sala.get('equipamentos', []):
            if eq.get('nome', '').lower() == 'sensor':
                dados = eq.get('dados', {})
                ip = dados.get('ip')
                if ip:
                    if nome_sala == "Sala 02":
                        url = "http://10.12.187.121/#/stage/(child:status)"
                        xpath = './/div[@class="ui-grid-col-8 breakword ng-star-inserted"]'
                    else:
                        url = f"http://{ip}/#/stage/(child:status)"
                        xpath = './/div[@class="ui-grid-col-8 ng-star-inserted"]'
                    nome = f"{nome_sala} - Sensor"
                    sensores.append({'Nome': nome, 'URL': url, 'XPath': xpath})

# Lista para armazenar os dados
data = []

for entry in sensores:
    nome = entry['Nome'].replace(' - Sensor', '')  # Remove o sufixo
    url = entry['URL']
    xpath = entry['XPath']
    print(f"Processando URL: {url} com XPath: {xpath}")
    driver.get(url)

    try:
        wait = WebDriverWait(driver, 15)
        accept_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="okBtn"]')))
        accept_button.click()

        section_header = wait.until(EC.element_to_be_clickable((By.XPATH, '//p-accordiontab[@id="statusOccupancy"]//a')))
        driver.execute_script("arguments[0].click();", section_header)

        accordion_tab = wait.until(EC.visibility_of_element_located((By.ID, 'statusOccupancy')))
        time.sleep(5)

        div_tags = accordion_tab.find_elements(By.XPATH, xpath)
        if div_tags:
            div_value = div_tags[0].text.strip()
            data.append({'Nome': nome, 'Status': div_value})
        else:
            data.append({'Nome': nome, 'Status': 'Tag div não encontrada'})
    except Exception as e:
        print(f"Erro ao processar a URL {url}: {e}")
        data.append({'Nome': nome, 'Status': 'Indefinido'})

# Salva apenas Nome e Status no JSON, sem o sufixo
df = pd.DataFrame(data)
df.to_json('salas_ocupadas.json', orient='records', force_ascii=False, indent=2)

driver.quit()
time.sleep(3)