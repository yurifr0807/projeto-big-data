# Pitch técnico — 10 minutos | Observatório de Equidade

Roteiro de apresentação; preencher números de KPI apenas após validação real no Aiven.

| Intervalo | Apresentação / demonstração |
|---|---|
| 0:00–1:30 | **Problema social** — ODS 5 e agenda brasileira ODS 18; por que medir representatividade no perfil de pesquisadores |
| 1:30–3:00 | **Arquitetura** — Excel oficial CNPq, ingestão com SHA-256, ETL Python, PostgreSQL Aiven, infraestrutura Terraform, Streamlit |
| 3:00–4:30 | **Critérios de tratamento** — 2023; `PQ 1A = Não`; normalização sexo/raça; contagem ponderada `SUM(quantidade)`; problemas de células mescladas |
| 4:30–7:30 | **Demonstração** — Abrir painel conectado à Aiven, mostrar 4 KPIs, selecionar Região e Sexo e observar as consultas/filtros; exibir mensagem de supressão quando aplicável |
| 7:30–9:00 | **Interpretação** — Falar dos denominadores conhecidos, da presença de PQ e da distribuição interseccional; evitar afirmar aprovação ou viés causal |
| 9:00–10:00 | **Decisões / desafios** — carga em lotes de 500, free tier, proteção de credenciais, k=5 como mecanismo mínimo, limites da publicação |

## Perguntas que podem surgir

**Por que 25.820 linhas representam 26.009 pessoas?**
Porque a base contém células multidimensionais agregadas e a coluna `quantidade` representa frequência. `COUNT(*)` conta linhas, `SUM(quantidade)` conta pessoas representadas.

**É possível provar viés na aprovação de bolsas?**
Não. O Painel Lattes 2023 documenta perfil e histórico/presença de bolsas; não contém número de candidaturas rejeitadas/aprovadas nem seus contextos. O projeto descreve representatividade, não causalidade.

**Por que apenas 2023?**
Porque a extração original escolhida possui um único ano; não é metodologicamente válido inventar série histórica.

**Como o painel se conecta ao banco?**
Via SQLAlchemy + psycopg, TLS, usuário somente leitura, SQL parametrizado e `GROUP BY` com contagem ponderada. Os dados vêm de Aiven, sem CSV público no Streamlit.

**A proteção de grupos pequenos é perfeita?**
Não. O bloqueio de células abaixo de 5 reduz exposição pontual; consultas complementares ainda exigem análise antes de liberar acesso público irrestrito.
