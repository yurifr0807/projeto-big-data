# Dicionário de dados — **PROVISÓRIO**

> Este dicionário descreve apenas o que a **documentação oficial** (Manual e Nota Técnica do Painel PQ) informa, e as
> categorias padronizadas já implementadas em `etl/tratamento.py`. **Nomes reais de colunas, tipos e domínios serão
> preenchidos após inspeção da planilha oficial exportada.** Não existe ainda modelagem definitiva de banco.

## Conceitos do painel PQ (fonte: Nota Técnica / Manual do CNPq)

| Conceito | Descrição oficial resumida | Observação para o ETL |
|---|---|---|
| Ano | Ano de lançamento da chamada PQ | `ano` (SMALLINT); validar intervalo 2012–2026 |
| Modalidade | PQ, PQ-Sr, DT | domínio fechado; validar |
| Categoria/nível | 2013–2023: 1A, 1B, 1C, 1D, 2; 2024+: A, B, C; SR | manter regimes **separados** |
| Grande área / Área / Subárea | Árvore de conhecimento do CNPq vigente no lançamento da chamada | DT usa subáreas tecnológicas do comitê |
| Comitê assessor (CA) | Comitê que julga | texto controlado |
| Instituição | Vínculo informado pelo proponente (onde pretende executar a bolsa) | texto; normalizar apenas grafia |
| Região / UF / Cidade | Localização da instituição de execução | domínio UF/região fechado |
| Sexo | Do Currículo Lattes; ausente = "Não informado" | ver tabela de categorias |
| Cor ou raça | Do Currículo Lattes; ausente = "Não informado"; recusa = "Não desejo declarar" | ver tabela de categorias |
| Parecer | Contemplado × não contemplado (inclui não aprovados) | base da taxa de contemplação |
| Processo/proposta | Unidade de observação do painel de chamadas | um pesquisador pode ter vários |
| Bolsista (CPF único) | Unidade da visão de pagamentos/vigência | **não** misturar com propostas |

## Categorias padronizadas (implementadas)

**Sexo** (`normalizar_sexo`): `Feminino`, `Masculino`, `Não informado`, `Não mapeado` (valor fora das equivalências de grafia).

**Cor/raça** (`normalizar_raca_cor`): `Branca`, `Preta`, `Parda`, `Amarela`, `Indígena`, `Não informado`, `Não desejo declarar`, `Não mapeado`.

Recodificação restrita a **equivalência de grafia** (caixa, acentos, forma masculina/feminina como "preto/preta", abreviações "F/M").
O valor de origem é sempre mantido em `<coluna>_original`. Qualquer valor desconhecido vira `Não mapeado` e é listado no
relatório de tratamento (`RelatorioTratamento.nao_mapeados`) para decisão humana.

> Para KPIs, "conhecido" = `Feminino`/`Masculino` (sexo) e as cinco categorias IBGE (raça/cor).
> `Não informado`, `Não desejo declarar` e `Não mapeado` ficam **fora do denominador** e são exibidos separadamente (cobertura).

## Tipos de conversão disponíveis (`tratar_dataframe`)

`texto`, `inteiro` (Int64 anulável), `ano` (Int64 validado), `data`, `monetario` (float64, 2 casas; formatos `3.500,50`, `R$ 1.234,56`, `3500.50`),
`sexo`, `raca_cor`. Inválidos → nulo + contagem; ausentes nunca viram zero.
