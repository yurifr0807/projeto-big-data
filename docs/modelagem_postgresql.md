# Modelagem PostgreSQL implementada — Painel Lattes 2023

## 1. Visão geral

A Fase 2 usa o PostgreSQL gerenciado da Aiven:

| Item | Valor |
|---|---|
| Banco | `observatorio` |
| Schema | `lattes_analytics` |
| Tabela | `perfil_pesquisadores_lattes_2023` |
| Granularidade | uma linha por combinação única das dimensões da planilha |
| Métrica | `quantidade` = número de mestres/doutores naquela célula |
| Volume | 25.820 linhas; `SUM(quantidade) = 26.009` |

A tabela é **desnormalizada**: ela preserva as 40 colunas da planilha oficial
e adiciona uma chave substituta `id_registro`. O modelo estrela foi avaliado,
mas não é o modelo físico implementado nesta fase.

> O tamanho real do banco (`pg_database_size`) **não foi medido** de forma
> independente. As estimativas abaixo são apenas estimativas.

## 2. Estrutura física

O DDL completo está em [`etl/ddl_lattes_2023.sql`](../etl/ddl_lattes_2023.sql).
Resumo das colunas:

| Grupo | Colunas | Tipo | Nulidade |
|---|---|---|---|
| Chave substituta | `id_registro` | `SERIAL` | PK |
| Tempo / metadados | `ano`, `data_extracao_bd_lattes` | `SMALLINT`, `VARCHAR(10)` | NOT NULL |
| Demografia | `sexo`, `cor_ou_raca`, `pais_de_nascimento` | `VARCHAR(20/30/60)` | `sexo`/`cor` NOT NULL |
| Formação | `pais_formacao`, `regiao_formacao`, `uf_formacao`, `cidade_formacao`, `grande_area_formacao`, `area_formacao`, `instituicao_formacao`, `nivel_formacao` | `VARCHAR` | Sim |
| Atuação | `pais_atuacao`, `regiao_atuacao`, `uf_atuacao`, `cidade_atuacao`, `grande_area_atuacao`, `area_atuacao`, `instituicao_atuacao`, `setor_de_atividade_atuacao`, `enquadramento_atuacao` | `VARCHAR` | Sim |
| Bolsas de formação | `bolsista_iniciacao_cientifica`, `bolsista_graduacao_sanduiche`, `bolsista_mestrado`, `bolsista_doutorado`, `bolsista_pos_doutorado` | `VARCHAR(3)` | NOT NULL |
| Bolsas PQ | `bolsista_pq`, `bolsista_pq_1a`, `bolsista_pq_1b`, `bolsista_pq_1c`, `bolsista_pq_1d`, `bolsista_pq_2_ou_1e` | `VARCHAR(3)` | NOT NULL |
| Bolsas DT | `bolsista_dt`, `bolsista_dt_1a`, `bolsista_dt_1b`, `bolsista_dt_1c`, `bolsista_dt_1d`, `bolsista_dt_2_ou_1e` | `VARCHAR(3)` | NOT NULL |
| Métrica | `quantidade` | `INTEGER` | NOT NULL, `CHECK (quantidade > 0)` |

### 2.1. Colunas que existem no CSV e não no banco

O CSV tratado tem 42 colunas:

- as 40 colunas da planilha;
- `sexo_original`;
- `cor_ou_raca_original`.

As duas colunas `*_original` são preservadas para auditoria do ETL, mas são
descartadas antes da carga (`etl/carga_lattes.py`). Por isso a tabela tem 40
colunas de dados + `id_registro`, enquanto o CSV tem 42.

### 2.2. Índices

O DDL cria índices B-Tree para:

- `sexo`;
- `cor_ou_raca`;
- `(sexo, cor_ou_raca)`;
- `bolsista_pq`;
- `bolsista_dt`;
- `grande_area_atuacao`;
- `regiao_atuacao`;
- `uf_atuacao`.

## 3. Carga e integridade

`etl/carga_lattes.py`:

1. aplica o DDL se o schema/tabela não existirem;
2. lê `dados/tratado/painel_lattes_2023_tratado.csv`;
3. remove `sexo_original` e `cor_ou_raca_original`;
4. insere em lotes de até 500 registros, em transação única;
5. se a tabela já contém 25.820 linhas e soma 26.009, não duplica (idempotência);
6. se encontra divergência, aborta com `CargaErro` e rollback;
7. permite diagnóstico não destrutivo com `python -m etl.carga_lattes --verificar`.

Resultado validado: 25.820 linhas e `SUM(quantidade) = 26.009`. Ver
[`docs/evidencias/validacao_carga_2026-11-06.md`](evidencias/validacao_carga_2026-11-06.md).

## 4. Por que tabela única (e não modelo estrela)

Para 25.820 linhas e 40 atributos, a tabela desnormalizada:

- elimina JOINs nas consultas de dashboard;
- reduz latência em um Free Tier com 1 GB de RAM;
- preserva a granularidade exata da fonte;
- ocupa estimados poucos MB (estimativa, não medição);
- simplifica a carga idempotente e a validação.

O modelo estrela só se justificaria se o volume crescesse muito ou se novas
fontes exigissem dimensões compartilhadas.

## 5. Proposta conceitual de evolução futura — modelo estrela

> **Status: não implementado.** Esta seção é apenas uma alternativa de
> evolução. Não existe DDL de dimensões/fato na Aiven nem no repositório.

Uma evolução possível separaria:

- `dim_tempo` (`ano`);
- `dim_demografia` (`sexo`, `cor_ou_raca`);
- `dim_geografia_formacao` e `dim_geografia_atuacao`;
- `dim_area_formacao` e `dim_area_atuacao`;
- `dim_instituicao`;
- `dim_modalidade_bolsa`;
- `fato_perfil_pesquisador` com `quantidade`.

Essa abordagem reduziria redundância textual, mas adicionaria JOINs e
complexidade operacional. Qualquer migração futura deve ser precedida de
medição de volume, plano de migração e validação de que os KPIs permanecem
idênticos. Não faz parte da entrega da Fase 2.
