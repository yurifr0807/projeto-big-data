# Procedimento oficial de download manual

O acesso automatizado aos dados do CNPq não está disponível (painéis Power BI sem link estático ou API) e o portal
da CAPES falha na verificação TLS neste ambiente. Use o procedimento abaixo e registre o arquivo no pipeline.

## CNPq — Painel de Bolsas de Produtividade (PQ)

1. Abra <https://www.gov.br/cnpq/pt-br/acesso-a-informacao/dados-abertos/paineis-de-dados/painel-de-chamadas-de-bolsas-de-produtividade-pq>
   e clique em **"Acesse o painel"**.
2. Na página inicial do painel, **sem aplicar filtros** (para obter todo o período), role a barra lateral até a parte
   inferior e clique em **"Baixar Planilhas"** (conforme o Manual oficial, seção 1).
3. Repita para cada modalidade/aba que ofereça o botão (PQ, PQ-Sr, DT) e, se existir, para a página analítica.
4. Salve os arquivos com o nome original, em uma pasta fora do repositório (ex.: `Downloads`).
5. Anote: **URL do painel**, **data/hora do download** e quaisquer filtros ativos.
6. Registre cada arquivo (copia para `dados/bruto/`, calcula SHA-256 e atualiza o manifesto):

```powershell
.\.venv\Scripts\python.exe -m etl.ingestao importar "C:\Users\<voce>\Downloads\arquivo.xlsx" `
  --subpasta cnpq/painel_pq `
  --origem "Painel PQ CNPq (https://www.gov.br/cnpq/.../painel-de-chamadas-de-bolsas-de-produtividade-pq), baixado em AAAA-MM-DD"
```

7. Informe os nomes de arquivo e abas; o próximo passo é inspecionar colunas e categorias reais e **só então**
   definir o esquema e a modelagem definitiva.

> Os arquivos em `dados/bruto/` são imutáveis e ignorados pelo Git. Não os edite; o reprocessamento parte sempre deles.

## CNPq — Painel Lattes (fonte efetiva da Fase 2)

A base entregue na Fase 2 é o Painel Lattes, recorte **2023**:

1. Abra <http://bi.cnpq.br/painel/formacao-atuacao-lattes/>.
2. Selecione o ano de referência **2023**.
3. Mantenha o filtro **Bolsista — PQ 1A = Não**.
4. Baixe a planilha com o nome original `Download - Tabela.xlsx`.
5. Confira o SHA-256:
   `939c5f4322e17a86970887f63def21de8b27033187f100ddeaefe9af4fe384e9`.
6. Registre com `--subpasta cnpq/painel_lattes`:

```powershell
python -m etl.ingestao importar "C:\Users\<voce>\Downloads\Download - Tabela.xlsx" `
  --subpasta cnpq/painel_lattes `
  --origem "Exportação oficial do Painel Lattes do CNPq, exportado em 2026-11-05 com ano=2023 e PQ 1A=Não"
```

Resultado esperado: 25.820 linhas, 40 colunas e `SUM(quantidade) = 26.009`.
O roteiro completo está em [`docs/reproducao_fase2.md`](reproducao_fase2.md).

## CAPES

1. Acesse <https://dadosabertos.capes.gov.br/organization/bolsas-e-auxilios?res_format=CSV> no navegador.
2. Baixe os CSVs desejados e registre com `--subpasta capes/bolsas`.
3. Alternativa para automatizar: defina `CA_BUNDLE` com o arquivo `.pem` da CA confiável da sua rede
   (nunca desative a verificação TLS).

## Documentação do CNPq (automatizável)

```powershell
.\.venv\Scripts\python.exe -m etl.ingestao baixar-documentacao
```
