# Evidência de carga e validação — PostgreSQL Aiven

- **Data:** 06/11/2026
- **Commit de referência:** `b28f88d`
- **Repositório:** <https://github.com/yurifr0807/projeto-big-data>
- **Fonte:** Painel Lattes — CNPq
- **Ano de referência:** 2023

## Infraestrutura

- Provedor: Aiven
- Serviço: PostgreSQL
- Plano: Free (1 GB)
- Projeto: `projeto-bigdata`
- Serviço: `pg-4f83b4b`
- Região: `do-sfo`
- Versão: PostgreSQL 18
- Banco: `observatorio`
- Schema: `lattes_analytics`
- Tabela: `perfil_pesquisadores_lattes_2023`
- Gerenciamento da infraestrutura: Terraform (`terraform/imports.tf` para o serviço existente)
- Estado do Terraform: local, não versionado

## Execução do ETL

A base tratada `painel_lattes_2023_tratado.csv` foi carregada no PostgreSQL por
meio de um pipeline Python com inserções em lotes de até 500 registros.

## Resultado da validação SQL

```text
Linhas: 25820
Soma ponderada: 26009
Validacao: APROVADA
```

Consulta de referência:

```sql
SELECT COUNT(*) AS linhas, SUM(quantidade) AS soma_ponderada
FROM lattes_analytics.perfil_pesquisadores_lattes_2023;
```

A consulta independente confirmou os valores esperados no banco de dados.

## Testes automatizados

```text
99 passed in 22.48s
```

> Este é o resultado histórico da validação no commit `b28f88d`. A suíte
> evoluiu com testes unitários adicionais (fallback de token) e a quantidade
> executada pode variar conforme disponibilidade dos dados locais e de `DB_*`.

### Execução local após os ajustes de documentação

Para validar as alterações sem abrir conexão com o PostgreSQL remoto:

```text
103 passed, 1 deselected in 19.56s
```

Comando: `pytest -q -m "not integracao"`. O teste de integração foi
deliberadamente excluído para não acessar a Aiven.

## Tamanho do banco

`pg_database_size` **não medido** nesta etapa. Nenhum valor foi inventado.

## Limitações

Os registros correspondem ao recorte exportado do Painel Lattes (ano 2023,
filtro PQ 1A = Não). A coluna `quantidade` representa frequências agregadas.
Os resultados não demonstram, isoladamente, taxas de aprovação de propostas de
financiamento científico. Ver [`docs/limitacoes_lattes_2023.md`](../limitacoes_lattes_2023.md).

## Resultado

**Carga e validação SQL aprovadas.**
