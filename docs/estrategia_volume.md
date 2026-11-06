# Estratégia de volume (limite de 1 GB — PostgreSQL Aiven Free Tier)

> **Status: decisões registradas ANTES de aplicação aos dados reais.** O tamanho real ainda não foi medido porque
> os arquivos oficiais ainda não foram baixados (ver `docs/fontes_dados.md`). Os limiares abaixo serão confrontados
> com o volume efetivo e este documento será atualizado com os números medidos.

## Princípios

1. **Orçamento:** dados + índices ≤ **~600 MB** (60 % de 1 GB), reservando o restante para sistema, WAL, estatísticas e crescimento.
2. **Ordem de aplicação (do menos ao mais intrusivo):** seleção de colunas → tipos compactos → deduplicação exata →
   recorte temporal → agregação → (último recurso) amostragem.
3. **Nada é descartado do bruto:** o arquivo original permanece em `dados/bruto/` (fora do banco, ignorado pelo Git).

## Decisões

| Técnica | Decisão | Justificativa e efeito na análise |
|---|---|---|
| **Seleção de colunas** | **Aplicar sempre.** Carregar somente colunas necessárias aos KPIs (ano, modalidade, nível, grande área/área, UF/região, instituição, sexo, cor/raça, parecer, valor se existir). Descartar identificadores pessoais (CPF, nome, e-mail) **antes** de qualquer persistência. | Minimização (LGPD) e redução de volume. Sem efeito sobre KPIs. |
| **Chunking** | **Aplicar sempre** (`etl.ingestao.ler_csv_em_chunks`, 100 mil linhas/lote) em CSV; XLSX é lido por aba (limite do formato). | Mantém memória constante. Sem efeito analítico. |
| **Tipos compactos** | `SMALLINT` (ano), `NUMERIC(14,2)` (valores), `TEXT` controlado por dimensões (chaves inteiras nas dimensões do modelo estrela). | Reduz tamanho de fato e índices. Sem efeito analítico. |
| **Deduplicação** | Somente duplicatas **100 % idênticas**. | Evita remover registros legítimos (propostas distintas de um mesmo pesquisador). |
| **Recorte temporal** | **Não aplicar a priori.** O escopo natural do painel PQ (2013–2024) é pequeno. Só recortar se o volume medido exceder o orçamento. | Preserva a série histórica para análises de evolução. |
| **Agregação prévia** | Manter **granularidade de proposta** (uma linha por processo/chamada) enquanto couber. Caso exceda, agregar por `ano × modalidade × nível × área × UF × instituição × sexo × raça × parecer` **com contagem** — preservando exatamente os KPIs e permitindo supressão de células pequenas. | Agregação nessa granularidade **não altera** taxas nem participações; só impede detalhes por proposta. |
| **Amostragem estatística** | **Não utilizar** para KPIs de taxa de aprovação. | Amostrar distorceria grupos pequenos (ex.: indígenas, amarelas) e inflaria a variância; seria incompatível com auditoria de viés. Admitida apenas para tabelas auxiliares volumosas (ex.: logs de exploração), nunca para fatos dos KPIs. |
| **Volumes de outras bases** (ex.: Demanda e Atendimento, Lattes) | Carregar **apenas agregados** (tabelas pré-agregadas por dimensão), nunca microdados. | Mantém a base dentro do orçamento. |

## Procedimento de verificação de tamanho (a ser executado após a carga)

```sql
SELECT pg_size_pretty(pg_database_size(current_database()));
SELECT relname, pg_size_pretty(pg_total_relation_size(oid))
FROM pg_class WHERE relkind = 'r' AND relnamespace = 'public'::regnamespace
ORDER BY pg_total_relation_size(oid) DESC;
```

O resultado deve ser registrado neste documento. Se > 600 MB, aplicar a próxima técnica da ordem acima e
**documentar o efeito antes de reexecutar**.
