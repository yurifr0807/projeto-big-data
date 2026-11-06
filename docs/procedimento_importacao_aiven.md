# Importação e Alinhamento do PostgreSQL Aiven com Terraform

Este guia registra como o serviço PostgreSQL existente na Aiven foi alinhado ao
Terraform e como reproduzir o procedimento com segurança. A Fase 2 já foi
executada: o serviço está provisionado, o banco `observatorio` existe e a tabela
`lattes_analytics.perfil_pesquisadores_lattes_2023` contém 25.820 linhas e
`SUM(quantidade) = 26.009`.

## 1. Dados da instância existente

| Item | Valor |
|---|---|
| Organização / Projeto Aiven | `projeto-bigdata` |
| Nome do serviço | `pg-4f83b4b` |
| Versão | PostgreSQL 18 |
| Região | `do-sfo` |
| Plano | `free-1-1gb` |
| Usuário administrador | `avnadmin` |
| Banco padrão | `defaultdb` |
| Banco analítico alvo | `observatorio` |

> **Atenção:** o `terraform.tfstate` local não é versionado. Em um clone limpo,
> use o bloco declarativo de `terraform/imports.tf` antes de qualquer `apply`.

## 2. Verificação do plano gratuito

No console da Aiven:

1. Abra o projeto `projeto-bigdata`.
2. Abra o serviço `pg-4f83b4b`.
3. Em **Overview**, confirme:
   - **Plan:** `Free` ou `free-1-1gb`;
   - **Cloud provider & region:** `do-sfo`;
   - **PostgreSQL version:** 18.

Se o serviço estiver em um plano de trial pago, não altere o plano sem
autorização; o objetivo é apenas conferir o estado atual.

## 3. Preparação das variáveis

```powershell
$env:AIVEN_TOKEN = "<seu-token-aiven>"
cd terraform
Copy-Item terraform.tfvars.example terraform.tfvars
```

Preencha `terraform.tfvars` com os valores do ambiente:

```hcl
aiven_project = "projeto-bigdata"
nome_servico  = "pg-4f83b4b"
versao_pg     = "18"
nome_banco    = "observatorio"
plano         = "free-1-1gb"
cloud_name    = "do-sfo"
```

Não grave o token em `terraform.tfvars` nem em arquivo JSON.

## 4. Importação declarativa (recomendada)

O arquivo `terraform/imports.tf` declara:

```hcl
import {
  to = aiven_pg.observatorio
  id = "${var.aiven_project}/${var.nome_servico}"
}
```

Procedimento:

```powershell
terraform init
terraform fmt -check
terraform validate
terraform plan -out=plano.tfplan
```

O plano deve mostrar a importação do serviço existente, sem recriá-lo. Revise:

- nenhum recurso marcado para `destroy` ou `forces replacement`;
- o banco `aiven_pg_database.observatorio` presente no estado ou tratado de
  forma consciente;
- diferenças de plano apenas nas configurações realmente desejadas.

Se o banco lógico também existir e não estiver no estado, importe-o antes de
aplicar. O ID de importação do banco segue o padrão do provider
(`projeto/serviço/banco`). Não use `terraform import` por CLI e o bloco
declarativo ao mesmo tempo para o mesmo recurso.

## 5. Aplicação controlada

Somente após revisar o plano e com autorização explícita:

```powershell
terraform apply plano.tfplan
```

> **Nunca execute `destroy`.** O serviço tem proteção contra exclusão por padrão.

## 6. Configuração do `.env` e carga

Com o banco criado e as credenciais obtidas no console da Aiven (não em arquivo
JSON), preencha o `.env` local:

```ini
DB_HOST=<host do serviço>
DB_PORT=17025
DB_NAME=observatorio
DB_USER=avnadmin
DB_PASSWORD=<senha local>
DB_SSLMODE=require
```

Depois, na raiz do projeto:

```powershell
python -m etl.carga_lattes
python -m etl.carga_lattes --verificar
```

Resultado esperado: `25.820` linhas, `26.009` indivíduos ponderados e status
`integra_completa`. A carga é idempotente e não sobrescreve dados existentes
quando a tabela já está íntegra.

Consulte também [`docs/reproducao_fase2.md`](reproducao_fase2.md) e a evidência
[`docs/evidencias/validacao_carga_2026-11-06.md`](evidencias/validacao_carga_2026-11-06.md).
