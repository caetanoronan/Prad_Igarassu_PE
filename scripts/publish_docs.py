#!/usr/bin/env python3
"""
Script simples para preparar os arquivos em `docs/` prontos para publicar no GitHub Pages.

O que faz:
- copia `relatorio.html`, `relatorio_tecnico.html` e `mapa.html` de `portfolio/Simulado_PE/visuais/` para `docs/Simulado_PE/visuais/`
- gera `docs/index.html` com um dashboard de entrega que incorpora links/iframes para os 3 produtos

Uso:
  python scripts/publish_docs.py
"""
import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.join(ROOT, 'portfolio', 'Simulado_PE', 'visuais')
DEST = os.path.join(ROOT, 'docs', 'Simulado_PE', 'visuais')

FILES = [
    'relatorio_tecnico.html',
    'relatorio.html',
    'mapa.html'
]

os.makedirs(DEST, exist_ok=True)

copied = []
for f in FILES:
    srcf = os.path.join(SRC, f)
    if os.path.exists(srcf):
        destf = os.path.join(DEST, f)
        shutil.copy2(srcf, destf)
        copied.append(f)
        print('Copiado', f, '->', destf)
    else:
        print('Aviso: arquivo não encontrado:', srcf)

index_path = os.path.join(ROOT, 'docs', 'index.html')
os.makedirs(os.path.dirname(index_path), exist_ok=True)

template = '''<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Entrega – PRAD Simulado_PE</title>
  <style>
    body{{font-family:Segoe UI,Arial,sans-serif;padding:28px;background:#f7fafc;color:#2c3e50}}
    .wrap{{max-width:1200px;margin:0 auto}}
    header{{display:flex;align-items:center;justify-content:space-between}}
    h1{{font-size:20px;margin:0}}
    .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:18px;margin-top:22px}}
    .card{{background:white;border-radius:8px;padding:14px;box-shadow:0 6px 18px rgba(0,0,0,0.06)}}
    .card h3{{margin-top:0;margin-bottom:8px;font-size:16px}}
    .frame{{width:100%;height:420px;border:1px solid #e6e6e6;border-radius:6px}}
    .links{margin-top:10px}
    .links a{{margin-right:8px;color:#2c3e50;text-decoration:none;background:#e6f0ff;padding:6px 9px;border-radius:6px;border:1px solid #cfe0ff}}
    footer{{margin-top:22px;text-align:center;font-size:13px;color:#718096}}
  </style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>Entrega final – PRAD (Simulado_PE)</h1>
      <div>Publicável via GitHub Pages • Copiado: {COPIED_PLACEHOLDER}</div>
    </header>

    <section class="cards">
      <div class="card">
        <h3>Relatório Técnico</h3>
        <iframe class="frame" src="Simulado_PE/visuais/relatorio_tecnico.html" title="Relatório Técnico"></iframe>
        <div class="links"><a href="Simulado_PE/visuais/relatorio_tecnico.html" target="_blank">Abrir em nova aba</a></div>
      </div>

      <div class="card">
        <h3>Dashboard de Monitoramento</h3>
        <iframe class="frame" src="Simulado_PE/visuais/relatorio.html" title="Dashboard"></iframe>
        <div class="links"><a href="Simulado_PE/visuais/relatorio.html" target="_blank">Abrir em nova aba</a></div>
      </div>

      <div class="card">
        <h3>Mapa Interativo</h3>
        <iframe class="frame" src="Simulado_PE/visuais/mapa.html" title="Mapa"></iframe>
        <div class="links"><a href="Simulado_PE/visuais/mapa.html" target="_blank">Abrir em nova aba</a></div>
      </div>
    </section>

    <footer>Autor: Ronan Armando Caetano — PRAD Simulado_PE • Gerado localmente</footer>
  </div>
</body>
</html>'''

content = template.replace('{COPIED_PLACEHOLDER}', ', '.join(copied) if copied else 'nenhum')

with open(index_path, 'w', encoding='utf-8') as fh:
    fh.write(content)

print('\nPágina de entrega gerada em docs/index.html')
