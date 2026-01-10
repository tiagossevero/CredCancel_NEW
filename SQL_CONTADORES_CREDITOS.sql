-- =============================================================================
-- PROJETO CREDITOS - SQL para Análise de Contadores
-- =============================================================================
-- Este script cria tabelas para análise de contadores/contabilistas
-- identificando aqueles com mais empresas com créditos acumulados
-- e comportamentos suspeitos relacionados à reforma tributária
-- =============================================================================

-- =============================================================================
-- 1. TABELA: credito_contador_carteira
-- Base de contadores com suas empresas e métricas de crédito
-- =============================================================================

DROP TABLE IF EXISTS teste.credito_contador_carteira;

CREATE TABLE teste.credito_contador_carteira AS
SELECT
    contrib.nu_cpf_cnpj_contador AS cpf_cnpj_contador,
    contrib.nm_contador AS nome_contador,
    contrib.nu_crc_contador AS crc_contador,
    contrib.nm_munic_contador AS municipio_contador,
    contrib.cd_uf_contador AS uf_contador,
    contrib.nm_email_contador AS email_contador,
    contrib.nu_telefone_contador AS telefone_contador,
    contrib.dt_ini_relac_contador AS dt_inicio_relac_contador,

    -- Dados da empresa
    cred.nu_cnpj AS cnpj_empresa,
    contrib.nm_razao_social AS razao_social_empresa,
    contrib.nm_gerfe AS gerfe_empresa,
    contrib.nm_munic AS municipio_empresa,
    contrib.cd_sit_cadastral AS cod_situacao_empresa,
    contrib.nm_sit_cadastral AS situacao_empresa,
    contrib.nm_reg_apuracao AS regime_apuracao,
    contrib.sn_simples_nacional_rfb AS flag_simples_nacional,
    contrib.de_cnae AS descricao_cnae,

    -- Métricas de crédito
    cred.saldo_credor_atual,
    cred.saldo_12m_atras,
    cred.saldo_60m_atras,
    cred.score_risco_12m,
    cred.score_risco_60m,
    cred.score_risco_combinado_12m,
    cred.score_risco_combinado_60m,
    cred.classificacao_risco_12m,
    cred.classificacao_risco_60m,
    cred.classificacao_risco_combinado_12m,
    cred.classificacao_risco_combinado_60m,
    cred.crescimento_saldo_percentual_12m,
    cred.crescimento_saldo_percentual_60m,
    cred.qtde_ultimos_12m_iguais,
    cred.vl_credito_presumido_12m,
    cred.vl_credito_presumido_60m,

    -- Flags de suspeita/fraude
    cred.flag_empresa_suspeita,
    cred.qtde_indicios_fraude,
    cred.sn_cancelado_inex_inativ,
    cred.flag_tem_declaracoes_zeradas,
    cred.flag_tem_omissoes

FROM teste.credito_dime_completo cred
LEFT JOIN usr_sat_ods.vw_cad_contrib contrib
    ON cred.nu_cnpj = contrib.nu_cnpj
WHERE contrib.nu_cpf_cnpj_contador IS NOT NULL
  AND TRIM(contrib.nu_cpf_cnpj_contador) != '';

-- =============================================================================
-- 2. TABELA: credito_contador_scores
-- Agregação e scores por contador
-- =============================================================================

DROP TABLE IF EXISTS teste.credito_contador_scores;

CREATE TABLE teste.credito_contador_scores AS
WITH base AS (
    SELECT * FROM teste.credito_contador_carteira
),

agregado AS (
    SELECT
        cpf_cnpj_contador,
        nome_contador,
        crc_contador,
        municipio_contador,
        uf_contador,
        email_contador,
        telefone_contador,

        -- Volume
        COUNT(DISTINCT cnpj_empresa) AS total_empresas_carteira,

        -- Empresas com saldo credor > 0
        SUM(CASE WHEN saldo_credor_atual > 0 THEN 1 ELSE 0 END) AS qtde_empresas_com_credito,

        -- Classificação de risco 12m
        SUM(CASE WHEN classificacao_risco_12m = 'CRÍTICO' THEN 1 ELSE 0 END) AS qtde_risco_critico_12m,
        SUM(CASE WHEN classificacao_risco_12m = 'ALTO' THEN 1 ELSE 0 END) AS qtde_risco_alto_12m,
        SUM(CASE WHEN classificacao_risco_12m = 'MÉDIO' THEN 1 ELSE 0 END) AS qtde_risco_medio_12m,
        SUM(CASE WHEN classificacao_risco_12m = 'BAIXO' THEN 1 ELSE 0 END) AS qtde_risco_baixo_12m,

        -- Classificação de risco 60m
        SUM(CASE WHEN classificacao_risco_60m = 'CRÍTICO' THEN 1 ELSE 0 END) AS qtde_risco_critico_60m,
        SUM(CASE WHEN classificacao_risco_60m = 'ALTO' THEN 1 ELSE 0 END) AS qtde_risco_alto_60m,
        SUM(CASE WHEN classificacao_risco_60m = 'MÉDIO' THEN 1 ELSE 0 END) AS qtde_risco_medio_60m,
        SUM(CASE WHEN classificacao_risco_60m = 'BAIXO' THEN 1 ELSE 0 END) AS qtde_risco_baixo_60m,

        -- Financeiro
        SUM(saldo_credor_atual) AS saldo_credor_total,
        AVG(saldo_credor_atual) AS saldo_credor_medio,
        MAX(saldo_credor_atual) AS saldo_credor_max,

        -- Evolução (reforma tributária)
        SUM(CASE WHEN saldo_credor_atual > saldo_12m_atras THEN 1 ELSE 0 END) AS qtde_aumentaram_12m,
        SUM(CASE WHEN saldo_credor_atual > saldo_60m_atras THEN 1 ELSE 0 END) AS qtde_aumentaram_60m,
        SUM(CASE WHEN saldo_credor_atual > 0 AND (saldo_60m_atras IS NULL OR saldo_60m_atras = 0) THEN 1 ELSE 0 END) AS qtde_novas_creditadoras,

        -- Crescimento
        AVG(crescimento_saldo_percentual_12m) AS crescimento_medio_12m,
        AVG(crescimento_saldo_percentual_60m) AS crescimento_medio_60m,
        SUM(CASE WHEN crescimento_saldo_percentual_12m > 100 THEN 1 ELSE 0 END) AS qtde_crescimento_alto_12m,
        SUM(CASE WHEN crescimento_saldo_percentual_60m > 100 THEN 1 ELSE 0 END) AS qtde_crescimento_alto_60m,

        -- Estagnação
        SUM(CASE WHEN qtde_ultimos_12m_iguais >= 6 THEN 1 ELSE 0 END) AS qtde_estagnadas_6m,
        SUM(CASE WHEN qtde_ultimos_12m_iguais >= 12 THEN 1 ELSE 0 END) AS qtde_estagnadas_12m,

        -- Crédito presumido
        SUM(vl_credito_presumido_12m) AS credito_presumido_total_12m,
        SUM(vl_credito_presumido_60m) AS credito_presumido_total_60m,
        SUM(CASE WHEN vl_credito_presumido_12m > 0 THEN 1 ELSE 0 END) AS qtde_com_credito_presumido,

        -- Suspeitas e fraudes
        SUM(CASE WHEN flag_empresa_suspeita = 1 THEN 1 ELSE 0 END) AS qtde_empresas_suspeitas,
        SUM(qtde_indicios_fraude) AS total_indicios_fraude,
        SUM(CASE WHEN qtde_indicios_fraude >= 5 THEN 1 ELSE 0 END) AS qtde_empresas_5plus_indicios,
        SUM(CASE WHEN sn_cancelado_inex_inativ = 1 THEN 1 ELSE 0 END) AS qtde_canceladas_inativas,
        SUM(CASE WHEN flag_tem_declaracoes_zeradas = 1 THEN 1 ELSE 0 END) AS qtde_com_declaracoes_zeradas,
        SUM(CASE WHEN flag_tem_omissoes = 1 THEN 1 ELSE 0 END) AS qtde_com_omissoes,

        -- Regime de apuração (comportamento reforma)
        SUM(CASE WHEN flag_simples_nacional = 1 THEN 1 ELSE 0 END) AS qtde_simples_nacional,
        SUM(CASE WHEN flag_simples_nacional = 0 OR flag_simples_nacional IS NULL THEN 1 ELSE 0 END) AS qtde_regime_normal,

        -- Scores médios
        AVG(score_risco_12m) AS score_medio_12m,
        AVG(score_risco_60m) AS score_medio_60m,
        AVG(score_risco_combinado_12m) AS score_combinado_medio_12m,
        AVG(score_risco_combinado_60m) AS score_combinado_medio_60m

    FROM base
    GROUP BY
        cpf_cnpj_contador,
        nome_contador,
        crc_contador,
        municipio_contador,
        uf_contador,
        email_contador,
        telefone_contador
)

SELECT
    *,
    -- Taxas
    ROUND(qtde_empresas_com_credito * 100.0 / NULLIF(total_empresas_carteira, 0), 2) AS taxa_com_credito_perc,
    ROUND((qtde_risco_critico_12m + qtde_risco_alto_12m) * 100.0 / NULLIF(total_empresas_carteira, 0), 2) AS taxa_risco_alto_critico_perc,
    ROUND(qtde_novas_creditadoras * 100.0 / NULLIF(total_empresas_carteira, 0), 2) AS taxa_novas_creditadoras_perc,
    ROUND(qtde_empresas_suspeitas * 100.0 / NULLIF(total_empresas_carteira, 0), 2) AS taxa_suspeitas_perc,
    ROUND(qtde_estagnadas_12m * 100.0 / NULLIF(total_empresas_carteira, 0), 2) AS taxa_estagnadas_perc,

    -- Scores do Contador (0-100)
    -- Score Volume (0-30): baseado na quantidade de empresas com crédito
    LEAST(30, ROUND(qtde_empresas_com_credito * 3.0, 0)) AS score_volume,

    -- Score Concentração (0-25): baseado na taxa de empresas com risco alto/crítico
    LEAST(25, ROUND((qtde_risco_critico_12m + qtde_risco_alto_12m) * 100.0 / NULLIF(total_empresas_carteira, 0) * 0.5, 0)) AS score_concentracao,

    -- Score Financeiro (0-25): baseado no saldo credor total
    LEAST(25, ROUND(LOG10(GREATEST(saldo_credor_total, 1)) * 2.5, 0)) AS score_financeiro,

    -- Score Suspeita (0-20): baseado em empresas suspeitas e indicios
    LEAST(20, ROUND((qtde_empresas_suspeitas * 5 + total_indicios_fraude * 0.5), 0)) AS score_suspeita

FROM agregado
WHERE total_empresas_carteira >= 1;

-- Adicionar score total e classificação
DROP TABLE IF EXISTS teste.credito_contador_final;

CREATE TABLE teste.credito_contador_final AS
SELECT
    *,
    (score_volume + score_concentracao + score_financeiro + score_suspeita) AS score_total_contador,

    CASE
        WHEN (score_volume + score_concentracao + score_financeiro + score_suspeita) >= 70 THEN 'CRÍTICO'
        WHEN (score_volume + score_concentracao + score_financeiro + score_suspeita) >= 50 THEN 'ALTO'
        WHEN (score_volume + score_concentracao + score_financeiro + score_suspeita) >= 30 THEN 'MÉDIO'
        ELSE 'BAIXO'
    END AS classificacao_risco_contador,

    CASE
        WHEN qtde_empresas_suspeitas >= 5 OR taxa_suspeitas_perc >= 30 THEN 'INVESTIGAR'
        WHEN qtde_novas_creditadoras >= 10 OR taxa_novas_creditadoras_perc >= 20 THEN 'ATENÇÃO ESPECIAL'
        WHEN (score_volume + score_concentracao + score_financeiro + score_suspeita) >= 50 THEN 'MONITORAR'
        ELSE 'NORMAL'
    END AS nivel_alerta_contador

FROM teste.credito_contador_scores;

-- Criar ranking
DROP TABLE IF EXISTS teste.credito_contador_ranking;

CREATE TABLE teste.credito_contador_ranking AS
SELECT
    ROW_NUMBER() OVER (ORDER BY score_total_contador DESC, saldo_credor_total DESC) AS ranking_contador,
    *
FROM teste.credito_contador_final
ORDER BY ranking_contador;

-- =============================================================================
-- 3. TABELA: credito_contador_reforma
-- Análise específica de comportamento pós-reforma tributária
-- =============================================================================

DROP TABLE IF EXISTS teste.credito_contador_reforma;

CREATE TABLE teste.credito_contador_reforma AS
WITH base AS (
    SELECT * FROM teste.credito_contador_carteira
),

-- Identificar empresas que começaram a se creditar recentemente (reforma)
novas_creditadoras AS (
    SELECT
        cpf_cnpj_contador,
        COUNT(*) AS qtde_novas,
        SUM(saldo_credor_atual) AS saldo_novas
    FROM base
    WHERE saldo_credor_atual > 0
      AND (saldo_60m_atras IS NULL OR saldo_60m_atras = 0)
    GROUP BY cpf_cnpj_contador
),

-- Empresas que saíram do Simples (ou nunca foram) e agora têm crédito
comportamento_regime AS (
    SELECT
        cpf_cnpj_contador,
        SUM(CASE WHEN flag_simples_nacional = 0 AND saldo_credor_atual > 0 THEN 1 ELSE 0 END) AS regime_normal_com_credito,
        SUM(CASE WHEN flag_simples_nacional = 1 AND saldo_credor_atual > 0 THEN 1 ELSE 0 END) AS simples_com_credito,
        SUM(CASE WHEN flag_simples_nacional = 0 AND crescimento_saldo_percentual_12m > 50 THEN 1 ELSE 0 END) AS regime_normal_crescendo,
        SUM(saldo_credor_atual) FILTER (WHERE flag_simples_nacional = 0) AS saldo_regime_normal,
        SUM(saldo_credor_atual) FILTER (WHERE flag_simples_nacional = 1) AS saldo_simples
    FROM base
    GROUP BY cpf_cnpj_contador
),

-- Crescimento acelerado (indicativo de preparação para reforma)
crescimento_acelerado AS (
    SELECT
        cpf_cnpj_contador,
        COUNT(*) AS qtde_crescimento_acelerado,
        SUM(saldo_credor_atual) AS saldo_crescimento_acelerado,
        AVG(crescimento_saldo_percentual_12m) AS media_crescimento
    FROM base
    WHERE crescimento_saldo_percentual_12m > 100
    GROUP BY cpf_cnpj_contador
)

SELECT
    r.ranking_contador,
    r.cpf_cnpj_contador,
    r.nome_contador,
    r.crc_contador,
    r.municipio_contador,
    r.uf_contador,
    r.total_empresas_carteira,
    r.saldo_credor_total,

    -- Novas creditadoras
    COALESCE(nc.qtde_novas, 0) AS qtde_novas_creditadoras,
    COALESCE(nc.saldo_novas, 0) AS saldo_novas_creditadoras,
    ROUND(COALESCE(nc.qtde_novas, 0) * 100.0 / NULLIF(r.total_empresas_carteira, 0), 2) AS perc_novas_creditadoras,

    -- Comportamento por regime
    COALESCE(cr.regime_normal_com_credito, 0) AS qtde_regime_normal_com_credito,
    COALESCE(cr.simples_com_credito, 0) AS qtde_simples_com_credito,
    COALESCE(cr.regime_normal_crescendo, 0) AS qtde_regime_normal_crescendo,
    COALESCE(cr.saldo_regime_normal, 0) AS saldo_regime_normal,
    COALESCE(cr.saldo_simples, 0) AS saldo_simples,

    -- Crescimento acelerado
    COALESCE(ca.qtde_crescimento_acelerado, 0) AS qtde_crescimento_acelerado,
    COALESCE(ca.saldo_crescimento_acelerado, 0) AS saldo_crescimento_acelerado,
    COALESCE(ca.media_crescimento, 0) AS media_crescimento_acelerado,

    -- Score de comportamento reforma (0-100)
    LEAST(100,
        COALESCE(nc.qtde_novas, 0) * 5 +
        COALESCE(ca.qtde_crescimento_acelerado, 0) * 3 +
        CASE WHEN COALESCE(nc.qtde_novas, 0) * 100.0 / NULLIF(r.total_empresas_carteira, 0) > 20 THEN 20 ELSE 0 END +
        CASE WHEN COALESCE(ca.media_crescimento, 0) > 200 THEN 20 ELSE 0 END
    ) AS score_comportamento_reforma,

    -- Classificação reforma
    CASE
        WHEN COALESCE(nc.qtde_novas, 0) >= 10 AND COALESCE(ca.qtde_crescimento_acelerado, 0) >= 5 THEN 'MUITO SUSPEITO'
        WHEN COALESCE(nc.qtde_novas, 0) >= 5 OR COALESCE(ca.qtde_crescimento_acelerado, 0) >= 3 THEN 'SUSPEITO'
        WHEN COALESCE(nc.qtde_novas, 0) >= 2 OR COALESCE(ca.qtde_crescimento_acelerado, 0) >= 1 THEN 'ATENÇÃO'
        ELSE 'NORMAL'
    END AS classificacao_reforma

FROM teste.credito_contador_ranking r
LEFT JOIN novas_creditadoras nc ON r.cpf_cnpj_contador = nc.cpf_cnpj_contador
LEFT JOIN comportamento_regime cr ON r.cpf_cnpj_contador = cr.cpf_cnpj_contador
LEFT JOIN crescimento_acelerado ca ON r.cpf_cnpj_contador = ca.cpf_cnpj_contador
ORDER BY r.ranking_contador;

-- =============================================================================
-- 4. TABELA: credito_contador_top100
-- Top 100 contadores para visualização rápida no dashboard
-- =============================================================================

DROP TABLE IF EXISTS teste.credito_contador_top100;

CREATE TABLE teste.credito_contador_top100 AS
SELECT * FROM teste.credito_contador_ranking
WHERE ranking_contador <= 100
ORDER BY ranking_contador;

-- =============================================================================
-- 5. VIEW DE RESUMO
-- Estatísticas gerais dos contadores
-- =============================================================================

DROP TABLE IF EXISTS teste.credito_contador_resumo;

CREATE TABLE teste.credito_contador_resumo AS
SELECT
    COUNT(DISTINCT cpf_cnpj_contador) AS total_contadores,
    SUM(total_empresas_carteira) AS total_empresas,
    SUM(qtde_empresas_com_credito) AS total_empresas_com_credito,
    SUM(saldo_credor_total) AS saldo_credor_total,
    AVG(saldo_credor_total) AS saldo_medio_por_contador,

    -- Por classificação
    SUM(CASE WHEN classificacao_risco_contador = 'CRÍTICO' THEN 1 ELSE 0 END) AS contadores_criticos,
    SUM(CASE WHEN classificacao_risco_contador = 'ALTO' THEN 1 ELSE 0 END) AS contadores_alto,
    SUM(CASE WHEN classificacao_risco_contador = 'MÉDIO' THEN 1 ELSE 0 END) AS contadores_medio,
    SUM(CASE WHEN classificacao_risco_contador = 'BAIXO' THEN 1 ELSE 0 END) AS contadores_baixo,

    -- Por alerta
    SUM(CASE WHEN nivel_alerta_contador = 'INVESTIGAR' THEN 1 ELSE 0 END) AS contadores_investigar,
    SUM(CASE WHEN nivel_alerta_contador = 'ATENÇÃO ESPECIAL' THEN 1 ELSE 0 END) AS contadores_atencao,
    SUM(CASE WHEN nivel_alerta_contador = 'MONITORAR' THEN 1 ELSE 0 END) AS contadores_monitorar,

    -- Saldos por classificação
    SUM(CASE WHEN classificacao_risco_contador = 'CRÍTICO' THEN saldo_credor_total ELSE 0 END) AS saldo_contadores_criticos,
    SUM(CASE WHEN classificacao_risco_contador = 'ALTO' THEN saldo_credor_total ELSE 0 END) AS saldo_contadores_alto,

    -- Métricas de suspeitas
    SUM(qtde_empresas_suspeitas) AS total_empresas_suspeitas,
    SUM(total_indicios_fraude) AS total_indicios,
    AVG(score_total_contador) AS score_medio_contadores

FROM teste.credito_contador_ranking;

-- =============================================================================
-- FIM DO SCRIPT
-- =============================================================================
