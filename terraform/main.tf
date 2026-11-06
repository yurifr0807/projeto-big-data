terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aiven = {
      source = "aiven/aiven"
      # 4.65.1 era a versão mais recente no Terraform Registry em 2026-11-05.
      version = "~> 4.65"
    }
  }
}

# O token NUNCA é escrito em arquivo: exporte AIVEN_API_TOKEN no ambiente
# (o provider lê essa variável automaticamente).
provider "aiven" {}

# Serviço PostgreSQL gerenciado (plano gratuito, ~1 GB de armazenamento).
# ATENÇÃO: este código foi apenas preparado/validado estaticamente;
# nenhum `terraform apply` foi executado.
resource "aiven_pg" "observatorio" {
  project      = var.aiven_project
  cloud_name   = var.cloud_name
  plan         = var.plano
  service_name = var.nome_servico

  # Impede exclusão acidental via API/Terraform. Para encerrar o serviço,
  # altere conscientemente para false e aplique antes de remover o recurso.
  termination_protection = var.protecao_contra_exclusao

  pg_user_config {
    pg_version = var.versao_pg

    # Restringe o acesso público a faixas de IP conhecidas quando informadas.
    # Lista vazia = comportamento padrão do serviço (conexão com TLS + senha).
    dynamic "ip_filter_object" {
      for_each = var.ip_filter
      content {
        network     = ip_filter_object.value
        description = "permitido via terraform"
      }
    }
  }
}

# Banco lógico dedicado ao projeto (o `defaultdb` permanece intocado).
resource "aiven_pg_database" "observatorio" {
  project       = var.aiven_project
  service_name  = aiven_pg.observatorio.service_name
  database_name = var.nome_banco
}
