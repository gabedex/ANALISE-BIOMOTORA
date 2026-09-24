# Changelog

Todas as mudanças notáveis deste projeto são registradas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). As categorias
usadas são: `Adicionado`, `Corrigido`, `Alterado`, `Removido` e `Conhecido` (bugs identificados
e ainda não resolvidos). Isso é o mesmo vocabulário dos comentários `[NOVO]`/`[CORRIGIDO]` que
já existem espalhados pelo código — o changelog é só o resumo, em ordem cronológica, do que
esses comentários contam arquivo por arquivo.

## Como manter isto atualizado

Toda vez que mexer em `app.py` ou em qualquer arquivo de `src/`, adicione uma linha aqui, na
seção `[Não lançado]`, na categoria certa. Quando fechar uma versão (por exemplo, para distribuir
o `.bat` para os alunos), renomeie `[Não lançado]` para `[X.Y.Z] - AAAA-MM-DD` e comece uma seção
`[Não lançado]` nova, vazia, no topo.

---

## [Não lançado]

Sem pendências conhecidas no momento.

---

## [1.0.1] - 2026-09-22 — correção dos bugs conhecidos da v1.0.0

### Corrigido
- **`calcular_angulo_360` usado para medir flexão de articulação**: em `calcular_metricas`
  (`src/metrics.py`), o modo "2D (imagem)" usava `calcular_angulo_360` para Cotovelo/Ombro/
  Joelho. Por ser um ângulo ORIENTADO, o mesmo grau de flexão dava números diferentes conforme o
  lado para onde a articulação dobrava (ex.: 135° dobrando para cima, 225° dobrando para baixo —
  a mesma dobra física). Trocado por `calcular_angulo` (interior, sempre 0°-180°, o mesmo valor
  não importa a direção) nos dois modos (2D e 3D) — só a fonte das coordenadas muda entre eles
  agora. `calcular_angulo_360` continua em `src/utils.py`, documentada como não-recomendada para
  esse uso, disponível para um caso futuro em que a direção do giro importe de verdade.
- **`np.argmax`/`np.argmin` com `NaN` em `detectar_fases_golpe`**: tanto a busca do quadro de
  "Contato" (`np.argmin` sobre a posição Y do pulso) quanto a de "Armada" (`np.argmax` sobre o
  score de recuo) podiam "grudar" num quadro qualquer sempre que houvesse um `NaN` na janela de
  busca (ponto não detectado naquele instante) — sem nenhum aviso, os botões "Armada (Auto)" e
  "Contato (Auto)" podiam levar para o quadro errado. Corrigido filtrando os `NaN` antes de cada
  busca (ou substituindo por `-inf`, conforme o caso), com um retorno de segurança para quando
  não sobra nenhum quadro confiável na janela.
- **Valor padrão de `lado` em `detectar_fases_golpe`**: era `"DIREITO"`, que não existe em
  `LADOS` (as chaves são `"Destro"`/`"Canhoto"`). Não quebrava porque `app.py` sempre passa
  `lado=lado` explicitamente, mas travaria com `KeyError` numa chamada futura sem esse argumento.
  Corrigido para `"Destro"`.

### Adicionado
- 9 testes cobrindo `calcular_angulo_360` (incluindo o comportamento orientado documentado acima)
  e `detectar_fases_golpe` (incluindo os dois cenários de `NaN` corrigidos), em
  `tests/test_utils.py` e `tests/test_metrics.py`. Total: 37 testes automatizados no projeto.

---



## [1.0.0] - 2026-09-22 — "ANALISE BIOMOTORA"

Renomeação do projeto (de `PROJETO` para `ANALISE BIOMOTORA`) e expansão bem além do módulo de
velocidade: navegação manual pelos quadros, marcadores personalizados e gráficos interativos.

### Adicionado
- `detectar_fases_golpe` (`src/metrics.py`): tenta localizar automaticamente os quadros de
  "Armada" (preparação) e "Contato" (impacto) do golpe, combinando a velocidade da mão com a
  posição do pulso/cotovelo/ombro.
- Painel lado a lado: player de vídeo (dinâmico) ao lado de um analisador de quadro estático,
  com um slider para navegar quadro a quadro.
- Botões de navegação rápida: "Armada (Auto)", "Contato (Auto)" e dois marcadores customizáveis
  ("Marcação 1"/"Marcação 2") que o professor pode nomear e salvar num quadro qualquer.
- Botão "💾 Baixar Foto (PNG)" do quadro congelado.
- Gráficos de velocidade e de ângulos migrados para Plotly, com linhas verticais marcando os
  eventos (armada, contato, marcadores customizados) diretamente no gráfico.
- `calcular_angulo_360` (`src/utils.py`): ângulo orientado (0°–360°) no plano da imagem — ver
  limitação em "Conhecido", acima.
- `Iniciar_Analisador.bat`: launcher para Windows que detecta o Python instalado, instala as
  dependências (`requirements.txt`) e sobe o Streamlit — pensado para alguém sem experiência
  técnica abrir o app com um duplo clique.
- Dependência `plotly` em `requirements.txt`.

### Alterado
- O modo "2D (imagem)" do ângulo articular passou a usar `calcular_angulo_360` em vez de
  `calcular_angulo` (ver limitação em "Conhecido").

---

## [0.2.0] - 2026-09-22 — comentários explicativos

Nenhuma mudança de comportamento — só documentação. Todo o código recebeu comentários marcados
com `[NOVO]` (funcionalidade adicionada) e `[CORRIGIDO]` (bug da versão anterior consertado), e o
`app.py` ganhou um mapa do fluxo no topo do arquivo.

### Adicionado
- Comentários `[NOVO]`/`[CORRIGIDO]` em todos os arquivos de `src/` e em `app.py`.
- Seção "Como ler o código" no `README.md`.

---

## [0.1.1] - 2026-09-21 — velocidade do golpe

### Adicionado
- Cálculo da velocidade da mão dominante (`velocidade_mao`, `src/metrics.py`), em dois métodos:
  - **3D estimado**: usa as coordenadas em metros que o MediaPipe já estima, sem calibração.
  - **2D calibrado**: converte pixels em metros a partir da altura informada do jogador.
- Suavização Savitzky-Golay (`suavizar`) e preenchimento de lacunas curtas (`preencher_lacunas`)
  antes de derivar a posição, para reduzir o ruído da detecção sem achatar o pico de velocidade.
- Detecção de picos de velocidade (`detectar_picos`) — um pico por golpe.
- Painel "⚡ Velocidade do golpe" no `app.py`, com o pico em km/h e m/s, o instante do pico e uma
  tabela com um golpe por linha.
- Exportação dos dados (CSV) e do vídeo anotado, com cache por combinação de opções do menu
  (mudar um checkbox não repete a detecção de pose, que é a etapa mais lenta).
- 28 testes automatizados cobrindo geometria (`test_utils.py`) e a matemática da velocidade
  (`test_metrics.py`).

### Corrigido
- **Ângulos distorcidos**: `calcular_angulo` recebia coordenadas normalizadas (0–1) do MediaPipe;
  como X é dividido pela largura e Y pela altura, o ângulo saía deformado em vídeos não quadrados
  (um ângulo real de 90° podia virar 121° ou 58°, dependendo da proporção do vídeo). Corrigido
  para trabalhar sempre em pixels (ou metros).
- **Métrica de tronco**: a função antiga de "rotação de tronco" dava 180° com a pessoa de frente
  para a câmera e ombros nivelados, e 0° de costas — e usava `abs()`, perdendo o sinal da
  inclinação. Virou duas métricas: `calcular_inclinacao_ombros` (2D, com sinal, não depende de
  frente/costas) e `calcular_separacao_quadril_ombro` (3D, a rotação de verdade).
- **Lado fixo**: o braço e a perna analisados eram sempre os do lado direito, mesmo com o menu
  dizendo "Braço Dominante". Adicionado o seletor Destro/Canhoto (`LADOS` em `src/config.py`).
- **Pontos pouco visíveis**: agora viram `NaN` em vez de gerar um valor a partir de uma posição
  "chutada" pelo modelo.
- **Reprocessamento a cada clique**: a detecção de pose (MediaPipe) passou a rodar uma única vez
  por vídeo, guardada em `st.session_state`; mudar uma opção do menu só recalcula as métricas e
  regrava o vídeo anotado, não refaz a detecção inteira.
- **Modo vídeo do MediaPipe**: trocado de detecção quadro a quadro (IMAGE) para o modo VIDEO, que
  rastreia a pessoa entre os quadros — curvas mais estáveis.
- **FPS truncado**: `int(fps)` truncava 29.97 para 29; o eixo do tempo "derivava" ao longo do
  vídeo. Corrigido para usar o valor float.
- **Caminho do modelo relativo**: só funcionava rodando da raiz do projeto; agora é resolvido a
  partir da localização do próprio arquivo.
- **Conversão de vídeo silenciosa**: se a conversão para H.264 falhasse, o app entregava um
  arquivo que o navegador não toca, sem avisar. Agora mostra um aviso.
- **Arquivos temporários nunca apagados**: corrigido.

### Removido
- Pastas `data/inputs` e `data/outputs` (vazias, não usadas pelo código).
- Dependência de `moviepy` (substituída por `imageio-ffmpeg`, já usado para outra coisa).

---

## [0.1.0] - antes das manutenções acima

Estado inicial recebido para análise: MVP funcional com Streamlit + MediaPipe, mas com os bugs
listados na versão 0.1.1 acima (ângulos distorcidos, métrica de tronco incorreta, lado sempre
direito, reprocessamento a cada clique, entre outros). Sem testes automatizados. O `.zip`
original enviado incluía a `.venv` inteira (~692 MB descompactados).
