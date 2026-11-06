# Projeto Big Data e Analytics: Observatório de Equidade no Fomento Científico Brasileiro

Solução técnica de engenharia, governança e análise de Big Data com foco em auditoria de viés étnico-racial e de gênero na ciência e pós-graduação brasileira.

- **Tema acadêmico:** Auditoria de Viés Étnico-Gênero no Fomento à Pesquisa Científica.
- **Aluno:** Yuri Figueiredo Ribeiro.
- **Repositório:** <https://github.com/yurifr0807/projeto-big-data>
- **Commit de referência da validação:** `b28f88d`.
- **Data da validação:** 06/11/2026.
- **Alinhamento:** ODS 5 (Igualdade de Gênero) e ODS 18 (Igualdade Étnico-Racial — iniciativa da agenda nacional brasileira, complementar às 17 ODS da ONU).

---

## 📊 Status da Fase 2

| Item | Resultado |
|---|---|
| Base oficial | Painel Lattes/CNPq, ano 2023, arquivo `Download - Tabela.xlsx` |
| Dimensões | 25.820 linhas × 40 colunas de dados (37.983 células mescladas resolvidas) |
| Total ponderado | **26.009** mestres/doutores (`SUM(quantidade)`) |
| Base tratada | `dados/tratado/painel_lattes_2023_tratado.csv` (42 colunas: 40 + 2 originais) |
| PostgreSQL | Aiven, banco `observatorio`, schema `lattes_analytics`, tabela `perfil_pesquisadores_lattes_2023` |
| Carga validada | **25.820 linhas** e **26.009** ponderados |
| Testes | **99 passed in 22.48s** (validação de referência, commit `b28f88d`) |
| Terraform | Serviço PostgreSQL aplicado/importado na Aiven; estado local não versionado |
| Publicação | GitHub |

> Este é o resultado de referência da validação no commit `b28f88d`. A suíte
> evoluiu com testes unitários adicionais; execute `pytest` para o total atual.
> A quantidade também pode variar em outros ambientes: os testes que dependem
> do arquivo bruto, do CSV tratado ou de `DB_*` configurado são ignorados
> quando esses pré-requisitos não estão disponíveis.

Evidência principal: [`docs/evidencias/validacao_carga_2026-11-06.md`](docs/evidencias/validacao_carga_2026-11-06.md).  
Reprodução completa: [`docs/reproducao_fase2.md`](docs/reproducao_fase2.md).

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem principal:** Python 3.14+ (Pandas, SQLAlchemy, psycopg 3, Openpyxl).
- **Infraestrutura como Código:** Terraform com provider oficial `aiven/aiven` (`~> 4.65`).
- **Banco relacional:** PostgreSQL 18 hospedado na Aiven (Free Tier, 1 GB).
- **Visualização analítica:** Streamlit e Plotly (planejados para a fase de dashboard).
- **Qualidade e testes:** pytest.

---

## 📁 Estrutura do Repositório

```text
projeto-big-data/
├── dados/
│   ├── bruto/              # Bases oficiais brutas (imutáveis, com manifesto e SHA-256)
│   │   └── cnpq/painel_lattes/Download - Tabela.xlsx
│   └── tratado/            # Bases limpas e padronizadas prontas para carga
│       └── painel_lattes_2023_tratado.csv
├── etl/                    # Módulos de Engenharia de Dados (ETL)
│   ├── ingestao.py         # Ingestão idempotente com verificação TLS e manifesto SHA-256
│   ├── leitor_lattes.py    # Leitura com resolução de células mescladas hierárquicas
│   ├── tratamento_lattes.py# Pipeline completo de ETL da base oficial do CNPq
│   ├── validacao.py        # Validação de schema, regras de negócio e relatório de qualidade
│   ├── linhagem.py         # Registro formal de linhagem e decisões técnicas de ETL
│   ├── carga_postgresql.py # Utilitários de carga relacional protegida por transações
│   ├── carga_lattes.py     # Carga idempotente da base Lattes no PostgreSQL
│   ├── ddl_lattes_2023.sql # Script SQL DDL da tabela e índices analíticos
│   └── consultas_validacao_lattes.sql # Consultas SQL analíticas ponderadas
├── terraform/              # Infraestrutura como Código para Aiven PostgreSQL
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── imports.tf          # Importação declarativa do serviço existente
│   ├── terraform.tfvars.example
│   └── .terraform.lock.hcl
├── tests/                  # Testes automatizados (pytest)
│   ├── test_tratamento.py
│   ├── test_ingestao.py
│   ├── test_tratamento_etl.py
│   ├── test_validacao.py
│   ├── test_lattes_etl.py
│   ├── test_carga.py
│   ├── test_linhagem.py
│   ├── test_modelagem_lattes.py
│   └── test_consultar_servico_aiven.py
├── docs/                   # Documentação acadêmica e técnica
│   ├── arquitetura.md
│   ├── checklist_fase2.md
│   ├── dicionario_dados.md
│   ├── download_manual.md
│   ├── estrategia_volume.md
│   ├── evidencias/validacao_carga_2026-11-06.md
│   ├── fontes_dados.md
│   ├── guia_terraform_aiven.md
│   ├── lgpd.md
│   ├── limitacoes_lattes_2023.md
│   ├── modelagem_postgresql.md
│   ├── procedimento_importacao_aiven.md
│   ├── rastreabilidade_requisitos.md
│   ├── regras_negocio.md
│   ├── reproducao_fase2.md
│   ├── linhagem/linhagem_lattes_2023.json
│   └── relatorio_qualidade_lattes_2023.json
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
```

> **Importante:** `dados/bruto/*`, `dados/tratado/*`, `*.csv` e `*.xlsx` são
> ignorados pelo Git. Um clone do repositório **não contém** os arquivos de
> dados. A reprodução exige o download oficial e a importação pelo manifesto,
> conforme [`docs/reproducao_fase2.md`](docs/reproducao_fase2.md).

---

## 🚀 Reprodução Rápida (Fase 2)

O guia completo, com comandos PowerShell, critérios de sucesso e solução de
problemas, está em [`docs/reproducao_fase2.md`](docs/reproducao_fase2.md).
Resumo:

```powershell
# 1. Ambiente
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Base oficial: baixar o XLSX e registrá-lo no manifesto
#    (ver docs/download_manual.md; o dado bruto não é versionado)
python -m etl.ingestao importar "C:\caminho\Download - Tabela.xlsx" `
  --subpasta cnpq/painel_lattes `
  --origem "Painel Lattes CNPq, exportado em 2026-11-05, ano=2023, PQ 1A=Não"

# 3. ETL
python -m etl.tratamento_lattes

# 4. Configurar o .env local (nunca versionar)
Copy-Item .env.example .env
# edite DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD e DB_SSLMODE

# 5. Carga idempotente e verificação
python -m etl.carga_lattes
python -m etl.carga_lattes --verificar

# 6. Testes
pytest -v
```

Critérios de sucesso do ETL:

- 25.820 linhas;
- 40 colunas de dados na planilha;
- `SUM(quantidade) = 26.009`;
- nenhuma duplicata exata removida.

Critérios de sucesso da carga:

- tabela `lattes_analytics.perfil_pesquisadores_lattes_2023` com 25.820 linhas;
- `SUM(quantidade) = 26.009`;
- status `integra_completa` no `--verificar`.

### Consultas e auditoria analítica

O arquivo [`etl/consultas_validacao_lattes.sql`](etl/consultas_validacao_lattes.sql)
contém as consultas oficiais de validação ponderada. Execute-o no Query Editor
da Aiven ou com `psql -f`; o total esperado é 26.009 indivíduos.

> A tabela física tem 40 colunas de dados + `id_registro` (chave substituta).
> O CSV tratado tem 42 colunas porque preserva `sexo_original` e
> `cor_ou_raca_original`; essas duas colunas são descartadas antes da carga.

---

## 🧭 Os 5 V's neste projeto

| Dimensão | Aplicação |
|---|---|
| **Volume** | 25.820 linhas; 26.009 indivíduos ponderados; arquivo bruto de 3.886.479 bytes. |
| **Velocidade** | Processamento em lote/offline; recorte anual, sem streaming. |
| **Variedade** | XLSX com 40 colunas e 37.983 células mescladas; saída tabular e PostgreSQL. |
| **Veracidade** | Manifesto com SHA-256, relatório de qualidade, validação SQL e testes automatizados. |
| **Valor** | Perfil/denominador para análises descritivas de equidade; não mede aprovação de propostas. |

---

## 🔒 Governança, Limitações e Aspectos Legais (LGPD)

1. **Ponderação obrigatória:** a base é multidimensional agregada. Use
   `SUM(quantidade)`; `COUNT(*)` conta células, não pessoas.
2. **Limitação de filtro (PQ 1A):** a extração tem a trava `PQ 1A = Não`,
   excluindo o estrato sênior 1A do topo da carreira científica do CNPq.
3. **Sem taxas de aprovação:** a base não contém propostas submetidas versus
   aprovadas/rejeitadas. Ela serve como estoque/perfil cadastral, não como
   evidência de taxa de aprovação ou de viés de fomento.
4. **Cobertura e missingness:** sexo e cor/raça são autodeclarados no Lattes.
   Há “Não informado”, “Não desejo declarar” e “Outra”; os percentuais devem
   ser acompanhados da cobertura. “0 nulos” no relatório significa ausência de
   nulos estruturais, não ausência de missingness substantivo.
5. **Sem inferência causal:** diferenças entre grupos são descritivas; não
   controlam área, nível, instituição, produtividade ou demanda.
6. **Pequenos grupos e LGPD:** células com contagem `< 5` devem ser suprimidas
   ou agrupadas em qualquer saída pública. A base no banco contém células
   agregadas; o acesso deve ser restrito.
7. **Licença:** a licença dos dados ainda não foi confirmada. Não redistribuir
   os arquivos brutos até a confirmação; consulte [`docs/lgpd.md`](docs/lgpd.md).
8. **Proteção de segredos:** credenciais e tokens nunca são versionados. O
   provider Terraform lê `AIVEN_TOKEN` do ambiente; o script auxiliar aceita
   `AIVEN_API_TOKEN` apenas como fallback legado.

Limitações completas: [`docs/limitacoes_lattes_2023.md`](docs/limitacoes_lattes_2023.md).
