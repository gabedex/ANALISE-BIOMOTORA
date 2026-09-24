import sys

print(">>> [DEBUG 1] Iniciando app.py...")

import hashlib
import shutil
import tempfile
from dataclasses import astuple
from pathlib import Path

print(">>> [DEBUG 2] Importando pacotes essenciais (OpenCV, NumPy, Pandas)...")
import cv2
import numpy as np
import pandas as pd

print(">>> [DEBUG 3] Importando Plotly...")
import plotly.graph_objects as go

print(">>> [DEBUG 4] Importando Streamlit...")
import streamlit as st

print(">>> [DEBUG 5] Importando módulos internos do projeto (src)...")
from src.config import LADOS, VISIBILIDADE_MIN_PADRAO
from src.desenho import OpcoesExibicao
from src.metrics import calcular_metricas, detectar_fases_golpe, detectar_picos, velocidade_mao
from src.pose_detector import PoseAnalyzer, detectar_video
from src.video_io import renderizar_video

print(">>> [DEBUG 6] Todos os imports foram concluídos com sucesso! Renderizando interface...")

# Configuração da página Streamlit
st.set_page_config(page_title="Analisador Biomecânico de Tênis e Vôlei", layout="wide")
st.title("🎾 Analisador Biomecânico de Tênis e Vôlei")

# ============================================================== MENU LATERAL
sb = st.sidebar
sb.header("⚙️ Opções de Análise")

lado = sb.radio("Mão dominante", list(LADOS), horizontal=True,
                help="Define qual braço e qual perna são analisados.")

min_vis = sb.slider("Confiança mínima do ponto", 0.1, 0.95, VISIBILIDADE_MIN_PADRAO, 0.05,
                    help="Pontos pouco visíveis são ignorados em vez de gerar valores falsos.")

modo_angulo = sb.radio("Ângulos articulares", ["2D (imagem)", "3D (estimado)"], horizontal=True,
                       help="2D mede o ângulo contínuo de 0° a 360°. 3D usa profundidade estimada.")

sb.markdown("---")
sb.subheader("1. Braço dominante")
analisar_braco = sb.checkbox("Ativar análise de braço", value=True)
exibir_cotovelo = exibir_ombro = exibir_pulso = False
if analisar_braco:
    exibir_cotovelo = sb.checkbox("Cotovelo (ângulo)", value=True)
    exibir_ombro = sb.checkbox("Ombro (elevação do braço)", value=True)
    exibir_pulso = sb.checkbox("Pulso/mão (ponto)", value=True)

sb.markdown("---")
sb.subheader("2. Membros inferiores")
analisar_perna = sb.checkbox("Ângulo do joelho (mesmo lado)", value=True)

sb.markdown("---")
sb.subheader("3. Tronco")
analisar_inclinacao = sb.checkbox("Inclinação dos ombros", value=False)
analisar_separacao = sb.checkbox("Separação quadril-ombro (3D)", value=False)

sb.markdown("---")
sb.subheader("4. Velocidade do golpe")
analisar_vel = sb.checkbox("Calcular velocidade da mão", value=True)
metodo_vel = "3d"
altura_cm = 175
janela_ms = 60
if analisar_vel:
    rotulo_metodo = sb.radio("Método", ["3D estimado (sem calibração)", "2D calibrado pela altura"])
    metodo_vel = "3d" if rotulo_metodo.startswith("3D") else "2d"
    if metodo_vel == "2d":
        altura_cm = sb.number_input("Altura do jogador (cm)", 120, 230, 175)
    janela_ms = sb.slider("Suavização (ms)", 20, 200, 60, 10)

# =================================================================== UPLOAD
video_file = st.file_uploader("Faça o upload do vídeo da jogada (MP4, MOV, AVI)",
                              type=["mp4", "mov", "avi"])
if video_file is None:
    st.info("Envie um vídeo para começar. Recomendado: câmera parada e gravado em câmera lenta.")
    st.stop()

ss = st.session_state
conteudo = video_file.getvalue()
video_id = hashlib.md5(conteudo).hexdigest()

if ss.get("video_id") != video_id:
    if ss.get("pasta_tmp"):
        shutil.rmtree(ss["pasta_tmp"], ignore_errors=True)
    pasta = Path(tempfile.mkdtemp(prefix="tenis_"))
    caminho = pasta / f"entrada{Path(video_file.name).suffix.lower() or '.mp4'}"
    caminho.write_bytes(conteudo)
    ss.update(
        video_id=video_id,
        pasta_tmp=str(pasta),
        caminho=str(caminho),
        deteccao=None,
        renders={},
        custom_1_frame=None,
        custom_1_nome="Marcação 1",
        custom_2_frame=None,
        custom_2_nome="Marcação 2"
    )

# ======================================= DETECÇÃO (MediaPipe)
if ss.get("deteccao") is None:
    barra = st.progress(0.0, text="Detectando a pose em cada quadro...")
    try:
        with PoseAnalyzer() as analisador:
            ss["deteccao"] = detectar_video(
                ss["caminho"], analisador,
                progresso=lambda p: barra.progress(p, text=f"Detectando a pose... {p:.0%}"))
    except Exception as e:
        barra.empty()
        st.error(f"Falha ao processar o vídeo: {e}")
        st.stop()
    barra.empty()

det = ss["deteccao"]
taxa = float(det.detectado.mean())

# ==================== MÉTRICAS
df = calcular_metricas(det, lado, modo_angulo.startswith("3D"), min_vis)
ativas = {"cotovelo": exibir_cotovelo, "ombro": exibir_ombro, "joelho": analisar_perna,
          "inclinacao_ombros": analisar_inclinacao, "separacao": analisar_separacao}
for nome, ligada in ativas.items():
    if not ligada:
        df[nome] = np.nan

vel_ms = vel_kmh = None
if analisar_vel:
    vel_ms, aviso_vel = velocidade_mao(det, lado, metodo_vel, altura_cm, janela_ms, min_vis)
    if aviso_vel:
        st.warning(aviso_vel)
    vel_kmh = vel_ms * 3.6
    df["vel_ms"], df["vel_kmh"] = vel_ms, vel_kmh

# ======================= VÍDEO ANOTADO
opc = OpcoesExibicao(cotovelo=exibir_cotovelo, ombro=exibir_ombro, pulso=exibir_pulso,
                     joelho=analisar_perna, inclinacao_ombros=analisar_inclinacao,
                     separacao=analisar_separacao, velocidade=analisar_vel)

chave = repr((lado, min_vis, modo_angulo, astuple(opc), metodo_vel, altura_cm, janela_ms))
renders = ss["renders"]

if chave not in renders:
    if len(renders) >= 4:
        antigo = renders.pop(next(iter(renders)))
        Path(antigo[0]).unlink(missing_ok=True)
    barra = st.progress(0.0, text="Gerando o vídeo anotado...")
    try:
        renders[chave] = renderizar_video(
            ss["caminho"], ss["pasta_tmp"], det, lado, min_vis, opc,
            {nome: df[nome].to_numpy() for nome in ativas}, vel_kmh,
            progresso=lambda p: barra.progress(p, text=f"Gerando o vídeo anotado... {p:.0%}"))
    except Exception as e:
        barra.empty()
        st.error(f"Falha ao gerar o vídeo anotado: {e}")
        st.stop()
    barra.empty()

caminho_video, aviso_video = renders[chave]

# ====================================================== ESTADO E PAINEL DE FASES (4 BOTÕES)
fases = detectar_fases_golpe(df, det=det, lado=lado)
idx_prep_auto = int(fases["preparacao"])
idx_imp_auto = int(fases["impacto"])
total_frames = int(det.n_quadros - 1)

# Inicializações no session_state
if "slider_static" not in st.session_state:
    st.session_state["slider_static"] = idx_imp_auto

if "custom_1_frame" not in st.session_state:
    st.session_state["custom_1_frame"] = None
if "custom_1_nome" not in st.session_state:
    st.session_state["custom_1_nome"] = "Arco e Flecha"

if "custom_2_frame" not in st.session_state:
    st.session_state["custom_2_frame"] = None
if "custom_2_nome" not in st.session_state:
    st.session_state["custom_2_nome"] = "Terminação"

# Callbacks de navegação rápida
def ir_para_armada_auto():
    st.session_state["slider_static"] = idx_prep_auto

def ir_para_impacto_auto():
    st.session_state["slider_static"] = idx_imp_auto

def ir_para_custom_1():
    if st.session_state["custom_1_frame"] is not None:
        st.session_state["slider_static"] = st.session_state["custom_1_frame"]

def ir_para_custom_2():
    if st.session_state["custom_2_frame"] is not None:
        st.session_state["slider_static"] = st.session_state["custom_2_frame"]

def salvar_custom_1():
    st.session_state["custom_1_frame"] = int(st.session_state["slider_static"])

def salvar_custom_2():
    st.session_state["custom_2_frame"] = int(st.session_state["slider_static"])

frame_idx = int(st.session_state["slider_static"])
c1_frame = st.session_state["custom_1_frame"]
c1_nome = st.session_state["custom_1_nome"]
c2_frame = st.session_state["custom_2_frame"]
c2_nome = st.session_state["custom_2_nome"]

# ====================================================== PAINEL LADO A LADO
st.markdown("---")
st.subheader("🎬 Reprodutor de Vídeo vs. 📸 Analisador de Frame")

_, col_midia, _ = st.columns([0.15, 0.7, 0.15])

with col_midia:
    col_video_play, col_frame_congelado = st.columns([1, 1])

    # --- ESQUERDA: Reprodutor de Vídeo Dinâmico
    with col_video_play:
        st.markdown("##### ⏯️ Análise em Vídeo (Dinâmica)")
        st.video(str(caminho_video))
        st.caption(f"**Vídeo:** {det.largura}x{det.altura}px · {det.fps:.1f} fps · {det.n_quadros} quadros")

        st.download_button(
            "⬇️ Baixar MP4",
            Path(caminho_video).read_bytes(),
            file_name="analise_golpe.mp4",
            mime="video/mp4"
        )

    # --- DIREITA: Analisador de Imagem Estática (Painel com 4 Botões)
    with col_frame_congelado:
        st.markdown("##### 🎯 Análise de Imagem (Estática)")
        
        # 4 BOTÕES DE NAVEGAÇÃO RÁPIDA
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            st.button("🔄 Armada (Auto)", on_click=ir_para_armada_auto, key="btn_armada_auto")
        with b2:
            st.button("🎾 Contato (Auto)", on_click=ir_para_impacto_auto, key="btn_impacto_auto")
        with b3:
            rotulo_c1 = f"📍 {c1_nome}" if c1_frame is not None else "📍 Custom 1"
            st.button(rotulo_c1, on_click=ir_para_custom_1, disabled=(c1_frame is None), key="btn_c1_goto")
        with b4:
            rotulo_c2 = f"📍 {c2_nome}" if c2_frame is not None else "📍 Custom 2"
            st.button(rotulo_c2, on_click=ir_para_custom_2, disabled=(c2_frame is None), key="btn_c2_goto")

        cap_frame = cv2.VideoCapture(str(caminho_video))
        cap_frame.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ok_f, frame_bgr = cap_frame.read()
        cap_frame.release()

        if ok_f:
            st.image(frame_bgr, channels="BGR",
                     caption=f"Quadro #{frame_idx} ({det.tempo[frame_idx]:.2f}s)")
        else:
            st.error("Não foi possível carregar o quadro do vídeo.")

        st.slider("Navegar quadro a quadro:", 0, total_frames, key="slider_static")

        # PAINEL DO PROFESSOR: DEFINIR E RENOMEAR OS 2 MARCADORES CUSTOM
        st.markdown("---")
        st.markdown("##### 🏷️ Personalização de Marcadores Extras (Professor)")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.caption("📌 **Marcador Custom 1**")
            st.text_input("Nome 1:", key="custom_1_nome", placeholder="Ex: Arco e Flecha")
            st.button(f"📍 Definir Frame #{frame_idx} como Marcador 1", on_click=salvar_custom_1, key="btn_save_c1")
            if c1_frame is not None:
                st.caption(f"Salvo: **Quadro #{c1_frame}** ({det.tempo[c1_frame]:.2f}s)")

        with col_m2:
            st.caption("📌 **Marcador Custom 2**")
            st.text_input("Nome 2:", key="custom_2_nome", placeholder="Ex: Terminação")
            st.button(f"📍 Definir Frame #{frame_idx} como Marcador 2", on_click=salvar_custom_2, key="btn_save_c2")
            if c2_frame is not None:
                st.caption(f"Salvo: **Quadro #{c2_frame}** ({det.tempo[c2_frame]:.2f}s)")

        st.markdown("---")

        val_cot = df.loc[frame_idx, "cotovelo"]
        val_omb = df.loc[frame_idx, "ombro"]
        val_joe = df.loc[frame_idx, "joelho"]
        val_vel = df.loc[frame_idx, "vel_kmh"] if "vel_kmh" in df.columns else np.nan

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Cotovelo", f"{val_cot:.0f}°" if np.isfinite(val_cot) else "N/A")
        m2.metric("Ombro", f"{val_omb:.0f}°" if np.isfinite(val_omb) else "N/A")
        m3.metric("Joelho", f"{val_joe:.0f}°" if np.isfinite(val_joe) else "N/A")
        if analisar_vel:
            m4.metric("Vel.", f"{val_vel:.1f} km/h" if np.isfinite(val_vel) else "N/A")

        if ok_f:
            _, buffer_img = cv2.imencode('.png', frame_bgr)
            st.download_button(
                label="💾 Baixar Foto (PNG)",
                data=buffer_img.tobytes(),
                file_name=f"analise_frame_{frame_idx}.png",
                mime="image/png"
            )

# Dicionário de Marcadores de Tempo para Inserir nos Gráficos (Plotly)
pontos_tempo_grafico = {
    "Armada (Auto)": (det.tempo[idx_prep_auto], "gray"),
    "Contato (Auto)": (det.tempo[idx_imp_auto], "red"),
}
if c1_frame is not None:
    pontos_tempo_grafico[f"📍 {c1_nome}"] = (det.tempo[c1_frame], "blue")
if c2_frame is not None:
    pontos_tempo_grafico[f"📍 {c2_nome}"] = (det.tempo[c2_frame], "green")

# ====================================================== VELOCIDADE E GRÁFICOS COM MARCADORES PLOTLY
if analisar_vel and vel_kmh is not None and np.isfinite(vel_kmh).any():
    st.markdown("---")
    st.subheader("⚡ Velocidade do golpe (mão dominante)")
    k_max = int(np.nanargmax(vel_kmh))
    picos = detectar_picos(det.tempo, vel_kmh)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pico de velocidade", f"{vel_kmh[k_max]:.0f} km/h")
    c2.metric("Em m/s", f"{vel_ms[k_max]:.1f}")
    c3.metric("Instante do pico", f"{det.tempo[k_max]:.2f} s")
    c4.metric("Golpes detectados", len(picos))

    fig_vel = go.Figure()
    fig_vel.add_trace(go.Scatter(x=det.tempo, y=vel_kmh, mode='lines', name='Velocidade mão (km/h)', line=dict(color='#1f77b4', width=2)))

    for rotulo, (tempo_pt, cor) in pontos_tempo_grafico.items():
        fig_vel.add_vline(x=tempo_pt, line_width=2, line_dash="dash", line_color=cor,
                          annotation_text=rotulo, annotation_position="top left")

    fig_vel.update_layout(xaxis_title="Tempo (s)", yaxis_title="Velocidade (km/h)", margin=dict(l=20, r=20, t=30, b=20), height=350)
    st.plotly_chart(fig_vel, use_container_width=True)

# ====================================================== GRÁFICO DE ÂNGULOS COM MARCADORES PLOTLY
st.markdown("---")
st.subheader("📊 Variação dos ângulos (curva do movimento)")
nomes = {"cotovelo": "Cotovelo (deg)", "ombro": "Ombro (deg)", "joelho": "Joelho (deg)",
         "inclinacao_ombros": "Inclinação ombros (deg)", "separacao": "Separação quadril-ombro (3D)"}

cols = [c for c in nomes if c in df.columns and df[c].notna().any()]
if cols:
    fig_ang = go.Figure()
    for col_nome in cols:
        fig_ang.add_trace(go.Scatter(x=det.tempo, y=df[col_nome], mode='lines', name=nomes[col_nome]))

    for rotulo, (tempo_pt, cor) in pontos_tempo_grafico.items():
        fig_ang.add_vline(x=tempo_pt, line_width=2, line_dash="dash", line_color=cor,
                          annotation_text=rotulo, annotation_position="top left")

    fig_ang.update_layout(xaxis_title="Tempo (s)", yaxis_title="Ângulo (graus)", margin=dict(l=20, r=20, t=30, b=20), height=380)
    st.plotly_chart(fig_ang, use_container_width=True)

# EXPORTAR DADOS
saida = df.drop(columns=[c for c in df.columns if c not in cols + ["quadro", "tempo_s", "vel_ms", "vel_kmh"]])
saida = saida.rename(columns={**nomes, "quadro": "Quadro", "tempo_s": "Tempo (s)",
                              "vel_ms": "Velocidade mão (m/s)", "vel_kmh": "Velocidade mão (km/h)"})

st.download_button("⬇️ Baixar dados (CSV)", saida.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                   file_name="metricas_tenis_volei.csv", mime="text/csv")