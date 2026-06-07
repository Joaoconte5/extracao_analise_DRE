"""
================================================================================
CARGA NO SQL SERVER — DRE AMBEV S.A.
================================================================================
Descrição:
    Evolução do pipeline de extração: além de gerar o CSV, este script
    carrega os dados diretamente na camada Raw do Data Warehouse DW_AMBEV
    no SQL Server, adicionando campos de rastreabilidade (dt_carga e
    arquivo_origem) antes da carga.

Arquitetura:
    PDF → Python → raw.lancamentos (SQL Server) → stg → dw → Power BI

Pré-requisito:
    - SQL Server 2022 instalado e acessível
    - Banco DW_AMBEV criado (script 01_criar_banco_schemas.sql)
    - ODBC Driver 17 for SQL Server instalado
    - pip install pdfplumber pandas sqlalchemy pyodbc

Configuração:
    Ajuste as variáveis na seção CONFIGURAÇÕES conforme seu ambiente.

Autor:
    João Vitor Kuhn Conte
    linkedin.com/in/joão-conte
================================================================================
"""

import urllib
import pdfplumber
import pandas as pd
import re
from sqlalchemy import create_engine


# ================================================================================
# CONFIGURAÇÕES
# ================================================================================

CAMINHO_PDF     = r"data/raw/DREAMBEV.pdf"   # Caminho relativo ao repositório
PAGINAS_ALVO    = [21, 22, 23]               # Índices das páginas (0-based)
ARQUIVO_SAIDA   = "data/dre_tratada.csv"     # CSV gerado como backup local

# Configurações do SQL Server — ajuste conforme seu ambiente
SQL_SERVER      = "JOAO3"                    # Nome do servidor (ou IP)
SQL_DATABASE    = "DW_AMBEV"
SQL_SCHEMA      = "raw"
SQL_TABELA      = "lancamentos"


# ================================================================================
# CONEXÃO COM SQL SERVER
# ================================================================================
# Autenticação Windows (Trusted_Connection) — sem usuário e senha.
# SQLAlchemy + pyodbc para compatibilidade com pandas to_sql().
# ================================================================================

def criar_engine():
    """Cria e retorna a engine de conexão com o SQL Server."""
    params = urllib.parse.quote_plus(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SQL_SERVER};"
        f"DATABASE={SQL_DATABASE};"
        f"Trusted_Connection=yes;"
    )
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
    print(f"✅ Conexão configurada → {SQL_SERVER}/{SQL_DATABASE}")
    return engine


# ================================================================================
# ETAPAS 1 A 3 — EXTRAÇÃO DO TEXTO DO PDF
# ================================================================================

print("📄 Iniciando extração do PDF...")
linhas_validas = []

with pdfplumber.open(CAMINHO_PDF) as pdf:
    for i in PAGINAS_ALVO:
        pagina = pdf.pages[i]
        texto = pagina.extract_text()

        for linha in texto.split("\n"):
            linha = linha.strip()
            if re.match(r"^\d+\.\d+", linha):
                linhas_validas.append(linha)

df = pd.DataFrame(linhas_validas, columns=["linha"])
print(f"   ✅ {len(df)} linhas extraídas do PDF.")


# ================================================================================
# ETAPAS 4 E 5 — PARSE ROBUSTO DAS LINHAS
# ================================================================================

def parse_linha(linha):
    """
    Recebe uma linha bruta do PDF e retorna uma Series com:
    [codigo, descricao, valor_2020, valor_2019, valor_2018]
    """
    if not linha or len(linha.strip()) == 0:
        return pd.Series([None, None, None, None, None])

    codigo_match = re.match(r"^(\d+(?:\.\d+)+)", linha)
    if not codigo_match:
        return pd.Series([None, None, None, None, None])

    codigo = codigo_match.group(1)
    resto = linha[len(codigo):].strip()

    # Remove percentuais antes de capturar valores monetários
    resto_sem_pct = re.sub(r"-?\d+[\d.,]*%", "", resto)

    # Extrai valores monetários
    valores = re.findall(r"-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|\d+", resto_sem_pct)
    valores = [v for v in valores if not re.match(r"^\d+\.\d+", v)]

    # Extrai descrição
    descricao_temp = re.sub(r"-?\d+[\d.,]*%", "", resto)
    descricao_temp = re.sub(r"-?\d[\d.,]*", "", descricao_temp)
    descricao = " ".join(descricao_temp.split()).strip()

    valor_2020 = valores[0] if len(valores) >= 1 else None
    valor_2019 = valores[1] if len(valores) >= 2 else None
    valor_2018 = valores[2] if len(valores) >= 3 else None

    return pd.Series([codigo, descricao, valor_2020, valor_2019, valor_2018])


print("🔍 Aplicando parse nas linhas...")
df_parsed = df["linha"].apply(parse_linha)
df_parsed.columns = ["codigo", "descricao", "valor_2020", "valor_2019", "valor_2018"]

df_parsed = df_parsed[df_parsed["codigo"].notna()]
df_parsed = df_parsed[df_parsed["codigo"].str.strip() != ""]
print(f"   ✅ {len(df_parsed)} contas identificadas.")


# ================================================================================
# ETAPA 6 — LIMPEZA DE VALORES
# ================================================================================

def tratar_valor(valor):
    """Converte string de valor monetário para float."""
    if pd.isna(valor):
        return None
    valor = str(valor).strip()
    if valor in ["", "-", "None"]:
        return None
    valor = valor.replace(" ", "")
    if re.search(r"\d,\d{2}$", valor):
        valor = valor.replace(".", "").replace(",", ".")
    else:
        valor = valor.replace(",", "")
    try:
        return float(valor)
    except:
        return None


print("🧹 Convertendo valores numéricos...")
df_parsed["valor_2020"] = df_parsed["valor_2020"].apply(tratar_valor)
df_parsed["valor_2019"] = df_parsed["valor_2019"].apply(tratar_valor)
df_parsed["valor_2018"] = df_parsed["valor_2018"].apply(tratar_valor)


# ================================================================================
# HIERARQUIA CONTÁBIL
# ================================================================================

df_parsed["codigo"] = df_parsed["codigo"].astype(str)
df_parsed["nivel_1"] = df_parsed["codigo"].str.split(".").str[0]
df_parsed["nivel_2"] = df_parsed["codigo"].str.split(".").str[1]
df_parsed["nivel_3"] = df_parsed["codigo"].str.split(".").str[2]


# ================================================================================
# ETAPA 7 — FORMATO ANALÍTICO (MELT)
# ================================================================================

print("🔄 Aplicando melt para formato analítico...")
df_melt = df_parsed.melt(
    id_vars=["codigo", "descricao", "nivel_1", "nivel_2", "nivel_3"],
    value_vars=["valor_2020", "valor_2019", "valor_2018"],
    var_name="ano",
    value_name="valor"
)
df_melt["ano"] = df_melt["ano"].str.extract(r"(\d+)")


# ================================================================================
# ETAPA 8A — EXPORTAR CSV (backup local)
# ================================================================================

df_melt.to_csv(ARQUIVO_SAIDA, index=False, encoding="utf-8-sig")
print(f"✅ CSV exportado → {ARQUIVO_SAIDA}")


# ================================================================================
# ETAPA 8B — CARGA NO SQL SERVER (camada Raw)
# ================================================================================
# Dois campos de rastreabilidade adicionados antes da carga:
#   dt_carga:       timestamp do momento exato da ingestão
#   arquivo_origem: nome do PDF de origem — rastreabilidade de linhagem
#
# if_exists='replace': substitui a tabela a cada execução (idempotência).
# A tabela Raw é gerenciada pelo Python — estrutura recriada automaticamente.
# ================================================================================

print(f"\n🗄️  Iniciando carga no SQL Server → {SQL_DATABASE}.{SQL_SCHEMA}.{SQL_TABELA}...")

# Adiciona campos de rastreabilidade
df_melt["dt_carga"]       = pd.Timestamp.now()
df_melt["arquivo_origem"] = "DREAMBEV.pdf"

engine = criar_engine()

df_melt.to_sql(
    name=SQL_TABELA,
    schema=SQL_SCHEMA,
    con=engine,
    if_exists="replace",   # substitui a cada execução
    index=False
)

print(f"✅ {len(df_melt)} registros carregados em {SQL_SCHEMA}.{SQL_TABELA}")
print(f"\n🏁 Pipeline concluído com sucesso!")
print(f"   Próximo passo: executar 03_staging_transformacao.sql no SQL Server")
