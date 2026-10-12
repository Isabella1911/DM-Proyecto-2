"""Recursos compartidos por las páginas: rutas, colores, estilo de gráficas, carga de datos y modelos."""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

APP = Path(__file__).resolve().parent
RAIZ = APP.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import biohub  # noqa: E402  (requiere RAIZ en sys.path)

DEMO = APP / "datos_demo"
EDA = APP / "datos_eda"
RESULTADOS = APP / "resultados_modelos"

# --- Colores -------------------------------------------------------------------
# Paleta categórica de referencia (validada para daltonismo con validate_palette.js):
# el color sigue a la entidad en toda la app y nunca se reutiliza para otra cosa.
COLOR = {
    "A": "#2a78d6",           # modelo A (azul)
    "C": "#eb6834",           # modelo C (naranja)
    "anotacion": "#1baf7a",   # anotación de referencia (aqua)
    "6bba": "#4a3aa7",        # embrión 6bba (violeta)
    "44b6": "#eda100",        # embrión 44b6 (amarillo)
}
# Forma del marcador: segunda codificación, para que la identidad no dependa solo del color
SIMBOLO = {"A": "cross-thin", "C": "x-thin", "anotacion": "circle-open"}
NOMBRE = {"A": "Modelo A · asignación lineal", "C": "Modelo C · btrack", "anotacion": "Anotación"}
TEXTO, TEXTO_2, GRILLA, SUPERFICIE = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"


def estilo(fig, alto=380, leyenda=True):
    """Estilo común: fondo claro, grilla recesiva, texto en tinta neutra, leyenda arriba."""
    con_titulo = bool(fig.layout.title.text)
    fig.update_layout(
        template="plotly_white", height=alto, margin=dict(l=10, r=10, t=90 if con_titulo else 40, b=10),
        paper_bgcolor=SUPERFICIE, plot_bgcolor=SUPERFICIE, font=dict(color=TEXTO, size=13),
        showlegend=leyenda, legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
        hoverlabel=dict(bgcolor="white", font_color=TEXTO),
    )
    if con_titulo:   # el título va arriba del todo; la leyenda queda entre el título y la gráfica
        fig.update_layout(title=dict(x=0, xanchor="left", y=0.98, yanchor="top", font=dict(size=15)))
    fig.update_xaxes(gridcolor=GRILLA, zerolinecolor=GRILLA, title_font_color=TEXTO_2)
    fig.update_yaxes(gridcolor=GRILLA, zerolinecolor=GRILLA, title_font_color=TEXTO_2)
    # Ejes logarítmicos: solo potencias de 10, sin las marcas intermedias que ensucian la lectura
    fig.for_each_yaxis(lambda e: e.update(dtick=1) if e.type == "log" else None)
    fig.for_each_xaxis(lambda e: e.update(dtick=1) if e.type == "log" else None)
    return fig


def hallazgo(texto):
    st.markdown(f"<div style='border-left:3px solid {TEXTO_2};padding:4px 12px;color:{TEXTO_2}'>{texto}</div>",
                unsafe_allow_html=True)


# --- Datos ---------------------------------------------------------------------
@st.cache_data
def tabla(carpeta, nombre):
    ruta = Path(carpeta) / nombre
    return pd.read_csv(ruta) if ruta.exists() else None


@st.cache_data
def indice_demo():
    ruta = DEMO / "indice.json"
    return json.loads(ruta.read_text()) if ruta.exists() else []


def etiqueta_demo(d):
    motivo = "contiene divisiones" if d["criterio"] == "divisiones" else "más células anotadas"
    return f"Embrión {d['embryo_id']} · {motivo} ({d['origen']})"


@st.cache_data
def volumen(nombre, t):
    return biohub.ArregloZarr(DEMO / f"{nombre}.zarr" / "0").instante(t)


@st.cache_data
def forma(nombre):
    return biohub.ArregloZarr(DEMO / f"{nombre}.zarr" / "0").shape


@st.cache_data
def anotacion(nombre):
    nodos, aristas, n_est = biohub.leer_grafo(DEMO / f"{nombre}.geff")
    return nodos, pd.DataFrame(aristas, columns=["source_id", "target_id"]), n_est


# --- Modelos -------------------------------------------------------------------
def btrack_disponible():
    try:
        from btrack import libwrapper
        libwrapper.get_library()
        return True
    except Exception:
        return False


@st.cache_data(show_spinner=False)
def detectar(nombre):
    """Preprocesamiento + detección (común a A y C): normalización, DoG y máximos locales."""
    t0 = time.time()
    det, n_t = biohub.detectar_muestra(DEMO / f"{nombre}.zarr", biohub.PARAMS_A, biohub.PARAMS_A["umbral"])
    return det, n_t, time.time() - t0


@st.cache_data(show_spinner=False)
def enlazar(nombre, modelo):
    det, n_t, seg_det = detectar(nombre)
    t0 = time.time()
    if modelo == "A":
        nodos, aristas = biohub.enlazar(det, n_t, biohub.PARAMS_A)
    else:
        from biohub.enlace_btrack import enlazar_btrack
        nodos, aristas = enlazar_btrack(det, n_t, forma(nombre)[1:], biohub.PARAMS_C)
    seg_enl = time.time() - t0
    gn, ga, n_est = anotacion(nombre)
    metrica = biohub.metrica_aristas(nodos, aristas, gn, ga.to_numpy(), n_est)
    return nodos, aristas, metrica, seg_det, seg_enl


def trayectorias(nodos, aristas):
    """Etiqueta de trayectoria por nodo (componentes conexas del grafo)."""
    n = len(nodos)
    pos = {v: i for i, v in enumerate(nodos["node_id"].to_numpy())}
    src = [pos[s] for s, d in zip(aristas["source_id"], aristas["target_id"]) if s in pos and d in pos]
    dst = [pos[d] for s, d in zip(aristas["source_id"], aristas["target_id"]) if s in pos and d in pos]
    _, etiqueta = connected_components(coo_matrix((np.ones(len(src)), (src, dst)), shape=(n, n)), directed=False)
    return etiqueta


def a_formato_competencia(nombre, nodos, aristas):
    filas_n = pd.DataFrame({"dataset": nombre, "row_type": "node", "node_id": nodos["node_id"],
                            "t": nodos["t"].astype(int), "z": nodos["z"].round().astype(int),
                            "y": nodos["y"].round().astype(int), "x": nodos["x"].round().astype(int),
                            "source_id": -1, "target_id": -1})
    filas_a = pd.DataFrame({"dataset": nombre, "row_type": "edge", "node_id": -1, "t": -1, "z": -1, "y": -1,
                            "x": -1, "source_id": aristas["source_id"], "target_id": aristas["target_id"]})
    tabla_ = pd.concat([filas_n, filas_a], ignore_index=True)
    tabla_.index.name = "id"
    return tabla_.to_csv().encode()


def faltan_datos():
    """Mensaje si no se descomprimieron los datos de la app."""
    faltan = [p.parent.name for p in (DEMO / "indice.json", EDA / "muestras.csv") if not p.exists()]
    if faltan:
        st.error(f"Faltan datos en `app/`: {', '.join(faltan)}. Ver app/README.md (notebook de exportación).")
        return True
    return False
