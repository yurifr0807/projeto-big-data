output "pg_host" {
  description = "Host do serviço PostgreSQL."
  value       = aiven_pg.observatorio.service_host
}

output "pg_porta" {
  description = "Porta do serviço PostgreSQL."
  value       = aiven_pg.observatorio.service_port
}

output "pg_banco" {
  description = "Banco lógico do projeto."
  value       = aiven_pg_database.observatorio.database_name
}

output "pg_usuario" {
  description = "Usuário administrador do serviço."
  value       = aiven_pg.observatorio.service_username
}

output "pg_senha" {
  description = "Senha do usuário administrador (sensível). Copie para o .env local; nunca versione."
  value       = aiven_pg.observatorio.service_password
  sensitive   = true
}

output "pg_uri" {
  description = "URI de conexão completa (sensível)."
  value       = aiven_pg.observatorio.service_uri
  sensitive   = true
}
