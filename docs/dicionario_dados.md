# Dicionário de dados — Painel Lattes 2023

## 1. Identificação

| Item | Valor |
|---|---|
| Fonte | CNPq — Painel Lattes: Formação e Atuação de Mestres e Doutores |
| Recorte | ano 2023; filtro `Bolsista — PQ 1A = Não` |
| Arquivo original | `Download - Tabela.xlsx` |
| SHA-256 | `939c5f4322e17a86970887f63def21de8b27033187f100ddeaefe9af4fe384e9` |
| Linhas | 25.820 |
| Colunas da fonte | 40 |
| Total ponderado | 26.009 (`SUM(quantidade)`) |
| Tabela PostgreSQL | `lattes_analytics.perfil_pesquisadores_lattes_2023` |

A unidade de observação é uma **célula agregada** (combinação de dimensões),
não uma pessoa. A coluna `quantidade` informa quantos mestres/doutores existem
naquela célula. Toda análise de pessoas deve usar `SUM(quantidade)`.

## 2. Colunas da fonte e da tabela

| Coluna | Tipo no banco | Nulidade | Descrição |
|---|---|---|---|
| `id_registro` | `SERIAL` | PK | Chave substituta gerada na carga (não existe na planilha) |
| `ano` | `SMALLINT` | NOT NULL | Ano de referência (2023) |
| `data_extracao_bd_lattes` | `VARCHAR(10)` | NOT NULL | Data de extração informada na base |
| `sexo` | `VARCHAR(20)` | NOT NULL | Sexo padronizado: `Feminino`, `Masculino`, `Não informado` |
| `cor_ou_raca` | `VARCHAR(30)` | NOT NULL | Cor/raça padronizada: `Branca`, `Preta`, `Parda`, `Amarela`, `Indígena`, `Não desejo declarar`, `Não informado` |
| `pais_de_nascimento` | `VARCHAR(60)` | Sim | País de nascimento |
| `pais_formacao` | `VARCHAR(60)` | Sim | País da formação |
| `regiao_formacao` | `VARCHAR(30)` | Sim | Região da formação |
| `uf_formacao` | `VARCHAR(30)` | Sim | UF da formação |
| `cidade_formacao` | `VARCHAR(100)` | Sim | Cidade da formação |
| `grande_area_formacao` | `VARCHAR(60)` | Sim | Grande área da formação |
| `area_formacao` | `VARCHAR(100)` | Sim | Área da formação |
| `instituicao_formacao` | `VARCHAR(255)` | Sim | Instituição de formação |
| `nivel_formacao` | `VARCHAR(30)` | Sim | Nível de formação (mestrado/doutorado etc.) |
| `pais_atuacao` | `VARCHAR(60)` | Sim | País de atuação |
| `regiao_atuacao` | `VARCHAR(30)` | Sim | Região de atuação |
| `uf_atuacao` | `VARCHAR(30)` | Sim | UF de atuação |
| `cidade_atuacao` | `VARCHAR(100)` | Sim | Cidade de atuação |
| `grande_area_atuacao` | `VARCHAR(60)` | Sim | Grande área de atuação |
| `area_atuacao` | `VARCHAR(100)` | Sim | Área de atuação |
| `instituicao_atuacao` | `VARCHAR(255)` | Sim | Instituição de atuação |
| `setor_de_atividade_atuacao` | `VARCHAR(100)` | Sim | Setor de atividade |
| `enquadramento_atuacao` | `VARCHAR(100)` | Sim | Enquadramento da atuação |
| `bolsista_iniciacao_cientifica` | `VARCHAR(3)` | NOT NULL | `Sim`/`Não` |
| `bolsista_graduacao_sanduiche` | `VARCHAR(3)` | NOT NULL | `Sim`/`Não` |
| `bolsista_mestrado` | `VARCHAR(3)` | NOT NULL | `Sim`/`Não` |
| `bolsista_doutorado` | `VARCHAR(3)` | NOT NULL | `Sim`/`Não` |
| `bolsista_pos_doutorado` | `VARCHAR(3)` | NOT NULL | `Sim`/`Não` |
| `bolsista_pq` | `VARCHAR(3)` | NOT NULL | `Sim`/`Não` |
| `bolsista_pq_1a` | `VARCHAR(3)` | NOT NULL | `Sim`/`Não`; nesta extração é sempre `Não` |
| `bolsista_pq_1b` | `VARCHAR(3)` | NOT NULL | `Sim`/`Não` |
| `bolsista_pq_1c` | `VARCHAR(3)` | NOT NULL | `Sim`/`Não` |
| `bolsista_pq_1d` | `VARCHAR(3)` | NOT NULL | `Sim`/`Não` |
| `bolsista_pq_2_ou_1e` | `VARCHAR(3)` | NOT NULL | `Sim`/`Não` |
| `bolsista_dt` | `VARCHAR(3)` | NOT NULL | `Sim`/`Não` |
| `bolsista_dt_1a` | `VARCHAR(3)` | NOT NULL | `Sim`/`Não` |
| `bolsista_dt_1b` | `VARCHAR(3)` | NOT NULL | `Sim`/`Não` |
| `bolsista_dt_1c` | `VARCHAR(3)` | NOT NULL | `Sim`/`Não` |
| `bolsista_dt_1d` | `VARCHAR(3)` | NOT NULL | `Sim`/`Não` |
| `bolsista_dt_2_ou_1e` | `VARCHAR(3)` | NOT NULL | `Sim`/`Não` |
| `quantidade` | `INTEGER` | NOT NULL | Número de pessoas na célula agregada (1 a 5 nesta base) |

## 3. Colunas apenas do CSV tratado

| Coluna | Descrição | Destino |
|---|---|---|
| `sexo_original` | Valor de sexo antes da normalização | Preservado no CSV; descartado na carga PostgreSQL |
| `cor_ou_raca_original` | Valor de cor/raça antes da normalização | Preservado no CSV; descartado na carga PostgreSQL |

O CSV tem 42 colunas; a tabela PostgreSQL tem 40 colunas de dados + `id_registro`.

## 4. Categorias e missingness

**Sexo** (vocabulário do ETL + categorias observadas nesta extração):

- `Feminino` — 13.632 linhas;
- `Masculino` — 11.990 linhas;
- `Não informado` — 198 linhas;
- `Não mapeado` — salvaguarda para valor desconhecido; **não ocorre** nesta extração.

**Cor/raça** (vocabulário do ETL + categorias observadas nesta extração):

- `Branca` — 15.581 linhas;
- `Parda` — 6.173 linhas;
- `Não desejo declarar` — 1.993 linhas;
- `Preta` — 1.644 linhas;
- `Amarela` — 345 linhas;
- `Indígena` — 84 linhas;
- `Não informado` — previsto no vocabulário, mas **não ocorre** nesta extração
  (a ausência é declarada como “Não desejo declarar”);
- `Não mapeado` — salvaguarda para valor desconhecido; **não ocorre** nesta
  extração.

As contagens acima são de **linhas**; consulte a seção 4.3 de
[`docs/limitacoes_lattes_2023.md`](limitacoes_lattes_2023.md) para a ressalva
sobre ponderação. No relatório de qualidade (`docs/relatorio_qualidade_lattes_2023.json`), as
categorias são contagens de **linhas**, não de pessoas. Exemplo: as categorias
de sexo somam 25.820 linhas; o total ponderado é 26.009. Use as consultas SQL
com `SUM(quantidade)` para análises de participação.

“0 nulos” no relatório significa que não há nulos estruturais após a resolução
das células mescladas. Isso não elimina missingness substantivo: há valores
“Não informado”, “Não desejo declarar” e “Outra” que precisam ser reportados
como cobertura.

## 5. Regras de interpretação

1. `COUNT(*)` conta células; `SUM(quantidade)` conta pessoas.
2. Não inferir sexo ou raça/cor a partir de nome, localização ou outros campos.
3. Não tratar “Não informado”/“Não desejo declarar” como categoria conhecida.
4. Células com contagem `< 5` devem ser suprimidas/agrupadas em saídas públicas.
5. A base não contém propostas submetidas/aprovadas; não calcular taxa de
   aprovação com esta tabela. Ver [`docs/regras_negocio.md`](regras_negocio.md).
