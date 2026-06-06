## Análise DRE AMBEV
Projeto de análise financeira completo, cobrindo o fluxo de ponta a ponta: da extração de dados em PDFs públicos até a construção de um dashboard gerencial interativo em Power BI.

---

## Objetivo

Transformar os dados da Demonstração do Resultado do Exercício (DRE) da AMBEV S.A., disponíveis publicamente na CVM, em um painel analítico que permita acompanhar a evolução financeira da companhia entre 2018 e 2020, com foco em margens, EBITDA e resultado líquido.

---

## Dashboard

### Tela 1 — Visão Gerencial e Demonstrativo
**Tela 1 — Visão Executiva:** 4 KPI cards com sparklines cobrindo a cadeia completa de geração de valor (Receita → Margem Bruta → EBITDA → Resultado Líquido), seguidos do demonstrativo completo da DRE com colunas de AV% e AH% para os três anos.
![Tela 1 - Análise Gerencial DRE](images/dashboard_tela1.png)

### Tela 2 — Análise de Margens e Evolução de Resultado
**Tela 2 — Diagnóstico:** Análise de margens por ano, waterfall de formação do resultado, evolução de EBITDA% e Lucro Líquido%, breakdown de despesas operacionais por subcategoria. Filtro de ano interativo.
![Tela 2 - Análise de Margens](images/dashboard_tela2.png)

---

## Estrutura do Projeto

```
analise-dre-ambev/
│
├── data/
│   └── raw/                    PDFs originais extraídos da CVM
│
├── notebooks/
│   └── extracao_dre.ipynb      Extração e tratamento dos dados com Python
│
├── powerbi/
│   └── dashboard_dre.pbix      Arquivo Power BI com modelo e dashboard
│
├── docs/
│   └── documentacao.pdf        Documentação técnica completa do projeto
│
├── images/
│   ├── dashboard_tela1.png
│   └── dashboard_tela2.png
│
└── README.md
```

---

## Tecnologias Utilizadas

| Ferramenta | Finalidade |
|---|---|
| Python | Extração e tratamento dos dados dos PDFs |
| pdfplumber | Leitura e parsing das páginas dos relatórios |
| pandas | Manipulação e estruturação dos dados |
| Power BI | Modelagem dimensional e visualização |
| DAX | Criação de métricas e KPIs analíticos |
| Power Query | Transformação e carga dos dados no modelo |

---

##  Etapas do Projeto

### Módulo 1 — Extração e Tratamento de Dados (Python)

Coleta dos relatórios anuais da AMBEV em PDF diretamente do portal da CVM. Desenvolvimento de script Python com `pdfplumber` para extração, limpeza e estruturação dos dados — tratando variações de formatação entre arquivos de diferentes anos.

O pipeline executa 8 etapas sequenciais:

| Etapa | O que acontece | Ferramenta |
|---|---|---|
| 1. Abertura do PDF | Arquivo carregado em memória | pdfplumber |
| 2. Seleção de páginas | Apenas páginas 22–24 processadas | pdfplumber |
| 3. Extração de texto | Texto bruto extraído linha a linha | pdfplumber |
| 4. Filtragem de linhas | Apenas linhas com código contábil mantidas | re (regex) |
| 5. Parse das linhas | Código, descrição e valores separados | re (regex) |
| 6. Limpeza de valores | Formato numérico brasileiro convertido para float | pandas |
| 7. Formato analítico | Tabela transposta para uma linha por conta/ano | pandas (melt) |
| 8. Exportação | CSV gerado com encoding utf-8-sig para Excel | pandas |

### Módulo 2 — Modelagem Dimensional (Power BI / Power Query)

Construção do modelo seguindo o padrão **Kimball Star Schema** com três tabelas:

**`d_PlanoContas`** — Dimensão com estrutura hierárquica das contas (N1, N2, N3), classificação sintética/analítica e código contábil. Permite navegação por nível de detalhe e evita dupla contagem ao filtrar apenas contas analíticas na tabela fato.

**`f_LancamentoDRE`** — Tabela fato com os valores financeiros por conta e ano, originada diretamente do CSV gerado pelo script Python. Contém apenas contas analíticas (folhas da hierarquia) para garantir precisão nos cálculos.

**`dCalendario`** — Tabela de tempo calculada em DAX com 6 colunas (Date, Ano, Mês, Mês Número, AnoMes, Trimestre), habilitando inteligência de tempo nativa do Power BI.

> **Decisão crítica de modelagem:** contas sintéticas são totalizadores — incluí-las na tabela fato junto de suas filhas analíticas geraria dupla contagem. Exemplo: somar a conta 3.04.01 (Despesas com Vendas: -R$ 12,6 Mi) com suas filhas resultaria em -R$ 25,3 Mi — quase o dobro do valor real.

### Módulo 3 — Definição de Indicadores e Métricas (DAX)

| Medida | Fórmula DAX | Finalidade |
|---|---|---|
| Receita Bruta | `CALCULATE(SUM(f_LancamentoDRE[valor]), d_Planocontas[Cód N1] = "3.01")` | Base de todos os percentuais |
| % Margem Bruta | `DIVIDE([Resultado Bruto], [Receita Bruta])` | Eficiência após CPV |
| % EBITDA | `DIVIDE([Ebitda], [Receita Bruta])` | Eficiência operacional |
| % Lucro | `DIVIDE([Resultado Liquido], [Receita Bruta])` | Margem líquida final |
| AV | `DIVIDE([DRE FINAL], CALCULATE([DRE FINAL], ALL(d_Planocontas), d_Planocontas[Cód N1] = "3.01"))` | Peso de cada linha sobre a receita |
| AH | `DIVIDE([DRE FINAL] - [DRE FINAL AA], ABS([DRE FINAL AA]))` | Variação vs. ano anterior |
| DRE FINAL AA | `CALCULATE([DRE FINAL], SAMEPERIODLASTYEAR(Calendario[Date]))` | Comparativo temporal |

### Módulo 4 — Visualização e Dashboard

**Tela 1 — Visão Executiva:** 4 KPI cards com sparklines cobrindo a cadeia completa de geração de valor (Receita → Margem Bruta → EBITDA → Resultado Líquido), seguidos do demonstrativo completo da DRE com colunas de AV% e AH% para os três anos.

**Tela 2 — Diagnóstico:** Análise de margens por ano, waterfall de formação do resultado, evolução de EBITDA% e Lucro Líquido%, breakdown de despesas operacionais por subcategoria. Filtro de ano interativo.

### 5. Análise e Insights
**1. Crescimento de receita com compressão de margens**
A receita cresceu 40% entre 2018 e 2020, mas o EBITDA recuou 7,6 pontos percentuais no mesmo período — evidenciando que os custos cresceram proporcionalmente mais rápido que a receita.

**2. CPV como principal driver de compressão**
O Custo dos Bens Vendidos passou de 41,7% para 48,9% da receita — alta de 7,2 pp em três anos. Com variação AH de -31,8% em 2020 contra crescimento de receita de +24,8%, o CPV é o maior responsável pela queda da Margem Bruta.

**3. Despesas Logísticas crescendo acima da receita**
As Despesas Logísticas cresceram ~42% enquanto a receita cresceu 25% — um gap de eficiência de 17 pp que representa aproximadamente R$ 6 Mi de despesa adicional acima do proporcional ao crescimento.

**4. Alívio tributário em 2020 mascarou deterioração operacional**
O Imposto de Renda apresentou AH de +63,9% em 2020 (pagamento proporcionalmente muito menor). Sem esse efeito, o Resultado Líquido teria recuado apesar do crescimento de receita.

**5. Aceleração da deterioração**
A queda do EBITDA foi de 3,6 pp entre 2018–2019 e de 4,0 pp entre 2019–2020 — sinal de que a deterioração está acelerando, não se estabilizando.

---

## Principais KPIs Analisados

| Indicador | 2018 | 2019 | 2020 |
|---|---|---|---|
| Receita Bruta | R$ 52,01 Mi | R$ 58,38 Mi | R$ 72,85 Mi |
| Margem Bruta | 58,3% | 53,6% | 51,1% |
| EBITDA % | 30,9% | 27,3% | 23,3% |
| Resultado Líquido % | 23,4% | 20,1% | 18,0% |

---

## Aprendizados
- Tratamento de PDFs com estruturas variáveis entre anos — parsing robusto com regex e validação de padrões
- Decisão de modelagem dimensional: separação de contas sintéticas e analíticas para evitar dupla contagem
- Construção de AV e AH em DAX com controle de contexto de filtro por período
- Uso de `SAMEPERIODLASTYEAR` para comparativos temporais corretos
- Exportação com `utf-8-sig` para compatibilidade com Excel em português
- Organização de modelo star schema para escalabilidade e performance no Power BI

---

## Documentação

A documentação técnica completa do projeto está disponível em [`docs/Doc_DRE_PBI.pdf`](docs/Doc_DRE_PBI.pdf), cobrindo decisões de modelagem, regras de negócio e dicionário de dados.

---

## Autor

**João Vitor Kuhn Conte**
Analytics & Business Intelligence | Performance | SQL · Power BI · Python

[![LinkedIn](https://img.shields.io/badge/LinkedIn-joão--conte-blue?style=flat&logo=linkedin)](https://www.linkedin.com/in/joão-conte)
