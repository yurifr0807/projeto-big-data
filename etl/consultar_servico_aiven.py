import sys
import os
import json
import requests

token = os.environ.get("AIVEN_API_TOKEN")
if not token:
    print("ERRO: A variável de ambiente AIVEN_API_TOKEN não está definida.")
    print("Defina-a no PowerShell com: $env:AIVEN_API_TOKEN = 'seu_token'")
    sys.exit(1)

project = "projeto-bigdata"
service = "pg-4f83b4b"
url = f"https://api.aiven.io/v1/project/{project}/service/{service}"

headers = {
    "Authorization": f"aivenv1 {token}",
    "Content-Type": "application/json"
}

try:
    resp = requests.get(url, headers=headers, timeout=20)
    if resp.status_code == 200:
        data = resp.json().get("service", {})
        print("=== DADOS OFICIAIS DO SERVIÇO NA AIVEN ===")
        print(f"Nome do Serviço: {data.get('service_name')}")
        print(f"Status Atual:    {data.get('state')}")
        print(f"Plano (Plan):    {data.get('plan')}")
        print(f"Região / Cloud:  {data.get('cloud_name')}")
        print(f"Tipo:            {data.get('service_type')}")
        user_config = data.get("user_config", {})
        print(f"Versão PG:       {user_config.get('pg_version')}")
        print("=========================================")
    elif resp.status_code == 401:
        print("ERRO 401: Token inválido ou sem permissão de leitura.")
    elif resp.status_code == 404:
        print(f"ERRO 404: Serviço '{service}' ou projeto '{project}' não encontrado.")
    else:
        print(f"ERRO {resp.status_code}: {resp.text}")
except Exception as e:
    print(f"Falha de conexão com a API da Aiven: {e}")
