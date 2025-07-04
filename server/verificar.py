import json
import subprocess
from datetime import datetime
import subprocess
import csv

# Carrega o JSON original
with open("audio-e-video.json", "r", encoding="utf-8") as f:
    ambientes = json.load(f)

def ping(ip):
    try:
        subprocess.check_output(["ping", "-n", "1", ip], stderr=subprocess.DEVNULL)
        return "Online"
    except subprocess.CalledProcessError:
        return "Offline"

equipamentos_testados = []

for andar_nome, andar in ambientes["andares"].items():
    for sala in andar["salas"]:
        for equipamento in sala["equipamentos"]:
            
            if "ip" in equipamento.get("dados", {}):
                ip = equipamento["dados"]["ip"]
                print({ip})
                if not ip:  # Se ip for vazio, None ou string vazia
                    status = "Sem Status"
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    equipamentos_testados.append({
                        "nome": equipamento["nome"],
                        "ip": ip,
                        "status": status,
                        "timestamp": timestamp,
                        "sala": sala["nome"],
                        "andar": andar["titulo"]
                    })
                else:
                    status = ping(ip)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    equipamentos_testados.append({
                        "nome": equipamento["nome"],
                        "ip": ip,
                        "status": status,
                        "timestamp": timestamp,
                        "sala": sala["nome"],
                        "andar": andar["titulo"]
                    })

# Salva o JSON resumido
with open("resultados_ping_resumido.json", "w", encoding="utf-8") as f:
    json.dump(equipamentos_testados, f, indent=4, ensure_ascii=False)

# Converte para CSV
csv_file = "G:/Meu Drive/inventario/resultados_ping.csv"
with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Nome", "IP", "Status", "Timestamp", "Sala", "Andar"])
    for equipamento in equipamentos_testados:
        writer.writerow([
            equipamento["nome"],
            equipamento["ip"],
            equipamento["status"],
            equipamento["timestamp"],
            equipamento["sala"],
            equipamento["andar"]
        ])


print("Arquivo 'resultados_ping_resumido.json' criado com sucesso.")
print("Arquivo 'resultados_ping.csv' criado com sucesso e enviado para o Google Drive.")


subprocess.run(['python', 'server/ocupacao_salas.py'],check=True)
print("Verificado salas ocupadas com sensor com sucesso!.")

subprocess.run(['python', 'server/ups.py'],check=True)
print("Verificado UPS com sucesso!.")
