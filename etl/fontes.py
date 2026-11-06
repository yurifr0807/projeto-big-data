"""Catálogo das fontes oficiais efetivamente VERIFICADAS (Fase 2).

Somente URLs e características confirmadas por acesso direto às páginas oficiais
(em 2026-11-05) entram aqui. Não há URL de arquivo de dados porque nenhuma foi
encontrada: os painéis do CNPq expõem os dados por interface (Power BI / bi.cnpq.br)
com botão de download, sem link estático ou API documentada.
Detalhes e evidências em docs/fontes_dados.md.
"""

from __future__ import annotations

from dataclasses import dataclass

BASE_CNPQ = "https://www.gov.br/cnpq/pt-br/acesso-a-informacao/dados-abertos"


@dataclass(frozen=True)
class Documento:
    url: str
    arquivo: str
    descricao: str


@dataclass(frozen=True)
class Fonte:
    id: str
    nome: str
    orgao: str
    pagina: str
    formato: str
    status: str  # VERIFICADA_MANUAL | PENDENTE_EXTERNA | CANDIDATA
    como_obter: str
    campos_documentados: tuple[str, ...] = ()
    observacoes: str = ""


DOCUMENTACAO_CNPQ: tuple[Documento, ...] = (
    Documento(
        f"{BASE_CNPQ}/paineis-de-dados/Manual_de_UtilizaoPainel_Bolsas_PQ_PQSR_DT.pdf",
        "manual_painel_pq.pdf",
        "Manual de Utilização do Painel de Bolsas de Produtividade em Pesquisa (PQ)",
    ),
    Documento(
        f"{BASE_CNPQ}/paineis-de-dados/Nota_TcnicaPainel_Bolsas_PQ_SR_DT_Junho_2016.pdf",
        "nota_tecnica_painel_pq.pdf",
        "Nota Técnica do Painel de Bolsas PQ (fontes, períodos, dimensões)",
    ),
    Documento(
        f"{BASE_CNPQ}/Plano_2664725_Plano_de_Dados_Abertos___PDA_do_CNPq_2026_28.pdf",
        "pda_cnpq_2026_28.pdf",
        "Plano de Dados Abertos do CNPq 2026-2028",
    ),
)

FONTES: tuple[Fonte, ...] = (
    Fonte(
        id="cnpq_painel_pq",
        nome="Painel de Chamadas de Bolsas de Produtividade em Pesquisa (PQ, PQ-Sr, DT)",
        orgao="CNPq",
        pagina=f"{BASE_CNPQ}/paineis-de-dados/painel-de-chamadas-de-bolsas-de-produtividade-pq",
        formato="Planilhas via botão 'Baixar Planilhas' do painel Power BI (formato exato a confirmar no download)",
        status="PENDENTE_EXTERNA",
        como_obter="Download manual pelo painel (docs/download_manual.md); depois: "
        "python -m etl.ingestao importar <arquivo> --subpasta cnpq/painel_pq --origem '<URL do painel + data>'",
        campos_documentados=(
            "ano (ano de lançamento da chamada, 2013-2024)", "modalidade (PQ, PQ-Sr, DT)",
            "categoria/nível", "grande área", "área do conhecimento", "comitê assessor",
            "instituição", "UF/região", "sexo (Lattes; inclui 'Não informado')",
            "cor ou raça (Lattes; inclui 'Não informado' e 'Não desejo declarar')",
            "parecer (contemplado / não contemplado)",
        ),
        observacoes="Unidade: processo/proposta por chamada (um pesquisador pode ter vários). "
        "Único conjunto encontrado com sexo + cor/raça + parecer (aprovação) simultâneos.",
    ),
    Fonte(
        id="cnpq_painel_demanda_atendimento",
        nome="Painel de Demanda e Atendimento",
        orgao="CNPq",
        pagina=f"{BASE_CNPQ}/paineis-de-dados/painel-de-demanda-e-atendimento",
        formato="Painel Power BI (download não confirmado)",
        status="CANDIDATA",
        como_obter="Inspecionar o painel manualmente para confirmar campos e opção de download.",
        observacoes="Cobre bolsas e auxílios desde 2006 (valores e quantidades, área, instituição, região). "
        "A descrição oficial NÃO menciona sexo nem cor/raça: não considerar adequada sem confirmar os campos.",
    ),
    Fonte(
        id="cnpq_painel_lattes",
        nome="Painel Lattes — Formação e Atuação de Mestres e Doutores",
        orgao="CNPq",
        pagina=f"{BASE_CNPQ}/paineis-de-dados/painel-lattes",
        formato="Excel ou CSV via download personalizado em http://bi.cnpq.br/painel/formacao-atuacao-lattes/",
        status="CANDIDATA",
        como_obter="Download manual pelo painel; confirmar campos.",
        observacoes="Traz sexo, faixa etária e cor/raça de pesquisadores (população de referência), "
        "não de fomento. Útil como denominador/contexto, não como base de concessão.",
    ),
    Fonte(
        id="capes_bolsas",
        nome="CAPES — Bolsas e Auxílios (dados abertos)",
        orgao="CAPES",
        pagina="https://dadosabertos.capes.gov.br/organization/bolsas-e-auxilios?res_format=CSV",
        formato="CSV (CKAN) — não confirmado",
        status="PENDENTE_EXTERNA",
        como_obter="Bloqueado: verificação TLS do portal falha neste ambiente (cadeia com certificado "
        "autoassinado). Resolver com CA_BUNDLE confiável ou download manual.",
        observacoes="Não foi possível listar datasets/campos. Pesquisa web (não verificada) sugere ausência de "
        "sexo/raça por bolsista.",
    ),
)
