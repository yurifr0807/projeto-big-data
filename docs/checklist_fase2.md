# Checklist de Requisitos Acadêmicos — Fase 2

Este documento compara os requisitos do professor (Guia de Orientação e
Solicitação de Entrega Técnica da Fase 2) com o estado implementado no
repositório `projeto-big-data`.

- **Data da validação:** 06/11/2026.
- **Commit de referência:** `b28f88d`.
- **Repositório:** <https://github.com/yurifr0807/projeto-big-data>
- **Evidência principal:** [`docs/evidencias/validacao_carga_2026-11-06.md`](evidencias/validacao_carga_2026-11-06.md).

---

## 1. Status Geral da Fase 2

| Requisito do Professor | Artefato no Repositório | Status Técnico | Observações / Justificativas |
| :--- | :--- | :--- | :--- |
| **1. Base de Dados Tratada** | `dados/tratado/painel_lattes_2023_tratado.csv` | **CONCLUÍDO E VALIDADO** | Base real do CNPq (25.820 linhas; 26.009 indivíduos ponderados). MergeCells resolvidos; 0 nulos estruturais, com missingness substantivo em categorias “Não informado”/“Não desejo declarar”. |
| **2. Origem e Versão Original** | `dados/bruto/manifesto_ingestao.json` | **CONCLUÍDO E VALIDADO** | SHA-256 `939c5f4322e17a86970887f63def21de8b27033187f100ddeaefe9af4fe384e9`; 3.886.479 bytes; origem, data e tipo de ingestão registrados. |
| **3. Processo de Tratamento (ETL)** | `etl/leitor_lattes.py`, `etl/tratamento_lattes.py` | **CONCLUÍDO E VALIDADO** | Código modular e reproduzível com `python -m etl.tratamento_lattes`. |
| **4. Justificativa das Decisões Técnicas** | `docs/linhagem/linhagem_lattes_2023.json` | **CONCLUÍDO E VALIDADO** | Linhagem com origem, SHA-256, tamanho, decisões e versão tratada verificável. |
| **5. Modelagem do Banco de Dados** | `docs/modelagem_postgresql.md`, `etl/ddl_lattes_2023.sql` | **CONCLUÍDO E VALIDADO** | Tabela analítica `lattes_analytics.perfil_pesquisadores_lattes_2023`: 40 colunas de dados + `id_registro`; índices B-Tree. |
| **6. Tratamento da Coluna Quantidade** | `etl/consultas_validacao_lattes.sql`, `tests/test_modelagem_lattes.py` | **CONCLUÍDO E VALIDADO** | Frequência ponderada aplicada (`SUM(quantidade) = 26.009`), evitando `COUNT(*)` como contagem de pessoas. |
| **7. Limitações de Recorte e Filtros** | `docs/limitacoes_lattes_2023.md` | **CONCLUÍDO E VALIDADO** | Recorte 2023, ausência de PQ 1A, veto a taxas de aprovação, agregação, missingness e não causalidade documentados. |
| **8. Infraestrutura como Código (Terraform)** | `terraform/*.tf`, `docs/guia_terraform_aiven.md` | **APLICADO/IMPORTADO NA AIVEN** | Serviço `pg-4f83b4b` (PostgreSQL 18, `do-sfo`, `free-1-1gb`) e banco `observatorio`. Estado local não versionado; `imports.tf` documenta a importação declarativa. |
| **9. Testes Automatizados** | `tests/` | **CONCLUÍDO E VALIDADO** | Resultado de referência: **`99 passed in 22.48s`** (06/11/2026, commit `b28f88d`). A suíte ganhou testes adicionais depois; a quantidade pode variar conforme dados locais e `DB_*`. |
| **10. Carga Real no PostgreSQL na Nuvem (Aiven)** | `etl/carga_lattes.py` | **CONCLUÍDO E VALIDADO** | 25.820 linhas e 26.009 ponderados; status `integra_completa`; carga idempotente e transacional. |

> O tamanho do banco (`pg_database_size`) **não foi medido** de forma
> independente nesta etapa. Não há valor inventado neste documento.

---

## 2. O que está funcional e verificável

- Ingestão imutável e resolução de células mescladas da base do CNPq.
- Tratamento e exportação da base tabular limpa para análise.
- DDL aplicado na Aiven e testado localmente via SQLAlchemy/SQLite.
- Consultas analíticas SQL que comprovam o total ponderado de 26.009 e as
  proporções por sexo e raça.
- Carga idempotente, com detecção de divergência e rollback transacional.
- Testes cobrindo leitura, transformação, validação, linhagem, carga e modelagem.
- Documentação de reprodução completa em
  [`docs/reproducao_fase2.md`](reproducao_fase2.md).

---

## 3. Evidências reais

| Evidência | Resultado |
|---|---|
| ETL | 25.820 linhas; 26.009 ponderados; 40 colunas de dados |
| Carga PostgreSQL | 25.820 linhas; 26.009 ponderados; `integra_completa` |
| Testes | `99 passed in 22.48s` (commit `b28f88d`) |
| Terraform | Serviço e banco aplicados/importados; sem `destroy` |
| Tamanho do banco | **Não medido** |

---

## 4. Próximas fases (fora do escopo desta entrega)

1. **Indicadores de fomento:** o Painel Lattes não contém propostas submetidas
   versus aprovadas. Taxas de aprovação/contemplação dependem do Painel PQ ou
   de outra fonte oficial.
2. **Dashboard:** Streamlit/Plotly com filtros e supressão de células `< 5`.
3. **Publicação online:** implantação e política de acesso.
4. **Licença:** confirmar a licença dos dados do CNPq antes de redistribuir
   arquivos brutos ou tratados.
5. **Medição de volume:** registrar `pg_database_size` em etapa futura, sem
   substituir a estimativa por valor inventado.
