# 📊 Guia de Uso - CSV de Síntese PRAD

## Arquivo Gerado
`portfolio/Simulado_PE/visuais/sintese_ultima_campanha.csv`

---

## 📋 Estrutura do CSV

### Campos (13 colunas)

| Campo | Tipo | Unidade | Descrição |
|-------|------|---------|-----------|
| `parcela` | string | - | Identificador da parcela (P01, P02, etc.) |
| `data` | date | YYYY-MM-DD | Data da última campanha de monitoramento |
| `sobrevivencia_pct` | float | % | Percentual de plantas vivas |
| `altura_media_m` | float | metros | Altura média das plantas |
| `diametro_medio_cm` | float | centímetros | Diâmetro médio do colo |
| `cobertura_copa_pct` | float | % | Cobertura de copa da vegetação plantada |
| `cobertura_invasoras_pct` | float | % | Cobertura de espécies invasoras |
| `razao_copa_invasoras` | float | razão | Copa ÷ Invasoras (maior = melhor) |
| `riqueza_especies` | int | n° espécies | Número de espécies com indivíduos vivos |
| `shannon_diversidade` | float | H' | Índice de diversidade de Shannon |
| `score_sucessional` | float | 0-100 | Pontuação do estágio sucessional |
| `estagio_sucessional` | string | - | Inicial, Intermediário ou Avançado |
| `alertas_criticos` | int | count | Número de alertas críticos |
| `alertas_atencao` | int | count | Número de alertas de atenção |

---

## 💻 Exemplos de Uso

### 1️⃣ Excel - Análise Rápida

```excel
1. Abrir CSV no Excel
2. Selecionar dados → Inserir → Tabela Dinâmica
3. Análises sugeridas:
   - Média de sobrevivência por parcela
   - Correlação entre copa e invasoras
   - Ranking por score sucessional
   - Contagem de alertas
```

**Fórmula de exemplo (Excel):**
```excel
=SE(D2<70;"Crítico";SE(D2<85;"Atenção";"OK"))  // Status sobrevivência
=MÉDIA(D:D)  // Sobrevivência média geral
=CONT.SE(L:L;"Avançado")  // Quantas parcelas estão em estágio avançado
```

---

### 2️⃣ Python - Análise Estatística

```python
import pandas as pd
import matplotlib.pyplot as plt

# Carregar CSV
df = pd.read_csv('sintese_ultima_campanha.csv')

# Estatísticas descritivas
print(df.describe())

# Correlação entre variáveis
correlacao = df[['sobrevivencia_pct', 'cobertura_copa_pct', 
                 'cobertura_invasoras_pct', 'shannon_diversidade']].corr()
print(correlacao)

# Gráfico: Score sucessional por parcela
df.plot(x='parcela', y='score_sucessional', kind='bar', 
        title='Score Sucessional por Parcela')
plt.ylabel('Score (0-100)')
plt.show()

# Filtrar parcelas com alertas
alertas = df[df['alertas_criticos'] > 0]
print("Parcelas com alertas críticos:")
print(alertas[['parcela', 'sobrevivencia_pct', 'alertas_criticos']])

# Classificação por estágio
print("\nDistribuição de estágios sucessoriais:")
print(df['estagio_sucessional'].value_counts())
```

**Saída esperada:**
```
Distribuição de estágios sucessoriais:
Avançado         2
Intermediário    0
Inicial          0
```

---

### 3️⃣ R - Modelagem Estatística

```r
# Carregar CSV
df <- read.csv('sintese_ultima_campanha.csv')

# Visualizar estrutura
str(df)
summary(df)

# Modelo de regressão: Sobrevivência vs. outras variáveis
modelo <- lm(sobrevivencia_pct ~ altura_media_m + cobertura_copa_pct + 
             cobertura_invasoras_pct + shannon_diversidade, data=df)
summary(modelo)

# Gráfico de dispersão
library(ggplot2)
ggplot(df, aes(x=cobertura_invasoras_pct, y=sobrevivencia_pct)) +
  geom_point(aes(color=estagio_sucessional), size=4) +
  geom_smooth(method='lm') +
  labs(title='Sobrevivência vs. Invasoras',
       x='Invasoras (%)', y='Sobrevivência (%)',
       color='Estágio') +
  theme_minimal()

# Teste t: Comparar P01 vs P02
t.test(sobrevivencia_pct ~ parcela, data=df)

# Boxplot de métricas
boxplot(df[,c('sobrevivencia_pct', 'altura_media_m', 
              'cobertura_copa_pct', 'shannon_diversidade')],
        main='Distribuição de Métricas',
        col=rainbow(4))
```

---

### 4️⃣ SQL - Consultas em Banco de Dados

```sql
-- Importar para SQLite/PostgreSQL
CREATE TABLE prad_sintese (
    parcela VARCHAR(10),
    data DATE,
    sobrevivencia_pct DECIMAL(5,2),
    altura_media_m DECIMAL(5,2),
    diametro_medio_cm DECIMAL(5,2),
    cobertura_copa_pct DECIMAL(5,2),
    cobertura_invasoras_pct DECIMAL(5,2),
    razao_copa_invasoras DECIMAL(6,2),
    riqueza_especies INT,
    shannon_diversidade DECIMAL(5,3),
    score_sucessional DECIMAL(5,2),
    estagio_sucessional VARCHAR(20),
    alertas_criticos INT,
    alertas_atencao INT
);

-- Consultas úteis
-- 1. Parcelas com melhor desempenho
SELECT parcela, score_sucessional, estagio_sucessional
FROM prad_sintese
ORDER BY score_sucessional DESC;

-- 2. Média de sobrevivência por estágio
SELECT estagio_sucessional, AVG(sobrevivencia_pct) as sobrev_media
FROM prad_sintese
GROUP BY estagio_sucessional;

-- 3. Parcelas que precisam atenção
SELECT parcela, sobrevivencia_pct, cobertura_invasoras_pct,
       (alertas_criticos + alertas_atencao) as total_alertas
FROM prad_sintese
WHERE alertas_criticos > 0 OR alertas_atencao > 0;

-- 4. Correlação visual (apenas valores)
SELECT 
    ROUND(AVG(sobrevivencia_pct), 1) as sobrev_media,
    ROUND(AVG(altura_media_m), 2) as altura_media,
    ROUND(AVG(cobertura_copa_pct), 1) as copa_media,
    ROUND(AVG(shannon_diversidade), 2) as shannon_medio
FROM prad_sintese;
```

---

## 📊 Casos de Uso Práticos

### 🌳 Gestão de Múltiplos PRADs

Se você tem vários PRADs, pode consolidar os CSVs:

```python
import pandas as pd
import glob

# Carregar todos os CSVs de diferentes projetos
arquivos = glob.glob('*/visuais/sintese_ultima_campanha.csv')
df_consolidado = pd.concat([pd.read_csv(f).assign(projeto=f.split('/')[0]) 
                            for f in arquivos])

# Ranking de projetos por score médio
ranking = df_consolidado.groupby('projeto')['score_sucessional'].mean().sort_values(ascending=False)
print("Ranking de projetos:")
print(ranking)

# Exportar relatório consolidado
df_consolidado.to_csv('relatorio_consolidado_PRADs.csv', index=False)
```

---

### 📈 Dashboard Executivo (Power BI / Tableau)

**Importação:**
1. Power BI → Obter Dados → Texto/CSV
2. Selecionar `sintese_ultima_campanha.csv`
3. Transformar dados (se necessário)

**Visualizações sugeridas:**
- **Gauge**: Score sucessional (0-100)
- **Mapa de calor**: Sobrevivência x Invasoras
- **Gráfico de barras**: Estágios sucessoriais
- **Indicadores**: Alertas críticos (vermelho se > 0)
- **Tabela**: Ranking de parcelas

---

### 🔔 Sistema de Alertas Automatizado

```python
import pandas as pd
import smtplib
from email.mime.text import MIMEText

# Carregar dados
df = pd.read_csv('sintese_ultima_campanha.csv')

# Verificar alertas críticos
criticos = df[df['alertas_criticos'] > 0]

if not criticos.empty:
    # Montar e-mail
    mensagem = f"""
    ALERTA PRAD - Ação Imediata Necessária
    
    Parcelas com alertas críticos:
    {criticos[['parcela', 'sobrevivencia_pct', 'cobertura_invasoras_pct']].to_string()}
    
    Recomendação: Realizar vistoria técnica urgente.
    """
    
    # Enviar (configurar servidor SMTP)
    # msg = MIMEText(mensagem)
    # msg['Subject'] = 'ALERTA CRÍTICO - PRAD Simulado PE'
    # msg['From'] = 'prad@exemplo.com'
    # msg['To'] = 'gestor@exemplo.com'
    # smtp.send_message(msg)
    
    print(mensagem)
else:
    print("✅ Nenhum alerta crítico. Sistema operando normalmente.")
```

---

## 📚 Interpretação de Valores

### Score Sucessional
| Score | Estágio | Ação Recomendada |
|-------|---------|------------------|
| 0-33 | Inicial | Intervenção intensiva: replantio, controle de invasoras |
| 34-66 | Intermediário | Monitoramento ativo, manutenção preventiva |
| 67-100 | Avançado | Manutenção reduzida, monitoramento de rotina |

### Índice de Shannon (H')
| H' | Interpretação | Recomendação |
|----|---------------|--------------|
| < 1.0 | Baixa diversidade | Enriquecimento com espécies tardias |
| 1.0-2.0 | Diversidade adequada | Manter monitoramento |
| > 2.0 | Alta diversidade | Excelente - sistema estável |

### Razão Copa/Invasoras
| Razão | Status | Interpretação |
|-------|--------|---------------|
| < 1.0 | ⚠️ Crítico | Invasoras dominam - controle urgente |
| 1.0-3.0 | ⚠️ Atenção | Competição equilibrada - monitorar |
| > 3.0 | ✅ Bom | Copa dominante - invasoras controladas |

---

## 🎯 Exemplo Real - Dados do Projeto

```csv
parcela,data,sobrevivencia_pct,altura_media_m,diametro_medio_cm,cobertura_copa_pct,cobertura_invasoras_pct,razao_copa_invasoras,riqueza_especies,shannon_diversidade,score_sucessional,estagio_sucessional,alertas_criticos,alertas_atencao
P01,2027-02-15,89.9,2.06,2.65,48.8,7.6,6.39,8,1.887,84.9,Avançado,0,0
P02,2027-02-15,83.6,1.84,2.50,44.2,10.1,4.37,8,1.896,80.7,Avançado,0,1
```

**Interpretação:**
- **P01**: Excelente desempenho (84.9), sem alertas
- **P02**: Bom desempenho (80.7), altura ligeiramente abaixo do esperado

**Recomendação técnica:**
- P01: Manutenção de rotina (capina semestral)
- P02: Monitorar crescimento; considerar adubação se estagnação persistir

---

## 📖 Referências para Análise

### Testes Estatísticos Recomendados
1. **Teste t**: Comparar métricas entre parcelas (APP vs RL)
2. **ANOVA**: Comparar múltiplos PRADs
3. **Regressão**: Modelar sobrevivência vs. variáveis ambientais
4. **Correlação de Pearson**: Relação entre copa e invasoras

### Softwares Compatíveis
- ✅ Excel / Google Sheets
- ✅ Python (pandas, scipy, matplotlib)
- ✅ R (tidyverse, ggplot2)
- ✅ Power BI / Tableau
- ✅ SPSS / SAS
- ✅ SQL (PostgreSQL, MySQL, SQLite)

---

**🎉 CSV de Síntese - Ferramenta versátil para análise e tomada de decisão em PRADs!**

---

**Autor:** Ronan Armando Caetano  
**Versão:** Dashboard PRAD v2.0  
**Data:** Novembro 2025
