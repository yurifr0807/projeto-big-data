"""Consulta somente leitura dos metadados do serviço PostgreSQL na Aiven.

A variável principal é ``AIVEN_TOKEN`` (a mesma lida pelo provider Terraform).
``AIVEN_API_TOKEN`` permanece como fallback de compatibilidade para ambientes
que já usavam o nome antigo. Nenhum token é gravado ou impresso por este módulo.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Mapping

import requests

PROJECT_PADRAO = "projeto-bigdata"
SERVICO_PADRAO = "pg-4f83b4b"
URL_API = "https://api.aiven.io/v1/project/{project}/service/{service}"


def obter_token(env: Mapping[str, str] | None = None) -> str | None:
    """Retorna ``AIVEN_TOKEN`` ou, como compatibilidade, ``AIVEN_API_TOKEN``."""
    ambiente = os.environ if env is None else env
    return ambiente.get("AIVEN_TOKEN") or ambiente.get("AIVEN_API_TOKEN")


def consultar_servico(
    token: str,
    *,
    project: str = PROJECT_PADRAO,
    service: str = SERVICO_PADRAO,
    session: Any | None = None,
    timeout: int = 20,
) -> Any:
    """Executa a chamada HTTP de leitura e devolve a resposta bruta."""
    cliente = session or requests
    url = URL_API.format(project=project, service=service)
    headers = {
        "Authorization": f"aivenv1 {token}",
        "Content-Type": "application/json",
    }
    return cliente.get(url, headers=headers, timeout=timeout)


def main(env: Mapping[str, str] | None = None, session: Any | None = None) -> int:
    """Executa a consulta e imprime os metadados públicos do serviço.

    Retorna um código de saída compatível com CLI (0 = sucesso).
    """
    token = obter_token(env)
    if not token:
        print("ERRO: defina AIVEN_TOKEN (ou o legado AIVEN_API_TOKEN) no ambiente.")
        print("PowerShell: $env:AIVEN_TOKEN = '<seu-token>'")
        return 1

    try:
        resp = consultar_servico(token, session=session)
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
            return 0
        if resp.status_code == 401:
            print("ERRO 401: Token inválido ou sem permissão de leitura.")
            return 2
        if resp.status_code == 404:
            print(
                f"ERRO 404: Serviço '{SERVICO_PADRAO}' ou projeto "
                f"'{PROJECT_PADRAO}' não encontrado."
            )
            return 3
        print(f"ERRO {resp.status_code}: {resp.text}")
        return 4
    except Exception as exc:  # pragma: no cover - depende da rede
        print(f"Falha de conexão com a API da Aiven: {exc}")
        return 5


if __name__ == "__main__":
    sys.exit(main())
