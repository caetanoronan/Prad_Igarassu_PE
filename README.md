# PRAD — Programa de Recuperação de Áreas Degradadas (repositório)

Este repositório reúne um projeto de exemplo (Simulado_PE) com scripts e artefatos para monitoramento, cálculo de indicadores e geração de visuais interativos (mapa + dashboard). O conteúdo foi preparado para publicação via GitHub Pages — veja o site de entrega abaixo.

Site público (GitHub Pages): https://caetanoronan.github.io/Prad_Igarassu_PE/

CI / Deploy automático
----------------------
Há um workflow (GitHub Actions) que regenerará os visuais e publicará automaticamente a pasta `docs/` no branch `gh-pages` sempre que houver push para `main` (ou via execução manual do workflow). Isso mantém o site atualizado sem necessidade de procedimentos manuais.

Licença
-------
Este projeto está licenciado sob MIT — veja o arquivo `LICENSE`.

# Estrutura do PRAD nesta pasta

Conteúdo criado para apoiar a elaboração do Programa de Recuperação de Áreas Degradadas (PRAD):

- `docs/Guia_PRAD.md` – Guia prático com critérios, métodos e cronograma de 24 anos.
- `templates/PRAD_template.md` – Template editável do PRAD, pronto para preencher.
- `planilhas/modelo_custos.csv` – Modelo de custos (itens e insumos principais).
- `checklists/checklist_monitoramento.md` – Checklist para campanhas de monitoramento.
- `dados/especies_PE_mata_atlantica.csv` – Lista regional de espécies para Mata Atlântica (PE).
- `dados/especies_PE_caatinga.csv` – Lista regional de espécies para Caatinga (PE).
- `planilhas/monitoramento_modelo.csv` – Estrutura de coleta de dados de campo.
- `planilhas/monitoramento_exemplo.csv` – Exemplo preenchido para teste.
- `scripts/indicadores_prad.py` – Script para gerar indicadores (sobrevivência, riqueza, cobertura, invasoras) a partir de planilha de monitoramento.
- `scripts/gerar_visuais.py` – Gera `visuais/relatorio.html` (gráficos por parcela + espécies) e `visuais/mapa.html` (Leaflet + GeoJSON) a partir de um CSV.

Sugestão de uso:
1. Leia o guia em `docs/Guia_PRAD.md`.
2. Duplique o `templates/PRAD_template.md` e preencha com os dados da sua área.
3. Ajuste o `planilhas/modelo_custos.csv` com quantidades e preços locais.
 4. Defina o bioma predominante e anexe a lista de espécies correspondente em `dados/` (adaptando conforme seu diagnóstico).
 5. Utilize `planilhas/monitoramento_modelo.csv` nas campanhas de campo (ou adapte para aplicativo).
 6. Após registrar dados, execute o script de indicadores.
 7. Use o checklist nas campanhas de campo e anexe os resultados ao PRAD.

## Executando o script de indicadores

Pré-requisitos: Python 3 instalado.

No PowerShell (Windows):

```powershell
python .\scripts\indicadores_prad.py --input .\planilhas\monitoramento_exemplo.csv
```

Saída:
- Gera `saidas/indicadores_resumo.csv` (cria pasta se não existir).
- Imprime resumo por parcela (última campanha) com status simples.

Campos avaliados:
- Taxa de sobrevivência (%) = soma plantadas_vivas / plantadas_totais * 100.
- Riqueza de espécies = número de espécies distintas por parcela/data.
- Cobertura média de copa e de invasoras (%) – valores médios das linhas.
Gatilhos exemplo já incluídos: sobrevivência < 80% (atenção), invasoras > 20% (atenção).

Observação: Adeque sempre à legislação federal, estadual e municipal aplicável e às exigências do órgão licenciador responsável.

## Caso simulado (Portfólio)

Para demonstrar sua capacidade em um cenário completo, incluímos um caso simulado em Pernambuco:

- Pasta: `portfolio/Simulado_PE/`
	- `PRAD_Simulado_PE.md` – PRAD preenchido (simulado)
	- `monitoramento_simulado.csv` – dados de 3 campanhas (02/2025, 08/2025, 02/2026)
	- `Resumo_Executivo.md` – síntese dos resultados e lições

Gerar indicadores do caso simulado (PowerShell):

```powershell
python .\scripts\indicadores_prad.py --input .\portfolio\Simulado_PE\monitoramento_simulado.csv
```

Saídas: `saidas/indicadores_resumo.csv` e resumo no console por parcela (última campanha).

Gerar visuais (gráficos e mapa) do caso simulado:

```powershell
python .\scripts\gerar_visuais.py --input .\portfolio\Simulado_PE\monitoramento_simulado.csv --out .\portfolio\Simulado_PE\visuais --geojson .\portfolio\Simulado_PE\geo\parcelas.geojson
```

Abra depois: `portfolio/Simulado_PE/visuais/relatorio.html` (gráficos por parcela e top 4 espécies) e `portfolio/Simulado_PE/visuais/mapa.html` (parcelas como polígonos).
