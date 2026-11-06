# LGPD, segurança e uso responsável

## 1. Finalidade e base legal

Pesquisa acadêmica sobre equidade de gênero e raça/cor no fomento científico
(ODS 5 e ODS 18 — iniciativa da agenda nacional brasileira), com dados públicos
oficiais do CNPq. O tratamento é limitado ao necessário para os indicadores
descritivos previstos na Fase 2.

## 2. Dados pessoais e minimização

- **Sexo e cor/raça são dados pessoais sensíveis** (LGPD, art. 5º, II). No
  Painel Lattes eles são autodeclarados e publicados de forma agregada.
- A base usada na Fase 2 **não contém CPF, nome, e-mail, telefone ou ID Lattes**.
  Ela é uma tabela multidimensional agregada.
- O CSV tratado preserva `sexo_original` e `cor_ou_raca_original` para
  auditoria do ETL. Essas colunas são descartadas antes da carga no PostgreSQL
  (`etl/carga_lattes.py`).
- Não inferir sexo ou raça/cor por nome, localização ou outros atributos.
  Valores ausentes permanecem como “Não informado”/“Não desejo declarar” e
  nunca são convertidos em categoria conhecida.
- O módulo genérico `tratar_dataframe(..., descartar_identificadores=True)`
  existe para bases com identificadores, mas **não é o caminho usado pelo
  pipeline Lattes**, que já recebe dados agregados.

## 3. Células pequenas e reidentificação

- Combinações raras (por exemplo, UF × instituição × raça × nível) podem
  permitir reidentificação, mesmo sem CPF/nome.
- `etl.validacao.agrupamentos_com_risco` identifica combinações com contagem
  `< 5` (limiar inicial; revisar com o orientador).
- Essas células devem ser **suprimidas ou agrupadas** em qualquer saída
  pública (dashboard, relatório, artigo).
- A tabela armazenada no PostgreSQL contém as células agregadas; o acesso deve
  ser restrito e auditável. A supressão é obrigatória na camada de apresentação.

## 4. Segredos

- `.env`, `*.tfvars`, `*.tfstate`, planos, chaves e certificados estão no
  `.gitignore`; `.env.example` e `terraform.tfvars.example` não contêm segredos.
- O token do provider Terraform é lido de **`AIVEN_TOKEN`** no ambiente.
- O script auxiliar `etl/consultar_servico_aiven.py` aceita
  `AIVEN_API_TOKEN` apenas como fallback legado.
- Senhas do banco ficam somente no `.env` local ou em gerenciador de segredos.
- Não grave outputs sensíveis do Terraform (`pg_senha`, `pg_uri`) em arquivos
  JSON ou em logs.
- Conexão com o banco com `sslmode=require`.

## 5. Dados no Git

`dados/bruto/*` e `dados/tratado/*` (e `*.csv`, `*.xlsx` etc.) são ignorados.
Só o catálogo/metadados (manifesto, linhagem, relatório de qualidade) são
versionados.

## 6. Licença e redistribuição (pendente)

A licença dos conjuntos do CNPq **não foi confirmada**. As páginas consultadas
citam a Política de Dados Abertos (Decreto nº 8.777/2016), mas não declaram a
licença específica do conjunto. Até a confirmação:

- não redistribuir os arquivos brutos;
- não publicar o CSV tratado como dataset aberto independente;
- citar a fonte oficial e a data de extração;
- registrar aqui a licença exibida no catálogo oficial quando confirmada.

## 7. Limites de interpretação

Diferenças entre grupos são **indicadores descritivos**, não prova de
discriminação causal. A base não controla produtividade, área, nível,
instituição ou perfil de demanda, e não contém propostas submetidas/aprovadas.
Ver [`docs/limitacoes_lattes_2023.md`](limitacoes_lattes_2023.md).
