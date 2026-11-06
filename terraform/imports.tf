# ==============================================================================
# BLOCO IMPORT DO TERRAFORM 1.5+
# Permite inspecionar a importação do recurso remoto existente com `terraform plan`
# ANTES de alterar o Terraform State ou aplicar qualquer modificação.
# ==============================================================================

import {
  to = aiven_pg.observatorio
  id = "${var.aiven_project}/${var.nome_servico}"
}
