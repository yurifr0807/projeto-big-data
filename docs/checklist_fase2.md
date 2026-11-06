# Checklist de Requisitos Acadêmicos — Fase 2

Este documento compara os requisitos do professor (Guia de Orientação e Solicitação de Entrega Técnica da Fase 2) com o estado atual da implementação no repositório `projeto-big-data`.

---

## 1. Status Geral da Fase 2

| Requisito do Professor | Artefato no Repositório | Status Técnico | Observações / Justificativas |
| :--- | :--- | :--- | :--- |
| **1. Base de Dados Tratada** | `dados/tratado/painel_lattes_2023_tratado.csv` | **CONCLUÍDO E VALIDADO** | Base real do CNPq (25.820 linhas, 26.009 indivíduos). MergeCells resolvidos e sem nulos indevidos. |
| **2. Origem e Versão Original** | `dados/bruto/manifesto_ingestao.json` | **CONCLUÍDO E VALIDADO** | SHA-256 oficial registrado, tamanho de 3,88 MB e procedência documentada. |
| **3. Processo de Tratamento (ETL)** | `etl/leitor_lattes.py`, `etl/tratamento_lattes.py` | **CONCLUÍDO E VALIDADO** | Código limpo, modular, documentado e reproduzível com `python -m etl.tratamento_lattes`. |
| **4. Justificativa das Decisões Técnicas** | `docs/linhagem/linhagem_lattes_2023.json` | **CONCLUÍDO E VALIDADO** | Linhagem formal registrando cada transformação com justificativa (LGPD, tipos, merges). |
| **5. Modelagem do Banco de Dados** | `docs/modelagem_postgresql.md`, `etl/ddl_lattes_2023.sql` | **CONCLUÍDO E VALIDADO** | Esquema analítico contendo todas as 40 colunas reais, tipos compactos, chaves e índices B-Tree. |
| **6. Tratamento da Coluna Quantidade** | `etl/consultas_validacao_lattes.sql`, `tests/test_modelagem_lattes.py` | **CONCLUÍDO E VALIDADO** | Frequência ponderada aplicada (`SUM(quantidade) = 26.009`), evitando a contagem simples de linhas. |
| **7. Limitações de Recorte e Filtros** | `docs/limitacoes_lattes_2023.md` | **CONCLUÍDO E VALIDADO** | Recorte estático de 2023, ausência de PQ 1A documentada e veto ao cálculo de taxas de aprovação nesta base. |
| **8. Infraestrutura como Código (Terraform)** | `terraform/*.tf`, `docs/guia_terraform_aiven.md` | **PREPARADO E VALIDADO LOCALMENTE** | Código HCL sintaticamente pronto para Aiven Provider ~> 4.65. Nenhum apply remoto executado. |
| **9. Testes Automatizados** | `tests/` (91 testes locais + 1 de integração) | **CONCLUÍDO E VALIDADO** | Suíte com 92 testes (100% dos testes unitários e de integração local aprovados). |
| **10. Carga Real no PostgreSQL na Nuvem (Aiven)** | `etl/carga_lattes.py` | **PENDENTE DE EXECUÇÃO REAL** | Script de carga transacional pronto; aguarda criação da conta/instância na Aiven pelo aluno. |

---

## 2. O que já está 100% Funcional e Verificável
- Ingestão imutável e resolução de células mescladas da base do CNPq.
- Tratamento e exportação da base tabular limpa para análise.
- DDL completo e testado em banco local via SQLAlchemy.
- Consultas analíticas SQL que comprovam o total ponderado de 26.009 mestres/doutores e as proporções por sexo e raça.
- Testes cobrindo cada função do pipeline.

---

## 3. O que depende de Ação na Nuvem (Próximos Passos)
1. **Provisionamento da Instância Aiven:**
   - Criar o serviço PostgreSQL na Aiven (Free Tier) utilizando o token da conta via Terraform (`terraform plan` / `terraform apply`) ou pelo Console Web.
2. **Configuração de Conexão no `.env`:**
   - Preencher as credenciais geradas (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`).
3. **Disparo da Carga:**
   - Executar `python -m etl.carga_lattes` para efetivar a gravação remota no PostgreSQL da Aiven.
