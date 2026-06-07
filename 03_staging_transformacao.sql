-- ================================================================================
-- 03_staging_transformacao.sql
-- ================================================================================
-- Descrição:
--   Transformação dos dados da camada Raw para Staging, e carga final
--   nas tabelas dimensão e fato da camada DW.
--
--   Etapa 1: Raw → Staging (filtragem, tipagem, limpeza)
--   Etapa 2: Staging → dw.d_planocontas (dimensão contábil)
--   Etapa 3: Staging → dw.f_lancamentos (tabela fato via JOIN com dimensão)
--
-- Pré-requisito:
--   Scripts 01 e 02 executados. Tabela raw.lancamentos populada pelo Python.
--
-- Projeto: Pipeline DW AMBEV S.A. — Portfólio de Análise Financeira e Dados
-- Autor:   João Vitor Kuhn Conte | linkedin.com/in/joão-conte
-- ================================================================================

USE DW_AMBEV;
GO

-- ================================================================================
-- ETAPA 1 — RAW → STAGING
-- ================================================================================
-- Três transformações aplicadas:
--
--   1. Filtragem por escopo: apenas contas da DRE (grupo 3.xx)
--      O PDF contém outras seções (Balanço Patrimonial, Notas Explicativas).
--      O escopo do projeto é exclusivamente a DRE.
--
--   2. Conversão de tipos: texto → tipos corretos para o DW
--      A Raw armazena tudo como texto (pandas to_sql() sem tipagem).
--      O DW precisa de tipos corretos para cálculos e relacionamentos.
--
--   3. TRY_CAST no valor: conversão resiliente a erros
--      TRY_CAST retorna NULL em vez de erro — linhas com valor inválido
--      são preservadas sem travar a carga.
-- ================================================================================

-- Criação da tabela Staging (executar apenas na primeira vez)
CREATE TABLE stg.lancamentos (
    codigo     VARCHAR(20),
    descricao  VARCHAR(200),
    nivel_1    VARCHAR(10),
    nivel_2    VARCHAR(10),
    nivel_3    VARCHAR(10),
    ano        SMALLINT,
    valor      DECIMAL(18,2),
    dt_carga   DATETIME
);
GO

-- Limpeza antes de reprocessar (idempotência)
TRUNCATE TABLE stg.lancamentos;
GO

-- Transformação e carga
INSERT INTO stg.lancamentos
SELECT
    TRIM(codigo)                           AS codigo,
    TRIM(descricao)                        AS descricao,
    TRIM(nivel_1)                          AS nivel_1,
    TRIM(nivel_2)                          AS nivel_2,
    TRIM(nivel_3)                          AS nivel_3,
    CAST(ano AS SMALLINT)                  AS ano,
    TRY_CAST(valor AS DECIMAL(18,2))       AS valor,   -- NULL se inválido
    dt_carga
FROM raw.lancamentos
WHERE codigo LIKE '3.%'                               -- apenas contas da DRE
  AND TRY_CAST(ano AS SMALLINT) IS NOT NULL           -- ano válido
  AND codigo IS NOT NULL;                             -- código não nulo
GO

-- Validação Staging
SELECT
    COUNT(*)                              AS total_registros,
    COUNT(DISTINCT codigo)                AS contas_unicas,
    COUNT(DISTINCT ano)                   AS anos,
    SUM(CASE WHEN valor IS NULL THEN 1 ELSE 0 END) AS valores_nulos
FROM stg.lancamentos;
-- Esperado: 108 registros | 36 contas | 3 anos | 0 valores nulos
GO

-- ================================================================================
-- ETAPA 2 — STAGING → dw.d_planocontas
-- ================================================================================
-- Carrega as contas únicas da DRE na dimensão contábil.
-- A surrogate key (sk_conta) é gerada automaticamente pelo IDENTITY.
-- As colunas de hierarquia descritiva (n1_desc, n2_desc, n3_desc) são
-- preenchidas na etapa seguinte — ver script 04_hierarquia_planocontas.sql
-- ================================================================================

TRUNCATE TABLE dw.d_planocontas;
GO

INSERT INTO dw.d_planocontas (codigo, descricao, nivel_1, nivel_2, nivel_3)
SELECT DISTINCT
    codigo,
    descricao,
    nivel_1,
    nivel_2,
    nivel_3
FROM stg.lancamentos
ORDER BY codigo;
GO

-- Validação dimensão
SELECT COUNT(*) AS total_contas FROM dw.d_planocontas;
-- Esperado: 36 contas
GO

-- ================================================================================
-- ETAPA 3 — STAGING → dw.f_lancamentos
-- ================================================================================
-- Carrega os lançamentos financeiros na tabela fato.
-- O JOIN com dw.d_planocontas resolve o codigo → sk_conta (surrogate key).
-- O JOIN com dw.d_data resolve o ano → sk_data.
-- Foreign keys garantem integridade: apenas registros com dimensões válidas
-- são inseridos.
-- ================================================================================

TRUNCATE TABLE dw.f_lancamentos;
GO

INSERT INTO dw.f_lancamentos (sk_conta, sk_data, codigo, valor)
SELECT
    p.sk_conta,
    d.sk_data,
    s.codigo,
    s.valor
FROM stg.lancamentos s
JOIN dw.d_planocontas p ON p.codigo = s.codigo
JOIN dw.d_data        d ON d.sk_data = s.ano;
GO

-- ================================================================================
-- VALIDAÇÃO FINAL DO MODELO
-- ================================================================================

SELECT 'd_planocontas' AS tabela, COUNT(*) AS linhas FROM dw.d_planocontas
UNION ALL
SELECT 'd_data',                   COUNT(*) FROM dw.d_data
UNION ALL
SELECT 'f_lancamentos',            COUNT(*) FROM dw.f_lancamentos;
-- Esperado: d_planocontas=36 | d_data=3 | f_lancamentos=108
GO

-- Amostra do modelo integrado
SELECT TOP 10
    f.sk_lancamento,
    p.codigo,
    p.descricao,
    d.ano,
    f.valor
FROM dw.f_lancamentos f
JOIN dw.d_planocontas p ON p.sk_conta = f.sk_conta
JOIN dw.d_data        d ON d.sk_data  = f.sk_data
ORDER BY d.ano, p.codigo;
GO
