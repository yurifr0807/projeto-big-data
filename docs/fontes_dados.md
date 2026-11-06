# Fontes de dados oficiais — Fase 2

## 1. Decisão da Fase 2

A fonte efetivamente entregue é o **CNPq — Painel Lattes 2023**, recorte de
formação e atuação de mestres e doutores:

- página: <http://bi.cnpq.br/painel/formacao-atuacao-lattes/>;
- arquivo: `Download - Tabela.xlsx`;
- filtros: ano **2023**; `Bolsista — PQ 1A = Não`;
- SHA-256: `939c5f4322e17a86970887f63def21de8b27033187f100ddeaefe9af4fe384e9`;
- 25.820 linhas; 40 colunas; 26.009 pessoas ponderadas.

Essa base permite análises descritivas de perfil (sexo, cor/raça, formação,
atuação, área, região e bolsas). Ela **não** permite calcular taxa de
aprovação/contemplação, pois não contém propostas submetidas/aprovadas.

## 2. Por que o Painel PQ não foi a base desta fase

O Painel de Chamadas de Bolsas de Produtividade (PQ) é a fonte natural para
indicadores de fomento, mas não foi usado como base da Fase 2. A pesquisa
abaixo permanece como referência para a fase futura.

### 2.1. Painel PQ — características oficiais

- Página: <https://www.gov.br/cnpq/pt-br/acesso-a-informacao/dados-abertos/paineis-de-dados/painel-de-chamadas-de-bolsas-de-produtividade-pq>
- Acesso: painel Power BI incorporado; o botão **“Baixar Planilhas”** permite
  exportar as bases usadas no painel. Não há link estático, API ou CSV/JSON
  listado na página.
- Unidade de observação: **processo/proposta** por chamada. Um mesmo
  pesquisador pode ter vários processos ao longo do período. Não misturar
  propostas com pessoas (CPF único).
- Parecer: contemplados = aprovados com bolsa concedida; não contemplados =
  avaliados sem classificação suficiente e também não aprovados. Sem seleção,
  os dados representam o total de propostas submetidas.
- Sexo e cor/raça vêm do Currículo Lattes; ausentes podem aparecer como
  “Não informado” ou “Não desejo declarar”.
- Localização: região/UF/cidade da instituição onde o proponente pretende
  executar a bolsa; não é residência.
- Níveis: 2013–2023 em 1A, 1B, 1C, 1D e 2; 2024 em diante em A, B, C; SR para
  sênior. Regimes não são diretamente comparáveis.

### 2.2. O que o Painel PQ permitiria

- taxa de contemplação = contempladas ÷ submetidas;
- diferenças por sexo, cor/raça, área, região e nível;
- análise de propostas, não de pessoas.

Esses indicadores ficam para fase futura e dependem de exportação oficial
validada.

## 3. Outras fontes candidatas

| Fonte | Uso potencial | Limitação |
|---|---|---|
| CNPq — Painel de Demanda e Atendimento | demanda × atendimento por área/instituição/região | descrição oficial não cita sexo nem cor/raça |
| CNPq — Painel de Fomento em CT&I | pagamentos de bolsas/auxílios | campos de sexo/raça não verificados |
| CAPES — Bolsas e Auxílios | contexto regional/institucional | acesso TLS bloqueado neste ambiente; sexo/raça não verificados |
| Portal da Transparência | pagamentos | sem raça/cor |
| Censo da Educação Superior/INEP | contexto educacional | granularidade distinta |

## 4. CAPES — pendência

`https://dadosabertos.capes.gov.br/` apresentou falha de verificação TLS neste
ambiente. A verificação não foi desativada. Caminhos possíveis: `CA_BUNDLE`
com a CA confiável da rede/órgão ou download manual pelo navegador
([`docs/download_manual.md`](download_manual.md)).

## 5. Licença e pendências externas

1. Confirmar a licença dos conjuntos do CNPq antes de redistribuir arquivos.
2. Para a fase futura, obter e validar a exportação do Painel PQ.
3. Para a CAPES, obter CA confiável ou arquivos baixados manualmente.
4. Registrar data, SHA-256 e filtros de cada novo arquivo no manifesto.
