# Estratégia de volume (limite de 1 GB — PostgreSQL Aiven Free Tier)

## 1. Status atual

- Arquivo bruto: `Download - Tabela.xlsx`, 3.886.479 bytes.
- Base tratada: 25.820 linhas, 40 colunas de dados (+ 2 colunas originais).
- Pessoas ponderadas: 26.009 (`SUM(quantidade)`).
- Tabela PostgreSQL: `lattes_analytics.perfil_pesquisadores_lattes_2023`.
- **Tamanho real do banco (`pg_database_size`): não medido.**
- Estimativa: poucos MB, muito abaixo da cota de 1 GB. A estimativa não
  substitui uma medição.

## 2. Princípios

1. **Orçamento:** dados + índices ≤ ~600 MB (60% de 1 GB), reservando o restante
   para sistema, WAL, estatísticas e crescimento.
2. **Ordem de aplicação (do menos ao mais intrusivo):** seleção de colunas →
   tipos compactos → deduplicação exata → recorte temporal → agregação →
   (último recurso) amostragem.
3. **Nada é descartado do bruto:** o arquivo original permanece em
   `dados/bruto/` (fora do Git).

## 3. Decisões para a base Lattes

| Técnica | Decisão | Justificativa |
|---|---|---|
| **Seleção de colunas** | Manter as 40 colunas da fonte; descartar `sexo_original`/`cor_ou_raca_original` antes da carga | Preserva a granularidade analítica; remove duplicação de auditoria |
| **Chunking** | Inserções em lotes de até 500 registros | Mantém memória constante e respeita o limite de parâmetros do PostgreSQL |
| **Tipos compactos** | `SMALLINT` para ano; `VARCHAR` para dimensões; `INTEGER` para `quantidade` | Reduz volume e mantém legibilidade |
| **Deduplicação** | Somente duplicatas 100% idênticas | Evita remover células legítimas |
| **Recorte temporal** | Não aplicar além de 2023 (o arquivo já é 2023) | O recorte é a própria base |
| **Agregação** | Manter a granularidade da planilha (célula agregada) | Preserva os KPIs e a fidelidade à fonte |
| **Amostragem** | **Não utilizar** nos fatos dos KPIs | Distorceria grupos pequenos e inflaria a variância |
| **Modelo** | Tabela analítica desnormalizada | Evita JOINs e cabe no Free Tier; modelo estrela fica como evolução futura |

## 4. Procedimento de verificação de tamanho

Quando houver autorização para consultar o banco, executar:

```sql
SELECT pg_size_pretty(pg_database_size(current_database()));

SELECT relname, pg_size_pretty(pg_total_relation_size(oid))
FROM pg_class
WHERE relkind = 'r'
  AND relnamespace = 'lattes_analytics'::regnamespace
ORDER BY pg_total_relation_size(oid) DESC;
```

Registrar o resultado neste documento. Se o tamanho medido ultrapassar 600 MB,
aplicar a próxima técnica da ordem acima e documentar o efeito antes de
reexecutar.

> **Status:** não medido. Não há valor de `pg_database_size` registrado nesta
> entrega.
