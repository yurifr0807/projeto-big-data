-- ============================================================================
-- DDL DE CRIAÇÃO DO SCHEMA E TABELAS ANALÍTICAS - BASE PAINEL LATTES 2023
-- Projeto: Auditoria de Viés Étnico-Gênero em Fomento à Pesquisa Científica
-- Alinhamento: ODS 5 (Igualdade de Gênero) e ODS 18 (Igualdade Étnico-Racial)
-- Banco Alvo: PostgreSQL na Nuvem (Aiven Free Tier - limite 1 GB)
-- ============================================================================

-- 1. Criação do Schema Dedicado
CREATE SCHEMA IF NOT EXISTS lattes_analytics;

-- 2. Tabela Analítica Agregada (Reflete fielmente a granularidade multidimensional da base)
-- Observação importante: cada registro nesta tabela representa uma combinação única
-- de atributos formativos, profissionais e demográficos. A coluna 'quantidade'
-- registra a frequência ponderada (número de mestres/doutores naquela célula).
CREATE TABLE IF NOT EXISTS lattes_analytics.perfil_pesquisadores_lattes_2023 (
    id_registro SERIAL PRIMARY KEY,

    -- Dimensão Temporal e Metadados
    ano SMALLINT NOT NULL,
    data_extracao_bd_lattes VARCHAR(10) NOT NULL,

    -- Demografia Interseccional (ODS 5 & 18)
    sexo VARCHAR(20) NOT NULL,
    cor_ou_raca VARCHAR(30) NOT NULL,
    pais_de_nascimento VARCHAR(60),

    -- Geografia e Formação Acadêmica
    pais_formacao VARCHAR(60),
    regiao_formacao VARCHAR(30),
    uf_formacao VARCHAR(30),
    cidade_formacao VARCHAR(100),
    grande_area_formacao VARCHAR(60),
    area_formacao VARCHAR(100),
    instituicao_formacao VARCHAR(255),
    nivel_formacao VARCHAR(30),

    -- Geografia e Atuação Profissional
    pais_atuacao VARCHAR(60),
    regiao_atuacao VARCHAR(30),
    uf_atuacao VARCHAR(30),
    cidade_atuacao VARCHAR(100),
    grande_area_atuacao VARCHAR(60),
    area_atuacao VARCHAR(100),
    instituicao_atuacao VARCHAR(255),
    setor_de_atividade_atuacao VARCHAR(100),
    enquadramento_atuacao VARCHAR(100),

    -- Trajetória de Bolsas de Formação
    bolsista_iniciacao_cientifica VARCHAR(3) NOT NULL,
    bolsista_graduacao_sanduiche VARCHAR(3) NOT NULL,
    bolsista_mestrado VARCHAR(3) NOT NULL,
    bolsista_doutorado VARCHAR(3) NOT NULL,
    bolsista_pos_doutorado VARCHAR(3) NOT NULL,

    -- Bolsas de Produtividade em Pesquisa (PQ)
    bolsista_pq VARCHAR(3) NOT NULL,
    bolsista_pq_1a VARCHAR(3) NOT NULL,  -- Limitação: 100% 'Não' devido a filtro da exportação
    bolsista_pq_1b VARCHAR(3) NOT NULL,
    bolsista_pq_1c VARCHAR(3) NOT NULL,
    bolsista_pq_1d VARCHAR(3) NOT NULL,
    bolsista_pq_2_ou_1e VARCHAR(3) NOT NULL,

    -- Bolsas de Desenvolvimento Tecnológico (DT)
    bolsista_dt VARCHAR(3) NOT NULL,
    bolsista_dt_1a VARCHAR(3) NOT NULL,
    bolsista_dt_1b VARCHAR(3) NOT NULL,
    bolsista_dt_1c VARCHAR(3) NOT NULL,
    bolsista_dt_1d VARCHAR(3) NOT NULL,
    bolsista_dt_2_ou_1e VARCHAR(3) NOT NULL,

    -- Métrica Analítica Agregada (Frequência Ponderada)
    quantidade INTEGER NOT NULL CHECK (quantidade > 0)
);

-- 3. Índices Estratégicos para Consultas Rápidas no Dashboard
CREATE INDEX IF NOT EXISTS idx_lattes_sexo ON lattes_analytics.perfil_pesquisadores_lattes_2023(sexo);
CREATE INDEX IF NOT EXISTS idx_lattes_raca ON lattes_analytics.perfil_pesquisadores_lattes_2023(cor_ou_raca);
CREATE INDEX IF NOT EXISTS idx_lattes_interseccional ON lattes_analytics.perfil_pesquisadores_lattes_2023(sexo, cor_ou_raca);
CREATE INDEX IF NOT EXISTS idx_lattes_pq ON lattes_analytics.perfil_pesquisadores_lattes_2023(bolsista_pq);
CREATE INDEX IF NOT EXISTS idx_lattes_dt ON lattes_analytics.perfil_pesquisadores_lattes_2023(bolsista_dt);
CREATE INDEX IF NOT EXISTS idx_lattes_area_atuacao ON lattes_analytics.perfil_pesquisadores_lattes_2023(grande_area_atuacao);
CREATE INDEX IF NOT EXISTS idx_lattes_regiao_atuacao ON lattes_analytics.perfil_pesquisadores_lattes_2023(regiao_atuacao);
CREATE INDEX IF NOT EXISTS idx_lattes_uf_atuacao ON lattes_analytics.perfil_pesquisadores_lattes_2023(uf_atuacao);
