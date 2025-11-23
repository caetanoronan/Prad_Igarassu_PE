# Caso Simulado – Pernambuco (Portfólio)

Este caso de PRAD é totalmente simulado e foi criado para demonstrar sua capacidade técnica no planejamento, execução e monitoramento de projetos de restauração.

Arquivos principais:
- `PRAD_Simulado_PE.md` – Documento do PRAD preenchido (simulado)
- `monitoramento_simulado.csv` – Dados simulados de 3 campanhas (02/2025, 08/2025, 02/2026) em 2 parcelas
- `visuais/relatorio.html` – Gráficos de evolução por parcela e por espécie (abrir no navegador)
- `visuais/mapa.html` – Mapa interativo com polígonos das parcelas (Leaflet + OpenStreetMap)
- `geo/parcelas.geojson` – Arquivo GeoJSON com geometrias das parcelas P01 e P02
- `Matriz_de_Riscos.md` – Análise de riscos com probabilidade x impactoComo gerar indicadores a partir do monitoramento simulado:

```powershell
python ..\..\scripts\indicadores_prad.py --input .\monitoramento_simulado.csv
```

Saídas esperadas:
- `saidas/indicadores_resumo.csv` (geral para o projeto)
- Resumo no console por parcela (última campanha)

Como gerar os visuais (gráficos por parcela, gráficos por espécie e mapa com polígonos):

```powershell
python ..\..\scripts\gerar_visuais.py --input .\monitoramento_simulado.csv --out .\visuais --geojson .\geo\parcelas.geojson
```

Depois, abra `visuais/relatorio.html` (gráficos de parcelas + espécies top 4) e `visuais/mapa.html` (parcelas como polígonos coloridos) no seu navegador.

Opcional – Exportar PRAD e Resumo para PDF (requer pandoc instalado):

```powershell
pandoc ..\..\portfolio\Simulado_PE\PRAD_Simulado_PE.md -o ..\..\portfolio\Simulado_PE\PRAD_Simulado_PE.pdf
pandoc ..\..\portfolio\Simulado_PE\Resumo_Executivo.md -o ..\..\portfolio\Simulado_PE\Resumo_Executivo.pdf
```

Destaques metodológicos no PRAD simulado:
- Estratégia PN + CRN, com uso intercalado de perenes exóticas ≤ 30% somente na RL e transição por desbaste a partir do 6º–8º ano.
- Cronograma de 24 anos com marcos claros (2, 5, 10 e 24 anos).
- Indicadores e gatilhos de gestão (sobrevivência < 80%; invasoras > 20%).

Você pode adaptar o município, área e a lista de espécies conforme novas oportunidades no portfólio.
