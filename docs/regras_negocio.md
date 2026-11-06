# Regras de negócio e indicadores — Lattes 2023

## 1. Escopo

A base da Fase 2 é o **Painel Lattes 2023**, uma tabela agregada de mestres e
doutores. Ela permite análises descritivas de **perfil** por sexo, cor/raça,
formação, atuação, área, região e bolsas.

Ela **não** contém propostas submetidas, aprovadas, rejeitadas ou contempladas.
Portanto, não permite calcular taxa de aprovação, taxa de contemplação ou
diferença de acesso a fomento. Esses indicadores dependem do Painel PQ ou de
outra fonte oficial e ficam para fase futura.

## 2. Regra central de contagem

- **Unidade de análise:** pessoa, representada pela soma de `quantidade`.
- **Nunca usar `COUNT(*)`** para contar pessoas: cada linha é uma célula
  agregada.
- **Denominador:** apenas registros com o atributo conhecido.
- **Categorias não conhecidas:** `Não informado`, `Não desejo declarar` e
  `Não mapeado` ficam fora do denominador e são reportadas à parte (cobertura).
- **Células pequenas:** suprimir ou agrupar contagens `< 5` em saídas públicas.
- **Diferenças:** são descritivas, não causais.

## 3. Indicadores possíveis com o Lattes

| # | Indicador | Fórmula | Campos | Limitações |
|---|---|---|---|---|
| 1 | Participação feminina | `SUM(quantidade) de Feminino ÷ SUM(quantidade) com sexo conhecido × 100` | `sexo`, `quantidade` | Exclui “Não informado”; reportar cobertura |
| 2 | Participação por cor/raça | `SUM(quantidade) da categoria ÷ SUM(quantidade) com raça conhecida × 100` | `cor_ou_raca`, `quantidade` | Exclui “Não desejo declarar”/“Não informado”; subdeclaração histórica |
| 3 | Interseccional sexo × raça | `SUM(quantidade)` por par, com percentual sobre o total conhecido | `sexo`, `cor_ou_raca`, `quantidade` | Células pequenas instáveis; suprimir `< 5` |
| 4 | Distribuição regional | `SUM(quantidade)` por região/UF ÷ total | `regiao_atuacao`, `uf_atuacao` | Reflete atuação, não residência |
| 5 | Distribuição por área | `SUM(quantidade)` por grande área/área ÷ total | `grande_area_atuacao`, `area_atuacao` | Categorias “Não informado”/“Outra” |
| 6 | Presença de bolsa PQ/DT | `SUM(quantidade)` com `Sim` ÷ total da categoria | `bolsista_pq`, `bolsista_dt`, `quantidade` | Indica presença/histórico, não taxa de concessão; PQ 1A ausente |
| 7 | Perfil por nível de formação | `SUM(quantidade)` por `nivel_formacao` | `nivel_formacao` | Depende da consistência da categoria |
| 8 | Formação por instituição/UF | `SUM(quantidade)` por instituição/UF de formação | `instituicao_formacao`, `uf_formacao` | Grafias e vínculos podem variar |

> As consultas de [`etl/consultas_validacao_lattes.sql`](../etl/consultas_validacao_lattes.sql)
> implementam as versões SQL ponderadas dos indicadores 1–6.

## 4. Indicadores de fomento — não disponíveis nesta base

| Indicador | Fórmula | Fonte necessária | Status |
|---|---|---|---|
| Taxa de aprovação | aprovadas ÷ submetidas × 100 | Painel PQ / chamadas | Não calculável com Lattes |
| Taxa de contemplação | contempladas ÷ submetidas × 100 | Painel PQ / chamadas | Não calculável com Lattes |
| Diferença de acesso | taxa grupo A − taxa grupo B | Painel PQ / chamadas | Não calculável com Lattes |
| Valores concedidos | soma/distribuição de valores | Painel PQ / outra fonte | Não disponível |

Esses indicadores não devem ser “aproximados” com a base Lattes. Fazer isso
criaria denominadores fictícios e conclusões inválidas.

## 5. Regras de apresentação

1. Exibir sempre `n` e cobertura ao lado de percentuais.
2. Não apresentar categorias “Não informado”/“Não desejo declarar” como se
   fossem grupos de interesse.
3. Suprimir células `< 5` ou agrupá-las antes de publicar.
4. Não usar linguagem causal (“causa”, “prova discriminação”) sem desenho
   estatístico adequado.
5. Separar claramente **perfil** (Lattes) de **fomento** (PQ).
