# Rastreabilidade: requisitos do professor → implementação

Fontes dos requisitos: **Guia de Orientação do Projeto Prático — Big Data** (6 páginas) e **Solicitação de Entrega Técnica — Fase 2**
(2 páginas), ambos lidos em `Downloads`. Tema do aluno (tabela do Guia, seção 3): *Auditoria de Viés Étnico-Gênero em Fomento à Pesquisa
Científica — Painel de Dados Abertos do CNPq e Portal da CAPES.* **O projeto continua o mesmo**; nada foi recriado ou substituído.

## Fase 2 — Unificação, Tratamento, Modelagem e Armazenamento

| Requisito da Fase 2 | Artefato | Estado |
|---|---|---|
| E1 · Base tratada: origem, versão original, versão tratada, decisões e justificativas | `etl/ingestao.py` (manifesto com origem + SHA-256), `etl/linhagem.py` (registro `docs/linhagem/*.json`), `etl/tratamento.py` | Mecanismo **pronto e testado**; falta rodar com dados reais |
| E2 · Processo de tratamento no repositório, com decisões técnicas documentadas | `etl/tratamento.py`, `etl/validacao.py`, `docs/dicionario_dados.md`, `docs/estrategia_volume.md` | Pronto; esquema real **pendente** (dados oficiais) |
| E3 · Base em banco na nuvem: estrutura, tabelas, campos/tipos, relacionamentos, **quantidade de dados** | `etl/carga_postgresql.py` (conexão TLS, carga em lotes, `contar_linhas`, `tamanho_banco_bytes`), `terraform/` | Carga genérica pronta e testada (SQLite); **modelo de tabelas só após o schema real**; Aiven **não provisionada** |
| Justificativa da estratégia de modelagem | a registrar em `docs/arquitetura.md` após o schema | Pendente |

## Guia — requisitos gerais

| Requisito do Guia | Atendimento |
|---|---|
| Só bases abertas governamentais brasileiras; ODS 5 e/ou 18 | CNPq (painel PQ); CAPES pendente. `docs/fontes_dados.md` |
| 6 etapas: Negócio & LGPD → Ingestão & Tipagem → ETL → Modelagem BD → Regras de Negócio → Dashboard | 1: `docs/lgpd.md`; 2: `etl/ingestao.py`; 3: `etl/tratamento.py`/`validacao.py`; 4: pendente de schema; 5: `docs/regras_negocio.md` (definições; sem cálculo); 6: **fora do escopo desta etapa** |
| Tratamento: padronizar colunas, nulos, tipos, duplicatas, **amostragem controlada** | Implementado, exceto amostragem: **decisão registrada de não amostrar fatos dos KPIs** (viés em grupos pequenos) — `docs/estrategia_volume.md`. Se o professor exigir amostragem, aplicar apenas a tabelas auxiliares |
| Tipagem correta (ex.: texto → decimal em valores monetários) | `converter_monetario`, `converter_inteiro`, `validar_ano`, `converter_data` |
| Processamento eficiente (Pandas **chunking**) | `ler_csv_em_chunks`, `carregar_em_lotes` |
| PostgreSQL Free Tier 1 GB | Orçamento ≤ ~600 MB em `docs/estrategia_volume.md`; `tamanho_banco_bytes` para verificar |
| Terraform (`main.tf`, `variables.tf`, `outputs.tf`) com Aiven Provider | `terraform/` (provider `~> 4.65`; atributos conferidos). **Sem `apply`** |
| Segurança: sem chaves/tokens/senhas no repositório; `.env` e Secrets | `.gitignore`, `.env.example`, `AIVEN_API_TOKEN` por ambiente, senha oculta em `repr`/URL |
| LGPD: eliminar dados sensíveis/identificáveis dos brutos | `remover_identificadores` / `tratar_dataframe(descartar_identificadores=True)` descarta CPF, nome, e-mail, telefone, nº do processo e id Lattes após a deduplicação (a ativar no ETL definitivo). Sexo e cor/raça são **necessários** à finalidade e usados só agregados, com supressão de células < 5. `docs/lgpd.md` |
| Pastas `/etl`, `/terraform`, `/dashboard` | Existentes; `/dashboard` ainda vazio |
| README completo (diagrama, 5 V's, tipos de dados, dicionário, regras, justificativa do BD, deployment guide) | **Pendente** (Fase 7). Diagrama e partes em `docs/` |
| Dashboard online: ≥ 4 KPIs, filtros cruzados (Ano, UF/Região, Sexo, Raça/Cor, **Faixa Etária**), seletor de métrica, drill-down | Fora do escopo agora. **Observação:** o painel PQ documentado não traz faixa etária; o filtro só existirá se a planilha real o trouxer (não será inventado) |
| Banco não relacional (OpenSearch) — **opcional** no Guia | Não previsto; PostgreSQL suficiente. Justificativa em `docs/arquitetura.md` |
| PySpark — citado como alternativa (Python/PySpark/Pandas) | Pandas com chunking (permitido pelo Guia) |
| Pitch de 10 min com demonstração do Terraform | Fase 7 |

## Marcos do cronograma
* **Marco 1** (tema, amostras da base pública, 5 V's/LGPD, conta Aiven): tema ✔; amostras ✖ (download manual pendente); 5 V's — a documentar no README; conta Aiven — pendente do aluno.
* **Marco 2** (Terraform + ETL + carga inicial no PostgreSQL): código preparado; **depende de dados reais + token/conta Aiven**.
* **Marco 3/Entrega final:** dashboard e publicação — próximas fases.

## Alterações em arquivos existentes (e motivo)

| Arquivo | Alteração | Requisito atendido | Funcionalidade anterior |
|---|---|---|---|
| `requirements.txt` | + `requests`, `openpyxl`, `plotly`; versões mínimas | Ingestão HTTP/XLSX; gráficos do dashboard | Dependências antigas mantidas |
| `.gitignore` | + `logs/` | Segurança/higiene | Todas as regras anteriores mantidas |
| `.env.example` | + `CA_BUNDLE` e nota do `AIVEN_API_TOKEN` | Segurança (credenciais por ambiente) | Variáveis `DB_*` intactas |
| `etl/tratar_csv_com_erros.py` | **Não modifiquei.** O `git diff` mostra uma linha em branco adicionada na linha 30, feita fora das minhas alterações (provavelmente pelo seu editor); sem efeito funcional | — | Preservado |

Scripts `exercicio_pandas.py`, `ler_csv.py`, `tratar_csv.py`, `tratar_csv_com_erros.py` e o teste `tests/test_tratamento.py` (7 testes) permanecem como estavam; novos arquivos têm nomes distintos.

## Itens a decidir pelo aluno/professor
1. Aceitar a **não utilização de amostragem** nos fatos (Guia cita "amostragem controlada" como etapa do ETL).
2. Se a planilha real não trouxer cruzamento sexo × raça × parecer, qual base complementar investigar.
