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

## CNPq — Painel Lattes (opcional, contexto populacional)

Em <http://bi.cnpq.br/painel/formacao-atuacao-lattes/> escolha a dimensão/filtros e use a opção de download
(Excel ou CSV) descrita na página oficial. Registre com `--subpasta cnpq/painel_lattes`.

## CAPES

1. Acesse <https://dadosabertos.capes.gov.br/organization/bolsas-e-auxilios?res_format=CSV> no navegador.
2. Baixe os CSVs desejados e registre com `--subpasta capes/bolsas`.
3. Alternativa para automatizar: defina `CA_BUNDLE` com o arquivo `.pem` da CA confiável da sua rede
   (nunca desative a verificação TLS).

## Documentação do CNPq (automatizável)

```powershell
.\.venv\Scripts\python.exe -m etl.ingestao baixar-documentacao
```
