#!/usr/bin/env python3
"""
Gera três arquivos HTML para o portfólio do PRAD Simulado:
- relatorio.html: gráficos (linha) de evolução de sobrevivência, cobertura de copa, invasoras por parcela + gráficos por espécie.
- mapa.html: mapa Leaflet mostrando polígonos das parcelas (carrega GeoJSON).

Uso:
  python scripts/gerar_visuais.py --input portfolio/Simulado_PE/monitoramento_simulado.csv --out portfolio/Simulado_PE/visuais --geojson portfolio/Simulado_PE/geo/parcelas.geojson

Sem bibliotecas externas (somente stdlib); gráficos renderizados via simples SVG inline.
"""
import csv
import os
import math
import sys
import json
import urllib.request
from collections import defaultdict
from typing import cast
from statistics import mean

DEFAULT_INPUT = os.path.join('portfolio','Simulado_PE','monitoramento_simulado.csv')
DEFAULT_OUT = os.path.join('portfolio','Simulado_PE','visuais')
DEFAULT_GEOJSON = os.path.join('portfolio','Simulado_PE','geo','parcelas.geojson')
DEFAULT_SINTESE = os.path.join('portfolio','Simulado_PE','visuais','sintese_ultima_campanha.csv')
DEFAULT_MUNICIPIOS = os.path.join('portfolio','Simulado_PE','geo','limite_municipios_pe.geojson')
DEFAULT_BIOMAS = os.path.join('portfolio','Simulado_PE','geo','limite_biomas.geojson')

FIELDS = ['parcela','data','especie','plantadas_vivas','plantadas_totais','cobertura_copa_pct','cobertura_invasoras_pct']

# Paleta ColorBrewer BuGn para alertas e estágios
COLOR_ALERTA_CRITICO = '#d73027'  # Vermelho
COLOR_ALERTA_ATENCAO = '#fee08b'  # Amarelo
COLOR_ALERTA_OK = '#1a9850'       # Verde

# Paleta ColorBrewer BuGn (3 classes) - usada para visualizações principais
CB_BUGN = ['#e5f5f9', '#99d8c9', '#2ca25f']

# counter used to provide unique ids for SVG <title>/<desc> elements
_svg_id_counter = 0

def read_rows(path):
    with open(path, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            yield row


def group_metrics(rows):
    # Agrupar por parcela+data
    grupos = defaultdict(list)
    datas_ordem = set()
    for r in rows:
        key = (r['parcela'], r['data'])
        grupos[key].append(r)
        datas_ordem.add(r['data'])

    datas = sorted(datas_ordem)
    series = defaultdict(lambda: {
        'datas': [],
        'sobrevivencia': [],
        'cobertura_copa': [],
        'cobertura_invasoras': [],
        'riqueza': [],
        'shannon': [],
        'altura_media': [],
        'diametro_medio': [],
        'razao_copa_invasoras': [],
    })

    # Calcular por parcela e data
    for (parcela, data), itens in grupos.items():
        plantadas_vivas = sum(int(i['plantadas_vivas']) for i in itens if i['plantadas_vivas'])
        plantadas_totais = sum(int(i['plantadas_totais']) for i in itens if i['plantadas_totais'])
        cobertura_copa = [float(i['cobertura_copa_pct']) for i in itens if i['cobertura_copa_pct']]
        cobertura_invas = [float(i['cobertura_invasoras_pct']) for i in itens if i['cobertura_invasoras_pct']]
        alturas = [float(i['altura_m']) for i in itens if i.get('altura_m')]
        diametros = [float(i['diametro_cm']) for i in itens if i.get('diametro_cm')]
        sobrevivencia = plantadas_vivas/plantadas_totais*100 if plantadas_totais>0 else 0
        copa_mean = mean(cobertura_copa) if cobertura_copa else 0
        invas_mean = mean(cobertura_invas) if cobertura_invas else 0
        altura_mean = mean(alturas) if alturas else 0
        diametro_mean = mean(diametros) if diametros else 0
        razao_ci = (copa_mean / (invas_mean if invas_mean > 0 else 1e-6)) if (copa_mean > 0 or invas_mean > 0) else 0
        # riqueza e Shannon por parcela/data
        vivos_por_sp = defaultdict(int)
        for i in itens:
            try:
                vivos = int(i['plantadas_vivas']) if i['plantadas_vivas'] else 0
            except ValueError:
                vivos = 0
            vivos_por_sp[i['especie']] += vivos
        riqueza = sum(1 for v in vivos_por_sp.values() if v > 0)
        total_vivos = sum(vivos_por_sp.values())
        if total_vivos > 0:
            from math import log
            p_list = [v/total_vivos for v in vivos_por_sp.values() if v > 0]
            shannon = -sum(p*log(p) for p in p_list)
        else:
            shannon = 0.0
        series[parcela]['datas'].append(data)
        series[parcela]['sobrevivencia'].append(sobrevivencia)
        series[parcela]['cobertura_copa'].append(copa_mean)
        series[parcela]['cobertura_invasoras'].append(invas_mean)
        series[parcela]['riqueza'].append(riqueza)
        series[parcela]['shannon'].append(shannon)
        series[parcela]['altura_media'].append(altura_mean)
        series[parcela]['diametro_medio'].append(diametro_mean)
        series[parcela]['razao_copa_invasoras'].append(razao_ci)

    # Ordenar cada série por datas globais
    for parcela, s in series.items():
        ordenados = sorted(zip(s['datas'], s['sobrevivencia'], s['cobertura_copa'], s['cobertura_invasoras']))
        s['datas'] = [d for d,_,__,___ in ordenados]
        s['sobrevivencia'] = [v for _,v,__,___ in ordenados]
        s['cobertura_copa'] = [v for _,__,v,___ in ordenados]
        s['cobertura_invasoras'] = [v for _,__,__,v in ordenados]

    return series, datas


def group_by_species(rows):
    """Agrupar por espécie + data para gerar séries temporais por espécie."""
    grupos = defaultdict(list)
    datas_ordem = set()
    for r in rows:
        key = (r['especie'], r['data'])
        grupos[key].append(r)
        datas_ordem.add(r['data'])
    
    datas = sorted(datas_ordem)
    series_sp = defaultdict(lambda: {'datas':[], 'sobrevivencia':[]})
    
    for (especie, data), itens in grupos.items():
        plantadas_vivas = sum(int(i['plantadas_vivas']) for i in itens if i['plantadas_vivas'])
        plantadas_totais = sum(int(i['plantadas_totais']) for i in itens if i['plantadas_totais'])
        sobrevivencia = plantadas_vivas/plantadas_totais*100 if plantadas_totais>0 else 0
        series_sp[especie]['datas'].append(data)
        series_sp[especie]['sobrevivencia'].append(sobrevivencia)
    
    # Ordenar
    for sp, s in series_sp.items():
        ordenados = sorted(zip(s['datas'], s['sobrevivencia']))
        s['datas'] = [d for d,_ in ordenados]
        s['sobrevivencia'] = [v for _,v in ordenados]
    
    return series_sp, datas


def scale(values, width, height, padding=30):
    if not values:
        return []
    vmax = max(values)
    vmin = min(values)
    if math.isclose(vmax, vmin):
        vmax = vmin + 1
    scaled = []
    for i, v in enumerate(values):
        x = padding + i*(width-2*padding)/(len(values)-1 if len(values)>1 else 1)
        y = height - padding - (v - vmin)/(vmax - vmin)*(height-2*padding)
        scaled.append((x,y))
    return scaled, vmin, vmax


def polyline(points, color):
    if not points:
        return ''
    pts = ' '.join(f"{x:.1f},{y:.1f}" for x,y in points)
    return f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{pts}" />'


def calcular_incrementos(series):
    """Calcula taxa de incremento (Δ altura e Δ diâmetro) entre campanhas consecutivas."""
    incrementos = {}
    
    for parcela, s in series.items():
        incrementos[parcela] = {
            'datas_intervalo': [],
            'delta_altura': [],
            'delta_diametro': [],
            'taxa_altura_mes': [],
            'taxa_diametro_mes': []
        }
        
        alturas = s.get('altura_media', [])
        diametros = s.get('diametro_medio', [])
        datas = s.get('datas', [])
        
        for i in range(1, len(datas)):
            # Calcular diferença absoluta
            delta_h = alturas[i] - alturas[i-1] if i < len(alturas) else 0
            delta_d = diametros[i] - diametros[i-1] if i < len(diametros) else 0
            
            # Calcular meses entre campanhas (aproximado: 6 meses)
            # Simplificado: assumir 6 meses entre campanhas
            meses = 6
            taxa_h = delta_h / meses if meses > 0 else 0
            taxa_d = delta_d / meses if meses > 0 else 0
            
            intervalo = f"{datas[i-1]} → {datas[i]}"
            incrementos[parcela]['datas_intervalo'].append(intervalo)
            incrementos[parcela]['delta_altura'].append(delta_h)
            incrementos[parcela]['delta_diametro'].append(delta_d)
            incrementos[parcela]['taxa_altura_mes'].append(taxa_h)
            incrementos[parcela]['taxa_diametro_mes'].append(taxa_d)
    
    return incrementos


def classificar_estagio_sucessional(series, ultima_data):
    """
    Classifica estágio sucessional de cada parcela com base em múltiplos indicadores.
    Score: 0-100
    - Inicial (0-33): Baixa diversidade, alta invasoras
    - Intermediário (34-66): Diversidade média, invasoras controladas
    - Avançado (67-100): Alta diversidade, copa dominante
    """
    classificacao = {}
    
    for parcela, s in series.items():
        if ultima_data not in s['datas']:
            continue
        
        idx = s['datas'].index(ultima_data)
        sobrev = s['sobrevivencia'][idx]
        shannon = s['shannon'][idx]
        riqueza = s['riqueza'][idx]
        copa = s['cobertura_copa'][idx]
        invasoras = s['cobertura_invasoras'][idx]
        razao = s['razao_copa_invasoras'][idx]
        
        # Pontuação por critério (0-100)
        score_sobrev = min(sobrev, 100)  # Sobrevivência já é %
        score_shannon = min((shannon / 2.0) * 100, 100)  # Shannon max ~2.0 para 8 espécies
        score_riqueza = min((riqueza / 8) * 100, 100)  # 8 espécies = máximo
        score_copa = min(copa, 100)  # Copa já é %
        score_invasoras = max(100 - invasoras, 0)  # Inverter (menos invasoras = melhor)
        score_razao = min((razao / 5) * 100, 100)  # Razão 5:1 = excelente
        
        # Média ponderada
        score_total = (
            score_sobrev * 0.25 +
            score_shannon * 0.15 +
            score_riqueza * 0.10 +
            score_copa * 0.20 +
            score_invasoras * 0.20 +
            score_razao * 0.10
        )
        
        # Classificar
        if score_total < 34:
            estagio = 'Inicial'
            cor = '#fee08b'
        elif score_total < 67:
            estagio = 'Intermediário'
            cor = '#91cf60'
        else:
            estagio = 'Avançado'
            cor = '#1a9850'
        
        classificacao[parcela] = {
            'score': score_total,
            'estagio': estagio,
            'cor': cor,
            'sobrevivencia': sobrev,
            'shannon': shannon,
            'riqueza': riqueza,
            'copa': copa,
            'invasoras': invasoras,
            'razao': razao
        }
    
    return classificacao


def gerar_alertas(series, ultima_data):
    """Gera alertas automáticos com base em critérios técnicos."""
    alertas = []
    
    for parcela, s in series.items():
        if ultima_data not in s['datas']:
            continue
        
        idx = s['datas'].index(ultima_data)
        sobrev = s['sobrevivencia'][idx]
        invasoras = s['cobertura_invasoras'][idx]
        copa = s['cobertura_copa'][idx]
        altura = s['altura_media'][idx]
        
        # Critérios de alerta
        if sobrev < 70:
            alertas.append({
                'parcela': parcela,
                'tipo': 'CRÍTICO',
                'categoria': 'Sobrevivência',
                'mensagem': f'Taxa de sobrevivência baixa ({sobrev:.1f}%) - Meta: ≥70%',
                'valor': sobrev,
                'cor': COLOR_ALERTA_CRITICO
            })
        
        if invasoras > 25:
            alertas.append({
                'parcela': parcela,
                'tipo': 'ATENÇÃO',
                'categoria': 'Invasoras',
                'mensagem': f'Cobertura de invasoras elevada ({invasoras:.1f}%) - Meta: ≤25%',
                'valor': invasoras,
                'cor': COLOR_ALERTA_ATENCAO
            })
        
        if copa < 40 and len(s['datas']) >= 3:  # Após 3+ campanhas
            alertas.append({
                'parcela': parcela,
                'tipo': 'ATENÇÃO',
                'categoria': 'Copa',
                'mensagem': f'Cobertura de copa insuficiente ({copa:.1f}%) - Meta: ≥40% após 18 meses',
                'valor': copa,
                'cor': COLOR_ALERTA_ATENCAO
            })
        
        if altura < 2.0 and len(s['datas']) >= 4:  # Após 4+ campanhas
            alertas.append({
                'parcela': parcela,
                'tipo': 'ATENÇÃO',
                'categoria': 'Crescimento',
                'mensagem': f'Crescimento lento - Altura média {altura:.2f}m após 2+ anos',
                'valor': altura,
                'cor': COLOR_ALERTA_ATENCAO
            })
    
    return alertas


def exportar_sintese_csv(series, classificacao, alertas, ultima_data, path_out):
    """Exporta CSV de síntese agregada da última campanha."""
    rows_out = []
    
    for parcela, s in series.items():
        if ultima_data not in s['datas']:
            continue
        
        idx = s['datas'].index(ultima_data)
        classif = classificacao.get(parcela, {})
        
        # Alertas para esta parcela
        alertas_parcela = [a for a in alertas if a['parcela'] == parcela]
        n_criticos = sum(1 for a in alertas_parcela if a['tipo'] == 'CRÍTICO')
        n_atencao = sum(1 for a in alertas_parcela if a['tipo'] == 'ATENÇÃO')
        
        row = {
            'parcela': parcela,
            'data': ultima_data,
            'sobrevivencia_pct': f"{s['sobrevivencia'][idx]:.1f}",
            'altura_media_m': f"{s['altura_media'][idx]:.2f}",
            'diametro_medio_cm': f"{s['diametro_medio'][idx]:.2f}",
            'cobertura_copa_pct': f"{s['cobertura_copa'][idx]:.1f}",
            'cobertura_invasoras_pct': f"{s['cobertura_invasoras'][idx]:.1f}",
            'razao_copa_invasoras': f"{s['razao_copa_invasoras'][idx]:.2f}",
            'riqueza_especies': int(s['riqueza'][idx]),
            'shannon_diversidade': f"{s['shannon'][idx]:.3f}",
            'score_sucessional': f"{classif.get('score', 0):.1f}",
            'estagio_sucessional': classif.get('estagio', 'N/A'),
            'alertas_criticos': n_criticos,
            'alertas_atencao': n_atencao
        }
        rows_out.append(row)
    
    # Escrever CSV
    if rows_out:
        fieldnames = list(rows_out[0].keys())
        with open(path_out, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows_out)
        print(f" - {path_out}")
    
    return rows_out


def make_chart(title, datas, series_dict, metric_key, colors):
    width, height = 520, 220
    # construir valores max/min globais para normalizar
    all_vals = []
    for parcela, s in series_dict.items():
        vals = s.get(metric_key, [])
        all_vals.extend(vals)
    if not all_vals:
        return f'<h3>{title}</h3><p>Sem dados.</p>'
    vmax = max(all_vals); vmin = min(all_vals)
    if math.isclose(vmax,vmin):
        vmax = vmin + 1

    def scale_specific(values):
        scaled = []
        for i, v in enumerate(values):
            x = 40 + i*(width-80)/(len(datas)-1 if len(datas)>1 else 1)
            y = height - 40 - (v - vmin)/(vmax - vmin)*(height-80)
            scaled.append((x,y))
        return scaled

    # create a unique id for the svg so we can reference title/desc with aria-labelledby
    global _svg_id_counter
    _svg_id_counter += 1
    uid = f"chart{_svg_id_counter}"
    lines = []
    legend_items = []
    palette_iter = iter(colors)
    for parcela, s in sorted(series_dict.items()):
        col = next(palette_iter, '#000000')
        vals_seq = []
        # alinhar às datas globais para manter consistência
        data_to_val = dict(zip(s['datas'], s[metric_key]))
        for d in datas:
            vals_seq.append(data_to_val.get(d, None))
        # filler para faltantes (usa último valor)
        clean = []
        last = None
        for v in vals_seq:
            if v is None:
                v = last if last is not None else (vmin)
            clean.append(v)
            last = v
        pts = scale_specific(clean)
        lines.append(f'<polyline fill="none" stroke="{col}" stroke-width="2" points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in pts)}" />')
        legend_items.append(f'<span style="color:{col}">■ {parcela}</span>')

    # Eixos simples
    svg = [f'<h3 id="{uid}-heading">{title}</h3>', f'<svg role="img" aria-labelledby="{uid}-title {uid}-desc" width="{width}" height="{height}" style="background:#fafafa;border:1px solid #e0e0e0;border-radius:8px;font-family:Arial,sans-serif;">', f'<title id="{uid}-title">{title}</title>', f'<desc id="{uid}-desc">Gráfico de linhas: {title}. Última data: {datas[-1] if datas else "N/A"}.</desc>']
    # eixo X
    svg.append('<line x1="40" y1="180" x2="480" y2="180" stroke="#333" stroke-width="1" />')
    # eixo Y
    svg.append('<line x1="40" y1="40" x2="40" y2="180" stroke="#333" stroke-width="1" />')
    # labels X
    for i,d in enumerate(datas):
        x = 40 + i*(width-80)/(len(datas)-1 if len(datas)>1 else 1)
        svg.append(f'<text x="{x:.1f}" y="195" font-size="10" text-anchor="middle">{d}</text>')
    # labels Y (5 divisões)
    # Y labels adapt to metric scale (0-1 for Shannon)
    y_ticks = 5
    if metric_key == 'shannon':
        # typical range 0-2.5
        vmin_disp, vmax_disp = 0.0, max(vmax, 2.0)
    else:
        vmin_disp, vmax_disp = vmin, vmax
    for j in range(y_ticks+1):
        val = vmin_disp + j*(vmax_disp-vmin_disp)/y_ticks
        y = 180 - j*(140)/y_ticks
        svg.append(f'<text x="35" y="{y+3:.1f}" font-size="10" text-anchor="end">{val:.1f}</text>')
        svg.append(f'<line x1="40" y1="{y:.1f}" x2="480" y2="{y:.1f}" stroke="#f0f0f0" stroke-width="1" />')

    svg.extend(lines)
    svg.append('</svg>')
    svg.append(f'<div class="legend">{" ".join(legend_items)}</div>')
    # add an accessible, screen-reader-visible data table fallback for users who cannot access the visual chart
    table_id = f"{uid}-data"
    table = ['<div class="sr-only" aria-hidden="false" role="region" aria-labelledby="'+uid+'-heading">', f'<table id="{table_id}" style="border-collapse:collapse; width:100%"><caption>{title} — dados por data</caption>']
    # header (add explicit Data column + parcelas)
    table.append('<thead><tr><th scope="col">Data</th>')
    for parcela in sorted(series_dict.keys()):
        table.append(f'<th scope="col">{parcela}</th>')
    table.append('</tr></thead>')
    # rows
    table.append('<tbody>')
    for i, d in enumerate(datas):
        table.append('<tr>')
        table.append(f'<th scope="row">{d}</th>')
        for parcela in sorted(series_dict.keys()):
            s = series_dict.get(parcela, {})
            vals = s.get(metric_key, [])
            val = vals[i] if i < len(vals) else ''
            if isinstance(val, float) or isinstance(val, int):
                cell = f"{val:.2f}"
            else:
                cell = str(val)
            table.append(f'<td>{cell}</td>')
        table.append('</tr>')
    table.append('</tbody></table></div>')
    svg.append('\n'.join(table))
    return '\n'.join(svg)


# Helper: baixa GeoJSONs oficiais quando ausentes (IBGE)
def download_geojson_if_missing(url, out_path):
    """Baixa a URL para out_path se o arquivo não existir. Retorna True em sucesso."""
    if not url or not out_path:
        return False
    if os.path.exists(out_path):
        return True
    try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        print(f'Baixando {url} → {out_path}')
        urllib.request.urlretrieve(url, out_path)
        return True
    except Exception as e:
        print('Falha ao baixar', url, '->', e)
        return False


def download_all_municipios_pe(out_path):
    """Baixa as malhas de todos os municípios de PE e agrega em um único GeoJSON."""
    if os.path.exists(out_path):
        return True
    try:
        url_list = 'https://servicodados.ibge.gov.br/api/v1/localidades/estados/26/municipios'
        print('Consultando lista de municípios de PE...')
        with urllib.request.urlopen(url_list) as resp:
            data_bytes = resp.read()
            try:
                municipios = json.loads(data_bytes.decode('utf-8'))
            except UnicodeDecodeError:
                import gzip
                municipios = json.loads(gzip.decompress(data_bytes).decode('utf-8'))

        features = []
        for m in municipios:
            mid = m.get('id')
            if not mid:
                continue
            try:
                malha_url = f'https://servicodados.ibge.gov.br/api/v3/malhas/municipios/{mid}?formato=application/vnd.geo+json'
                with urllib.request.urlopen(malha_url) as r:
                    data_bytes = r.read()
                    try:
                        js = json.loads(data_bytes.decode('utf-8'))
                    except UnicodeDecodeError:
                        import gzip
                        try:
                            js = json.loads(gzip.decompress(data_bytes).decode('utf-8'))
                        except Exception:
                            js = None
                    if isinstance(js, dict) and js.get('type') == 'FeatureCollection' and 'features' in js:
                        features.extend(js['features'])
                    elif isinstance(js, dict) and js.get('type') == 'Feature':
                        features.append(js)
            except Exception as e:
                print('Aviso: falha ao baixar malha municipio', mid, '-', e)

        combined = {'type': 'FeatureCollection', 'features': features}
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(combined, f, ensure_ascii=False)
        print('Arquivo combinado de municípios salvo em', out_path)
        return True
    except Exception as e:
        print('Falha ao compilar municipios PE:', e)
        return False


def download_all_biomas(out_path):
    """Baixa malhas de biomas (tenta baixar por lista /api/v1/localidades/biomas e agrega)."""
    if os.path.exists(out_path):
        return True
    try:
        url_list = 'https://servicodados.ibge.gov.br/api/v1/localidades/biomas'
        print('Consultando lista de biomas (IBGE)...')
        with urllib.request.urlopen(url_list) as resp:
            data_bytes = resp.read()
            try:
                biomas = json.loads(data_bytes.decode('utf-8'))
            except UnicodeDecodeError:
                import gzip
                biomas = json.loads(gzip.decompress(data_bytes).decode('utf-8'))

        features = []
        for b in biomas:
            bid = b.get('id')
            if not bid:
                continue
            try:
                malha_url = f'https://servicodados.ibge.gov.br/api/v3/malhas/biomas/{bid}?formato=application/vnd.geo+json'
                with urllib.request.urlopen(malha_url) as r:
                    data_bytes = r.read()
                    try:
                        js = json.loads(data_bytes.decode('utf-8'))
                    except UnicodeDecodeError:
                        import gzip
                        try:
                            js = json.loads(gzip.decompress(data_bytes).decode('utf-8'))
                        except Exception:
                            js = None
                    if isinstance(js, dict) and js.get('type') == 'FeatureCollection' and 'features' in js:
                        features.extend(js['features'])
                    elif isinstance(js, dict) and js.get('type') == 'Feature':
                        features.append(js)
            except Exception as e:
                print('Aviso: falha ao baixar malha bioma', bid, '-', e)

        combined = {'type': 'FeatureCollection', 'features': features}
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(combined, f, ensure_ascii=False)
        print('Arquivo combinado de biomas salvo em', out_path)
        return True
    except Exception as e:
        print('Falha ao compilar biomas:', e)
        return False


def write_relatorio(path_out, series, datas, series_sp, rows):
    # Paleta principal para gráficos (BuGn 3 - sequencial acessível)
    colors = CB_BUGN
    
    # Calcular última data
    ultima_data = max(datas) if datas else ''
    
    # Calcular incrementos, classificação e alertas
    incrementos = calcular_incrementos(series)
    classificacao = classificar_estagio_sucessional(series, ultima_data)
    alertas = gerar_alertas(series, ultima_data)
    
    # Calcular métricas-chave (última campanha)
    sobrev_p01 = series.get('P01', {}).get('sobrevivencia', [0])[-1] if 'P01' in series else 0
    sobrev_p02 = series.get('P02', {}).get('sobrevivencia', [0])[-1] if 'P02' in series else 0
    sobrev_media = (sobrev_p01 + sobrev_p02) / 2
    
    copa_p01 = series.get('P01', {}).get('cobertura_copa', [0])[-1] if 'P01' in series else 0
    copa_p02 = series.get('P02', {}).get('cobertura_copa', [0])[-1] if 'P02' in series else 0
    copa_media = (copa_p01 + copa_p02) / 2
    
    invas_p01 = series.get('P01', {}).get('cobertura_invasoras', [0])[-1] if 'P01' in series else 0
    invas_p02 = series.get('P02', {}).get('cobertura_invasoras', [0])[-1] if 'P02' in series else 0
    invas_media = (invas_p01 + invas_p02) / 2
    
    num_especies = len(series_sp)
    # Riqueza e Shannon (média últimas por parcela)
    riqueza_vals = []
    shannon_vals = []
    for parcela, s in series.items():
        if s['riqueza']:
            riqueza_vals.append(s['riqueza'][-1])
        if s['shannon']:
            shannon_vals.append(s['shannon'][-1])
    riqueza_media = mean(riqueza_vals) if riqueza_vals else 0
    shannon_medio = mean(shannon_vals) if shannon_vals else 0

    # Painel de sucessão: espécies presentes na última campanha e seus grupos funcionais
    especies_csv = os.path.join('dados','especies_PE_mata_atlantica.csv')
    sp_to_group = {}
    sp_to_pop = {}
    if os.path.exists(especies_csv):
        with open(especies_csv, newline='', encoding='utf-8') as f:
            r = csv.DictReader(f)
            for row in r:
                sp_to_group[row['nome_cientifico']] = row['grupo_funcional']
                sp_to_pop[row['nome_cientifico']] = row.get('nome_popular','')
    latest = max(datas) if datas else ''
    presentes = defaultdict(int)
    for r in rows:
        if r['data'] == latest:
            try:
                vivos = int(r['plantadas_vivas']) if r['plantadas_vivas'] else 0
            except ValueError:
                vivos = 0
            if vivos > 0:
                presentes[r['especie']] += vivos
    grupos_presentes = defaultdict(list)
    for sp in sorted(presentes.keys()):
        grupo = sp_to_group.get(sp, 'Outros')
        nome_pop = sp_to_pop.get(sp, '')
        label = f"{nome_pop} ({sp})" if nome_pop else sp
        grupos_presentes[grupo].append(label)
    
    parts = [
        '<!DOCTYPE html><html lang="pt-br"><head><meta charset="utf-8" />',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>Dashboard PRAD – Monitoramento e Indicadores</title>',
        '<style>',
        ':root {',
        "  --bg: #f7fcfb;",
        "  --card: #ffffff;",
        "  --muted: #61707a;",
        "  --accent: #2ca25f;",
        "  --bugn-1: #e5f5f9;",
        "  --bugn-2: #99d8c9;",
        "  --bugn-3: #2ca25f;",
        '}',
        '* { margin: 0; padding: 0; box-sizing: border-box; }',
        'body { font-family: "Inter", "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; background: var(--bg); color: #17323b; padding: 18px; -webkit-font-smoothing:antialiased; }',
        '.dashboard { max-width: 1200px; margin: 0 auto; }',
        '.skip-link { position: absolute; left: -999px; top: auto; width:1px; height:1px; overflow:hidden; }',
        '.skip-link:focus { left: 18px; top: 18px; width:auto; height:auto; padding:8px 12px; background:var(--card); border-radius:6px; box-shadow:0 6px 18px rgba(0,0,0,0.12); z-index:2000; }',
        '.sr-only { position:absolute !important; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; border:0; }',
        '.header { background: var(--card); padding: 20px; border-radius: 10px; margin-bottom: 16px; box-shadow: 0 6px 18px rgba(0,0,0,0.06); }',
        '.header h1 { color: #0f3b2d; font-size: 26px; margin-bottom: 6px; }',
        '.header p { color: var(--muted); font-size: 14px; }',
        '.metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-bottom: 18px; }',
        '.metric-card { background: var(--card); padding: 18px; border-radius: 10px; box-shadow: 0 6px 18px rgba(3,19,16,0.04); transition: transform 0.18s ease-in-out; }',
        '.metric-card:hover { transform: translateY(-6px); }',
        '.metric-label { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px; }',
        '.metric-value { font-size: 30px; font-weight: 700; color: #082a20; margin-bottom: 4px; }',
        '.metric-unit { font-size: 14px; color: var(--muted); margin-left: 6px; }',
        '.metric-trend { font-size: 12px; color: var(--accent); margin-top: 6px; }',
        '.metric-trend.negative { color: #bf2b2b; }',
        '.metric-icon { float: right; font-size: 28px; opacity: 0.25; }',
        '.section-title { background: transparent; padding: 8px 0; margin: 18px 0 8px 0; }',
        '.section-title h2 { color: #0f3b2d; font-size: 20px; margin: 0; border-left: 4px solid var(--bugn-3); padding-left: 12px; }',
        '.charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 16px; margin-bottom: 18px; }',
        '.charts-grid-single { display: grid; grid-template-columns: 1fr; gap: 16px; margin-bottom: 18px; }',
        '.chart-card { background: var(--card); padding: 18px; border-radius: 10px; box-shadow: 0 6px 18px rgba(3,19,16,0.04); }',
        '.chart-card h3 { color: #082a20; font-size: 16px; margin-bottom: 12px; }',
        '.footer { background: transparent; padding: 12px 0; text-align: center; color: var(--muted); font-size: 13px; }',
        '.legend { margin-top: 12px; font-size: 13px; color: var(--muted); }',
        '.legend span { margin-right: 12px; display:inline-block; }',
        '@media (max-width: 900px) { .charts-grid, .charts-grid-single { grid-template-columns: 1fr; } .metrics { grid-template-columns: repeat(auto-fit,minmax(180px,1fr)); } }',
        '@media print { body { background: white; } .header, .metric-card, .chart-card { box-shadow: none !important; } }',
        '@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }',
        '</style>',
        '</head><body>',
        '<a class="skip-link" href="#main">Pular para o conteúdo</a>',
        '<div class="dashboard" id="main" role="main">',
        '<div class="header">',
        '<h1>📊 Dashboard PRAD – Monitoramento e Indicadores</h1>',
        '<p>Programa de Recuperação de Áreas Degradadas | Igarassu/PE | Última atualização: ' + datas[-1] + '</p>',
    '</div>',
    '<div style="text-align:right;margin-bottom:12px;">',
    '<button type="button" onclick="window.print()" aria-label="Salvar relatório em PDF" title="Salvar relatório em PDF" style="background:#2c3e50;color:#fff;border:none;padding:10px 14px;border-radius:8px;cursor:pointer;">Salvar PDF</button>',
    '</div>',
        
        # Cards de métricas
    '<div class="metrics">',
        '<div class="metric-card">',
        '<div class="metric-icon">🌱</div>',
        '<div class="metric-label">Sobrevivência Média</div>',
        f'<div class="metric-value">{sobrev_media:.1f}<span class="metric-unit">%</span></div>',
        '<div class="metric-trend">↗ Tendência positiva</div>',
        '</div>',
        
        '<div class="metric-card">',
        '<div class="metric-icon">🌳</div>',
        '<div class="metric-label">Cobertura de Copa</div>',
        f'<div class="metric-value">{copa_media:.1f}<span class="metric-unit">%</span></div>',
        '<div class="metric-trend">↗ Em expansão</div>',
        '</div>',
        
        '<div class="metric-card">',
        '<div class="metric-icon">⚠️</div>',
        '<div class="metric-label">Invasoras</div>',
        f'<div class="metric-value">{invas_media:.1f}<span class="metric-unit">%</span></div>',
        '<div class="metric-trend negative">↘ Em declínio</div>',
        '</div>',
        
        '<div class="metric-card">',
        '<div class="metric-icon">🔬</div>',
        '<div class="metric-label">Riqueza de Espécies</div>',
    f'<div class="metric-value">{riqueza_media:.1f}<span class="metric-unit"> spp</span></div>',
    '<div class="metric-trend">Última campanha</div>',
    '</div>',

    '<div class="metric-card">',
    '<div class="metric-icon">📈</div>',
    '<div class="metric-label">Diversidade (Shannon)</div>',
    f'<div class="metric-value">{shannon_medio:.2f}</div>',
    '<div class="metric-trend">Última campanha</div>',
        '</div>',
        '</div>',
        
        # SEÇÃO 1: Indicadores Estruturais
        '<div class="section-title"><h2>📊 Indicadores Estruturais da Vegetação</h2></div>',
        '<div class="charts-grid">',
        '<div class="chart-card">',
        make_chart('Taxa de Sobrevivência (%)', datas, series, 'sobrevivencia', colors),
        '</div>',
        '<div class="chart-card">',
        make_chart('Altura Média (m)', datas, series, 'altura_media', colors),
        '</div>',
        '<div class="chart-card">',
        make_chart('Diâmetro Médio (cm)', datas, series, 'diametro_medio', colors),
        '</div>',
        '<div class="chart-card">',
        make_chart('Cobertura de Copa (%)', datas, series, 'cobertura_copa', colors),
        '</div>',
        '</div>',
        
        # SEÇÃO 2: Controle de Invasoras
        '<div class="section-title"><h2>⚠️ Controle de Espécies Invasoras</h2></div>',
        '<div class="charts-grid">',
        '<div class="chart-card">',
        make_chart('Cobertura de Invasoras (%)', datas, series, 'cobertura_invasoras', colors),
        '</div>',
        '<div class="chart-card">',
        make_chart('Razão Copa/Invasoras', datas, series, 'razao_copa_invasoras', colors),
        '</div>',
        '</div>',
        
        # SEÇÃO 3: Diversidade Biológica
        '<div class="section-title"><h2>🌿 Diversidade Biológica</h2></div>',
        '<div class="charts-grid">',
        '<div class="chart-card">',
        make_chart('Riqueza de Espécies (spp)', datas, series, 'riqueza', colors),
        '</div>',
        '<div class="chart-card">',
        make_chart('Índice de Shannon (H\')', datas, series, 'shannon', colors),
        '</div>',
        
        # Gráfico por espécie
        '<div class="chart-card">',
    ]
    
    top_species = sorted(series_sp.items(), key=lambda x: x[0])[:4]
    parts.append(make_chart_species('Sobrevivência por Espécie - Top 4', datas, dict(top_species), colors))
    parts.append('</div>')
    parts.append('</div>')

    # SEÇÃO 4: Sucessão Ecológica e Comparações
    parts.append('<div class="section-title"><h2>🌳 Sucessão Ecológica e Composição Florística</h2></div>')
    parts.append('<div class="charts-grid-single">')
    # Painel de sucessão ecológica
    parts.append('<div class="chart-card">')
    parts.append('<h3>Espécies presentes na última campanha (' + latest + ')</h3>')
    parts.append('<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;">')
    for grupo in sorted(grupos_presentes.keys()):
        lista = grupos_presentes[grupo]
        items = ''.join(f'<li>{x}</li>' for x in lista)
        parts.append(f'<div><strong>{grupo}</strong><ul style="margin-top:6px;line-height:1.5">{items}</ul></div>')
    parts.append('</div>')
    parts.append('</div>')
    
    # Comparativo APP vs RL (assumindo P01=APP, P02=RL)
    parts.append('<div class="chart-card">')
    parts.append('<h3>Comparativo APP vs RL – Última campanha (' + latest + ')</h3>')
    subarea_map = {'P01': 'APP', 'P02': 'RL'}
    agg = defaultdict(lambda: {'vivas':0,'totais':0,'copa':[],'invas':[]})
    for r in rows:
        if r['data'] == latest:
            sa = subarea_map.get(r['parcela'], 'Outros')
            try:
                viv = int(r['plantadas_vivas']) if r['plantadas_vivas'] else 0
                tot = int(r['plantadas_totais']) if r['plantadas_totais'] else 0
                cc = float(r['cobertura_copa_pct']) if r['cobertura_copa_pct'] else 0
                ci = float(r['cobertura_invasoras_pct']) if r['cobertura_invasoras_pct'] else 0
            except ValueError:
                viv, tot, cc, ci = 0, 0, 0.0, 0.0
            # ensure aggregated types are as expected before altering
            entry = agg[sa]
            # normalize / coerce types explicitly to avoid analyzer confusion
            entry['vivas'] = cast(int, entry.get('vivas', 0)) + viv
            entry['totais'] = cast(int, entry.get('totais', 0)) + tot
            # ensure copa & invas are lists and append
            if not isinstance(entry.get('copa'), list):
                entry['copa'] = list(cast(list, entry.get('copa') or []))
            cast(list, entry['copa']).append(cc)
            if not isinstance(entry.get('invas'), list):
                entry['invas'] = list(cast(list, entry.get('invas') or []))
            cast(list, entry['invas']).append(ci)
    table_rows = []
    for sa in ['APP','RL']:
        a = agg.get(sa)
        if a:
            totais_val = cast(int, a.get('totais', 0))
            viv_val = cast(int, a.get('vivas', 0))
            surv = (viv_val / totais_val * 100) if totais_val > 0 else 0
            copa_sa = mean(list(cast(list, a.get('copa', [])))) if a.get('copa') else 0
            invas_sa = mean(list(cast(list, a.get('invas', [])))) if a.get('invas') else 0
            table_rows.append(f'<tr><td>{sa}</td><td>{surv:.1f}%</td><td>{copa_sa:.1f}%</td><td>{invas_sa:.1f}%</td></tr>')
    parts.append('<table style="width:100%;border-collapse:collapse;margin-top:8px;">')
    parts.append('<thead><tr><th style="text-align:left;border-bottom:2px solid #ecf0f1;">Subárea</th><th style="text-align:right;border-bottom:2px solid #ecf0f1;">Sobrevivência</th><th style="text-align:right;border-bottom:2px solid #ecf0f1;">Copa</th><th style="text-align:right;border-bottom:2px solid #ecf0f1;">Invasoras</th></tr></thead>')
    parts.append('<tbody>')
    parts.append(''.join(table_rows) if table_rows else '<tr><td colspan="4">Sem dados.</td></tr>')
    parts.append('</tbody></table>')
    parts.append('</div>')
    parts.append('</div>')
    
    # SEÇÃO 5: Alertas Automáticos
    if alertas:
        parts.append('<div class="section-title"><h2>🚨 Alertas e Recomendações Técnicas</h2></div>')
        parts.append('<div class="charts-grid-single">')
        parts.append('<div class="chart-card">')
        parts.append('<div style="display:grid;gap:12px;">')
        
        # Agrupar por parcela
        alertas_por_parcela = defaultdict(list)
        for a in alertas:
            alertas_por_parcela[a['parcela']].append(a)
        
        for parcela in sorted(alertas_por_parcela.keys()):
            parts.append(f'<div style="border-left:4px solid #e74c3c;padding-left:12px;margin-bottom:12px;">')
            parts.append(f'<strong style="color:#2c3e50;">Parcela {parcela}</strong>')
            parts.append('<ul style="margin-top:8px;line-height:1.8;">')
            for a in alertas_por_parcela[parcela]:
                icon = '🔴' if a['tipo'] == 'CRÍTICO' else '⚠️'
                parts.append(f'<li style="color:#555;"><strong style="color:{a["cor"]}">{icon} [{a["categoria"]}]</strong> {a["mensagem"]}</li>')
            parts.append('</ul>')
            parts.append('</div>')
        
        parts.append('</div>')
        parts.append('</div>')
        parts.append('</div>')
    
    # SEÇÃO 6: Classificação Sucessional
    parts.append('<div class="section-title"><h2>🌲 Classificação de Estágio Sucessional</h2></div>')
    parts.append('<div class="charts-grid">')
    
    for parcela in sorted(classificacao.keys()):
        c = classificacao[parcela]
        parts.append('<div class="chart-card">')
        parts.append(f'<h3>Parcela {parcela}</h3>')
        parts.append(f'<div style="text-align:center;margin:20px 0;">')
        parts.append(f'<div style="display:inline-block;background:{c["cor"]};color:#fff;padding:12px 24px;border-radius:8px;font-size:18px;font-weight:bold;margin-bottom:12px;">')
        parts.append(f'{c["estagio"]}</div>')
        parts.append(f'<div style="color:#7f8c8d;font-size:14px;">Score: {c["score"]:.1f}/100</div>')
        parts.append('</div>')
        
        # Indicadores detalhados
        parts.append('<table style="width:100%;margin-top:16px;border-collapse:collapse;">')
        parts.append('<tr style="border-bottom:1px solid #ecf0f1;"><td style="padding:8px;color:#7f8c8d;">Sobrevivência</td><td style="text-align:right;padding:8px;font-weight:bold;">{:.1f}%</td></tr>'.format(c['sobrevivencia']))
        parts.append('<tr style="border-bottom:1px solid #ecf0f1;"><td style="padding:8px;color:#7f8c8d;">Diversidade (Shannon)</td><td style="text-align:right;padding:8px;font-weight:bold;">{:.2f}</td></tr>'.format(c['shannon']))
        parts.append('<tr style="border-bottom:1px solid #ecf0f1;"><td style="padding:8px;color:#7f8c8d;">Riqueza</td><td style="text-align:right;padding:8px;font-weight:bold;">{:.0f} spp</td></tr>'.format(c['riqueza']))
        parts.append('<tr style="border-bottom:1px solid #ecf0f1;"><td style="padding:8px;color:#7f8c8d;">Cobertura Copa</td><td style="text-align:right;padding:8px;font-weight:bold;">{:.1f}%</td></tr>'.format(c['copa']))
        parts.append('<tr style="border-bottom:1px solid #ecf0f1;"><td style="padding:8px;color:#7f8c8d;">Invasoras</td><td style="text-align:right;padding:8px;font-weight:bold;">{:.1f}%</td></tr>'.format(c['invasoras']))
        parts.append('<tr><td style="padding:8px;color:#7f8c8d;">Razão Copa/Invasoras</td><td style="text-align:right;padding:8px;font-weight:bold;">{:.2f}</td></tr>'.format(c['razao']))
        parts.append('</table>')
        parts.append('</div>')
    
    parts.append('</div>')
    
    # SEÇÃO 7: Incrementos de Crescimento
    parts.append('<div class="section-title"><h2>📈 Taxa de Incremento (Δ Altura e Δ Diâmetro)</h2></div>')
    parts.append('<div class="charts-grid">')
    
    for parcela in sorted(incrementos.keys()):
        inc = incrementos[parcela]
        if not inc['datas_intervalo']:
            continue
        
        parts.append('<div class="chart-card">')
        parts.append(f'<h3>Parcela {parcela} - Incrementos por Período</h3>')
        parts.append('<table style="width:100%;border-collapse:collapse;margin-top:8px;font-size:13px;">')
        parts.append('<thead><tr>')
        parts.append('<th style="text-align:left;border-bottom:2px solid #ecf0f1;padding:8px;">Período</th>')
        parts.append('<th style="text-align:right;border-bottom:2px solid #ecf0f1;padding:8px;">Δ Altura (m)</th>')
        parts.append('<th style="text-align:right;border-bottom:2px solid #ecf0f1;padding:8px;">Taxa/mês (m)</th>')
        parts.append('<th style="text-align:right;border-bottom:2px solid #ecf0f1;padding:8px;">Δ Diâmetro (cm)</th>')
        parts.append('<th style="text-align:right;border-bottom:2px solid #ecf0f1;padding:8px;">Taxa/mês (cm)</th>')
        parts.append('</tr></thead>')
        parts.append('<tbody>')
        
        for i in range(len(inc['datas_intervalo'])):
            periodo = inc['datas_intervalo'][i]
            dh = inc['delta_altura'][i]
            dd = inc['delta_diametro'][i]
            th = inc['taxa_altura_mes'][i]
            td = inc['taxa_diametro_mes'][i]
            
            # Cor baseada em taxa positiva/negativa
            cor_h = '#27ae60' if dh > 0 else '#e74c3c'
            cor_d = '#27ae60' if dd > 0 else '#e74c3c'
            
            parts.append('<tr style="border-bottom:1px solid #ecf0f1;">')
            parts.append(f'<td style="padding:8px;color:#7f8c8d;">{periodo}</td>')
            parts.append(f'<td style="text-align:right;padding:8px;color:{cor_h};font-weight:bold;">{dh:+.2f}</td>')
            parts.append(f'<td style="text-align:right;padding:8px;color:#95a5a6;">{th:.3f}</td>')
            parts.append(f'<td style="text-align:right;padding:8px;color:{cor_d};font-weight:bold;">{dd:+.2f}</td>')
            parts.append(f'<td style="text-align:right;padding:8px;color:#95a5a6;">{td:.3f}</td>')
            parts.append('</tr>')
        
        parts.append('</tbody></table>')
        parts.append('</div>')
    
    parts.append('</div>')
    
    parts.append('<div class="footer">Dashboard gerado automaticamente por gerar_visuais.py | Autor: Ronan Armando Caetano — Graduando em Ciências Biológicas (UFSC) • Técnico em Geoprocessamento (IFSC) • Técnico em Saneamento (IFSC) | PRAD Simulado PE</div>')
    parts.append('</div></body></html>')
    
    with open(path_out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(parts))


def make_chart_species(title, datas, series_dict, colors):
    """Gráfico de linha para séries de espécies (sobrevivência)."""
    width, height = 520, 220
    all_vals = []
    for sp, s in series_dict.items():
        vals = s.get('sobrevivencia', [])
        all_vals.extend(vals)
    if not all_vals:
        return f'<h3>{title}</h3><p>Sem dados.</p>'
    vmax = max(all_vals); vmin = min(all_vals)
    if math.isclose(vmax,vmin):
        vmax = vmin + 1

    def scale_specific(values):
        scaled = []
        for i, v in enumerate(values):
            x = 40 + i*(width-80)/(len(datas)-1 if len(datas)>1 else 1)
            y = height - 40 - (v - vmin)/(vmax - vmin)*(height-80)
            scaled.append((x,y))
        return scaled

    # unique svg id for species charts
    global _svg_id_counter
    _svg_id_counter += 1
    uid = f"chartsp{_svg_id_counter}"

    lines = []
    legend_items = []
    palette_iter = iter(colors)
    for sp, s in sorted(series_dict.items()):
        col = next(palette_iter, '#000000')
        vals_seq = []
        data_to_val = dict(zip(s['datas'], s['sobrevivencia']))
        for d in datas:
            vals_seq.append(data_to_val.get(d, None))
        clean = []
        last = None
        for v in vals_seq:
            if v is None:
                v = last if last is not None else vmin
            clean.append(v)
            last = v
        pts = scale_specific(clean)
        lines.append(f'<polyline fill="none" stroke="{col}" stroke-width="2" points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in pts)}" />')
        sp_short = sp.split()[-1] if len(sp.split())>1 else sp  # nome popular
        legend_items.append(f'<span style="color:{col}">■ {sp_short}</span>')

    svg = [f'<h3 id="{uid}-heading">{title}</h3>', f'<svg role="img" aria-labelledby="{uid}-title {uid}-desc" width="{width}" height="{height}" style="background:#fafafa;border:1px solid #e0e0e0;border-radius:8px;font-family:Arial,sans-serif;">', f'<title id="{uid}-title">{title}</title>', f'<desc id="{uid}-desc">Gráfico por espécie mostrando sobrevivência por data. Última data: {datas[-1] if datas else "N/A"}.</desc>']
    svg.append('<line x1="40" y1="180" x2="480" y2="180" stroke="#333" stroke-width="1" />')
    svg.append('<line x1="40" y1="40" x2="40" y2="180" stroke="#333" stroke-width="1" />')
    for i,d in enumerate(datas):
        x = 40 + i*(width-80)/(len(datas)-1 if len(datas)>1 else 1)
        svg.append(f'<text x="{x:.1f}" y="195" font-size="10" text-anchor="middle">{d}</text>')
    for j in range(6):
        val = vmin + j*(vmax-vmin)/5
        y = 180 - j*(140)/5
        svg.append(f'<text x="35" y="{y+3:.1f}" font-size="10" text-anchor="end">{val:.0f}</text>')
        svg.append(f'<line x1="40" y1="{y:.1f}" x2="480" y2="{y:.1f}" stroke="#f0f0f0" stroke-width="1" />')

    svg.extend(lines)
    svg.append('</svg>')
    svg.append(f'<div class="legend">{" ".join(legend_items)}</div>')
    # accessible fallback table
    table_id = f"{uid}-data"
    table = ['<div class="sr-only" aria-hidden="false" role="region" aria-labelledby="'+uid+'-heading">', f'<table id="{table_id}" style="border-collapse:collapse; width:100%"><caption>{title} — dados por data</caption>']
    table.append('<thead><tr><th scope="col">Data</th>')
    for sp in sorted(series_dict.keys()):
        short = sp.split()[-1] if len(sp.split())>1 else sp
        table.append(f'<th scope="col">{short}</th>')
    table.append('</tr></thead>')
    table.append('<tbody>')
    for i, d in enumerate(datas):
        table.append('<tr>')
        table.append(f'<th scope="row">{d}</th>')
        for sp in sorted(series_dict.keys()):
            s = series_dict.get(sp,{})
            vals = s.get('sobrevivencia', [])
            val = vals[i] if i < len(vals) else ''
            if isinstance(val, float) or isinstance(val, int):
                cell = f"{val:.2f}"
            else:
                cell = str(val)
            table.append(f'<td>{cell}</td>')
        table.append('</tr>')
    table.append('</tbody></table></div>')
    svg.append('\n'.join(table))
    return '\n'.join(svg)


def write_mapa(path_out, geojson_path):
    # Mapa com pol�gonos GeoJSON carregados
    leaflet_css = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    leaflet_js = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    
    # Carregar GeoJSON principal (parcelas) se existir
    geojson_data = "{}"
    if geojson_path and os.path.exists(geojson_path):
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = f.read()

    # Procurar limites opcionais (limite estadual e municipal) na mesma pasta do GeoJSON
    geojson_estadual = None
    geojson_municipal = None
    try:
        geo_dir = os.path.dirname(geojson_path) if geojson_path else os.path.join('portfolio','Simulado_PE','geo')
    except Exception:
        geo_dir = os.path.join('portfolio','Simulado_PE','geo')

    est_path = os.path.join(geo_dir, 'limite_estadual.geojson')
    mun_path = os.path.join(geo_dir, 'limite_municipal.geojson')
    if os.path.exists(est_path):
        with open(est_path, 'r', encoding='utf-8') as f:
            geojson_estadual = f.read()
    if os.path.exists(mun_path):
        with open(mun_path, 'r', encoding='utf-8') as f:
            geojson_municipal = f.read()
    # Ler camada com todos os municípios de PE e os biomas (se existirem)
    municipios_pe_path = os.path.join(geo_dir, 'limite_municipios_pe.geojson')
    biomas_path = os.path.join(geo_dir, 'limite_biomas.geojson')
    geojson_municipios_pe = None
    geojson_biomas = None
    if os.path.exists(municipios_pe_path):
        with open(municipios_pe_path, 'r', encoding='utf-8') as f:
            geojson_municipios_pe = f.read()
    if os.path.exists(biomas_path):
        with open(biomas_path, 'r', encoding='utf-8') as f:
            geojson_biomas = f.read()
    
    html = f"""<!DOCTYPE html><html lang='pt-br'><head><meta charset='utf-8'/><title>Mapa – PRAD Simulado Pernambuco</title>
<link rel='stylesheet' href='{leaflet_css}'/>
<style>
:root {{
    --bg: #f7fcfb;
    --card: #ffffff;
    --muted: #425b55;
    --accent: #2ca25f;
    --bugn-1: #e5f5f9;
    --bugn-2: #99d8c9;
    --bugn-3: #2ca25f;
}}
body,html{{height:100%;margin:0;padding:0;font-family:Arial,sans-serif;background:var(--bg);color:#0b2e24}}
#map{{height:calc(100% - 64px);width:100%;}}
.header{{background:var(--card);color:var(--muted);padding:12px 20px;font-size:18px;font-weight:700;text-align:center;border-bottom:4px solid var(--bugn-2);}}
.info{{background:var(--card);padding:12px 14px;border:1px solid rgba(6,33,24,0.08);position:absolute;top:120px;left:12px;z-index:900;font-size:14px;line-height:1.5;max-width:360px;box-shadow:0 8px 20px rgba(6,33,24,0.06);border-radius:8px;overflow:auto;max-height:60vh;transition:transform 180ms ease,opacity 180ms ease;}}
.info h3{{margin:0 0 8px 0;font-size:15px;border-bottom:2px solid var(--bugn-1);padding-bottom:6px;color:#073826}}
.legend-item{{margin:6px 0;display:flex;align-items:center;gap:8px}}
.legend-item .swatch{{display:inline-block;width:22px;height:14px;border-radius:3px;border:1px solid rgba(0,0,0,0.06)}}
.footer{{position:absolute;bottom:12px;left:12px;background:rgba(255,255,255,0.95);padding:8px 12px;font-size:12px;border-radius:8px;z-index:900;text-align:left;max-width:calc(100% - 40px);box-shadow:0 6px 14px rgba(6,33,24,0.06)}}
/* Garantir controles do Leaflet por cima dos elementos informativos */
.leaflet-control-container{{z-index:1600 !important}}

@media (max-width: 700px) {{
        .info {{ position: fixed; bottom: 88px; left: 12px; right: 12px; top: auto; max-width: none; max-height:36vh; }}
        #map {{ height: calc(100% - 156px); }}
        .info h3 {{ font-size:14px; }}
        .footer {{ left: 12px; right: 12px; bottom: 12px; max-width: none; }}
}}
/* legenda sempre visível; botão de alternar removido do template para evitar bloqueio */
</style>
</head><body>
<div class='header'>PRAD Simulado – Mata Atlântica (Pernambuco)</div>
<div id='map'></div>
<div class='info' id='infoPanel'>
  <h3>Local de Estudo</h3>
    <strong>Município:</strong> Igarassu/PE<br/>
  <strong>Bioma:</strong> Mata Atlântica<br/>
  <strong>Área:</strong> 12 ha (APP + RL)<br/>
  <hr style='margin:8px 0;'/>
  <h3>Legendas</h3>
    <div class='legend-item'><span class='swatch' style='background:var(--bugn-3);'></span>Parcela P01 – Desempenho alto</div>
    <div class='legend-item'><span class='swatch' style='background:var(--bugn-2);'></span>Parcela P02 – Recuperação progressiva</div>
    <!-- Limites estadual e municipal removidos da legenda conforme solicitado -->
</div>
<div class='footer'><strong>Autor:</strong> Ronan Armando Caetano — Graduando em Ciências Biológicas (UFSC) • Técnico em Geoprocessamento (IFSC) • Técnico em Saneamento (IFSC)</div>
<script src='{leaflet_js}'></script>
<script>
var map = L.map('map', {{
  minZoom: 12,
  maxZoom: 18,
  maxBounds: [[-7.95, -35.05], [-7.72, -34.80]]
}}).setView([-7.8340,-34.9060], 14);

L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  maxZoom: 19, 
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contribuidores'
}}).addTo(map);

var geojsonData = {geojson_data};
var geojsonEstadual = {geojson_estadual if geojson_estadual is not None else 'null'};
var geojsonMunicipal = {geojson_municipal if geojson_municipal is not None else 'null'};
var geojsonMunicipiosPE = {geojson_municipios_pe if geojson_municipios_pe is not None else 'null'};
var geojsonBiomas = {geojson_biomas if geojson_biomas is not None else 'null'};

// legenda sempre visível; controle de toggle removido do template

// Camada principal: parcelas (visível por padrão)
var parcelasLayer = L.geoJSON(geojsonData, {{
    style: function(feature) {{
        return {{
            color: feature.properties.parcela === 'P01' ? '#2b8cbe' : '#de2d26',
            weight: 1.8,
            fillOpacity: 0.45
        }};
    }},
    onEachFeature: function(feature, layer) {{
        if (feature.properties && feature.properties.descricao) {{
            layer.bindPopup('<b>'+feature.properties.parcela+'</b><br/>'+feature.properties.descricao);
        }}
        layer.on('mouseover', function() {{ this.setStyle({{weight:3, fillOpacity:0.6}}); }});
        layer.on('mouseout', function() {{ this.setStyle({{weight:1.8, fillOpacity:0.45}}); }});
    }}
}}).addTo(map);

// Ajustar zoom inicial para as parcelas
if (parcelasLayer.getBounds && parcelasLayer.getBounds().isValid()) {{
    map.fitBounds(parcelasLayer.getBounds(), {{padding: [50, 50]}});
}}

// Camada: limite estadual (opcional)
var estadoLayer = null;
    if (geojsonEstadual) {{
    try {{
        estadoLayer = L.geoJSON(geojsonEstadual, {{
            style: function(f) {{ return {{color:'#1b7837', weight:3, fillOpacity:0}}; }},
            onEachFeature: function(feature, layer) {{
                var name = feature.properties && (feature.properties.nome || feature.properties.codarea || feature.properties.name);
                if (name) layer.bindPopup('<strong>UF:</strong> ' + name);
            }}
        }});
    }} catch(e) {{
        console.warn('Falha ao adicionar limite estadual:', e);
    }}
    // adicionar ao mapa por padrão para que fique visível
    estadoLayer && estadoLayer.addTo(map);
}}

// Camada: limite municipal (Igarassu) - opcional
var municipalLayer = null;
    if (geojsonMunicipal) {{
    try {{
        municipalLayer = L.geoJSON(geojsonMunicipal, {{
            style: function(f) {{ return {{color:'#984ea3', weight:2, dashArray:'6 6', fillOpacity:0}}; }},
            onEachFeature: function(feature, layer) {{
                var v = feature.properties && (feature.properties.nome || feature.properties.codarea || feature.properties.name);
                if (v) layer.bindPopup('<strong>Município:</strong> ' + v);
            }}
        }});
    }} catch(e) {{
        console.warn('Falha ao adicionar limite municipal:', e);
    }}
    // adicionar ao mapa por padrão
    municipalLayer && municipalLayer.addTo(map);
}}

// Camada: todos os municípios de Pernambuco (opcional)
var municipiosPELayer = null;
if (geojsonMunicipiosPE) {{
    try {{
        municipiosPELayer = L.geoJSON(geojsonMunicipiosPE, {{
            style: function(f) {{ return {{color:'#ff7f00', weight:1, fillOpacity:0}}; }},
            onEachFeature: function(feature, layer) {{
                var nm = feature.properties && (feature.properties.nome || feature.properties.NM_MUNICIP || feature.properties.name);
                if (nm) layer.bindPopup('<strong>Município:</strong> ' + nm);
            }}
        }});
    }} catch(e) {{
        console.warn('Falha ao adicionar camada municípios PE:', e);
    }}
}}

// Camada: biomas (opcional) - destaca Mata Atlântica quando presente
var biomasLayer = null;
if (geojsonBiomas) {{
    try {{
        biomasLayer = L.geoJSON(geojsonBiomas, {{
            style: function(f) {{
                var name = (f.properties && (f.properties.nome || f.properties.NM_BIOMA || f.properties.name)) || '';
                if (name.toLowerCase().indexOf('mata') !== -1) {{
                    return {{color:'#2b8cbe', weight:1.5, fillOpacity:0.06}};
                }}
                return {{color:'#666', weight:1, fillOpacity:0.02}};
            }},
            onEachFeature: function(feature, layer) {{
                var n = feature.properties && (feature.properties.nome || feature.properties.NM_BIOMA || feature.properties.name);
                if (n) layer.bindPopup('<strong>Bioma:</strong> ' + n);
            }}
        }});
    }} catch(e) {{
        console.warn('Falha ao adicionar camada biomas:', e);
    }}
}}

// Controle de camadas — adicione apenas as que existem
var overlays = {{ 'Parcelas': parcelasLayer }};
if (estadoLayer) overlays['Limite Estadual'] = estadoLayer;
if (municipalLayer) overlays['Limite Municipal (Igarassu)'] = municipalLayer;
if (municipiosPELayer) overlays['Municípios (PE)'] = municipiosPELayer;
if (biomasLayer) overlays['Biomas (Mata Atlântica)'] = biomasLayer;

L.control.layers(null, overlays, {{collapsed:false}}).addTo(map);
</script>
</body></html>"""
    with open(path_out, 'w', encoding='utf-8') as f:
        f.write(html)


def main(argv):
    input_file = DEFAULT_INPUT
    out_dir = DEFAULT_OUT
    geojson_file = DEFAULT_GEOJSON
    for i,a in enumerate(argv):
        if a in ('-i','--input') and i+1 < len(argv):
            input_file = argv[i+1]
        if a in ('-o','--out') and i+1 < len(argv):
            out_dir = argv[i+1]
        if a in ('-g','--geojson') and i+1 < len(argv):
            geojson_file = argv[i+1]
    if not os.path.exists(input_file):
        print(f"Arquivo de entrada não encontrado: {input_file}")
        return 2
    os.makedirs(out_dir, exist_ok=True)

    rows = list(read_rows(input_file))
    series, datas = group_metrics(rows)
    series_sp, _ = group_by_species(rows)
    
    # Calcular última data
    ultima_data = max(datas) if datas else ''
    
    # Calcular classificação e alertas para síntese
    classificacao = classificar_estagio_sucessional(series, ultima_data)
    alertas = gerar_alertas(series, ultima_data)
    
    # Gerar arquivos
    relatorio_path = os.path.join(out_dir, 'relatorio.html')
    mapa_path = os.path.join(out_dir, 'mapa.html')
    sintese_path = os.path.join(out_dir, 'sintese_ultima_campanha.csv')
    
    write_relatorio(relatorio_path, series, datas, series_sp, rows)
    # Garantir que temos os limites oficiais adicionais (municipios PE / biomas) — baixar se necessário
    # Tentar baixar malha dos municípios de PE via endpoint direto; se falhar, agregar via lista de municípios
    ok_mun = download_geojson_if_missing('https://servicodados.ibge.gov.br/api/v3/malhas/estados/26/municipios?formato=application/vnd.geo+json', DEFAULT_MUNICIPIOS)
    if not ok_mun:
        download_all_municipios_pe(DEFAULT_MUNICIPIOS)

    # Biomas: a tentativa direta pode falhar — tentar baixar por lista/IDs
    ok_biomas = download_geojson_if_missing('https://servicodados.ibge.gov.br/api/v3/malhas/biomas?formato=application/vnd.geo+json', DEFAULT_BIOMAS)
    if not ok_biomas:
        download_all_biomas(DEFAULT_BIOMAS)

    write_mapa(mapa_path, geojson_file)
    exportar_sintese_csv(series, classificacao, alertas, ultima_data, sintese_path)

    print('Arquivos gerados:')
    print(' -', relatorio_path)
    print(' -', mapa_path)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
