import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from comun import COLOR, EDA, TEXTO_2, estilo, faltan_datos, hallazgo, tabla

st.title("Explorar los datos")
st.caption("Conjunto de entrenamiento completo después de la limpieza: 199 videos de 100 instantes, con las "
           "coordenadas ya convertidas a micras. Cada pestaña muestra un hallazgo y la decisión de modelado que motivó.")
if faltan_datos():
    st.stop()

muestras, nodos, aristas = tabla(EDA, "muestras.csv"), tabla(EDA, "nodos.csv.gz"), tabla(EDA, "aristas.csv.gz")
linajes, intensidad, perfiles = tabla(EDA, "linajes.csv.gz"), tabla(EDA, "intensidad.csv"), tabla(EDA, "perfiles_z.csv.gz")

EMB = [e for e in ["6bba", "44b6"] if e in set(muestras["embryo_id"])]
elegidos = st.multiselect("Embriones", EMB, default=EMB, help="Filtra todas las gráficas de esta página")
if not elegidos:
    st.info("Elige al menos un embrión.")
    st.stop()
f = lambda d: d[d["embryo_id"].isin(elegidos)]
muestras, nodos, aristas, linajes, intensidad, perfiles = map(f, [muestras, nodos, aristas, linajes, intensidad, perfiles])
COLORES = {e: COLOR[e] for e in EMB}
ORDEN = {"embryo_id": [e for e in EMB if e in elegidos]}
NEUTRO = "#7a7974"   # series únicas sin identidad (no compiten con los colores de modelos o embriones)

tabs = st.tabs(["Variables", "Anotación dispersa", "Movimiento", "Deriva", "Divisiones y linajes", "Imagen"])

# --- Variables -----------------------------------------------------------------
with tabs[0]:
    st.subheader("Las tablas del análisis")
    st.markdown("Los grafos de referencia (`.geff`) se convirtieron en cuatro tablas con distinta unidad de observación.")
    diccionario = pd.DataFrame([
        ("muestras", "sample, embryo_id", "categórica", "video (campo de visión) y embrión de origen"),
        ("muestras", "n_nodos, n_estimado", "numérica", "células anotadas y estimación del total de células del video"),
        ("muestras", "densidad_pct", "numérica", "% de células anotadas sobre las estimadas"),
        ("muestras", "deriva_dz/dy/dx_um", "numérica", "desplazamiento medio por instante en cada eje (µm)"),
        ("nodos", "t, z_um, y_um, x_um", "numérica", "instante y centro del núcleo en micras"),
        ("nodos", "in_degree, out_degree", "numérica discreta", "enlaces entrantes / salientes (2 salientes = división)"),
        ("aristas", "dz_um, dy_um, dx_um, dist_um", "numérica", "desplazamiento de la célula entre dos instantes consecutivos"),
        ("aristas", "sale_de_division", "binaria", "el enlace parte de una célula que se divide"),
        ("linajes", "n_nodos, duracion, n_divisiones", "numérica", "tamaño, duración (instantes) y divisiones de cada trayectoria"),
    ], columns=["tabla", "variable", "tipo", "descripción"])
    st.dataframe(diccionario, hide_index=True, width="stretch")
    c = st.columns(4)
    c[0].metric("Muestras", f"{len(muestras):,}")
    c[1].metric("Nodos (células anotadas)", f"{len(nodos):,}")
    c[2].metric("Aristas (enlaces)", f"{len(aristas):,}")
    c[3].metric("Linajes", f"{len(linajes):,}")
    cual = st.radio("Ver tabla", ["muestras", "nodos", "aristas", "linajes"], horizontal=True)
    datos = {"muestras": muestras, "nodos": nodos, "aristas": aristas, "linajes": linajes}[cual]
    st.dataframe(datos.head(5000), hide_index=True, width="stretch", height=320)
    st.caption(f"Se muestran hasta 5,000 de {len(datos):,} filas.")
    with st.expander("Estadística descriptiva"):
        st.dataframe(datos.describe().T.round(3), width="stretch")

# --- Anotación dispersa -------------------------------------------------------
with tabs[1]:
    st.subheader("Solo una pequeña parte de las células está anotada")
    c1, c2 = st.columns([3, 2])
    fig = px.scatter(muestras, x="n_estimado", y="n_nodos", color="embryo_id", color_discrete_map=COLORES,
                     category_orders=ORDEN, hover_name="sample",
                     hover_data={"densidad_pct": ":.2f", "embryo_id": False},
                     labels={"n_estimado": "células estimadas en el video", "n_nodos": "células anotadas"})
    fig.update_traces(marker=dict(size=9, line=dict(width=1, color="white")))
    c1.plotly_chart(estilo(fig, 400), width="stretch")
    fig = px.box(muestras, x="embryo_id", y="densidad_pct", color="embryo_id", color_discrete_map=COLORES,
                 category_orders=ORDEN, points="all", hover_name="sample",
                 labels={"densidad_pct": "% de células anotadas", "embryo_id": "embrión"})
    c2.plotly_chart(estilo(fig, 400, leyenda=False), width="stretch")
    dens = 100 * muestras["n_nodos"].sum() / muestras["n_estimado"].sum()
    hallazgo(f"Está anotado el <b>{dens:.1f}%</b> de las células estimadas, con mucha variación entre videos y entre "
             f"embriones. <b>Decisión:</b> las detecciones sin pareja anotada no se tratan como errores, y los modelos "
             f"detectan todas las células, no solo las anotadas.")

# --- Movimiento -------------------------------------------------------------------
with tabs[2]:
    st.subheader("Las células se mueven poco entre instantes")
    log = st.toggle("Escala logarítmica en el conteo", value=True)
    p99 = aristas["dist_um"].quantile(.99)
    fig = px.histogram(aristas, x="dist_um", color="embryo_id", color_discrete_map=COLORES, category_orders=ORDEN,
                       nbins=120, barmode="overlay", opacity=.65, log_y=log,
                       labels={"dist_um": "desplazamiento entre instantes consecutivos (µm)", "embryo_id": "embrión"})
    fig.update_yaxes(title_text="número de enlaces")
    fig.add_vline(x=p99, line_dash="dash", line_color=TEXTO_2,
                  annotation_text=f"p99 = {p99:.1f} µm → radio de enlace", annotation_position="top right")
    st.plotly_chart(estilo(fig, 380), width="stretch")
    q = aristas.groupby("embryo_id")["dist_um"].quantile([.5, .95, .99]).unstack().round(2)
    q.columns = ["mediana (µm)", "p95 (µm)", "p99 (µm)"]
    st.dataframe(q, width="stretch")
    hallazgo(f"La mitad de los enlaces mide menos de {aristas['dist_um'].median():.1f} µm y el 99% menos de "
             f"{p99:.1f} µm, con valores parecidos en ambos embriones. <b>Decisión:</b> el enlace de los dos modelos "
             f"solo considera pares a menos de ~8.4 µm.")

# --- Deriva -------------------------------------------------------------------------
with tabs[3]:
    st.subheader("El tejido se desplaza en una dirección preferente")
    d = muestras.melt(id_vars=["sample", "embryo_id"], value_vars=["deriva_dz_um", "deriva_dy_um", "deriva_dx_um"],
                      var_name="eje", value_name="media_um")
    d["eje"] = d["eje"].map({"deriva_dz_um": "Z", "deriva_dy_um": "Y", "deriva_dx_um": "X"})
    fig = px.box(d, x="eje", y="media_um", color="embryo_id", color_discrete_map=COLORES, category_orders=ORDEN,
                 points="all", hover_name="sample",
                 labels={"media_um": "desplazamiento medio por instante (µm)", "eje": "eje", "embryo_id": "embrión"})
    fig.add_hline(y=0, line_color=TEXTO_2, line_width=1)
    st.plotly_chart(estilo(fig, 400), width="stretch")
    neg = (aristas.loc[aristas["dz_um"] != 0, "dz_um"] < 0).mean()
    hallazgo(f"El {100 * neg:.0f}% de los pasos en Z van hacia Z negativo: hay una deriva sistemática que varía entre "
             f"videos. <b>Decisión:</b> el modelo A estima la deriva de cada instante y la descuenta antes de enlazar "
             f"(mejora el Jaccard de 0.734 a 0.745).")

# --- Divisiones y linajes ----------------------------------------------------
with tabs[4]:
    st.subheader("Las divisiones son raras y las células hijas saltan")
    c1, c2 = st.columns(2)
    div = muestras.groupby("embryo_id", as_index=False).agg(divisiones=("n_divisiones", "sum"), nodos=("n_nodos", "sum"))
    div["por cada 1,000 células"] = 1000 * div["divisiones"] / div["nodos"]
    fig = px.bar(div, x="embryo_id", y="por cada 1,000 células", color="embryo_id", color_discrete_map=COLORES,
                 category_orders=ORDEN, text="divisiones", labels={"embryo_id": "embrión"})
    fig.update_traces(texttemplate="%{text} divisiones", textposition="outside", marker_line_width=0)
    c1.plotly_chart(estilo(fig, 360, leyenda=False), width="stretch")
    a = aristas.assign(tipo=np.where(aristas["sale_de_division"], "sale de una división", "enlace normal"))
    fig = px.box(a, x="tipo", y="dist_um", log_y=True, color_discrete_sequence=[NEUTRO],
                 labels={"dist_um": "desplazamiento (µm, escala log)", "tipo": ""})
    c2.plotly_chart(estilo(fig, 360, leyenda=False), width="stretch")
    fig = px.histogram(linajes, x="duracion", color="embryo_id", color_discrete_map=COLORES, category_orders=ORDEN,
                       nbins=50, barmode="overlay", opacity=.65,
                       labels={"duracion": "duración de la trayectoria (instantes)", "embryo_id": "embrión"})
    fig.update_yaxes(title_text="número de linajes")
    st.plotly_chart(estilo(fig, 320), width="stretch")
    hallazgo(f"Solo hay {int(muestras['n_divisiones'].sum())} divisiones entre {len(nodos):,} células (≈ 1 de cada "
             f"{len(nodos) // max(int(muestras['n_divisiones'].sum()), 1):,}), y los enlaces que salen de una división "
             f"se desplazan mucho más. <b>Decisión:</b> los modelos no fuerzan divisiones: en validación, agregarlas "
             f"producía más enlaces erróneos que aciertos (y pesan solo 0.1 en la métrica).")

# --- Imagen -----------------------------------------------------------------------
with tabs[5]:
    st.subheader("El brillo cambia entre videos, embriones e instantes")
    c1, c2 = st.columns(2)
    p = perfiles.copy()
    p["relativa"] = p["intensidad_media"] / p.groupby(["sample", "t"])["intensidad_media"].transform(lambda s: s.iloc[:4].mean())
    fig = go.Figure()
    for (s, t), g in p.groupby(["sample", "t"]):
        e = g["embryo_id"].iat[0]
        fig.add_trace(go.Scatter(x=g["z_um"], y=g["relativa"], mode="lines", line=dict(width=1.5, color=COLOR[e]),
                                 opacity=.5, name=e, legendgroup=e, showlegend=False,
                                 hovertemplate=f"{s} · t={t}<br>Z %{{x:.0f}} µm: %{{y:.2f}}<extra></extra>"))
    for e in ORDEN["embryo_id"]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(width=2, color=COLOR[e]), name=e))
    fig.update_layout(xaxis_title="profundidad Z (µm)", yaxis_title="intensidad / intensidad en la superficie")
    c1.plotly_chart(estilo(fig, 380), width="stretch")
    i = intensidad.assign(instante=intensidad["t"].astype(str))
    fig = px.box(i, x="instante", y="p99", color="embryo_id", color_discrete_map=COLORES, category_orders=ORDEN,
                 points="all", hover_name="sample",
                 labels={"p99": "percentil 99 de intensidad", "instante": "instante t", "embryo_id": "embrión"})
    c2.plotly_chart(estilo(fig, 380), width="stretch")
    hallazgo("La atenuación con la profundidad varía mucho entre videos (algunos son más brillantes en el fondo), un "
             "embrión es ~3 veces más brillante que el otro y la señal crece con el tiempo. <b>Decisión:</b> cada "
             "volumen se normaliza por sus propios percentiles en cada instante, en lugar de usar una escala fija.")
