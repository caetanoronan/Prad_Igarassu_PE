# PRAD – Programa de Recuperação de Áreas Degradadas (Simulado – Pernambuco)

Este documento é um protótipo para portfólio. Todos os dados são simulados para demonstrar estrutura, métodos e indicadores.

## 1. Identificação
- Empreendimento/Imóvel: Projeto Simulado "Mata Alta"
- Responsável legal: Simulado LTDA (CNPJ 00.000.000/0000-00)
- Responsável técnico: Eng. Florestal(a) Nome Sobrenome – CREA 0000000/PE (ART simulada)
- Localização: Igarassu/PE - Zona Rural (coordenadas aproximadas -7.8340, -34.9060)
- Área total (ha): 15 | Área a recuperar (ha): 12 | APP: 5 ha | RL: 7 ha | Outras: 0 ha

## 2. Base legal e enquadramento
- Situação: APP (margens de curso d’água) e Reserva Legal em propriedade ≤ 4 módulos fiscais (simulada)
- Fundamentação: Lei 12.651/2012 (Código Florestal) e normas estaduais aplicáveis
- Observação: uso intercalado de exóticas perenes até 50% permitido nos termos do Código para a situação descrita; neste plano, adota-se uso de exóticas em até 30% apenas na RL, com desbaste programado

## 3. Caracterização da área
- Bioma e clima: Mata Atlântica (Zona da Mata), tropical úmido, chuvas no outono–inverno
- Relevo e topografia: suavemente ondulado; declividades 5–18%
- Solos: Argissolos distróficos, textura média, baixa saturação de bases
- Hidrografia e APPs: faixa ciliar de 30 m em ambos os lados de curso d’água perene (5 ha)
- Uso atual e passivos: pastagem degradada com presença de braquiária e áreas pontuais de erosão laminar

## 4. Diagnóstico da degradação
- Degradação: supressão de vegetação nativa, compactação, invasão por gramíneas exóticas
- Regeneração natural: presente em manchas (1–2 ind/m²) próximas a fragmentos; serapilheira moderada
- Invasoras: Urochloa spp. (40–60% de cobertura inicial), Pontos com leucena pontual
- Paisagem: fragmentos a 250–400 m; conectividade moderada

## 5. Objetivos e metas (SMART)
- Objetivo geral: restabelecer estrutura e funções ecológicas compatíveis com estágio médio de regeneração em 24 anos
- Metas:
  - 2 anos: sobrevivência ≥ 80%; cobertura de copas ≥ 60%; invasoras ≤ 20%
  - 5 anos: dossel contínuo ≥ 70%; riqueza ≥ 40 spp/ha; presença de regeneração natural
  - 10 anos: riqueza ≥ 60 spp/ha; estabilidade estrutural; invasoras ≤ 10%
  - 24 anos: indicadores atendidos; transição para manutenção mínima

## 6. Metodologia de recuperação
Estratégia combinada (PN + CRN) com arranjos diferenciados entre APP e RL, e uso intercalado de exóticas perenes de baixo risco apenas na RL (≤ 30%) com desbaste programado.

### 6.1 Condução de regeneração natural (CRN) – APP e manchas na RL
- Cercamento e aceiros; exclusão de gado e prevenção de fogo
- Manejo inicial de invasoras: 2 capinas químico-mecânicas dirigidas/ano (conforme autorização)
- Nucleação: ilhas de galharia, transposição de serapilheira e poleiros artificiais
- Obras conservacionistas: bacias de captação em contorno e cobertura morta
- Enriquecimento pontual em lacunas com baixa densidade

### 6.2 Plantio de espécies nativas (PN) – lacunas e RL
- Preparo do solo: subsolagem em nível; coveamento 40×40×40 cm
- Lista de espécies: ver `dados/especies_PE_mata_atlantica.csv` (anexo). Proporção sugerida: 50% pioneiras, 35% secundárias, 15% clímax; incluir leguminosas fixadoras e frutíferas
- Arranjo e espaçamento: 3×2 m nas lacunas; linhas em nível
- Época de plantio: início das chuvas; replantios em 3–6 e 12 meses
- Controle: formigas cortadeiras (rodadas quinzenais no 1º trimestre); invasoras conforme metas

### 6.3 RL com intercalado de perenes exóticas (≤ 30% da área)
- Desenho: linhas alternadas com nativas, mantendo luz para nativas
- Critérios de seleção: baixo risco invasivo; foco em sombreamento e biomassa
- Transição: desbaste/clareamento a partir do 6º–8º ano, priorizando dossel nativo

## 7. Plano de execução
- Insumos e serviços: conforme `planilhas/modelo_custos.csv`
- Equipe e segurança: equipe de campo 6–8 pessoas; EPIs completos; treinamento de brigada
- Logística: água para irrigação emergencial (somente plantio), acesso por estradas vicinais

## 8. Cronograma físico-financeiro
- 0–6 meses: licenças, cercamento, aceiros, preparo de solo, aquisição de mudas
- 6–24 meses: plantio, 4–6 capinas/coroamentos no 1º ano; 2–4 no 2º; replantios
- 3–5 anos: fechamento do dossel; manutenção decrescente; enriquecimento final
- 6–10 anos: estabilidade; início dos desbastes na RL
- 11–24 anos: consolidação; monitoramento anual/bianual

## 9. Monitoramento e indicadores
- Parcelas permanentes: 2 parcelas de 20×20 m por talhão (simulação)
- Indicadores: sobrevivência, riqueza, altura/diâmetro médios, cobertura de copas, cobertura de invasoras, erosão
- Periodicidade: 6, 12, 24 meses; anual até 5 anos; bianual de 6–24 anos
- Coleta: `portfolio/Simulado_PE/monitoramento_simulado.csv`
- Processamento: `scripts/indicadores_prad.py`

## 10. Gestão adaptativa e contingências
- Riscos: estiagens prolongadas; fogo; reinfestação por braquiária; herbivoria
- Respostas: irrigação emergencial; brigada/aceiros; janelas de controle de invasoras; protetores físicos
- Reserva de contingência: 15% do orçamento

## 11. Orçamento
- Ver `planilhas/modelo_custos.csv` (ajustar quantidades e preços locais)

## 12. Anexos
- Listas de espécies (`dados/especies_PE_mata_atlantica.csv`)
- Planilhas de monitoramento e resultados (`portfolio/Simulado_PE/monitoramento_simulado.csv`, `saidas/indicadores_resumo.csv`)
- Fotos georreferenciadas: não aplicável nesta simulação
