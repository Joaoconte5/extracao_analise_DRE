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

### 1. Extração de Dados
Coleta dos relatórios anuais da AMBEV em formato PDF diretamente do portal da CVM. Desenvolvimento de script em Python com `pdfplumber` para extração, limpeza e padronização dos dados, tratando variações de formatação entre os arquivos de cada ano.

### 2. Modelagem e Estrutura Analítica
Construção do modelo dimensional no Power BI seguindo o padrão **Kimball Star Schema**, com três tabelas:
- `f_LancamentoDRE` — tabela fato com os valores financeiros
- `d_PlanoContas` — dimensão com a estrutura de contas da DRE
- `dCalendario` — dimensão de tempo para análises por período

### 3. Definição de Indicadores e Métricas (DAX)
Desenvolvimento de medidas para os principais KPIs financeiros:
- **Receita Bruta** e variação anual (AH%)
- **Margem Bruta** (AV% e evolução)
- **EBITDA** e percentual sobre receita
- **Resultado Líquido** e margem líquida
- Análise Horizontal (AH) e Análise Vertical (AV) para todas as linhas da DRE

### 4. Visualização e Dashboard
Construção de duas telas complementares:
- **Tela 1:** KPI cards com sparklines, demonstrativo completo da DRE com AV% e AH%
- **Tela 2:** Análise de margens por ano, waterfall de resultado, evolução de EBITDA e Resultado Líquido

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

A documentação técnica completa do projeto está disponível em [`docs/documentacao.pdf`](docs/documentacao.pdf), cobrindo decisões de modelagem, regras de negócio e dicionário de dados.

---

## Autor

**João Vitor Kuhn Conte**
Analytics & Business Intelligence | Performance | SQL · Power BI · Python

[![LinkedIn](https://img.shields.io/badge/LinkedIn-joão--conte-blue?style=flat&logo=linkedin)](https://www.linkedin.com/in/joão-conte)
