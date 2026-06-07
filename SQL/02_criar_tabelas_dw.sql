-- ================================================================================
-- 02_criar_tabelas_dw.sql
-- ================================================================================
-- Descrição:
--   Criação das tabelas do modelo estrela (Star Schema) na camada DW:
--
--   dw.d_planocontas  → dimensão contábil com hierarquia N1/N2/N3
--   dw.d_data         → dimensão temporal (anos 2018, 2019, 2020)
--   dw.f_lancamentos  → tabela fato com os valores financeiros da DRE
--
-- Também cria a tabela de entrada da camada Raw:
--   raw.lancamentos   → recebe os dados brutos carregados pelo Python
--
-- Projeto: Pipeline DW AMBEV S.A. — Portfólio de Análise Financeira e Dados
-- Autor:   João Vitor Kuhn Conte | linkedin.com/in/joão-conte
-- ================================================================================

USE DW_AMBEV;
GO

-- ================================================================================
-- CAMADA RAW — Tabela de entrada do pipeline
-- ================================================================================
-- Recebe todos os dados extraídos do PDF sem nenhum filtro ou transformação.
-- Inclui campos de rastreabilidade (dt_carga, arquivo_origem) adicionados
-- pelo script Python antes da carga.
-- Esta tabela é gerenciada pelo Python via to_sql() com if_exists='replace'.
-- ================================================================================

-- Nota: esta tabela é criada automaticamente pelo pandas to_sql().
-- O script abaixo serve apenas como referência da estrutura esperada.

/*
CREATE TABLE raw.lancamentos (
    codigo          VARCHAR(20),
    descricao       VARCHAR(200),
    nivel_1         VARCHAR(10),
    nivel_2         VARCHAR(10),
    nivel_3         VARCHAR(10),
    ano             VARCHAR(10),
    valor           VARCHAR(50),    -- texto, sem conversão — Raw preserva tudo
    dt_carga        DATETIME,
    arquivo_origem  VARCHAR(100)
);
*/

-- ================================================================================
-- CAMADA DW — Dimensão: dw.d_planocontas
-- ================================================================================
-- Dimensão contábil do modelo estrela.
-- Descreve O QUE SÃO as contas da DRE — enquanto a fato registra o que aconteceu.
--
-- Decisões de modelagem:
--   sk_conta: surrogate key gerada pelo banco (IDENTITY) — não usa o código
--             contábil como PK para proteger o modelo contra mudanças futuras
--             na codificação das contas.
--   n1_desc, n2_desc, n3_desc: hierarquia descritiva preenchida via T-SQL
--             (Self JOIN + CHARINDEX) — ver script 04_hierarquia_planocontas.sql
-- ================================================================================

CREATE TABLE dw.d_planocontas (
    sk_conta   INT IDENTITY(1,1) PRIMARY KEY,  -- surrogate key
    codigo     VARCHAR(20)  NOT NULL,           -- código contábil (ex: 3.04.01)
    descricao  VARCHAR(200),                    -- nome da conta
    nivel_1    VARCHAR(10),                     -- primeiro segmento do código
    nivel_2    VARCHAR(10),                     -- segundo segmento
    nivel_3    VARCHAR(10),                     -- terceiro segmento
    n1_desc    VARCHAR(200),                    -- descrição do grupo nível 1
    n2_desc    VARCHAR(200),                    -- descrição do grupo nível 2
    n3_desc    VARCHAR(200),                    -- descrição do grupo nível 3
    dt_carga   DATETIME DEFAULT GETDATE()       -- timestamp de rastreabilidade
);
GO

-- ================================================================================
-- CAMADA DW — Dimensão: dw.d_data
-- ================================================================================
-- Dimensão temporal com os três anos do período analisado.
-- Granularidade anual — reflete exatamente o escopo do projeto sem complexidade
-- desnecessária. sk_data usa o próprio ano como chave (2018, 2019, 2020).
-- ================================================================================

CREATE TABLE dw.d_data (
    sk_data  INT  PRIMARY KEY,   -- chave = ano (2018, 2019, 2020)
    ano      SMALLINT,
    dt_ref   DATE                -- data de referência: 01/01/AAAA
);
GO

-- Carga direta — 3 registros fixos do período analisado
INSERT INTO dw.d_data (sk_data, ano, dt_ref) VALUES
    (2018, 2018, '2018-01-01'),
    (2019, 2019, '2019-01-01'),
    (2020, 2020, '2020-01-01');
GO

-- ================================================================================
-- CAMADA DW — Tabela Fato: dw.f_lancamentos
-- ================================================================================
-- Registra OS VALORES financeiros — uma linha por combinação de conta e ano.
-- Foreign keys garantem integridade referencial: não é possível inserir um
-- lançamento com conta ou data inexistente nas dimensões.
-- ================================================================================

CREATE TABLE dw.f_lancamentos (
    sk_lancamento  INT IDENTITY(1,1) PRIMARY KEY,
    sk_conta       INT REFERENCES dw.d_planocontas(sk_conta),  -- FK → dimensão contábil
    sk_data        INT REFERENCES dw.d_data(sk_data),          -- FK → dimensão temporal
    codigo         VARCHAR(20),                                  -- código contábil (referência)
    valor          DECIMAL(18,2),                               -- valor financeiro em R$ mil
    dt_carga       DATETIME DEFAULT GETDATE()
);
GO

-- ================================================================================
-- VALIDAÇÃO — Estrutura das tabelas criadas
-- ================================================================================

SELECT
    t.TABLE_SCHEMA AS schema_name,
    t.TABLE_NAME   AS table_name,
    COUNT(c.COLUMN_NAME) AS num_colunas
FROM INFORMATION_SCHEMA.TABLES t
JOIN INFORMATION_SCHEMA.COLUMNS c
    ON t.TABLE_NAME = c.TABLE_NAME
    AND t.TABLE_SCHEMA = c.TABLE_SCHEMA
WHERE t.TABLE_SCHEMA IN ('raw', 'dw')
GROUP BY t.TABLE_SCHEMA, t.TABLE_NAME
ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME;
-- Esperado: dw.d_data (3 col), dw.d_planocontas (10 col), dw.f_lancamentos (6 col)
