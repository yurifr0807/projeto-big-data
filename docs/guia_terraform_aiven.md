# Provisionamento e Infraestrutura como Código (Terraform & Aiven)

Este documento descreve o estado da infraestrutura da Fase 2 e o procedimento
seguro para reproduzi-la ou reconciliá-la. O ambiente de referência já está
provisionado na Aiven:

| Item | Valor |
|---|---|
| Projeto Aiven | `projeto-bigdata` |
| Serviço PostgreSQL | `pg-4f83b4b` |
| Região | `do-sfo` |
| Versão do PostgreSQL | 18 |
| Plano | `free-1-1gb` |
| Banco analítico | `observatorio` |
| Schema/tabela | `lattes_analytics.perfil_pesquisadores_lattes_2023` |

> **Segurança:** nunca grave tokens, senhas ou o conteúdo de `terraform.tfstate`
> em arquivos versionados. O token do provider é lido de `AIVEN_TOKEN` no
> ambiente. `terraform.tfvars`, `*.tfstate` e planos são ignorados pelo Git.

---

## 1. Pré-requisitos

1. Conta ativa na [Aiven Console](https://console.aiven.io/).
2. Projeto `projeto-bigdata` e serviço `pg-4f83b4b` existentes (ambiente atual).
3. Terraform CLI `>= 1.5.0` instalado (`terraform -version`).
4. Token pessoal da Aiven em local seguro (o console só o exibe uma vez).

---

## 2. Configuração do token e das variáveis

No PowerShell, na raiz do projeto:

```powershell
# Token do provider (não coloque em arquivo)
$env:AIVEN_TOKEN = "<seu-token-aiven>"

# Entrar no diretório do Terraform
cd terraform

# Criar o arquivo local de variáveis (ignorado pelo Git)
Copy-Item terraform.tfvars.example terraform.tfvars
```

O `terraform.tfvars.example` já reflete o ambiente atual. Para outro ambiente,
edite `terraform.tfvars` com os valores exibidos no console da Aiven:

```hcl
aiven_project = "projeto-bigdata"
nome_servico  = "pg-4f83b4b"
versao_pg     = "18"
nome_banco    = "observatorio"
plano         = "free-1-1gb"
cloud_name    = "do-sfo"
```

> O nome legado `AIVEN_API_TOKEN` não é usado pelo provider Terraform. Ele
> permanece apenas como fallback no script auxiliar `etl/consultar_servico_aiven.py`.

---

## 3. Importação declarativa do serviço existente

O arquivo `terraform/imports.tf` contém um bloco `import` para o serviço já
existente:

```hcl
import {
  to = aiven_pg.observatorio
  id = "${var.aiven_project}/${var.nome_servico}"
}
```

Esse é o caminho recomendado para um clone limpo, pois o `terraform.tfstate`
local não é versionado. O `terraform plan` lê o bloco e propõe a importação do
serviço para o estado, sem recriá-lo.

```powershell
terraform init
terraform fmt -check
terraform validate
terraform plan -out=plano.tfplan
```

No plano, verifique:

- o serviço `aiven_pg.observatorio` aparece como importação, não como criação
  de um novo serviço;
- **nenhum recurso existente aparece para destruição ou `forces replacement`**;
- o banco lógico `aiven_pg_database.observatorio` já está no estado ou será
  importado/criado de forma consciente.

Se o banco lógico também existir na Aiven e não estiver no estado, importe-o
antes de aplicar qualquer alteração. O ID de importação do recurso de banco
segue o formato indicado pela documentação do provider
(`projeto/serviço/banco`). Não execute `terraform apply` sem revisar o plano e
sem autorização explícita.

> **Alternativa por CLI:** `terraform import aiven_pg.observatorio projeto-bigdata/pg-4f83b4b`.
> Não use as duas abordagens ao mesmo tempo para o mesmo recurso.

---

## 4. Aplicação controlada

Somente depois de revisar o plano e confirmar que não há destruição:

```powershell
terraform apply plano.tfplan
```

O recurso possui `termination_protection = true` por padrão. Para encerrar o
serviço seria necessário alterar essa variável conscientemente; isso está fora
do escopo da Fase 2.

---

## 5. Credenciais e conexão com o banco

Não grave outputs sensíveis (`pg_senha`, `pg_uri`) em arquivos JSON ou logs.
Prefira consultar os valores individualmente no console da Aiven ou usar um
gerenciador de segredos.

Para preencher o `.env` local, use os campos exibidos no console da Aiven:

```ini
DB_HOST=<host do serviço>
DB_PORT=17025
DB_NAME=observatorio
DB_USER=avnadmin
DB_PASSWORD=<senha local, nunca versionada>
DB_SSLMODE=require
```

O arquivo `.env` é ignorado pelo Git. Não há necessidade de criar arquivos
temporários de credenciais.

---

## 6. Carga da base

Com o `.env` preenchido e a base tratada disponível:

```powershell
cd ..
.\.venv\Scripts\python.exe -m etl.carga_lattes
.\.venv\Scripts\python.exe -m etl.carga_lattes --verificar
```

Resultado esperado: 25.820 linhas e `SUM(quantidade) = 26.009`. A carga é
idempotente e não executa operações destrutivas. O procedimento completo está
em [`docs/reproducao_fase2.md`](reproducao_fase2.md).
