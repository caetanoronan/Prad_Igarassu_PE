#!/usr/bin/env python3
"""
Script simples para calcular indicadores de PRAD a partir de uma planilha CSV de monitoramento.

Entrada (CSV): colunas obrigatórias
- parcela,data,bioma,coordenada_lat,coordenada_lon,especie,nome_popular,
  plantadas_vivas,plantadas_totais,altura_m,diametro_cm,cobertura_copa_pct,
  cobertura_invasoras_pct,observacoes,foto

Saídas:
- saidas/indicadores_resumo.csv (por parcela e data)
- impressão no console de um resumo agregado

Uso:
  python scripts/indicadores_prad.py --input planilhas/monitoramento_exemplo.csv
  (ou apenas executar sem argumentos para usar o arquivo de exemplo)

Sem dependências externas (usa apenas biblioteca padrão).
"""
import csv
import os
import sys
from collections import defaultdict
from statistics import mean
from datetime import datetime

DEFAULT_INPUT = os.path.join('planilhas', 'monitoramento_exemplo.csv')
OUTPUT_DIR = 'saidas'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'indicadores_resumo.csv')

REQUIRED_COLUMNS = [
    'parcela','data','bioma','coordenada_lat','coordenada_lon','especie','nome_popular',
    'plantadas_vivas','plantadas_totais','altura_m','diametro_cm','cobertura_copa_pct',
    'cobertura_invasoras_pct','observacoes','foto'
]

def parse_float(x, default=None):
    try:
        if x is None or x == '':
            return default
        return float(x)
    except Exception:
        return default


def parse_int(x, default=None):
    try:
        if x is None or x == '':
            return default
        return int(float(x))
    except Exception:
        return default


def read_rows(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        cols = [c.strip() for c in reader.fieldnames or []]
        missing = [c for c in REQUIRED_COLUMNS if c not in cols]
        if missing:
            raise ValueError(f'Colunas faltantes no CSV: {missing}')
        for row in reader:
            yield {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}


def compute_indicators(rows):
    # Agrupar por (parcela, data)
    groups = defaultdict(list)
    for r in rows:
        key = (r['parcela'], r['data'])
        groups[key].append(r)

    summaries = []
    for (parcela, data), itens in groups.items():
        plantadas_vivas = [parse_int(r['plantadas_vivas'], 0) for r in itens]
        plantadas_totais = [parse_int(r['plantadas_totais'], 0) for r in itens]
        alturas = [parse_float(r['altura_m']) for r in itens if parse_float(r['altura_m']) is not None]
        diametros = [parse_float(r['diametro_cm']) for r in itens if parse_float(r['diametro_cm']) is not None]
        cobertura_copa = [parse_float(r['cobertura_copa_pct']) for r in itens if parse_float(r['cobertura_copa_pct']) is not None]
        cobertura_invas = [parse_float(r['cobertura_invasoras_pct']) for r in itens if parse_float(r['cobertura_invasoras_pct']) is not None]
        especies = set([r['especie'] for r in itens if r['especie']])
        biomas = set([r['bioma'] for r in itens if r['bioma']])

        total_vivas = sum(plantadas_vivas)
        total_plantadas = sum(plantadas_totais)
        taxa_sobrevivencia = (total_vivas / total_plantadas * 100.0) if total_plantadas > 0 else None
        altura_media = mean(alturas) if alturas else None
        diametro_medio = mean(diametros) if diametros else None
        cobertura_copa_media = mean(cobertura_copa) if cobertura_copa else None
        cobertura_invas_media = mean(cobertura_invas) if cobertura_invas else None
        riqueza = len(especies)
        bioma = ';'.join(sorted(biomas)) if biomas else ''

        # Classificar status em relação a metas simples
        status = []
        if taxa_sobrevivencia is not None:
            status.append('OK_sobrevivencia' if taxa_sobrevivencia >= 80 else 'ATENCAO_sobrevivencia')
        if cobertura_invas_media is not None:
            status.append('OK_invasoras' if cobertura_invas_media <= 20 else 'ATENCAO_invasoras')

        summaries.append({
            'parcela': parcela,
            'data': data,
            'bioma': bioma,
            'riqueza_especies': riqueza,
            'total_plantadas': total_plantadas,
            'total_vivas': total_vivas,
            'taxa_sobrevivencia_pct': round(taxa_sobrevivencia, 2) if taxa_sobrevivencia is not None else '',
            'altura_media_m': round(altura_media, 2) if altura_media is not None else '',
            'diametro_medio_cm': round(diametro_medio, 2) if diametro_medio is not None else '',
            'cobertura_copa_media_pct': round(cobertura_copa_media, 2) if cobertura_copa_media is not None else '',
            'cobertura_invasoras_media_pct': round(cobertura_invas_media, 2) if cobertura_invas_media is not None else '',
            'status': ','.join(status)
        })

    return summaries


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main(argv):
    input_file = None
    for i, a in enumerate(argv):
        if a in ('-i', '--input') and i+1 < len(argv):
            input_file = argv[i+1]
    if input_file is None:
        input_file = DEFAULT_INPUT
    if not os.path.exists(input_file):
        print(f"Arquivo de entrada não encontrado: {input_file}")
        return 2

    rows = list(read_rows(input_file))
    summaries = compute_indicators(rows)
    write_csv(OUTPUT_FILE, summaries)

    # Resumo no console agregado por parcela (última data)
    last_by_parcela = {}
    for s in sorted(summaries, key=lambda x: (x['parcela'], x['data'])):
        last_by_parcela[s['parcela']] = s

    print('Resumo (última campanha por parcela):')
    for parcela, s in last_by_parcela.items():
        print(f"- {parcela} {s['data']}: sobrevivência={s['taxa_sobrevivencia_pct']}%, riqueza={s['riqueza_especies']}, invasoras={s['cobertura_invasoras_media_pct']}% -> {s['status']}")
    print(f"\nArquivo gerado: {OUTPUT_FILE}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
