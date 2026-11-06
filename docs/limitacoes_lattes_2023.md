# Limitações e escopo — Base Oficial Painel Lattes 2023

## 1. Contexto e identificação da base real

- **Fonte oficial:** CNPq — Painel Lattes: Formação e Atuação de Mestres e Doutores
  (<http://bi.cnpq.br/painel/formacao-atuacao-lattes/>).
- **Arquivo importado:** `Download - Tabela.xlsx`, armazenado em
  `dados/bruto/cnpq/painel_lattes/`.
- **Hash SHA-256:** `939c5f4322e17a86970887f63def21de8b27033187f100ddeaefe9af4fe384e9`.
- **Tamanho:** 3.886.479 bytes (≈3,71 MiB / 3,89 MB).
- **Dimensões brutas:** 25.820 linhas de dados × 40 colunas.
- **Total ponderado:** **26.009** mestres/doutores (`SUM(quantidade)`).
- **Data de exportação:** 2026-11-05; ano de referência: 2023.

## 2. Limitações de escopo e filtros

### 2.1. Recorte temporal fixo em 2023

A exportação contém exclusivamente o ano-base **2023**. Não é possível inferir
séries históricas, tendências longitudinais ou mudanças antes/depois de 2023.
O resultado é um diagnóstico pontual de estoque.

### 2.2. Filtro PQ 1A travado em “Não”

O filtro `Bolsista — PQ 1A` estava configurado como **“Não”**. Portanto:

- o conjunto exclui todos os pesquisadores com bolsa PQ nível 1A;
- o topo da carreira científica do CNPq não está representado;
- não concluir que “não existem bolsistas 1A no Brasil”;
- a limitação deve ser comunicada no dashboard e nos relatórios.

### 2.3. Não aplicável para taxa de aprovação/contemplação

A planilha reflete perfil cadastral e presença/histórico de bolsas. Ela **não
contém** propostas submetidas versus aprovadas/rejeitadas/contempladas. Não
calcular taxa de aprovação com esta base: o denominador seria fictício. Taxas
de fomento dependem do Painel PQ ou de outra fonte oficial.

## 3. Natureza agregada e ponderação

### 3.1. Cada linha é uma célula, não uma pessoa

A base é multidimensional agregada. `COUNT(*)` conta células; `SUM(quantidade)`
conta pessoas. Toda análise descritiva deve usar a soma ponderada.

### 3.2. `quantidade` é uma frequência agregada

A coluna sem cabeçalho da planilha foi renomeada para `quantidade`. Os valores
são inteiros positivos (1 a 5) e somam 26.009. Não há pesos amostrais,
intervalos de confiança ou microdados.

### 3.3. Sem identificadores individuais

Não há CPF, nome ou ID Lattes. Não é possível deduplicar pessoas entre células,
acompanhar trajetórias ou garantir que cada pessoa apareça uma única vez em
todos os recortes.

## 4. Cobertura, missingness e categorias

### 4.1. Sexo e cor/raça são autodeclarados

Os campos vêm do Currículo Lattes e podem estar ausentes ou recusados. No
relatório de qualidade:

- `sexo`: 198 registros “Não informado” (contagem de linhas);
- `cor_ou_raca`: 1.993 registros “Não desejo declarar” (contagem de linhas);
- `grande_area_atuacao`: 3.408 “Não informado” e 305 “Outra” (contagem de linhas).

Percentuais devem ser acompanhados da cobertura.

### 4.2. “0 nulos” não significa ausência de missingness

O relatório mostra 0 nulos estruturais porque as células mescladas foram
resolvidas. Isso não elimina missingness substantivo codificado como
“Não informado”, “Não desejo declarar” ou “Outra”.

### 4.3. Contagens do relatório são de linhas

As categorias do relatório somam 25.820 (linhas), não 26.009 (pessoas). Não use
essas contagens como se fossem pessoas; use SQL com `SUM(quantidade)`.

## 5. Cobertura populacional

A base representa mestres/doutores cadastrados no Lattes, não toda a população
de pesquisadores. Não mede produtividade, financiamento recebido, propostas
submetidas ou decisões de fomento. É um retrato de perfil/estoque.

## 6. Pequenos grupos e LGPD

Categorias pequenas (por exemplo, 84 registros de “Indígena” em nível de linha)
e cruzamentos interseccionais podem ter contagens muito baixas. Células `< 5`
devem ser suprimidas ou agrupadas em saídas públicas para reduzir risco de
reidentificação. Ver [`docs/lgpd.md`](lgpd.md).

## 7. Snapshot, não versão oficial congelada

O arquivo foi exportado em 2026-11-05 com referência 2023. Não é uma versão
oficial versionada do CNPq; é um snapshot. Registrar sempre origem, data, SHA
e filtros aplicados.

## 8. Sem inferência causal

Diferenças por sexo, raça, região ou área são descritivas. A base não controla
produtividade, área, nível, instituição, idade ou perfil de demanda. Portanto,
não prova discriminação nem causalidade.

## 9. Licença e redistribuição

A licença dos dados do CNPq não foi confirmada. Não redistribuir os arquivos
brutos ou tratados até a confirmação. Ver [`docs/lgpd.md`](lgpd.md).

## 10. Resolução de células mescladas

A planilha do Power BI usa 37.983 mesclagens verticais. O leitor
`etl/leitor_lattes.py` propaga o valor âncora para todas as linhas do bloco,
sem imputar valores arbitrários. As 40 colunas resultam com 0 nulos estruturais
após essa etapa.
