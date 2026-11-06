# Evidência de carga e validação — PostgreSQL Aiven

**Data:** 06/11/2026
**Fonte:** Painel Lattes — CNPq
**Ano de referência:** 2023

## Infraestrutura

- Provedor: Aiven
- Serviço: PostgreSQL
- Plano: Free (1 GB)
- Projeto: `projeto-bigdata`
- Banco: `observatorio`
- Schema: `lattes_analytics`
- Tabela: `perfil_pesquisadores_lattes_2023`
- Gerenciamento da infraestrutura: Terraform

## Execução do ETL

A base tratada `painel_lattes_2023_tratado.csv` foi carregada no PostgreSQL por meio de um pipeline Python com inserções em lotes de até 500 registros.

## Resultado da validação SQL

```text
Linhas: 25820
Soma ponderada: 26009
Validacao: APROVADA
```

A consulta independente confirmou os valores esperados no banco de dados.

## Testes automatizados

```text
99 passed in 22.48s
```

## Limitações

Os registros correspondem ao recorte exportado do Painel Lattes. A coluna `quantidade` representa frequências agregadas. Os resultados não demonstram, isoladamente, taxas de aprovação de propostas de financiamento científico.

## Resultado

**Carga e validação SQL aprovadas.**
