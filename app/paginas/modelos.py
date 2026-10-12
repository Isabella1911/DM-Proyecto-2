import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import ndimage

import biohub
from biohub.deteccion import normalizar, reducir_xy
from comun import (COLOR, NOMBRE, SIMBOLO, TEXTO_2, a_formato_competencia, anotacion, btrack_disponible, detectar,
                   enlazar, estilo, etiqueta_demo, faltan_datos, forma, indice_demo, trayectorias, volumen)

st.title("Probar los modelos")
st.caption("Elige una muestra y los modelos. La aplicación prepara la imagen, detecta los núcleos, los enlaza entre "
           "instantes y compara el resultado con la anotación de referencia.")
if faltan_datos():
    st.stop()

demos = indice_demo()
hay_c = btrack_disponible()
c1, c2 = st.columns([3, 2])
demo = c1.selectbox("Muestra", demos, format_func=etiqueta_demo)
opciones = ["A", "C"] if hay_c else ["A"]
modelos = c2.multiselect("Modelos", opciones, default=opciones, format_func=lambda m: NOMBRE[m])
if not hay_c:
    c2.warning("btrack no está disponible en este equipo: el modelo C está desactivado.")
if not modelos:
    st.info("Elige al menos un modelo.")
    st.stop()

nombre = demo["nombre"]
T, Z, Y, X = forma(nombre)
st.caption(f"Recorte de {T} instantes × {Z} × {Y} × {X} vóxeles del video `{demo['origen']}` "
           f"(desde t = {demo['t0']}), con {demo['nodos_anotados']} células y {demo['aristas_anotadas']} enlaces anotados.")

with st.spinner("Detectando núcleos y enlazando trayectorias..."):
    res = {m: enlazar(nombre, m) for m in modelos}
gn, ga, n_est = anotacion(nombre)

# --- Preprocesamiento (automático; se puede ver si interesa) -------------------
with st.expander("¿Qué hace la aplicación con la muestra? (preprocesamiento)"):
    st.markdown(
        "1. **Normaliza** cada instante con sus propios percentiles 1 y 99.9, porque el brillo cambia entre videos y "
        "en el tiempo.\n"
        "2. **Promedia bloques de 2×2 en XY**, para que el vóxel quede casi isotrópico (1.6 × 0.8 × 0.8 µm).\n"
        "3. Aplica una **diferencia de gaussianas** con σ = 2.5 µm, que realza objetos del tamaño de un núcleo y resta el "
        "fondo.\n"
        "4. Los **máximos locales** de esa respuesta son los centros de los núcleos.")
    tp = st.slider("Instante a inspeccionar", 0, T - 1, 0, key="t_prep")
    v = volumen(nombre, tp)
    p = biohub.PARAMS_A
    vr = reducir_xy(normalizar(v), p["reduccion_xy"])
    vox = biohub.VOXEL_UM * np.array([1, p["reduccion_xy"], p["reduccion_xy"]])
    s1 = p["sigma_um"] / vox
    dog = ndimage.gaussian_filter(vr, s1) - ndimage.gaussian_filter(vr, s1 * p["k_dog"])
    cols = st.columns(3)
    for col, img, titulo in zip(cols, [v.max(axis=0), normalizar(v).max(axis=0), dog.max(axis=0)],
                                ["1. Imagen original", "2. Normalizada", "3. Diferencia de gaussianas"]):
        fig = px.imshow(img, color_continuous_scale="gray", origin="upper")
        fig.update_layout(coloraxis_showscale=False, title=titulo)
        fig.update_xaxes(showticklabels=False); fig.update_yaxes(showticklabels=False)
        col.plotly_chart(estilo(fig, 300, leyenda=False), width="stretch")
    st.caption("Proyección de máxima intensidad sobre Z.")

# --- Resultados ---------------------------------------------------------------------
st.subheader("Resultado")
cols = st.columns(len(modelos))
for col, m in zip(cols, modelos):
    nodos, aristas, met, seg_det, seg_enl = res[m]
    col.markdown(f"<span style='color:{COLOR[m]};font-size:1.3em'>■</span> **{NOMBRE[m]}**", unsafe_allow_html=True)
    a, b, c = col.columns(3)
    a.metric("Jaccard ajustado", f"{met['jaccard_ajustado']:.3f}", help="Métrica oficial de aristas (0 a 1, más es mejor)")
    b.metric("Núcleos anotados encontrados", f"{100 * met['recall_nodos']:.0f}%")
    c.metric("Tiempo", f"{seg_det + seg_enl:.1f} s", help=f"detección {seg_det:.1f} s + enlace {seg_enl:.1f} s")
    col.caption(f"{len(nodos):,} núcleos detectados · {len(aristas):,} enlaces · "
                f"{met['tp']} aciertos, {met['fp']} enlaces erróneos, {met['fn']} omitidos")

# --- Visor ---------------------------------------------------------------------------
st.subheader("Visor")
c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
t = c1.slider("Instante", 0, T - 1, min(5, T - 1))
estela = c2.slider("Estela (instantes previos)", 0, 10, 4)
m_vis = c3.radio("Trayectorias de", modelos, format_func=lambda m: f"Modelo {m}", horizontal=True,
                 help="Los dos modelos comparten las detecciones; lo que cambia es cómo las enlazan")
ver_anot = c4.toggle("Mostrar anotación", value=True)

mip = volumen(nombre, t).max(axis=0)
fig = px.imshow(mip, color_continuous_scale="gray", origin="upper",
                zmin=float(np.percentile(mip, 1)), zmax=float(np.percentile(mip, 99.5)))
fig.update_layout(coloraxis_showscale=False)
det_t = res[modelos[0]][0]
det_t = det_t[det_t["t"] == t]
fig.add_trace(go.Scatter(x=det_t["x"], y=det_t["y"], mode="markers", name="Núcleos detectados",
                         marker=dict(symbol="cross-thin", size=8, color="white", line=dict(width=1.5, color="white")),
                         hovertemplate="detección (%{x:.0f}, %{y:.0f})<extra></extra>"))
for m in [m_vis]:
    nodos, aristas = res[m][0], res[m][1]
    etiqueta = trayectorias(nodos, aristas)
    n = nodos.assign(tray=etiqueta)
    vivas = set(n.loc[n["t"] == t, "tray"])
    tramo = n[n["tray"].isin(vivas) & n["t"].between(t - estela, t)].sort_values(["tray", "t"])
    xs, ys = [], []
    for _, g in tramo.groupby("tray"):
        if len(g) > 1:
            xs += g["x"].tolist() + [None]
            ys += g["y"].tolist() + [None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", name=f"Trayectorias · {NOMBRE[m]}",
                             line=dict(width=2, color=COLOR[m]), hoverinfo="skip"))
if ver_anot:
    g = gn[gn["t"] == t]
    fig.add_trace(go.Scatter(x=g["x"], y=g["y"], mode="markers", name="Anotación",
                             marker=dict(symbol=SIMBOLO["anotacion"], size=16, color=COLOR["anotacion"],
                                         line=dict(width=2, color=COLOR["anotacion"])),
                             hovertemplate="célula anotada (%{x:.0f}, %{y:.0f})<extra></extra>"))
fig.update_xaxes(showticklabels=False, range=[0, X - 1]); fig.update_yaxes(showticklabels=False, range=[Y - 1, 0])
st.plotly_chart(estilo(fig, 620), width="stretch")
st.caption("Proyección de máxima intensidad sobre Z en el instante elegido. Las líneas muestran por dónde pasó cada "
           "célula en los instantes previos según el modelo elegido; los círculos son las células anotadas.")

# --- Trayectorias en 3D --------------------------------------------------------------
st.subheader("Trayectorias en el espacio")
c1, c2 = st.columns([2, 3])
m3 = c1.radio("Modelo", modelos, format_func=lambda m: NOMBRE[m], horizontal=True)
min_len = c2.slider("Longitud mínima de la trayectoria (instantes)", 2, T, min(10, T))
fig = go.Figure()


def trazo_3d(nodos, aristas, nombre_traza, color, ancho):
    n = nodos.assign(tray=trayectorias(nodos, aristas))
    n = n[n.groupby("tray")["t"].transform("size") >= min_len].sort_values(["tray", "t"])
    um = n[["z", "y", "x"]].to_numpy() * biohub.VOXEL_UM
    n = n.assign(z_um=um[:, 0], y_um=um[:, 1], x_um=um[:, 2])
    xs, ys, zs = [], [], []
    for _, g in n.groupby("tray"):
        xs += g["x_um"].tolist() + [None]; ys += g["y_um"].tolist() + [None]; zs += g["z_um"].tolist() + [None]
    fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode="lines", name=nombre_traza,
                               line=dict(width=ancho, color=color), hoverinfo="skip"))
    return n["tray"].nunique()


k = trazo_3d(res[m3][0], res[m3][1], NOMBRE[m3], COLOR[m3], 3)
if ver_anot:
    trazo_3d(gn, ga, "Anotación", COLOR["anotacion"], 6)
fig.update_layout(scene=dict(xaxis_title="X (µm)", yaxis_title="Y (µm)", zaxis_title="Z (µm)",
                             aspectmode="data"))
st.plotly_chart(estilo(fig, 560), width="stretch")
st.caption(f"{k} trayectorias de al menos {min_len} instantes. La anotación cubre solo una parte de las células, así "
           "que muchas trayectorias del modelo no tienen pareja anotada (y eso no se cuenta como error).")

# --- Comparación y descarga ----------------------------------------------------------
st.subheader("Comparación en esta muestra")
filas = []
for m in modelos:
    met = res[m][2]
    filas += [{"modelo": NOMBRE[m], "clave": m, "tipo": tipo, "enlaces": met[k_]}
              for tipo, k_ in [("aciertos", "tp"), ("erróneos", "fp"), ("omitidos", "fn")]]
d = pd.DataFrame(filas)
fig = px.bar(d, x="tipo", y="enlaces", color="modelo", barmode="group", text="enlaces",
             color_discrete_map={NOMBRE[m]: COLOR[m] for m in modelos}, labels={"tipo": ""})
fig.update_traces(textposition="outside", marker_line_width=0)
st.plotly_chart(estilo(fig, 340), width="stretch")

c = st.columns(len(modelos))
for col, m in zip(c, modelos):
    col.download_button(f"Descargar predicción · {NOMBRE[m]} (CSV)", a_formato_competencia(nombre, *res[m][:2]),
                        file_name=f"{nombre}_modelo_{m}.csv", mime="text/csv", width="stretch")
st.caption("El CSV usa el formato de envío de la competencia (filas de nodos y de aristas).")
