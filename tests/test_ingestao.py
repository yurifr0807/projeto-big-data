"""Testes de ingestão: sem rede, sem serviços externos (sessão HTTP simulada, fixtures pequenas em tmp_path)."""

import json

import pandas as pd
import pytest
import requests

from etl import ingestao
from etl.ingestao import IngestaoErro


class RespostaFalsa:
    def __init__(self, conteudo=b"", status=200):
        self._conteudo = conteudo
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def raise_for_status(self):
        if self.status >= 400:
            raise requests.exceptions.HTTPError(f"HTTP {self.status}")

    def iter_content(self, chunk_size=1):
        for i in range(0, len(self._conteudo), chunk_size):
            yield self._conteudo[i:i + chunk_size]


class SessaoFalsa:
    def __init__(self, resposta=None, erro=None):
        self.resposta, self.erro, self.chamadas, self.kwargs = resposta, erro, 0, None

    def get(self, url, **kwargs):
        self.chamadas += 1
        self.kwargs = kwargs
        if self.erro:
            raise self.erro
        return self.resposta


URL = "https://exemplo.gov.br/arquivo.csv"


def test_download_grava_arquivo_e_manifesto(tmp_path):
    sessao = SessaoFalsa(RespostaFalsa(b"a,b\n1,2\n"))
    res = ingestao.baixar_arquivo(URL, tmp_path / "x" / "arquivo.csv", dir_bruto=tmp_path, sessao=sessao)
    assert res.baixado and res.caminho.read_bytes() == b"a,b\n1,2\n"
    manifesto = json.loads((tmp_path / ingestao.NOME_MANIFESTO).read_text(encoding="utf-8"))
    assert manifesto["arquivo.csv"]["origem"] == URL
    assert manifesto["arquivo.csv"]["sha256"] == res.sha256
    # TLS sempre verificado e timeout presente
    assert sessao.kwargs["verify"] is True
    assert sessao.kwargs["timeout"] == ingestao.TIMEOUT_PADRAO


def test_nao_baixa_novamente_arquivo_ja_ingerido(tmp_path):
    destino = tmp_path / "arquivo.csv"
    sessao = SessaoFalsa(RespostaFalsa(b"a\n1\n"))
    ingestao.baixar_arquivo(URL, destino, dir_bruto=tmp_path, sessao=sessao)
    res = ingestao.baixar_arquivo(URL, destino, dir_bruto=tmp_path, sessao=sessao)
    assert sessao.chamadas == 1 and res.baixado is False


def test_arquivo_bruto_alterado_apos_ingestao_gera_erro(tmp_path):
    destino = tmp_path / "arquivo.csv"
    sessao = SessaoFalsa(RespostaFalsa(b"a\n1\n"))
    ingestao.baixar_arquivo(URL, destino, dir_bruto=tmp_path, sessao=sessao)
    destino.write_bytes(b"adulterado")
    with pytest.raises(IngestaoErro, match="imutáveis"):
        ingestao.baixar_arquivo(URL, destino, dir_bruto=tmp_path, sessao=sessao)


def test_erro_http_levanta_ingestao_erro_sem_deixar_parcial(tmp_path):
    destino = tmp_path / "arquivo.csv"
    with pytest.raises(IngestaoErro, match="Falha no download"):
        ingestao.baixar_arquivo(URL, destino, dir_bruto=tmp_path, sessao=SessaoFalsa(RespostaFalsa(b"", 404)))
    assert not destino.exists() and not list(tmp_path.glob("*.parcial"))


def test_erro_tls_orienta_ca_bundle_e_nao_desativa_verificacao(tmp_path):
    sessao = SessaoFalsa(erro=requests.exceptions.SSLError("self-signed certificate in certificate chain"))
    with pytest.raises(IngestaoErro, match="CA_BUNDLE"):
        ingestao.baixar_arquivo(URL, tmp_path / "a.csv", dir_bruto=tmp_path, sessao=sessao)


def test_timeout_vira_ingestao_erro(tmp_path):
    sessao = SessaoFalsa(erro=requests.exceptions.ConnectTimeout("timeout"))
    with pytest.raises(IngestaoErro):
        ingestao.baixar_arquivo(URL, tmp_path / "a.csv", dir_bruto=tmp_path, sessao=sessao)


def test_download_vazio_e_rejeitado(tmp_path):
    with pytest.raises(IngestaoErro, match="vazio"):
        ingestao.baixar_arquivo(URL, tmp_path / "a.csv", dir_bruto=tmp_path, sessao=SessaoFalsa(RespostaFalsa(b"")))


def test_url_invalida():
    with pytest.raises(IngestaoErro, match="URL inválida"):
        ingestao.baixar_arquivo("ftp://x/y", ingestao.DIR_BRUTO / "nao_usado.csv")


def test_ca_bundle_inexistente_gera_erro(monkeypatch, tmp_path):
    monkeypatch.setenv("CA_BUNDLE", str(tmp_path / "nao_existe.pem"))
    with pytest.raises(IngestaoErro, match="CA_BUNDLE"):
        ingestao.baixar_arquivo(URL, tmp_path / "a.csv", dir_bruto=tmp_path, sessao=SessaoFalsa(RespostaFalsa(b"x")))


def test_ca_bundle_valido_e_repassado_ao_requests(monkeypatch, tmp_path):
    pem = tmp_path / "ca.pem"
    pem.write_text("-----BEGIN CERTIFICATE-----\n", encoding="utf-8")
    monkeypatch.setenv("CA_BUNDLE", str(pem))
    sessao = SessaoFalsa(RespostaFalsa(b"x"))
    ingestao.baixar_arquivo(URL, tmp_path / "a.csv", dir_bruto=tmp_path, sessao=sessao)
    assert sessao.kwargs["verify"] == str(pem)


def test_importacao_manual_preserva_original_e_registra(tmp_path):
    origem = tmp_path / "downloads" / "painel.csv"
    origem.parent.mkdir()
    origem.write_text("a;b\n1;2\n", encoding="utf-8")
    bruto = tmp_path / "bruto"
    res = ingestao.importar_arquivo_manual(
        origem, subpasta="cnpq/painel_pq", descricao_origem="painel X em 2026-11-05", dir_bruto=bruto
    )
    assert res.baixado and (bruto / "cnpq/painel_pq/painel.csv").exists() and origem.exists()
    m = ingestao.carregar_manifesto(bruto)
    assert m["cnpq/painel_pq/painel.csv"]["tipo_origem"] == "manual"
    # reimportar o mesmo arquivo é idempotente
    assert ingestao.importar_arquivo_manual(
        origem, subpasta="cnpq/painel_pq", descricao_origem="x", dir_bruto=bruto
    ).baixado is False


def test_importacao_manual_nao_sobrescreve_arquivo_diferente(tmp_path):
    bruto = tmp_path / "bruto"
    (bruto / "s").mkdir(parents=True)
    (bruto / "s" / "p.csv").write_text("antigo", encoding="utf-8")
    novo = tmp_path / "p.csv"
    novo.write_text("novo", encoding="utf-8")
    with pytest.raises(IngestaoErro, match="arquivo diferente"):
        ingestao.importar_arquivo_manual(novo, subpasta="s", descricao_origem="x", dir_bruto=bruto)
    assert (bruto / "s" / "p.csv").read_text(encoding="utf-8") == "antigo"


def test_importacao_manual_arquivo_inexistente_ou_vazio(tmp_path):
    with pytest.raises(IngestaoErro, match="não encontrado"):
        ingestao.importar_arquivo_manual(tmp_path / "x.csv", subpasta="s", descricao_origem="x", dir_bruto=tmp_path)
    vazio = tmp_path / "v.csv"
    vazio.write_bytes(b"")
    with pytest.raises(IngestaoErro, match="vazio"):
        ingestao.importar_arquivo_manual(vazio, subpasta="s", descricao_origem="x", dir_bruto=tmp_path)


def test_manifesto_corrompido_gera_erro(tmp_path):
    (tmp_path / ingestao.NOME_MANIFESTO).write_text("{nao eh json", encoding="utf-8")
    with pytest.raises(IngestaoErro, match="corrompido"):
        ingestao.carregar_manifesto(tmp_path)


# ---------------- leitura ---------------- #
def test_ler_csv_latin1_ponto_e_virgula_como_texto(tmp_path):
    arq = tmp_path / "a.csv"
    arq.write_bytes("Nome;Valor\nJosé;1.234,50\nAna;\n".encode("cp1252"))
    df = ingestao.ler_csv(arq)
    assert list(df.columns) == ["Nome", "Valor"]
    assert df.loc[0, "Nome"] == "José" and df.loc[0, "Valor"] == "1.234,50"
    assert df.loc[1, "Valor"] == ""  # vazio preservado como texto; tratamento posterior decide
    assert all(t == "object" or str(t).startswith("str") for t in df.dtypes.astype(str))


def test_ler_csv_utf8_bom_virgula(tmp_path):
    arq = tmp_path / "a.csv"
    arq.write_bytes("\ufeffa,b\n1,2\n".encode("utf-8"))
    assert list(ingestao.ler_csv(arq).columns) == ["a", "b"]


def test_ler_csv_vazio_gera_erro(tmp_path):
    arq = tmp_path / "v.csv"
    arq.write_text("", encoding="utf-8")
    with pytest.raises(IngestaoErro):
        ingestao.ler_csv(arq)


def test_chunks_selecionam_colunas_e_cobrem_todas_as_linhas(tmp_path):
    arq = tmp_path / "g.csv"
    linhas = "\n".join(f"{i},x{i},lixo{i}" for i in range(25))
    arq.write_text(f"id, nome ,extra\n{linhas}\n", encoding="utf-8")
    lotes = list(ingestao.ler_csv_em_chunks(arq, colunas=["id", "nome"], tamanho_chunk=10))
    assert [len(l) for l in lotes] == [10, 10, 5]
    assert all("extra" not in l.columns for l in lotes)
    assert pd.concat(lotes)["id"].tolist() == [str(i) for i in range(25)]


def test_chunks_coluna_ausente_gera_erro(tmp_path):
    arq = tmp_path / "g.csv"
    arq.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(IngestaoErro, match="ausentes"):
        list(ingestao.ler_csv_em_chunks(arq, colunas=["a", "z"]))


def test_ler_json(tmp_path):
    arq = tmp_path / "a.json"
    arq.write_text(json.dumps([{"a": "1", "b": "x"}, {"a": "2", "b": "y"}]), encoding="utf-8")
    assert len(ingestao.ler_arquivo(arq)) == 2


def test_ler_json_invalido(tmp_path):
    arq = tmp_path / "a.json"
    arq.write_text("{quebrado", encoding="utf-8")
    with pytest.raises(IngestaoErro):
        ingestao.ler_arquivo(arq)


def test_ler_xlsx(tmp_path):
    pytest.importorskip("openpyxl", reason="openpyxl não instalado")
    arq = tmp_path / "a.xlsx"
    pd.DataFrame({"a": ["1", "2"], "b": ["x", "y"]}).to_excel(arq, index=False)
    assert ingestao.ler_arquivo(arq)["b"].tolist() == ["x", "y"]


def test_formato_nao_suportado(tmp_path):
    with pytest.raises(IngestaoErro, match="não suportado"):
        ingestao.ler_arquivo(tmp_path / "a.parquet")


def test_catalogo_de_fontes_nao_inventa_urls_de_dados():
    from etl import fontes

    for doc in fontes.DOCUMENTACAO_CNPQ:
        assert doc.url.startswith("https://www.gov.br/cnpq/")
    ids = {f.id for f in fontes.FONTES}
    assert {"cnpq_painel_pq", "capes_bolsas"} <= ids
    assert next(f for f in fontes.FONTES if f.id == "capes_bolsas").status == "PENDENTE_EXTERNA"
