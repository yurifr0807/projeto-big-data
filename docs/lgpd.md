# LGPD, segurança e uso responsável

## Finalidade e base
Pesquisa acadêmica sobre equidade de gênero e raça/cor no fomento científico (ODS 5 e 18), com **dados públicos oficiais**
(CNPq/CAPES). Tratamento limitado ao necessário para os indicadores.

## Dados pessoais
* Sexo e cor/raça são dados pessoais **sensíveis** (LGPD, art. 5º, II). O painel PQ os recupera dos Currículos Lattes
  e os publica de forma agregada por proposta; mesmo assim, **combinações raras** (ex.: UF × instituição × raça × nível)
  podem reidentificar pessoas.
* **Minimização:** `tratar_dataframe(..., descartar_identificadores=True)` descarta CPF, nome, e-mail, telefone, nº do processo e id Lattes,
  caso apareçam nas planilhas, **após** a deduplicação (para não confundir propostas distintas com duplicatas). A opção ficará ativa no ETL
  definitivo; o padrão é desligado só até o schema real ser conhecido. Nenhum desses campos será gravado em `dados/tratado/` nem no PostgreSQL.
* **Supressão de células pequenas:** `etl.validacao.agrupamentos_com_risco` identifica combinações com contagem < 5
  (limiar inicial; revisar com o orientador). Essas células serão **suprimidas ou agrupadas** em qualquer saída pública (dashboard).
* **Sem inferência:** é proibido inferir sexo ou raça/cor por nome, localização ou outros atributos. Valores ausentes ficam
  como "Não informado" / "Não desejo declarar"; nunca são convertidos em categoria conhecida.

## Segredos
* `.env`, `*.tfvars`, `*.tfstate`, chaves e certificados estão no `.gitignore`; `.env.example` e `terraform.tfvars.example` não contêm segredos.
* Token da Aiven somente por `AIVEN_API_TOKEN`. Senhas do banco somente em `.env` local ou no gerenciador de segredos da publicação.
* Conexão com o banco com `sslmode=require`.

## Dados no Git
`dados/bruto/*` e `dados/tratado/*` (e `*.csv`, `*.xlsx` etc.) são ignorados. Só o catálogo/metadados são versionados.

## Licença e termos (pendente)
Licença dos conjuntos **não confirmada**: as páginas do CNPq consultadas citam a Política de Dados Abertos (Decreto nº 8.777/2016) mas
não declaram a licença do conjunto. Registrar aqui, após o download, a licença exibida no catálogo oficial e eventuais restrições de
redistribuição. Até lá, **não republicar** os arquivos brutos.

## Limites da interpretação
Diferenças entre grupos são **indicadores descritivos**, não prova de discriminação causal: não controlam produtividade, área,
nível, instituição ou perfil de demanda.
