# Reprodução da Fase 2 — ETL, PostgreSQL Aiven e validação

Este é o procedimento completo para reproduzir a base da Fase 2 em Windows
PowerShell. Ele cobre a obtenção da planilha oficial, o registro no manifesto,
o ETL, a configuração do PostgreSQL na Aiven, a carga idempotente e a validação.

> **Escopo e segurança:** este guia não contém credenciais. Nunca versione
> `.env`, `terraform.tfvars`, `terraform.tfstate` ou arquivos temporários com
> senhas. O token do Terraform é lido de `AIVEN_TOKEN`.

---

## 0. Resultado esperado

| Métrica | Valor |
|---|---|
| Arquivo original | `Download - Tabela.xlsx` |
| SHA-256 do original | `939c5f4322e17a86970887f63def21de8b27033187f100ddeaefe9af4fe384e9` |
| Tamanho do original | 3.886.479 bytes |
| Linhas da planilha | 25.820 |
| Colunas de dados | 40 |
| Células mescladas resolvidas | 37.983 |
| Total ponderado | 26.009 (`SUM(quantidade)`) |
| CSV tratado | `dados/tratado/painel_lattes_2023_tratado.csv` |
| Colunas do CSV tratado | 42 (40 + `sexo_original` + `cor_ou_raca_original`) |
| Tabela PostgreSQL | `lattes_analytics.perfil_pesquisadores_lattes_2023` |
| Linhas no PostgreSQL | 25.820 |
| Soma no PostgreSQL | 26.009 |
| Testes de referência | `99 passed in 22.48s` (commit `b28f88d`) |

A quantidade de testes pode variar em outros ambientes: os testes que dependem
do arquivo bruto, do CSV tratado ou de `DB_*` configurado são ignorados quando
esses pré-requisitos não estão disponíveis.

---

## 1. Pré-requisitos

- Windows com PowerShell.
- Python 3.14+ (ou a versão compatível com o ambiente do projeto).
- Git.
- Terraform `>= 1.5.0` apenas se for reconciliar a infraestrutura.
- Conta/projeto na Aiven com o serviço PostgreSQL existente.
- Acesso ao Painel Lattes do CNPq para baixar a planilha oficial.

Verificações:

```powershell
python --version
git --version
terraform -version
```

---

## 2. Clonar o repositório e criar o ambiente

```powershell
git clone https://github.com/yurifr0807/projeto-big-data.git
cd projeto-big-data

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Se a execução de scripts estiver bloqueada no PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

---

## 3. Obter a base oficial do CNPq

### 3.1. Download manual

1. Abra o Painel Lattes:
   <http://bi.cnpq.br/painel/formacao-atuacao-lattes/>
2. Selecione o ano de referência **2023**.
3. Mantenha o filtro **Bolsista — PQ 1A = Não** (é o recorte da Fase 2).
4. Use a opção de download e salve o arquivo com o nome original:
   `Download - Tabela.xlsx`.
5. Guarde o arquivo fora do repositório (ex.: `C:\Users\<voce>\Downloads`).

> O recorte exclui deliberadamente os bolsistas PQ 1A. Isso é uma limitação
> documentada, não um erro de extração.

### 3.2. Conferir o SHA-256

No PowerShell, no diretório onde o arquivo foi salvo:

```powershell
Get-FileHash ".\Download - Tabela.xlsx" -Algorithm SHA256
```

O hash deve ser exatamente:

```text
939c5f4322e17a86970887f63def21de8b27033187f100ddeaefe9af4fe384e9
```

Se o hash divergir, o arquivo baixado não é o mesmo recorte usado na Fase 2.
Não prossiga: baixe novamente e confira os filtros.

### 3.3. Registrar no manifesto de ingestão

O comando copia o arquivo para `dados/bruto/` e registra origem, data, tamanho e
SHA-256 em `dados/bruto/manifesto_ingestao.json`.

```powershell
python -m etl.ingestao importar "C:\Users\<voce>\Downloads\Download - Tabela.xlsx" `
  --subpasta cnpq/painel_lattes `
  --origem "Exportação oficial do Painel Lattes do CNPq (http://bi.cnpq.br/painel/formacao-atuacao-lattes/), arquivo Download - Tabela.xlsx exportado em 2026-11-05 com ano=2023, filtro PQ 1A travado em Não"
```

O arquivo ficará em:

```text
dados/bruto/cnpq/painel_lattes/Download - Tabela.xlsx
```

> `dados/bruto/*` e `dados/tratado/*` são ignorados pelo Git. Eles não existem
> em um clone limpo e não devem ser publicados sem verificar a licença.

---

## 4. Executar o ETL

```powershell
python -m etl.tratamento_lattes
```

O pipeline:

1. lê o XLSX e resolve as células mescladas;
2. padroniza colunas e categorias;
3. preserva `sexo_original` e `cor_ou_raca_original`;
4. valida tipos e regras;
5. grava o CSV tratado;
6. atualiza `docs/relatorio_qualidade_lattes_2023.json`;
7. atualiza `docs/linhagem/linhagem_lattes_2023.json`.

### 4.1. Conferir o CSV tratado

```powershell
python -c "import pandas as pd; df=pd.read_csv('dados/tratado/painel_lattes_2023_tratado.csv'); print(len(df), int(df['quantidade'].sum()), len(df.columns))"
```

Saída esperada:

```text
25820 26009 42
```

Critérios adicionais:

- `ano` é `Int64` e contém 2023;
- `quantidade` é `int64`, positiva e soma 26.009;
- não há duplicatas exatas;
- categorias de sexo e raça estão no vocabulário controlado.

> O relatório de qualidade usa contagem de **linhas** nas categorias; o total
> de **pessoas** é sempre `SUM(quantidade)`. Não compare diretamente os dois.

### 4.2. Evitar sobrescrita de evidências em testes

O ETL expõe `registrar_evidencias=False` para execuções exploratórias. Os testes
automatizados usam essa opção para não regravar a linhagem e o relatório
versionados apenas por causa de timestamps. A execução oficial via
`python -m etl.tratamento_lattes` mantém o comportamento padrão e atualiza as
evidências.

---

## 5. Configurar o PostgreSQL localmente

```powershell
Copy-Item .env.example .env
notepad .env
```

Preencha com os dados do console da Aiven:

```ini
DB_HOST=<host do serviço>
DB_PORT=17025
DB_NAME=observatorio
DB_USER=avnadmin
DB_PASSWORD=<senha local, nunca versionada>
DB_SSLMODE=require
```

Regras:

- `.env` é ignorado pelo Git;
- `DB_PASSWORD` no `.env.example` é apenas um placeholder fictício;
- não grave credenciais em arquivos JSON;
- não desative a verificação TLS.

---

## 6. Reconciliação da infraestrutura (Terraform)

O serviço `pg-4f83b4b` já existe na Aiven. O `terraform.tfstate` local não é
versionado, então um clone limpo deve usar o bloco declarativo de
`terraform/imports.tf` antes de qualquer alteração.

```powershell
$env:AIVEN_TOKEN = "<seu-token-aiven>"
cd terraform
Copy-Item terraform.tfvars.example terraform.tfvars
# edite terraform.tfvars com os valores do ambiente, se necessário

terraform init
terraform fmt -check
terraform validate
terraform plan -out=plano.tfplan
```

Verifique no plano:

- o serviço existente é importado, não recriado;
- nenhum recurso existente aparece para destruição ou `forces replacement`;
- o banco `observatorio` está presente no estado ou será tratado de forma
  consciente.

Só execute `terraform apply plano.tfplan` após revisar o plano e com autorização
explícita. Nunca execute `terraform destroy`.

---

## 7. Carregar no PostgreSQL

Na raiz do projeto:

```powershell
python -m etl.carga_lattes
```

O script:

- aplica o DDL se o schema/tabela não existirem;
- lê o CSV tratado;
- remove `sexo_original` e `cor_ou_raca_original` antes da carga;
- insere em lotes de até 500 registros, em transação única;
- se a tabela já estiver íntegra, não duplica dados;
- se houver divergência, aborta com `CargaErro` e rollback.

### 7.1. Verificar o estado

```powershell
python -m etl.carga_lattes --verificar
```

Saída esperada:

```text
[DIAGNÓSTICO AIVEN] Tabela: lattes_analytics.perfil_pesquisadores_lattes_2023 | Linhas: 25820 | Soma: 26009 | Status: integra_completa
Detalhes: Tabela já contém os 25.820 registros e soma ponderada 26.009 (carga íntegra).
```

O comando é somente leitura e não altera o banco.

Outros status possíveis:

- `tabela_inexistente`: o DDL será aplicado na próxima carga;
- `pronta_para_carga`: tabela vazia;
- `divergente`: intervenção manual necessária; não apague dados sem analisar.

---

## 8. Validação SQL

### Opção A — Python (lê o `.env` local)

```powershell
python -c "from etl import carga_postgresql as cp; from sqlalchemy import text; e=cp.criar_engine(); c=e.connect(); print(c.execute(text('SELECT COUNT(*), SUM(quantidade) FROM lattes_analytics.perfil_pesquisadores_lattes_2023')).fetchone()); c.close()"
```

Saída esperada:

```text
(25820, 26009)
```

### Opção B — Query Editor da Aiven

Abra [`etl/consultas_validacao_lattes.sql`](../etl/consultas_validacao_lattes.sql)
no Query Editor da Aiven e execute as consultas. A primeira consulta deve
retornar 25.820 linhas e 26.009 indivíduos ponderados.

### Opção C — psql

```powershell
$env:DB_HOST = "<host>"
$env:DB_PORT = "17025"
$env:DB_USER = "avnadmin"
$env:DB_NAME = "observatorio"
psql -h $env:DB_HOST -p $env:DB_PORT -U $env:DB_USER -d $env:DB_NAME `
  -f .\etl\consultas_validacao_lattes.sql
```

O `psql` solicitará a senha; não a coloque no comando.

---

## 9. Testes automatizados

```powershell
pytest -v
```

Resultado de referência no commit `b28f88d`, em 06/11/2026:

```text
99 passed in 22.48s
```

Após essa validação, a suíte ganhou testes unitários adicionais para o fallback
de token. Execute `pytest` para obter o total atual do seu ambiente.

Em outros ambientes, a quantidade pode variar:

- sem o arquivo bruto, os testes do leitor/ETL Lattes são ignorados;
- sem o CSV tratado, o teste de modelagem é ignorado;
- sem `DB_*`, o teste de integração com a Aiven é ignorado.

Para rodar apenas os testes que não dependem de serviço externo:

```powershell
pytest -v -m "not integracao"
```

---

## 10. Problemas comuns

| Sintoma | Causa provável | Ação |
|---|---|---|
| `FileNotFoundError: Download - Tabela.xlsx` | arquivo ausente ou fora do caminho esperado | importar com `etl.ingestao importar` e conferir o caminho |
| SHA-256 divergente | recorte/filtro diferente ou download incompleto | baixar novamente com ano=2023 e PQ 1A=Não |
| `Variáveis de ambiente ausentes` | `.env` não criado/preenchido | copiar `.env.example` e preencher `DB_*` |
| `DIVERGÊNCIA DETECTADA` | carga parcial ou tabela alterada | não apagar às cegas; inspecionar e decidir manualmente |
| `tabela_inexistente` | DDL ainda não aplicado | executar `python -m etl.carga_lattes` |
| Terraform propõe `forces replacement` | valores de região/plano/versão divergentes | parar, revisar `terraform.tfvars` e o estado; não aplicar |
| Teste de integração falha | credenciais/rede/TLS | conferir `.env`, `DB_SSLMODE=require` e acesso à Aiven |

---

## 11. Licença e redistribuição

Os dados brutos e tratados estão fora do Git por tamanho, privacidade e
governança. A licença dos conjuntos do CNPq ainda não foi confirmada em
[`docs/lgpd.md`](lgpd.md). Até a confirmação:

- não redistribua os arquivos brutos;
- não publique o CSV tratado como se fosse um dataset aberto independente;
- cite a fonte oficial e a data de extração.
