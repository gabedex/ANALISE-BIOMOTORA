# 🎾🏐 Analisador Biomecânico de Tênis e Volêi

Envie o vídeo de um golpe e o app detecta a pose do jogador (MediaPipe), desenha o esqueleto no vídeo,
mostra a curva dos ângulos articulares e calcula a **velocidade da mão** durante o golpe.

## Ainda está sendo atualizado para abranger os dois esportes de forma mais precisa ##

## Como rodar

```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate          # Windows   (Linux/macOS: source .venv/bin/activate)
```
```bash
pip install -r requirements.txt
```
```bash
streamlit run app.py
```

> Se você já tinha instalado `opencv-python` ou `opencv-python-headless`, recrie o ambiente (ou rode
> `pip uninstall -y opencv-python opencv-python-headless opencv-contrib-python` e instale de novo).
> Essas variantes conflitam entre si.

## Rodar diretamente via .bat
> Instalar Python (3.11, 3.12 ou 3.14) (compatíveis e otimizados para o MediaPipe, Streamlit e Plotly)
Ao instalar o Python marcar a opção "Add Python.exe to PATH"
> Clique em "Iniciar_Analisador.bat" para fazer a verificação de arquivos dentro do projeto e iniciar a aba no localhost

Ambiente em que o projeto foi desenvolvido: Python 3.14, streamlit 1.63, mediapipe 1.0.1, numpy 2.5, pandas 3.0.

## Como fazer as gravações

- **Câmera parada**, num tripé ou apoiada. Nada de panorâmica.
- **Corpo inteiro** do jogador em quadro durante todo o golpe.
- **60 fps ou mais** (modo câmera lenta do celular: 120/240 fps). Veja "Limitações".
- Iluminação boa e só o jogador em destaque (o app analisa uma pessoa por vez).
- Para ângulos 2D fiéis, o movimento deve acontecer de frente para a câmera (o ângulo do cotovelo, por
  exemplo, só é fiel se o braço se dobra no plano da imagem).

## O que o app calcula

| Métrica | Como |
|---|---|
| Cotovelo | ângulo ombro–cotovelo–pulso |
| Ombro | ângulo quadril–ombro–cotovelo (elevação do braço) |
| Joelho | ângulo quadril–joelho–tornozelo (180° = perna esticada) |
| Inclinação dos ombros | linha dos ombros vs. horizontal da imagem (com sinal) |
| Separação quadril-ombro | giro dos ombros em relação ao quadril no plano horizontal (3D) |
| **Velocidade da mão** | velocidade do pulso da mão dominante, em m/s e km/h |

Braço e perna analisados são os do lado da **mão dominante** escolhida na barra lateral.
Pontos que o modelo considera pouco visíveis (ex.: braço atrás do corpo) são ignorados.

### Velocidade da mão

Posição do pulso a cada quadro → preenche falhas de até 5 quadros → suaviza (Savitzky-Golay) → deriva no
tempo → norma → m/s e km/h. Dois métodos:

- **3D estimado:** usa as coordenadas em metros que o próprio MediaPipe estima (origem no quadril).
  Não precisa de calibração. Mede a mão **em relação ao corpo**.
- **2D calibrado:** converte pixels em metros usando a altura do jogador (erro típico de 10–15%).
  Inclui o deslocamento do corpo todo, mas só no plano da imagem.

"Golpes detectados" é uma heurística: máximos locais acima de 50% do maior pico, com no mínimo 0,6 s
entre eles.

## Limitações (leia com atenção antes de confiar num número)

- **É a velocidade do pulso, não da raquete nem da bola.** A cabeça da raquete costuma ser bem mais
  rápida. Use o valor para **comparar golpes/evolução** em vídeos filmados do mesmo jeito. Velocidade da
  bola exigiria rastrear a bola, o que este projeto não faz.
- **FPS baixo subestima o pico.** Numa simulação de um golpe de ~0,1 s, o pico medido foi ~73% do real
  a 30 fps, ~95% a 60 fps e ~99% a 120 fps ou mais.
- O modelo incluído (`pose_landmarker.task`, ~5,7 MB) é leve e rápido. Para mais precisão em movimentos
  rápidos, baixe uma versão *full* ou *heavy* na documentação do MediaPipe Pose Landmarker e substitua
  o arquivo (mesmo nome).
- As coordenadas 3D (e portanto a separação quadril-ombro e o método 3D) vêm de uma estimativa do modelo
  a partir de uma única câmera: a profundidade é a parte mais ruidosa.

## Estrutura

```
app.py                  interface Streamlit
pose_landmarker.task    modelo do MediaPipe
src/
  config.py             constantes (índices dos pontos, limites)
  tipos.py              DeteccaoVideo (resultado bruto da detecção)
  pose_detector.py      detecção com MediaPipe (modo vídeo)
  metrics.py            ângulos e cálculo da velocidade (numpy puro)
  utils.py              geometria (ângulos 2D/3D)
  desenho.py            overlays sobre o vídeo
  video_io.py           gravação do vídeo anotado + conversão H.264
tests/                  testes unitários
```

Fluxo: a detecção (etapa cara) roda **uma vez por vídeo**; mudar opções do menu só recalcula as métricas
(rápido) e regrava o vídeo anotado. Vídeos já gerados para uma combinação de opções ficam em cache.

## Como ler o código

Os comentários marcam o que mudou na última manutenção:

- `[NOVO]` = funcionalidade adicionada (velocidade do golpe, seletor destro/canhoto, filtro de visibilidade, etc.)
- `[CORRIGIDO]` = bug da versão anterior que foi consertado (ângulos distorcidos, métrica de tronco, etc.)

Para entender a velocidade do golpe, comece por `src/metrics.py` (seção "VELOCIDADE") e depois `app.py`
(o mapa do fluxo está no topo do arquivo).

## Testes

```bash
python -m unittest discover -s tests -t . -v
```
