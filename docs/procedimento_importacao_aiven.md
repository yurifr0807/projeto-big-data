# Procedimento de Importação e Alinhamento do PostgreSQL Aiven com Terraform

Este guia orienta o alinhamento seguro entre a instância PostgreSQL criada na interface da Aiven e a infraestrutura gerenciada via Terraform no repositório.

---

## 1. Dados da Instância Existente
- **Organização / Projeto Aiven:** `projeto-bigdata`
- **Nome do Serviço:** `pg-4f83b4b`
- **Versão:** PostgreSQL 18
- **Usuário Administrador:** `avnadmin`
- **Banco Padrão:** `defaultdb`
- **Banco Analítico Alvo:** `observatorio`

---

## 2. Verificação Obrigatória: Plano Gratuito vs Trial Pago

> [!WARNING]
> Na Aiven, ao criar uma conta nova, é comum a concessão de um trial com créditos (ex.: US$ 300).
> Se o serviço foi criado em um plano como `startup-4`, ele consumirá créditos e passará a gerar cobrança após o término do período de trial.

**Como verificar na Console da Aiven:**
1. Acesse o [Aiven Console](https://console.aiven.io/) e entre no projeto `projeto-bigdata`.
2. Clique no serviço `pg-4f83b4b`.
3. Na aba **Overview**:
   - Verifique o campo **Plan**: se estiver escrito `Free` ou `free-1-1gb`, o serviço é permanentemente gratuito.
   - Se estiver escrito `Startup-4` ou similar, o serviço está consumindo créditos de trial.
   - Verifique também o campo **Cloud provider & region** (ex.: `google-europe-west1`, `aws-sa-east-1`, etc.).

---

## 3. Preparação das Variáveis de Infraestrutura

1. Crie o arquivo `terraform/terraform.tfvars` (já protegido no `.gitignore`):
   ```powershell
   cd terraform
   Copy-Item terraform.tfvars.example terraform.tfvars
   ```

2. Preencha `terraform.tfvars` com as informações exatas da console:
   ```hcl
   aiven_project = "projeto-bigdata"
   nome_servico  = "pg-4f83b4b"
   versao_pg     = "18"
   nome_banco    = "observatorio"

   # Preencha com o plano e a região exatos vistos na console do pg-4f83b4b:
   plano         = "free-1-1gb"            # ou o plano exibido na console
   cloud_name    = "google-europe-west1"   # ou a região exibida na console
   ```

---

## 4. Procedimento Oficial de Importação (Sem Recriar a Instância)

Para que o Terraform passe a gerenciar o serviço existente **sem tentar criar outro ou deletar o atual**, utilize o comando oficial de importação do provedor Aiven:

```powershell
# 1. Definir o token pessoal via terminal (sem gravar em arquivo)
$env:AIVEN_API_TOKEN = "seu_token_aiven_aqui"

# 2. Entrar na pasta terraform
cd terraform

# 3. Importar o serviço PostgreSQL existente para o estado
terraform import aiven_pg.observatorio projeto-bigdata/pg-4f83b4b

# 4. Inspecionar o plano de execução
terraform plan
```

### O que observar no `terraform plan`:
- O Terraform deve indicar:
  `Plan: 1 to add, 0 to change, 0 to destroy.` (adicionando apenas o banco `aiven_pg_database.observatorio` dentro da instância existente `pg-4f83b4b`).
- **Nenhum recurso deve estar marcado para destruição (`forces replacement` ou `destroy`).**

---

## 5. Criação do Banco Lógico e Carga de Dados

Após a importação e o planejamento validado:
1. Aplique apenas a criação do banco lógico `observatorio`:
   ```powershell
   terraform apply -target=aiven_pg_database.observatorio
   ```

2. Configure seu `.env` local na raiz do projeto com as credenciais obtidas no console da Aiven:
   ```ini
   DB_HOST=<Host exibido na console do pg-4f83b4b>
   DB_PORT=<Porta exibida na console>
   DB_NAME=observatorio
   DB_USER=avnadmin
   DB_PASSWORD=<Senha exibida na console>
   DB_SSLMODE=require
   ```

3. Dispare a carga automatizada da base do CNPq (25.820 linhas e 26.009 indivíduos ponderados):
   ```powershell
   python -m etl.carga_lattes
   ```
