"""Observatório de Equidade — Dashboard Streamlit / PostgreSQL Aiven.

Executar na raiz: streamlit run dashboard/app.py
Dependências e secrets: docs/dashboard_implantacao.md
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.analytics import kpis, safe_cross, safe_distribution, safe_pq_by_sex
from dashboard.db import ConfigError, connection_settings, get_filter_options, make_engine, query_groups

load_dotenv(ROOT / ".env")
st.set_page_config(page_title="Observatório de Equidade | CNPq", page_icon="🔬", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
.block-container {max-width: 1350px; padding-top: 1.8rem;}
.main-title {font-size: 2rem; font-weight: 800; margin-bottom: .1rem; letter-spacing: -.035em;}
.intro {color: #718096; font-size: .95rem; margin-bottom: 1.25rem;}
.tag {display:inline-block; border:1px solid #9ABDD2; color:#2675A2; padding: .2rem .55rem; border-radius: 1rem; font-size:.72rem; font-weight:700; margin-right:.4rem;}
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def cached_engine(config_key: tuple):
    return make_engine(dict(config_key))


@st.cache_data(ttl=180, show_spinner=False)
def cached_options(_engine):
    with _engine.connect() as connection:
        return get_filter_options(connection)


@st.cache_data(ttl=60, show_spinner=False)
def cached_results(_engine, selected: tuple):
    filters = dict(selected)
    with _engine.connect() as connection:
        return {
            "sexo": query_groups(connection, ("sexo",), filters),
            "raca": query_groups(connection, ("cor_ou_raca",), filters),
            "cruzamento": query_groups(connection, ("sexo", "cor_ou_raca"), filters),
            "regiao": query_groups(connection, ("regiao_atuacao",), filters),
            "area": query_groups(connection, ("grande_area_atuacao",), filters),
        }


def format_pct(value):
    return "—" if value is None else f"{value:.1f}%".replace(".", ",")


def display_chart(title, records, blocked, *, x="categoria", y="pessoas", color=None, orientation="v"):
    st.subheader(title)
    if blocked:
        st.info("Detalhamento não exibido: a seleção contém grupo com menos de 5 pessoas ou não há dados suficientes.")
        return
    frame = pd.DataFrame(records)
    if frame.empty:
        st.info("Sem dados para os filtros selecionados.")
        return
    chart = px.bar(frame, x=x, y=y, color=color, orientation=orientation, text_auto=True, color_discrete_sequence=px.colors.qualitative.Safe)
    chart.update_layout(margin=dict(t=12,b=25,l=8,r=8), height=345, legend_title_text="", yaxis_title="Pessoas (ponderadas)" if orientation == "v" else "")
    st.plotly_chart(chart, use_container_width=True, config={"displaylogo": False})


st.markdown('<span class="tag">ODS 5</span><span class="tag">ODS 18</span><span class="tag">CNPq · Lattes 2023</span>', unsafe_allow_html=True)
st.markdown('<div class="main-title">Observatório de Equidade na Pesquisa Científica</div>', unsafe_allow_html=True)
st.markdown('<div class="intro">Análise descritiva do perfil de mestres e doutores por sexo, raça/cor, região e presença de bolsa PQ.</div>', unsafe_allow_html=True)

try:
    # O Streamlit pode não ter arquivo secrets.toml, no modo local com .env.
    try:
        secrets = dict(st.secrets)
    except (FileNotFoundError, RuntimeError):
        secrets = {}
    settings = connection_settings(secrets=secrets)
    engine = cached_engine(tuple(sorted(settings.items())))
    options = cached_options(engine)
except ConfigError as exc:
    st.error(str(exc))
    st.code("streamlit run dashboard/app.py", language="powershell")
    st.info("Configure .env local ou os Secrets do Streamlit. Nunca envie sua senha ao GitHub ou ao chat.")
    st.stop()
except Exception:
    st.error("Não foi possível estabelecer conexão com o banco configurado. Confira credenciais, rede e TLS.")
    st.stop()

st.sidebar.header("Filtros de análise")
st.sidebar.caption("Recorte único: ano de referência 2023. Não existe série temporal nesta extração.")
filter_names = [
    ("regiao", "Região de atuação"),
    ("uf", "UF de atuação"),
    ("area", "Grande área científica"),
    ("formacao", "Nível de formação"),
    ("sexo", "Sexo"),
    ("raca", "Raça/cor"),
]
selected = {}
for key, label in filter_names:
    choice = st.sidebar.selectbox(label, ["Todas"] + options.get(key, []), key=f"filter_{key}")
    if choice != "Todas":
        selected[key] = choice

# Limite conservador de recortes cruzados; não substitui revisão formal de risco de inferência.
if len(selected) > 2:
    st.warning("Para limitar recortes excessivamente específicos, selecione no máximo dois filtros simultâneos.")
    st.stop()

if st.sidebar.button("🔄 Atualizar consultas", use_container_width=True):
    cached_results.clear()
    cached_options.clear()
    st.rerun()
st.sidebar.caption("Os resultados são agregados diretamente no PostgreSQL. Cache de 60 segundos para as consultas; atualização manual disponível.")
st.sidebar.warning("Prévia técnica. Antes da publicação aberta, faça avaliação de privacidade dos filtros combinados e de ataques por diferença.")

try:
    result = cached_results(engine, tuple(sorted(selected.items())))
except Exception as exc:
    original = getattr(exc, "orig", None)
    sqlstate = getattr(original, "sqlstate", None)

    print(
        f"DB_DIAGNOSTICO: tipo={type(exc).__name__}; "
        f"sqlstate={sqlstate or 'indisponivel'}",
        flush=True
    )

    st.error(
        "Não foi possível estabelecer conexão com o banco. "
        "Consulte os logs para identificar a categoria do erro."
    )
    st.stop()

metrics = kpis(result["sexo"], result["raca"], result["cruzamento"])
if metrics["total"] is None:
    st.warning("Recorte não exibido: total insuficiente para publicação (menos de 5 pessoas).")
    st.stop()

st.caption("Fonte de consulta: PostgreSQL Aiven · Tabela Lattes 2023 · Frequência ponderada por SUM(quantidade).")
st.metric("Perfis representados no recorte", f"{metrics['total']:,}".replace(",", "."))
c1,c2,c3,c4 = st.columns(4)
with c1:
    st.metric("Participação feminina", format_pct(metrics["female_pct"]))
    st.caption(f"Cobertura de sexo: {format_pct(metrics['female_coverage'])}")
with c2:
    st.metric("Participação preta ou parda", format_pct(metrics["black_brown_pct"]))
    st.caption(f"Cobertura de raça/cor: {format_pct(metrics['race_coverage'])}")
with c3:
    st.metric("Mulheres pretas ou pardas", format_pct(metrics["intersect_pct"]))
    st.caption("Entre os perfis com sexo e raça/cor conhecidos")
with c4:
    st.metric("Presença de bolsa PQ", format_pct(metrics["pq_pct"]))
    st.caption("Presença/histórico no painel; NÃO é taxa de aprovação")

st.divider()
left,right = st.columns(2, gap="large")
with left:
    data, hidden = safe_distribution(result["sexo"], "sexo")
    display_chart("Distribuição por sexo", data, hidden)
with right:
    data, hidden = safe_distribution(result["raca"], "cor_ou_raca")
    display_chart("Distribuição por raça/cor", data, hidden)

st.divider()
left,right=st.columns(2,gap="large")
with left:
    st.subheader("Interseccionalidade: sexo × raça/cor")
    intersection, hidden = safe_cross(result["cruzamento"])
    if hidden:
        st.info("Cruzamento suprimido: existem contagens pequenas ou o recorte não permite divulgar os grupos.")
    else:
        df = pd.DataFrame(intersection)
        chart = px.density_heatmap(df, x="raça/cor", y="sexo", z="pessoas", histfunc="sum", text_auto=True,
                                   color_continuous_scale="Blues")
        chart.update_layout(margin=dict(t=12,b=25,l=8,r=8), height=350)
        st.plotly_chart(chart, use_container_width=True, config={"displaylogo":False})
with right:
    st.subheader("Presença de bolsa PQ por sexo")
    pq_sex, hidden = safe_pq_by_sex(result["sexo"])
    if hidden:
        st.info("Taxas PQ suprimidas para evitar divulgação de grupos menores que cinco.")
    else:
        df = pd.DataFrame(pq_sex)
        chart = px.bar(df, x="sexo", y="presença de PQ (%)", text_auto=".1f", range_y=[0,100], color="sexo",
                       color_discrete_sequence=px.colors.qualitative.Safe)
        chart.update_layout(margin=dict(t=12,b=25,l=8,r=8), height=350, showlegend=False)
        st.plotly_chart(chart, use_container_width=True, config={"displaylogo":False})

st.divider()
left,right = st.columns(2, gap="large")
with left:
    data, hidden = safe_distribution(result["regiao"], "regiao_atuacao")
    display_chart("Distribuição por região de atuação", data, hidden)
with right:
    data, hidden = safe_distribution(result["area"], "grande_area_atuacao")
    display_chart("Distribuição por grande área", data, hidden)

with st.expander("Metodologia, cobertura e limitações — leia antes de interpretar"):
    st.markdown("""
    **Origem:** Painel Lattes/CNPq (formação e atuação), extraído em 05/11/2026,
    com ano-base **2023**. O filtro **PQ 1A = Não** excluiu esse estrato da extração.

    - Cada linha no banco é uma célula agregada; os gráficos usam `SUM(quantidade)`.
    - Percentuais de gênero e raça têm denominadores apenas de categorias conhecidas.
    - Categorias desconhecidas ou recusadas são excluídas de cada denominador e há indicação de cobertura.
    - Células positivas com menos de 5 pessoas bloqueiam o detalhamento correspondente.
    - Presença de bolsa PQ **não** indica candidatura, aprovação, valor concedido ou discriminação.
    - Dados descritivos de 2023; não representam evolução temporal nem relação causal.
    - Filtros dinâmicos podem criar risco de inferência por diferença entre consultas;
      uma publicação pública exige revisão formal adicional, mesmo com supressão de células.

    A fonte não contém dados de propostas submetidas ou rejeitadas. **Não é possível
    estimar taxas de aprovação de fomento científico com esta base.**
    """)

st.caption("Observatório de Equidade · Projeto acadêmico Big Data e Analytics · Banco Aiven / Python / Streamlit")
