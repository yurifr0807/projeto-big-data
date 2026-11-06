# Fontes de dados oficiais — levantamento da Fase 2

Levantamento realizado em **2026-11-05** por acesso direto às páginas oficiais (HTTP com TLS verificado).
Só consta como fato o que foi lido nas páginas/documentos oficiais; o restante está marcado como **não verificado**.

## Resultado resumido

| Fonte | Sexo | Cor/raça | Aprovação (parecer) | UF/Região | Área | Instituição | Valores | Acesso automatizado |
|---|---|---|---|---|---|---|---|---|
| **CNPq — Painel de Chamadas de Bolsas PQ** (PQ, PQ-Sr, DT) | Sim | Sim | Sim (contemplado / não contemplado) | Sim | Sim (grande área, área) | Sim | "recursos financeiros concedidos" (citado no manual; campo exato a confirmar) | **Não encontrado** (Power BI; botão "Baixar Planilhas" na interface) |
| CNPq — Painel de Demanda e Atendimento | não citado | não citado | demanda bruta × atendida | Sim | Sim | Sim | Sim (quantidade e valores) | Não encontrado (Power BI) |
| CNPq — Painel Lattes (formação/atuação) | Sim | Sim | — (não é fomento) | Sim | Sim | — | — | Download Excel/CSV pela interface `bi.cnpq.br` |
| CAPES — Bolsas e Auxílios | **não verificado** | **não verificado** | — | — | — | — | — | **Bloqueado** (TLS) |

**Conclusão:** o único conjunto oficial identificado que permite o cruzamento **sexo × cor/raça × aprovação** é o
**Painel de Chamadas de Bolsas de Produtividade (PQ)** do CNPq — **desde que a exportação de planilhas confirme
a granularidade esperada** (ver "Pendências"). Nenhum campo foi considerado adequado sem esta confirmação.

## 1. CNPq — Painel de Chamadas de Bolsas de Produtividade em Pesquisa (fonte principal)

* Página: <https://www.gov.br/cnpq/pt-br/acesso-a-informacao/dados-abertos/paineis-de-dados/painel-de-chamadas-de-bolsas-de-produtividade-pq>
* Formato de acesso: painel **Power BI** incorporado (link `app.powerbi.com/view?r=…` na página). O Manual oficial informa
  que, na página inicial do painel, o botão **"Baixar Planilhas"** permite o download "das bases de dados utilizadas no painel".
  **Não há link estático de arquivo, API ou arquivo CSV/JSON listado na página.** Nenhuma URL de download foi inventada.
* Período: propostas submetidas e aprovadas **2013 a 2023** segundo o texto da página; o Manual e a Nota Técnica
  citam filtro de ano **2013–2024** (PQ e PQ-Sr) e **2012–2024** (DT) e indicadores vigentes até 2026. **Divergência
  a resolver com o arquivo real.**
* Documentação oficial (baixada para `dados/bruto/cnpq/documentacao/`, não versionada):
  * Manual de Utilização do Painel PQ (38 páginas) — `Manual_de_UtilizaoPainel_Bolsas_PQ_PQSR_DT.pdf`
  * Nota Técnica do Painel PQ (6 páginas; o nome do arquivo cita "Junho 2016", mas o conteúdo descreve dados até 2026) — `Nota_TcnicaPainel_Bolsas_PQ_SR_DT_Junho_2016.pdf`
* Definições relevantes da Nota Técnica:
  * **Unidade de observação do painel de chamadas:** número de **processo** (proposta) por chamada; "um mesmo
    pesquisador pode ter vários processos ao longo do período". Já a visão de bolsistas (pagamentos/vigência)
    conta **CPF único por modalidade**. *Propostas e pessoas não podem ser misturadas.*
  * **Ano** = ano de lançamento da chamada (a bolsa é implementada em março do ano seguinte).
  * **Parecer:** *contemplados* = aprovados e com bolsa concedida; *não contemplados* = avaliados sem classificação
    suficiente **e também os não aprovados**. Sem seleção, os dados são o total de **propostas submetidas**.
    ⇒ A taxa (contempladas ÷ submetidas) é viável; "aprovadas mas não contempladas" não é separável.
  * **Sexo:** vem do Currículo Lattes; ausente → "Não informado".
  * **Cor ou raça:** vem do Currículo Lattes; ausente (campo só passou a ser exigido a partir de certo período) →
    "Não informado"; recusa explícita → "Não desejo declarar". **Não existe no painel CONFAP.**
  * **Localização:** região/UF/cidade da **instituição onde o proponente pretende executar a bolsa**.
  * **Instituição:** instituição de vínculo informada na proposta.
  * **Níveis:** 2013–2023 em cinco níveis (1A, 1B, 1C, 1D, 2); 2024 em diante em três (A, B, C); SR para sênior.
    Mantidos separados — **não comparáveis diretamente**.
  * **Filtros do painel:** ano, área, instituição, UF, grande área, comitê assessor (CA), parecer, modalidade, categoria/nível.
* Atualização/versão: o site não exibe número de versão; registrar a **data do download** e o **SHA-256** no manifesto.
* Licença/termos: a página não declara licença própria; o CNPq publica sob a Política de Dados Abertos
  (Decreto nº 8.777/2016) e há página de "Privacidade e Proteção de Dados". **Pendente:** confirmar a licença
  (p. ex. CC-BY) no catálogo oficial ao baixar; registrar em `docs/lgpd.md`.

### Possibilidade de cruzamento interseccional
Sexo e cor/raça estão no **mesmo painel**; o cruzamento só será confirmado se a planilha exportada trouxer ambos no mesmo
nível de linha (ou em tabela cruzada). Caso as planilhas venham em tabelas separadas (marginais), **o cruzamento
interseccional não será possível** — esse caso será registrado como limitação e investigada outra base (abaixo).

## 2. Outras bases CNPq (candidatas)

| Base | Para que serve | Limitação |
|---|---|---|
| Painel de Demanda e Atendimento (Power BI, desde 2006) | Demanda × atendimento de **todas** as linhas de fomento, com valores, por área/instituição/região | A descrição oficial não cita sexo nem cor/raça |
| Painel Lattes (`bi.cnpq.br/painel/formacao-atuacao-lattes/`, Excel/CSV) | Perfil (sexo, faixa etária, cor/raça) da população de mestres e doutores — **denominador/contexto** | Não é concessão de fomento |
| Painel de Fomento em CT&I (`bi.cnpq.br/painel/v2/p-fomento-cti.html`) | Pagamentos de bolsas/auxílios | Campos de sexo/raça **não verificados** |
| Plano de Dados Abertos 2026–2028 | Lista de bases a abrir (inclui "Julgamento das propostas", meta Dez/24; "Plataforma Lattes – Mestres e Doutores" com sexo/raça/cor) | É cronograma: a abertura efetiva **não foi verificada**; o portal `dadosabertos.cnpq.br` recusou a conexão (reset) durante o levantamento |

`dados.gov.br` exige token para a API (HTTP 401 sem credencial). Não foi usada nenhuma credencial nem rota alternativa.

## 3. CAPES (pendência temporária)

* `https://dadosabertos.capes.gov.br/` — a verificação TLS falha neste ambiente
  (`CERTIFICATE_VERIFY_FAILED: self-signed certificate in certificate chain`). **A verificação não foi desativada**
  e nenhuma lista de datasets foi obtida. Caminhos legítimos: (a) `CA_BUNDLE` com a CA confiável da rede/órgão;
  (b) download manual pelo navegador (`docs/download_manual.md`).
* Pesquisa web (não verificada) sugere que a CAPES não divulga sexo/raça por bolsista. Se confirmado, a CAPES servirá
  apenas para contexto regional/institucional, e **não será integrada ao CNPq** sem compatibilidade de indicadores,
  granularidade, períodos e definições.

## 4. Outras bases oficiais a investigar caso o cruzamento falhe
Pistas **não verificadas** (apenas candidatas): Portal da Transparência (pagamentos a favorecidos — sem raça/cor),
Censo da Educação Superior/INEP e Painel Lattes. A decisão só será tomada após a confirmação dos campos reais.

## Pendências externas desta fonte
1. Baixar manualmente as planilhas do painel PQ (ver `docs/download_manual.md`) e importá-las com `python -m etl.ingestao importar`.
2. Confirmar nomes de colunas, categorias, anos e se o cruzamento sexo × raça × parecer existe por linha.
3. Confirmar licença.
4. CAPES: fornecer CA confiável ou arquivos baixados manualmente.
