-- ================================================================================
-- 01_criar_banco_schemas.sql
-- ================================================================================
-- Descrição:
--   Criação do banco de dados DW_AMBEV e dos três schemas que estruturam
--   a arquitetura de dados do projeto:
--
--   raw  → cópia fiel da origem, nunca alterada
--   stg  → dado tratado, validado e filtrado
--   dw   → modelo estrela pronto para consumo no Power BI
--
-- Projeto: Pipeline DW AMBEV S.A. — Portfólio de Análise Financeira e Dados
-- Autor:   João Vitor Kuhn Conte | linkedin.com/in/joão-conte
-- ================================================================================

-- ----------------------------------------
-- 1. CRIAÇÃO DO BANCO DE DADOS
-- ----------------------------------------
-- Banco central do projeto. Todos os schemas,
-- tabelas e dados do pipeline residem aqui.
-- ----------------------------------------

CREATE DATABASE DW_AMBEV;
GO

USE DW_AMBEV;
GO

-- ----------------------------------------
-- 2. CRIAÇÃO DOS SCHEMAS
-- ----------------------------------------
-- Cada schema tem uma responsabilidade única.
-- O dado percorre sempre a sequência:
-- raw → stg → dw. Nunca pula etapas.
-- ----------------------------------------

CREATE SCHEMA raw;   -- dado bruto, preservado como chegou da origem
CREATE SCHEMA stg;   -- dado limpo, tipado e filtrado por escopo
CREATE SCHEMA dw;    -- modelo dimensional, pronto para BI
GO

-- ----------------------------------------
-- VALIDAÇÃO
-- ----------------------------------------
SELECT name AS schema_name
FROM sys.schemas
WHERE name IN ('raw', 'stg', 'dw')
ORDER BY name;
-- Esperado: 3 linhas (dw, raw, stg)
