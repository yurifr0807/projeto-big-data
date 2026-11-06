# Limitações e Escopo: Base Oficial Painel Lattes 2023

## 1. Contexto e Identificação da Base Real
- **Fonte Oficial:** CNPq — Painel Lattes: Formação e Atuação de Mestres e Doutores (<http://bi.cnpq.br/painel/formacao-atuacao-lattes/>).
- **Arquivo Importado:** `Download - Tabela.xlsx` (armazenado de forma imutável em `dados/bruto/cnpq/painel_lattes/`).
- **Hash SHA-256:** `939c5f4322e17a86970887f63def21de8b27033187f100ddeaefe9af4fe384e9`.
- **Tamanho:** 3.886.479 bytes (~3,7 MB).
- **Dimensões Brutas:** 25.820 linhas de dados × 40 colunas.
- **Total Ponderado de Indivíduos:** **26.009** mestres e doutores (somatório da coluna de contagem).

---

## 2. Limitações de Escopo e Filtros

### 2.1. Recorte Temporal Fixo em 2023
- **Natureza da Limitação:** A exportação contém exclusivamente o ano-base **2023** (`.Ano = 2023` constante em todas as 25.820 linhas).
- **Impacto Analítico:** Não permite inferir séries históricas ou tendências longitudinais antes ou depois de 2023 a partir deste arquivo específico. Serve como um diagnóstico pontual de estoque (população de pesquisadores formados e ativos cadastrados no Lattes naquele ano).

### 2.2. Filtro de Bolsista PQ 1A Travado em "Não"
- **Natureza da Limitação:** Na interface de consulta do Painel Lattes, o filtro `.Bolsista - PQ 1A` encontrava-se configurado como **"Não"**.
- **Impacto Analítico:**
  - O conjunto **exclui** todos os pesquisadores com bolsa de Produtividade em Pesquisa nível 1A (o nível mais sênior e prestigioso da carreira do CNPq).
  - Isso afeta a análise do topo da pirâmide científica: a ausência desse estrato impede visualizar o teto de liderança das bolsas PQ neste arquivo específico.
  - A base contém bolsistas PQ de outros níveis (PQ 1B, 1C, 1D, 2 ou 1E) e bolsistas DT (Desenvolvimento Tecnológico), mas o topo 1A está ausente por desenho do filtro exportado.
  - **Decisão:** Esta limitação deve ser explicitamente comunicada no Dashboard e nos relatórios de governança para evitar a conclusão errônea de que "não existem bolsistas 1A no Brasil".

### 2.3. Não Aplicabilidade para Cálculo de Taxa de Aprovação / Contemplação
- **Natureza da Limitação:** A planilha reflete o perfil cadastral de pesquisadores com títulos de mestrado/doutorado e o estado de vigência/histórico de bolsas (sim/não). Ela **não contém** o número de propostas submetidas vs. aprovadas/rejeitadas por chamada.
- **Diretriz Obrigatória:** **Não calcular taxa de aprovação** com base nesta tabela, sob pena de gerar denominadores fictícios e conclusões espúrias. O cálculo de taxa de aprovação depende estritamente das planilhas de chamadas do Painel de Produtividade (PQ/DT).

---

## 3. Resolução Estrutural de Células Mescladas (MergeCells)

- **Comportamento da Fonte:** O sistema Power BI exporta dados agrupados com `mergeCell` nativo no XML do Excel (37.983 mesclagens verticais).
- **Tratamento:** O leitor `etl/leitor_lattes.py` identifica as coordenadas de cada mesclagem vertical (ex.: `A2:A25821`) e propaga o valor âncora para as linhas do bloco correspondente.
- **Garantia de Qualidade:** Todas as 40 colunas resultam com 0% de nulos indevidos, preservando a exata chave multidimensional de cada linha da agregação.

---

## 4. Coluna 40: Contagem de Ocorrências (`quantidade`)
- A última coluna do arquivo original veio sem cabeçalho (`None`).
- A inspeção revelou que todos os valores são inteiros positivos (1 a 5), somando 26.009 indivíduos.
- Foi formalmente renomeada para `quantidade` no pipeline ETL.
