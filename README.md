# Projeto Big Data e Analytics

Este repositório contém a estrutura base para o desenvolvimento de um projeto acadêmico aplicado à disciplina de **Big Data e Analytics**. 

O objetivo do projeto é consolidar uma esteira completa de engenharia e análise de dados, englobando infraestrutura como código (IaC), ingestão e processamento de dados (ETL), persistência analítica e disponibilização de insights por meio de um dashboard interativo.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem Principal**: [Python](https://www.python.org/) (manipulação, pipelines e visualização)
- **Banco de Dados**: [PostgreSQL](https://www.postgresql.org/) hospedado via [Aiven](https://aiven.io/)
- **Infraestrutura como Código (IaC)**: [Terraform](https://www.terraform.io/)
- **Visualização de Dados**: [Streamlit](https://streamlit.io/)
- **Bibliotecas Python Iniciais**: `pandas`, `sqlalchemy`, `psycopg`, `streamlit`, `python-dotenv`

---

## 📁 Estrutura do Projeto

A organização de diretórios e arquivos foi planejada segundo boas práticas de engenharia de software e ciência de dados:

```text
projeto-big-data/
├── dados/
│   ├── bruto/              # Dados brutos obtidos diretamente da fonte original (imutáveis)
│   └── tratado/            # Dados limpos, enriquecidos e prontos para carga ou análise
├── etl/                    # Scripts e módulos de Extração, Transformação e Carga (ETL)
├── terraform/              # Arquivos de Infraestrutura como Código (IaC) para serviços de nuvem
├── dashboard/              # Aplicação interativa desenvolvida com Streamlit
├── .env.example            # Modelo de configuração de variáveis de ambiente
├── .gitignore              # Regras para evitar versionamento de dados pesados e credenciais
├── README.md               # Documentação inicial e guia do repositório
└── requirements.txt        # Especificação das dependências do projeto
```

### Finalidade de Cada Pasta e Arquivo

1. **`dados/bruto/`**:
   - Destinado ao armazenamento local dos dados brutos (raw data) baixados da fonte pública selecionada.
   - Deve ser tratado como uma camada imutável e somente leitura (read-only).
   - O conteúdo desta pasta é ignorado pelo Git para não sobrecarregar o repositório com arquivos volumosos.

2. **`dados/tratado/`**:
   - Destinado aos dados que passaram por processos de limpeza, padronização, tipagem e enriquecimento.
   - Arquivos aqui gerados servem de base para carga no banco de dados analítico ou consumo direto.
   - Assim como a pasta de dados brutos, seu conteúdo é ignorado pelo controle de versão.

3. **`etl/`**:
   - Conterá o pipeline de processamento (Extract, Transform, Load).
   - Abriga os scripts responsáveis pela leitura dos dados brutos, transformações analíticas e ingestão nas tabelas do PostgreSQL na Aiven.

4. **`terraform/`**:
   - Abriga os manifestos do Terraform (`.tf`) para provisionamento automatizado da infraestrutura (ex.: serviços gerenciados na Aiven).
   - O arquivo de lock de provedores (`.terraform.lock.hcl`) deve ser versionado aqui, enquanto arquivos de estado (`.tfstate`) e variáveis sensíveis (`.tfvars`) permanecem ignorados.

5. **`dashboard/`**:
   - Armazena a interface gráfica analítica construída com Streamlit.
   - Conecta-se à base de dados para apresentar relatórios visuais, KPIs e gráficos interativos para tomada de decisão.

6. **`.env.example`**:
   - Documenta quais parâmetros e chaves de ambiente são requeridos pela aplicação (ex.: host, porta, usuário, banco e senha do PostgreSQL).
   - Serve como referência para a criação do arquivo `.env` local.

7. **`.gitignore`**:
   - Impede o envio acidental de arquivos confidenciais (chaves, senhas, `.env`), ambientes virtuais (`.venv`), caches do compilador (`__pycache__`) e arquivos grandes de dados (CSVs, Parquets, compactados).
   - Permite o versionamento de arquivos `.json` de configuração e metadados, além do `.terraform.lock.hcl`.

8. **`requirements.txt`**:
   - Lista as dependências essenciais do ecossistema Python para execução do projeto.

---

## 🚀 Guia de Inicialização do Ambiente

Quando o projeto for iniciado e as dependências precisarem ser instaladas, siga os passos abaixo:

### 1. Criar e ativar o ambiente virtual (Python)

No Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar dependências

Com o ambiente virtual ativado:
```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

Crie uma cópia do arquivo `.env.example` nomeada como `.env`:
```bash
cp .env.example .env
```
Edite o arquivo `.env` inserindo as credenciais de conexão do PostgreSQL (Aiven). **Nunca comite o arquivo `.env`.**
