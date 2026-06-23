# Financial Dashboard

Dashboard interativo para consolidação e análise de extratos bancários brasileiros, com categorização automática de transações e visualizações de fluxo de caixa.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.45+-FF4B4B?logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.0+-3F4F75?logo=plotly&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## Problema

Quem usa mais de um banco no Brasil sabe: cada instituição exporta o extrato CSV em um formato diferente. Nomes de colunas variam ("Valor", "Vlr", "valor (r$)"), encodings mudam (UTF-8, CP1252, Latin-1), separadores alternam entre vírgula e ponto-e-vírgula, e valores monetários aparecem no formato brasileiro (1.234,56).

Consolidar esses arquivos manualmente em uma planilha para entender o fluxo de caixa é um processo repetitivo que consome tempo toda vez que precisa ser feito.

## Solução

Um dashboard web que recebe múltiplos CSVs via upload, detecta automaticamente o formato de cada arquivo e gera análises visuais prontas para uso.

### O que o pipeline faz

- **Detecção automática de formato:** testa 4 encodings × 3 separadores (12 combinações) para encontrar a configuração correta de cada CSV
- **Mapeamento flexível de colunas:** busca por match exato e parcial para localizar as colunas de data, valor e descrição, cobrindo variações como "Data Lançamento", "Histórico", "Vlr Transação"
- **Parse de valores brasileiros:** converte formatos como `R$ 1.234,56` e `1.234,56` para float
- **Categorização por regras:** classifica transações em 9 categorias (Água, Energia, Telefone/Internet, Cartão de Crédito, Alimentação, Transporte, Transferências, Recebimentos, Boletos) usando palavras-chave extraídas da descrição
- **Tratamento de dados inválidos:** remove linhas com data ou valor não parseáveis e informa quantas foram descartadas

### Visualizações

| Gráfico | O que mostra |
|---|---|
| Fluxo de Caixa Mensal | Barras agrupadas separando entradas (verde) e saídas (vermelho) por mês |
| Distribuição de Gastos | Pizza (donut) com participação percentual de cada categoria nas saídas |
| Top 5 Maiores Despesas | Barras horizontais com as 5 transações de maior valor absoluto |
| Evolução por Categoria | Barras empilhadas mostrando como cada categoria evolui mês a mês |
| Saldo Acumulado | Linha com saldo cumulativo ao longo do tempo |

A aplicação também apresenta KPIs (total de entradas, saídas, saldo líquido e número de transações), uma tabela com todas as transações e a opção de exportar o CSV consolidado.

## Bancos testados

Caixa Econômica, Nubank, Itaú, Bradesco, Inter. A lógica de detecção é genérica, então CSVs de outros bancos que sigam a estrutura padrão (colunas de data, valor e descrição) devem funcionar sem ajustes.

## Como rodar localmente

```bash
# Clonar o repositório
git clone https://github.com/cjinfoaulas-psy/financial-dashboard.git
cd financial-dashboard

# Instalar dependências
pip install -r requirements.txt

# Executar
streamlit run dashboard.py
```

O navegador abre automaticamente em `http://localhost:8501`. Arraste seus arquivos CSV para a área de upload.

Se o comando `streamlit` não for reconhecido, use:

```bash
python -m streamlit run dashboard.py
```

## Estrutura do projeto

```
financial-dashboard/
├── dashboard.py          # Aplicação principal (leitura, processamento, visualização)
├── requirements.txt      # Dependências Python
└── README.md
```

## Stack

- **pandas** para leitura, limpeza e transformação dos dados
- **Plotly** para gráficos interativos (zoom, hover, responsivos)
- **Streamlit** como framework web (sem necessidade de HTML/CSS/JS)

## Decisões técnicas

**Por que detecção automática em vez de configuração manual?**
O objetivo é que qualquer pessoa consiga usar sem precisar saber o encoding ou separador do seu CSV. O custo computacional de testar 12 combinações é desprezível para arquivos de extrato (tipicamente < 5 mil linhas).

**Por que categorização por regras em vez de ML?**
Para dados financeiros pessoais com volume baixo, regras baseadas em palavras-chave são mais previsíveis e auditáveis do que um classificador. O dicionário de palavras-chave é facilmente extensível editando a lista `CATEGORIAS` no início do arquivo.

**Por que `nsmallest` em vez de `nlargest` para despesas?**
Despesas são valores negativos no extrato. Usar `nlargest` retorna os valores mais próximos de zero (menores despesas). O correto é `nsmallest`, que pega os valores mais negativos (maiores despesas em valor absoluto).

## Extensões possíveis

- Conexão direta com APIs bancárias (Open Finance) para eliminar o upload manual
- Categorização via embeddings ou LLM para transações ambíguas
- Previsão de gastos mensais com séries temporais
- Alertas de gastos acima de thresholds configuráveis

## Licença

MIT
