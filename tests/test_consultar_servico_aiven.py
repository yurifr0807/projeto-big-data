"""Testes do cliente de consulta à API da Aiven, sem credenciais reais ou rede."""

from etl import consultar_servico_aiven as c


class RespostaFalsa:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = ""

    def json(self):
        return self._payload


class SessaoFalsa:
    def __init__(self, resposta):
        self.resposta = resposta
        self.chamadas = []

    def get(self, url, headers=None, timeout=None):
        self.chamadas.append({"url": url, "headers": headers, "timeout": timeout})
        return self.resposta


def test_obter_token_prefere_aiven_token():
    assert c.obter_token({"AIVEN_TOKEN": "novo", "AIVEN_API_TOKEN": "antigo"}) == "novo"


def test_obter_token_usa_fallback_legado():
    assert c.obter_token({"AIVEN_API_TOKEN": "antigo"}) == "antigo"


def test_obter_token_ausente_retorna_none():
    assert c.obter_token({}) is None


def test_main_sem_token_nao_chama_rede(capsys):
    sessao = SessaoFalsa(RespostaFalsa())
    assert c.main(env={}, session=sessao) == 1
    assert sessao.chamadas == []
    assert "AIVEN_TOKEN" in capsys.readouterr().out


def test_main_usa_aiven_token_e_consulta_servico():
    payload = {
        "service": {
            "service_name": "pg-teste",
            "state": "RUNNING",
            "plan": "free-1-1gb",
            "cloud_name": "do-sfo",
            "service_type": "pg",
            "user_config": {"pg_version": "18"},
        }
    }
    sessao = SessaoFalsa(RespostaFalsa(payload=payload))
    assert c.main(env={"AIVEN_TOKEN": "token-ficticio"}, session=sessao) == 0
    assert len(sessao.chamadas) == 1
    chamada = sessao.chamadas[0]
    assert chamada["headers"]["Authorization"] == "aivenv1 token-ficticio"
    assert "pg-4f83b4b" in chamada["url"]
