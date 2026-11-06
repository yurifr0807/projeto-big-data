# Projeto Big Data e Analytics: Observatório de Equidade no Fomento Científico Brasileiro

Este repositório consolida uma solução técnica de engenharia, governança e análise de Big Data com foco em auditoria de viés étnico-racial e de gênero na ciência e pós-graduação brasileira.

- **Tema Acadêmico:** Auditoria de Viés Étnico-Gênero em Fomento à Pesquisa Científica.
- **Aluno:** Yuri Figueiredo Ribeiro.
- **Alinhamento às ODS da ONU:**
  - **ODS 5:** Igualdade de Gênero.
  - **ODS 18:** Igualdade Étnico-Racial.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem Principal:** Python 3.14+ (Pandas, SQLAlchemy, psycopg 3, OpenpyXL)
- **Infraestrutura como Código (IaC):** Terraform com provedor oficial `aiven/aiven` (~> 4.65)
- **Banco de Dados Relacional:** PostgreSQL hospedado via Aiven Cloud (Free Tier - 1 GB)
- **Visualização Analítica:** Streamlit e Plotly (planejado para a Fase 6)
- **Qualidade e Testes:** pytest (suíte com 92 testes automatizados)

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
│   ├── leitor_lattes.py    # Leitura com resolução de 37.983 mergeCells hierárquicos
│   ├── tratamento.py       # Padronização, tipos de dados e normalização de categorias
│   ├── tratamento_lattes.py# Pipeline completo de ETL da base oficial do CNPq
│   ├── validacao.py        # Validação de schema, regras de negócio e relatório de qualidade
│   ├── linhagem.py         # Registro formal de linhagem e decisões técnicas de ETL
│   ├── carga_postgresql.py # Utilitários de carga relacional protegida por transações
│   ├── carga_lattes.py     # Carga idempotente da base Lattes no PostgreSQL
│   ├── ddl_lattes_2023.sql # Script SQL DDL da tabela e índices analíticos
│   └── consultas_validacao_lattes.sql # Consultas SQL analíticas (ponderadas)
├── terraform/              # Infraestrutura como Código para Aiven PostgreSQL
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars.example
├── tests/                  # Testes automatizados (pytest)
│   ├── test_tratamento.py       # Exercício inicial de QA (preservado)
│   ├── test_ingestao.py         # Testes de ingestão e segurança
│   ├── test_tratamento_etl.py   # Testes das transformações e LGPD
│   ├── test_validacao.py        # Testes de schema e qualidade
│   ├── test_lattes_etl.py       # Testes da base oficial Lattes 2023
│   ├── test_carga.py            # Testes de carga e integridade relacional
│   ├── test_linhagem.py         # Testes de rastreabilidade de dados
│   └── test_modelagem_lattes.py # Testes de esquema e validação ponderada
├── docs/                   # Documentação Acadêmica e Técnica
│   ├── arquitetura.md
│   ├── limitacoes_lattes_2023.md
│   ├── modelagem_postgresql.md
│   ├── guia_terraform_aiven.md
│   ├── estrategia_volume.md
│   ├── rastreabilidade_requisitos.md
│   └── linhagem/
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
```

---

## 🚀 Guia de Reprodução Rápida (Fase 2)

### 1. Inicializar o Ambiente Virtual e Dependências
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Executar a Suíte Completa de Testes Automatizados
```powershell
pytest -v
```
*Resultado esperado: 92 testes aprovados (1 teste de integração externa ignorado enquanto a instância da Aiven não for conectada).*

### 3. Executar o Pipeline de Tratamento da Base Oficial do CNPq
```powershell
python -m etl.tratamento_lattes
```
*O script processa a planilha oficial de 25.820 linhas, resolve as 37.983 células mescladas, padroniza as colunas demográficas, emite o relatório de qualidade e exporta `dados/tratado/painel_lattes_2023_tratado.csv`.*

### 4. Consultas e Auditoria Analítica
Consulte [etl/consultas_validacao_lattes.sql](file:///c:/Users/dell/Desktop/projeto-big-data/etl/consultas_validacao_lattes.sql) para executar as queries oficiais de validação ponderada pela coluna `quantidade` (totalizando 26.009 indivíduos).

---

## 🔒 Governança, Limitações e Aspectos Legais (LGPD)

1. **Ponderação Obrigatória:** A base é multidimensional agregada. Qualquer análise descritiva deve utilizar `SUM(quantidade)` em vez de `COUNT(*)`.
2. **Limitação de Filtro (PQ 1A):** A extração possui a trava `PQ 1A = Não`, excluindo os pesquisadores 1A do topo da carreira científica do CNPq.
3. **Não Utilização para Taxas de Aprovação:** Esta base não contém propostas submetidas vs. aprovadas/rejeitadas. Portanto, não é utilizada para calcular taxas de aprovação, atuando como denominador de estoque/perfil cadastral de pós-graduação.
4. **Proteção de Segredos:** Credenciais e tokens nunca são expostos em código. A infraestrutura Aiven é configurada via variáveis de ambiente seguras (`$env:AIVEN_API_TOKEN`).
