"""
================================================================================
EXTRAÇÃO E TRATAMENTO DE DADOS — DRE AMBEV S.A.
================================================================================
Descrição:
    Script de extração automatizada dos dados da Demonstração do Resultado
    do Exercício (DRE) da AMBEV S.A. a partir de relatórios anuais em PDF,
    com tratamento, estruturação e exportação para CSV analítico.

Fonte dos dados:
    Relatórios anuais da AMBEV S.A. disponíveis publicamente na CVM
    (Comissão de Valores Mobiliários) — www.cvm.gov.br

Período analisado:
    2018, 2019 e 2020
    
Autor:
    João Vitor Kuhn Conte
    linkedin.com/in/joão-conte
================================================================================
"""

import pdfplumber
import pandas as pd
import re


# ================================================================================
# CONFIGURAÇÕES
# ================================================================================

CAMINHO_PDF = r"data/raw/DREAMBEV.pdf"   # Caminho relativo ao repositório
PAGINAS_ALVO = [21, 22, 23]              # Índices das páginas (0-based → páginas 22, 23 e 24)
ARQUIVO_SAIDA = "data/dre_tratada.csv"


# ================================================================================
# ETAPAS 1 A 3 — EXTRAÇÃO DO TEXTO DO PDF
# ================================================================================
# Abre o PDF com pdfplumber, navega até as páginas que contêm a DRE e extrai
# apenas as linhas que começam com um código contábil (ex: 3.01, 3.04.01).
# A biblioteca pdfplumber preserva o layout textual, diferente de outras
# bibliotecas que retornam o texto em fluxo linear ignorando colunas.
# ================================================================================

print("Iniciando extração do PDF...")
linhas_validas = []

with pdfplumber.open(CAMINHO_PDF) as pdf:
    for i in PAGINAS_ALVO:
        pagina = pdf.pages[i]
        texto = pagina.extract_text()

        for linha in texto.split("\n"):
            linha = linha.strip()
            # Mantém apenas linhas com padrão de código contábil no início
            # Exemplos válidos: "3.01 Receita...", "3.04.01 Despesas..."
            if re.match(r"^\d+\.\d+", linha):
                linhas_validas.append(linha)

df = pd.DataFrame(linhas_validas, columns=["linha"])
print(f"  {len(df)} linhas extraídas do PDF.")


# ================================================================================
# ETAPAS 4 E 5 — PARSE ROBUSTO DAS LINHAS
# ================================================================================
# Cada linha extraída tem o formato:
#   "3.04.01 Despesas com Vendas -12.647.536 -10.876.234 -9.234.112 -41,7% ..."
#
# A função abaixo separa:
#   - Código contábil (ex: 3.04.01)
#   - Descrição da conta (ex: Despesas com Vendas)
#   - Valores monetários por ano (2020, 2019, 2018)
#
# Desafios tratados:
#   1. Código extraído ANTES de qualquer limpeza para evitar perda
#   2. Percentuais (ex: -41,7%) removidos antes de capturar valores monetários
#   3. Tokens que parecem código contábil filtrados da lista de valores
#   4. Atribuição posicional segura: valores[0]=2020, [1]=2019, [2]=2018
# ================================================================================

def parse_linha(linha):
    """
    Recebe uma linha bruta do PDF e retorna uma Series com:
    [codigo, descricao, valor_2020, valor_2019, valor_2018]
    Retorna None em todos os campos se a linha não for válida.
    """
    if not linha or len(linha.strip()) == 0:
        return pd.Series([None, None, None, None, None])

    # Extrai código contábil antes de qualquer transformação
    codigo_match = re.match(r"^(\d+(?:\.\d+)+)", linha)
    if not codigo_match:
        return pd.Series([None, None, None, None, None])

    codigo = codigo_match.group(1)
    resto = linha[len(codigo):].strip()

    # Remove percentuais antes de capturar valores monetários
    # Exemplos: "100.00%", "-27.77%", "51.05%" — interferem na lista de valores
    resto_sem_pct = re.sub(r"-?\d+[\d.,]*%", "", resto)

    # Extrai valores monetários (inteiros ou decimais, com ou sem separadores)
    valores = re.findall(r"-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|\d+", resto_sem_pct)

    # Remove tokens que parecem códigos contábeis (ex: "3.04.01")
    valores = [v for v in valores if not re.match(r"^\d+\.\d+", v)]

    # Extrai a descrição: remove percentuais e números, normaliza espaços
    descricao_temp = re.sub(r"-?\d+[\d.,]*%", "", resto)
    descricao_temp = re.sub(r"-?\d[\d.,]*", "", descricao_temp)
    descricao = " ".join(descricao_temp.split()).strip()

    # Atribuição posicional: PDF organiza da esquerda para direita: 2020, 2019, 2018
    valor_2020 = valores[0] if len(valores) >= 1 else None
    valor_2019 = valores[1] if len(valores) >= 2 else None
    valor_2018 = valores[2] if len(valores) >= 3 else None

    return pd.Series([codigo, descricao, valor_2020, valor_2019, valor_2018])


print("Aplicando parse nas linhas...")
df_parsed = df["linha"].apply(parse_linha)
df_parsed.columns = ["codigo", "descricao", "valor_2020", "valor_2019", "valor_2018"]


# ================================================================================
# ETAPA — REMOÇÃO DE LINHAS INVÁLIDAS
# ================================================================================

df_parsed = df_parsed[df_parsed["codigo"].notna()]
df_parsed = df_parsed[df_parsed["codigo"].str.strip() != ""]
print(f"  {len(df_parsed)} contas contábeis identificadas após limpeza.")


# ================================================================================
# ETAPA 6 — LIMPEZA E CONVERSÃO DE VALORES NUMÉRICOS
# ================================================================================
# Os valores extraídos chegam como strings com formatação variável:
#   - Padrão brasileiro: "12.647.536" (ponto como milhar, vírgula como decimal)
#   - Padrão americano: "12,647,536" (vírgula como milhar)
#   - Valores nulos representados por "-" ou string vazia
#
# A função detecta o padrão e converte para float de forma segura.
# ================================================================================

def tratar_valor(valor):
    """
    Converte string de valor monetário para float.
    Trata formatos brasileiro e americano, além de nulos e strings inválidas.
    Retorna None para valores não conversíveis.
    """
    if pd.isna(valor):
        return None
    valor = str(valor).strip()
    if valor in ["", "-", "None"]:
        return None
    valor = valor.replace(" ", "")

    # Detecta padrão brasileiro: vírgula como separador decimal (ex: "1.234,56")
    if re.search(r"\d,\d{2}$", valor):
        valor = valor.replace(".", "").replace(",", ".")
    else:
        # Padrão americano ou número inteiro: remove vírgulas de milhar
        valor = valor.replace(",", "")

    try:
        return float(valor)
    except:
        return None


print("Convertendo valores numéricos...")
df_parsed["valor_2020"] = df_parsed["valor_2020"].apply(tratar_valor)
df_parsed["valor_2019"] = df_parsed["valor_2019"].apply(tratar_valor)
df_parsed["valor_2018"] = df_parsed["valor_2018"].apply(tratar_valor)


# ================================================================================
# ETAPA 5 — HIERARQUIA CONTÁBIL
# ================================================================================
# Extrai os níveis hierárquicos do código contábil para permitir
# navegação e agrupamento no Power BI (N1, N2, N3).
# Exemplo: código "3.04.01" → N1="3", N2="04", N3="01"
# ================================================================================

df_parsed["codigo"] = df_parsed["codigo"].astype(str)
df_parsed["nivel_1"] = df_parsed["codigo"].str.split(".").str[0]
df_parsed["nivel_2"] = df_parsed["codigo"].str.split(".").str[1]
df_parsed["nivel_3"] = df_parsed["codigo"].str.split(".").str[2]


# ================================================================================
# DIAGNÓSTICO — VALIDAÇÃO INTERMEDIÁRIA
# ================================================================================
# Bloco de verificação para garantir que a extração está correta antes
# de aplicar o melt. Pode ser removido após validação do pipeline.
# ================================================================================

print("\n=== AMOSTRA RAW (antes do melt) ===")
print(df_parsed[["codigo", "descricao", "valor_2020", "valor_2019", "valor_2018"]].head(20).to_string())

linhas_sem_valor = df_parsed[
    df_parsed[["valor_2020", "valor_2019", "valor_2018"]].isna().all(axis=1)
]
if not linhas_sem_valor.empty:
    print(f"\n{len(linhas_sem_valor)} linhas sem nenhum valor — verifique:")
    print(linhas_sem_valor[["codigo", "descricao"]].to_string())
else:
    print("\n Nenhuma linha sem valor encontrada.")


# ================================================================================
# ETAPA 7 — FORMATO ANALÍTICO (MELT / PIVOT INVERSO)
# ================================================================================
# O CSV intermediário tem uma linha por conta com três colunas de valor
# (valor_2020, valor_2019, valor_2018)  formato wide, difícil de filtrar.
#
# A função melt() transforma para o formato long (vertical):
#   Uma linha por conta por ano — padrão ideal para Power BI e ferramentas de BI.
#
# Antes:  codigo | descricao | valor_2020 | valor_2019 | valor_2018
# Depois: codigo | descricao | ano        | valor
# ================================================================================

print("\n Aplicando melt para formato analítico...")
df_melt = df_parsed.melt(
    id_vars=["codigo", "descricao", "nivel_1", "nivel_2", "nivel_3"],
    value_vars=["valor_2020", "valor_2019", "valor_2018"],
    var_name="ano",
    value_name="valor"
)

# Extrai apenas o número do ano (remove prefixo "valor_")
df_melt["ano"] = df_melt["ano"].str.extract(r"(\d+)")


# ================================================================================
# ETAPA 8 — VALIDAÇÃO FINAL E EXPORTAÇÃO
# ================================================================================
# Exporta com encoding utf-8-sig: adiciona um BOM (Byte Order Mark) invisível
# no início do arquivo que instrui o Excel a interpretar como UTF-8.
# Sem isso, caracteres especiais do português (ã, ç, é) aparecem corrompidos.
# ================================================================================

print("\n Preview final:")
print(df_melt.head(15).to_string())
print("\nTipos de dados:")
print(df_melt.dtypes)
print(f"\nTotal de registros: {len(df_melt)}")

df_melt.to_csv(ARQUIVO_SAIDA, index=False, encoding="utf-8-sig")
print(f"\n CSV exportado com sucesso → {ARQUIVO_SAIDA}")
