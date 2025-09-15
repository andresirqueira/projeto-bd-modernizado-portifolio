import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from datetime import datetime
import time
import tempfile
import shutil
import os

# Escolha do navegador
navegador = "edge"  # ou "edge"

user_data_dir = tempfile.mkdtemp() 

# Configurar WebDriver
if navegador == "chrome":
    options = ChromeOptions()
    options.add_argument(f'--user-data-dir={user_data_dir}')
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    service = ChromeService("C:\\WebDriver\\chromedriver.exe")  # atualize o caminho
    driver = webdriver.Chrome(service=service, options=options)

elif navegador == "edge":
    options = EdgeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    service = EdgeService("C:\\WebDriver\\msedgedriver.exe")  # atualize o caminho
    driver = webdriver.Edge(service=service, options=options)

try:
    driver.get("http://10.12.65.151/")
    wait = WebDriverWait(driver, 30)
    iframe = wait.until(EC.presence_of_element_located((By.ID, "showpage")))
    driver.switch_to.frame(iframe)
    time.sleep(10)

    # Captura de dados
    def get_value(id_):
        return float(wait.until(EC.presence_of_element_located((By.ID, id_))).text)

    l1, l2, l3 = get_value("inputVoltage"), get_value("inputVoltageS"), get_value("inputVoltageT")
    l1o, l2o, l3o = get_value("outputVoltage"), get_value("outputVoltageS"), get_value("outputVoltageT")
    l1c, l2c, l3c = get_value("outputCurrent"), get_value("outputCurrentS"), get_value("outputCurrentT")

    ups_mode = wait.until(EC.presence_of_element_located((By.ID, "upsMode"))).text
    ups_temp = wait.until(EC.presence_of_element_located((By.ID, "upsTemp"))).text
    ups_battery = wait.until(EC.presence_of_element_located((By.ID, "batteryCapacity"))).text
    ups_backup = wait.until(EC.presence_of_element_located((By.ID, "backupTime"))).text

    # Timestamp
    now = datetime.now()
    timestamp = now.strftime("%d-%m-%Y %H:%M:%S")

    # Dados em JSON
    dados = {
        "timestamp": timestamp,
        "ups_mode": ups_mode,
        "ups_temp": ups_temp,
        "ups_battery": ups_battery,
        "ups_backup": ups_backup,
        "entrada": [l1, l2, l3],
        "saida": [l1o, l2o, l3o],
        "corrente": [l1c, l2c, l3c]
    }

    # Salvar JSON
    with open("dados_ups.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

    print("Dados salvos como 'dados_ups.json'")

except Exception as e:
    import traceback
    print(f"Ocorreu um erro: {e}")
    traceback.print_exc()

finally:
    driver.quit()
    shutil.rmtree(user_data_dir, ignore_errors=True)

