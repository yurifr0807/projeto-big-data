# Guia de Provisionamento e Infraestrutura como Código (Terraform & Aiven)

Este documento detalha o que é necessário para provisionar a instância gerenciada do **PostgreSQL na Aiven (Free Tier)** via Terraform.

> **Regra de Segurança e Governança:**
> - Nunca execute `terraform apply` sem autorização prévia e deliberada da equipe.
> - Nenhum token, senha ou segredo deve ser colocado nos arquivos `.tf` ou commitado no repositório.

---

## 1. Pré-requisitos
1. **Conta na Aiven:** Ter uma conta ativa na plataforma [Aiven Console](https://console.aiven.io/).
2. **Projeto Criado na Aiven:** Obter o nome do projeto (ex.: `projeto-yuri-bigdata`).
3. **Token de API Pessoal (Aiven API Token):**
   - Acesse *User profile* -> *Tokens* -> *Generate token*.
   - Guarde o token em local seguro (ele só é exibido uma vez).
4. **Terraform CLI Instalado:**
   - Instale o binário do Terraform (versão >= 1.5.0).
   - Verifique com: `terraform -version`.

---

## 2. Configuração de Variáveis de Ambiente (Sem expor segredos)

No Windows (PowerShell):
```powershell
# 1. Definir o Token da Aiven como variável de ambiente (o provider lê automaticamente)
$env:AIVEN_API_TOKEN = "seu-token-secreto-aiven"

# 2. Entrar na pasta do Terraform
cd terraform

# 3. Criar arquivo de variáveis locais (já incluído no .gitignore)
Copy-Item terraform.tfvars.example terraform.tfvars
```

Edite o arquivo `terraform/terraform.tfvars` inserindo apenas o nome do seu projeto:
```hcl
aiven_project = "nome-do-seu-projeto-aiven"
nome_servico  = "pg-observatorio-equidade"
plano         = "free-1-1gb"
cloud_name    = "google-europe-west1"
versao_pg     = "17"
nome_banco    = "observatorio"
```

---

## 3. Comandos de Validação e Planejamento (Seguros)

Execute no diretório `terraform/`:

```powershell
# 1. Inicializar os providers (baixa o provider aiven/aiven ~> 4.65)
terraform init

# 2. Verificar formatação do código HCL
terraform fmt -check

# 3. Validar a sintaxe dos manifestos
terraform validate

# 4. Gerar o plano de execução para inspecionar os recursos antes da criação
terraform plan -out=plano.tfplan
```

---

## 4. Provisionamento Efetivo (Quando Autorizado)

```powershell
# Aplicar o plano inspecionado
terraform apply plano.tfplan

# Obter as credenciais geradas de forma segura:
terraform output -json > credenciais_temporarias.json
```

Transfira as credenciais para o seu `.env` local na raiz do projeto:
```ini
DB_HOST=<pg_host do output>
DB_PORT=<pg_porta do output>
DB_NAME=observatorio
DB_USER=<pg_usuario do output>
DB_PASSWORD=<pg_senha do output>
DB_SSLMODE=require
```

Apague imediatamente o arquivo `credenciais_temporarias.json` após preencher o `.env`.
Em seguida, execute a carga automatizada da base:
```powershell
.\.venv\Scripts\python.exe -m etl.carga_lattes
```
