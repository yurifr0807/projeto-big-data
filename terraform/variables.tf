variable "aiven_project" {
  description = "Nome do projeto na Aiven onde o serviço será criado."
  type        = string
}

variable "nome_servico" {
  description = "Nome do serviço PostgreSQL."
  type        = string
  default     = "pg-4f83b4b"
}

variable "plano" {
  description = "Plano do serviço existente na Aiven."
  type        = string
  default     = "free-1-1gb"
}

variable "cloud_name" {
  description = "Nuvem/região DigitalOcean na Aiven onde o serviço free-1-1gb foi provisionado."
  type        = string
  default     = "do-sfo"
}

variable "versao_pg" {
  description = "Versão major do PostgreSQL do serviço existente."
  type        = string
  default     = "18"
}

variable "nome_banco" {
  description = "Banco lógico do projeto."
  type        = string
  default     = "observatorio"
}

variable "protecao_contra_exclusao" {
  description = "Ativa a proteção contra exclusão do serviço."
  type        = bool
  default     = true
}

variable "ip_filter" {
  description = "Lista de CIDRs autorizados a conectar (ex.: [\"203.0.113.10/32\"]). Vazia = sem filtro adicional."
  type        = list(string)
  default     = []
}
