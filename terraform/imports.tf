# ==============================================================================
# BLOCO IMPORT DO TERRAFORM 1.5+
# Permite inspecionar a importação do serviço PostgreSQL existente com
# `terraform plan` ANTES de alterar o Terraform State ou aplicar mudanças.
#
# Nota: este bloco cobre apenas aiven_pg.observatorio. Se o banco lógico
# aiven_pg_database.observatorio já existir e não estiver no state, importe-o
# separadamente (ID no formato projeto/serviço/banco) antes de qualquer apply.
# ==============================================================================

import {
  to = aiven_pg.observatorio
  id = "${var.aiven_project}/${var.nome_servico}"
}
