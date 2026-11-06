# Rastreabilidade: requisitos do professor → implementação

Fontes dos requisitos: **Guia de Orientação do Projeto Prático — Big Data** e
**Solicitação de Entrega Técnica — Fase 2**. O tema permanece:
*Auditoria de Viés Étnico-Gênero em Fomento à Pesquisa Científica — Painel de
Dados Abertos do CNPq e Portal da CAPES*.

- **Data da validação:** 06/11/2026.
- **Commit de referência:** `b28f88d`.
- **Repositório:** <https://github.com/yurifr0807/projeto-big-data>

## Fase 2 — Unificação, Tratamento, Modelagem e Armazenamento

| Requisito da Fase 2 | Artefato | Estado |
|---|---|---|
| E1 · Base tratada: origem, versão original, versão tratada, decisões e justificativas | `etl/ingestao.py` (manifesto com origem + SHA-256), `etl/linhagem.py` (`docs/linhagem/linhagem_lattes_2023.json`), `etl/tratamento_lattes.py` | **Concluído** com a base real: 25.820 linhas e 26.009 ponderados |
| E2 · Processo de tratamento no repositório, com decisões técnicas documentadas | `etl/tratamento_lattes.py`, `etl/validacao.py`, `docs/dicionario_dados.md`, `docs/estrategia_volume.md` | **Concluído**; decisões de mergeCells, tipagem, categorias e não imputação registradas |
| E3 · Base em banco na nuvem: estrutura, tabelas, campos/tipos, relacionamentos e quantidade de dados | `etl/ddl_lattes_2023.sql`, `etl/carga_lattes.py`, `terraform/` | **Concluído**: PostgreSQL Aiven, banco `observatorio`, schema `lattes_analytics`, tabela `perfil_pesquisadores_lattes_2023` |
| Justificativa da estratégia de modelagem | `docs/modelagem_postgresql.md` | **Concluído**: tabela desnormalizada; modelo estrela como evolução conceitual |

## Guia — requisitos gerais

| Requisito do Guia | Atendimento |
|---|---|
| Só bases abertas governamentais brasileiras; ODS 5 e/ou 18 | CNPq — Painel Lattes 2023. ODS 18 tratada como iniciativa da agenda nacional brasileira, complementar às 17 ODS da ONU. CAPES/PQ permanecem como fontes futuras. |
| 6 etapas: Negócio & LGPD → Ingestão & Tipagem → ETL → Modelagem BD → Regras de Negócio → Dashboard | 1: `docs/lgpd.md`; 2: `etl/ingestao.py` + `etl/leitor_lattes.py`; 3: `etl/tratamento_lattes.py`/`validacao.py`; 4: `etl/ddl_lattes_2023.sql`/`carga_lattes.py`; 5: `docs/regras_negocio.md` (definições); 6: dashboard em fase futura |
| Tratamento: padronizar colunas, nulos, tipos, duplicatas, amostragem controlada | Implementado, exceto amostragem: decisão registrada de **não amostrar** os fatos dos KPIs, para não distorcer grupos pequenos. Ver `docs/estrategia_volume.md`. |
| Tipagem correta | `ano` como `Int64`; `quantidade` como `int64`; categorias normalizadas; booleanos de bolsa como texto controlado. |
| Processamento eficiente (Pandas chunking) | `ler_csv_em_chunks` para CSV e `carregar_em_lotes` para PostgreSQL; leitura XLSX por aba. |
| PostgreSQL Free Tier 1 GB | Banco atual muito abaixo do limite; tamanho real (`pg_database_size`) **não medido** nesta etapa. |
| Terraform (`main.tf`, `variables.tf`, `outputs.tf`, `imports.tf`) com provider Aiven | Provider `~> 4.65`; serviço e banco aplicados/importados; estado local não versionado; `AIVEN_TOKEN` no ambiente. |
| Segurança: sem chaves/tokens/senhas no repositório | `.gitignore` cobre `.env`, `*.tfvars`, `*.tfstate`, planos e certificados; senha oculta em `repr`/URL; token via `AIVEN_TOKEN`. |
| LGPD: eliminar dados sensíveis/identificáveis dos brutos | A base Lattes é agregada e não contém CPF/nome. `sexo_original` e `cor_ou_raca_original` ficam no CSV tratado e são descartados antes da carga. Células `< 5` devem ser suprimidas em saídas públicas. Ver `docs/lgpd.md`. |
| Pastas `/etl`, `/terraform`, `/dashboard` | Existentes; `/dashboard` ainda sem implementação. |
| README completo | Atualizado para a Fase 2, com status, reprodução, 5 V's, limitações e links. |
| Dashboard online: ≥ 4 KPIs, filtros, seletor de métrica, drill-down | Fora do escopo desta fase. A base Lattes não traz faixa etária nem aprovação de propostas; filtros serão definidos conforme a fonte. |
| Banco não relacional (OpenSearch) — opcional | Não previsto; PostgreSQL é suficiente para o volume atual. |
| PySpark — alternativa | Pandas com processamento em lotes é suficiente e permitido pelo Guia. |
| Pitch de 10 min com demonstração do Terraform | Fase futura. |

## Marcos do cronograma

- **Marco 1** (tema, amostras da base pública, 5 V's/LGPD, conta Aiven):
  concluído; base Lattes obtida e conta/projeto Aiven existentes.
- **Marco 2** (Terraform + ETL + carga inicial no PostgreSQL): concluído;
  serviço/banco aplicados, ETL executado e carga validada.
- **Marco 3/Entrega final** (dashboard e publicação): próxima fase.

## Decisões e pendências

1. **Fonte da Fase 2:** Painel Lattes 2023, por permitir o recorte de perfil
   com sexo e cor/raça. O Painel PQ é a fonte candidata para taxas de
   aprovação/contemplação em fase futura.
2. **Modelo físico:** tabela analítica desnormalizada, não modelo estrela.
3. **Licença:** confirmar a licença dos dados do CNPq antes de redistribuir
   arquivos brutos ou tratados. Ver `docs/lgpd.md`.
4. **Volume:** medir `pg_database_size` em etapa futura; não inventar valor.
5. **Dashboard:** definir KPIs e filtros somente após confirmar os campos
   disponíveis na fonte.
