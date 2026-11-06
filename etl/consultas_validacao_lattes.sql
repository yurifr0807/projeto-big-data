-- ============================================================================
-- CONSULTAS ANALÍTICAS DE VALIDAÇÃO E AUDITORIA - BASE PAINEL LATTES 2023
-- ============================================================================

-- 1. Verificação Geral de Registros e Soma Ponderada
-- Deve retornar:
-- total_linhas_armazenadas = 25.820
-- total_pesquisadores_ponderado = 26.009
SELECT
    COUNT(*) AS total_linhas_armazenadas,
    SUM(quantidade) AS total_pesquisadores_ponderado
FROM lattes_analytics.perfil_pesquisadores_lattes_2023;

-- 2. Distribuição por Sexo (Ponderada vs Contagem Simples)
-- Demonstra a importância de ponderar pela coluna 'quantidade'
SELECT
    sexo,
    COUNT(*) AS linhas_contagem_simples,
    SUM(quantidade) AS total_pesquisadores,
    ROUND(SUM(quantidade)::numeric / SUM(SUM(quantidade)) OVER () * 100, 2) AS percentual_ponderado
FROM lattes_analytics.perfil_pesquisadores_lattes_2023
GROUP BY sexo
ORDER BY total_pesquisadores DESC;

-- 3. Distribuição por Raça/Cor (Ponderada)
SELECT
    cor_ou_raca,
    SUM(quantidade) AS total_pesquisadores,
    ROUND(SUM(quantidade)::numeric / SUM(SUM(quantidade)) OVER () * 100, 2) AS percentual_ponderado
FROM lattes_analytics.perfil_pesquisadores_lattes_2023
GROUP BY cor_ou_raca
ORDER BY total_pesquisadores DESC;

-- 4. Análise Interseccional Completa: Gênero x Raça/Cor
SELECT
    sexo,
    cor_ou_raca,
    SUM(quantidade) AS total_pesquisadores,
    ROUND(SUM(quantidade)::numeric / SUM(SUM(quantidade)) OVER () * 100, 2) AS percentual_sobre_total
FROM lattes_analytics.perfil_pesquisadores_lattes_2023
GROUP BY sexo, cor_ou_raca
ORDER BY total_pesquisadores DESC;

-- 5. Presença de Bolsistas de Produtividade (PQ) por Sexo e Raça/Cor
-- Lembrar: PQ 1A está travado em 'Não' nesta extração
SELECT
    sexo,
    cor_ou_raca,
    SUM(CASE WHEN bolsista_pq = 'Sim' THEN quantidade ELSE 0 END) AS bolsistas_pq,
    SUM(CASE WHEN bolsista_dt = 'Sim' THEN quantidade ELSE 0 END) AS bolsistas_dt,
    SUM(quantidade) AS total_na_categoria,
    ROUND(SUM(CASE WHEN bolsista_pq = 'Sim' THEN quantidade ELSE 0 END)::numeric / NULLIF(SUM(quantidade), 0) * 100, 2) AS taxa_bolsistas_pq_pct
FROM lattes_analytics.perfil_pesquisadores_lattes_2023
GROUP BY sexo, cor_ou_raca
ORDER BY bolsistas_pq DESC;

-- 6. Distribuição Regional de Pesquisadores Ativos
SELECT
    regiao_atuacao,
    SUM(quantidade) AS total_pesquisadores,
    ROUND(SUM(quantidade)::numeric / SUM(SUM(quantidade)) OVER () * 100, 2) AS percentual
FROM lattes_analytics.perfil_pesquisadores_lattes_2023
GROUP BY regiao_atuacao
ORDER BY total_pesquisadores DESC;
