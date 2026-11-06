# Regras de negócio e indicadores — **definições planejadas (não calculadas)**

> Nenhum indicador foi calculado: ainda não há dados oficiais carregados. Cada KPI só será habilitado se os campos
> exigidos existirem na planilha real (`etl.validacao.checar_campos_indicador`).
> Unidade de contagem: **proposta/processo** (painel de chamadas). Propostas, pessoas (CPF) e valores financeiros
> **não são misturados**.

Regras gerais: denominador = apenas registros com o atributo **conhecido**; "Não informado"/"Não desejo declarar" reportados à parte
(cobertura); células com contagem < 5 suprimidas; diferenças são descritivas, **não causais**.

| # | KPI | Fórmula | Campos | Denominador | Ausentes | Fonte | Limitações |
|---|---|---|---|---|---|---|---|
| 1 | Participação feminina | `propostas contempladas de mulheres ÷ contempladas com sexo conhecido × 100` (e idem para submetidas) | ano, sexo, parecer, [UF, área, modalidade, nível] | contempladas (ou submetidas) com sexo ∈ {F, M} | "Não informado" excluído; % de cobertura exibida | CNPq — Painel PQ | Não reflete a composição do corpo de pesquisadores; níveis 2013–23 × 2024+ não comparáveis |
| 2 | Participação por raça/cor | `contempladas da categoria ÷ contempladas com raça/cor conhecida × 100` | ano, cor_raca, parecer | contempladas com cor/raça ∈ 5 categorias | "Não informado" e "Não desejo declarar" excluídos e exibidos; cobertura varia no tempo (campo recente no Lattes) | CNPq — Painel PQ | Subdeclaração histórica; categorias pequenas exigem supressão |
| 3 | Taxa de contemplação interseccional | `contempladas ÷ submetidas × 100` por (sexo × cor/raça) | ano, sexo, cor_raca, parecer | submetidas do grupo (sexo e raça conhecidos) | idem | CNPq — Painel PQ | "Contemplada" ≠ "aprovada": não contemplados incluem aprovados sem cota; grupos pequenos instáveis (exibir n) |
| 4 | Diferença de acesso (p.p.) | `taxa_grupo_A − taxa_grupo_B` (KPI 3 ou participação) | os do KPI 3 | os do KPI 3 | idem | CNPq — Painel PQ | Sem controle de área/nível/instituição; não prova discriminação; reportar n e, se possível, intervalo de confiança |
| 5* | Distribuição regional | contempladas por região/UF ÷ total | UF/região, parecer | contempladas com UF conhecida | UF ausente reportada | CNPq — Painel PQ | UF = instituição de execução, não residência |
| 6* | Participação por área | contempladas por grande área ÷ total | grande área, parecer | contempladas com área | — | CNPq — Painel PQ | Árvore de áreas varia por chamada |
| 7* | Evolução temporal por grupo | KPI 1–3 por ano | ano | por ano | — | CNPq — Painel PQ | Ano = lançamento da chamada (implementação no ano seguinte) |
| 8* | Valores de financiamento | distribuição de valores concedidos | campo de valor (se existir) | contempladas com valor | valor ausente ≠ 0 | a confirmar | Só se a planilha trouxer valores por proposta |

\* adicionais, condicionados à presença dos campos.

## Integração CNPq × CAPES
Somente quando houver compatibilidade de indicadores, granularidade, períodos e definições. Hoje **não aplicável** (CAPES não verificada).
