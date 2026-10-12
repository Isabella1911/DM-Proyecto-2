import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import biohub
from comun import COLOR, NOMBRE, RESULTADOS, TEXTO, TEXTO_2, estilo, hallazgo, tabla

st.title("Rendimiento de los modelos")
st.caption("Métrica: Jaccard de aristas ajustado (la parte de aristas de la métrica oficial, verificada contra su "
           "implementación). Más alto es mejor; 1 sería recuperar todos los enlaces anotados sin errores.")

secciones = st.multiselect("Secciones visibles", ["Comparación A vs. C", "Ajuste del modelo A", "Ajuste del modelo C"],
                           default=["Comparación A vs. C", "Ajuste del modelo A", "Ajuste del modelo C"],
                           help="Puedes ocultar cualquier sección")
GRUPO = {"total": TEXTO_2, "6bba": COLOR["6bba"], "44b6": COLOR["44b6"]}

# --- Comparación A vs. C --------------------------------------------------------------
if "Comparación A vs. C" in secciones:
    st.header("Comparación A vs. C")
    pm = tabla(RESULTADOS, "resultados_por_muestra.csv")     # por muestra (celda final de la notebook C)
    rs = tabla(RESULTADOS, "resultados_resumen.csv")         # resumen por conjunto, modelo y embrión
    if pm is None and rs is None:
        st.info("Pendiente: faltan los resultados de `modelos/modelo_C_btrack.ipynb` en `app/resultados_modelos/`.")
    else:
        base = pm if pm is not None else rs
        conjunto = st.radio("Conjunto de validación", sorted(base["conjunto"].unique()), horizontal=True,
                            help="VAL_A: las 16 muestras con que se ajustó el modelo A. VAL_B: las 19 del split 0 "
                                 "(las que el modelo base de la competencia no vio al entrenar).")
        if pm is not None:
            d = pm[pm["conjunto"] == conjunto]
            filas = []
            for m, g in d.groupby("modelo"):
                for grupo, gg in [("total", g)] + list(g.groupby("embryo_id")):
                    filas.append({"modelo": m, "grupo": grupo, **biohub.agregar(gg).to_dict(),
                                  "seg_enlace_por_muestra": gg["seg_enlace"].mean()})
            r = pd.DataFrame(filas)
        else:
            r = rs[rs["conjunto"] == conjunto].copy()
        r["nombre"] = r["modelo"].map(NOMBRE)
        colores = {NOMBRE[m]: COLOR[m] for m in "AC"}

        fig = px.bar(r, x="grupo", y="jaccard_ajustado", color="nombre", barmode="group", text_auto=".3f",
                     color_discrete_map=colores, category_orders={"grupo": ["total", "6bba", "44b6"]},
                     labels={"jaccard_ajustado": "Jaccard de aristas ajustado", "grupo": "", "nombre": ""})
        fig.update_traces(textposition="outside", marker_line_width=0)
        fig.update_yaxes(range=[0, 1])
        st.plotly_chart(estilo(fig, 380), width="stretch")

        c1, c2 = st.columns(2)
        if pm is not None:
            ancho = d.pivot_table(index=["sample", "embryo_id"], columns="modelo", values="jaccard_ajustado").reset_index()
            fig = px.scatter(ancho, x="A", y="C", color="embryo_id", hover_name="sample",
                             color_discrete_map={e: COLOR[e] for e in ["6bba", "44b6"]},
                             category_orders={"embryo_id": ["6bba", "44b6"]},
                             labels={"A": "Modelo A (Jaccard ajustado)", "C": "Modelo C (Jaccard ajustado)",
                                     "embryo_id": "embrión"})
            fig.update_traces(marker=dict(size=10, line=dict(width=1, color="white")))
            fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(color=TEXTO_2, dash="dash", width=1),
                                     name="igual desempeño", hoverinfo="skip"))
            fig.update_layout(title="Cada punto es una muestra")
            c1.plotly_chart(estilo(fig, 400), width="stretch")
            c1.caption(f"Sobre la diagonal, C es mejor. C supera a A en {(ancho['C'] > ancho['A']).sum()} de "
                       f"{len(ancho)} muestras.")
        else:
            t = r[r["grupo"] == "total"].melt(id_vars=["nombre"], value_vars=["tp", "fp", "fn"], var_name="tipo",
                                              value_name="enlaces")
            t["tipo"] = t["tipo"].map({"tp": "aciertos", "fp": "erróneos", "fn": "omitidos"})
            fig = px.bar(t, x="tipo", y="enlaces", color="nombre", barmode="group", text_auto=",.0f",
                         color_discrete_map=colores, labels={"tipo": "", "nombre": ""})
            fig.update_traces(textposition="outside", marker_line_width=0)
            fig.update_layout(title="Enlaces anotados: aciertos, errores y omisiones")
            c1.plotly_chart(estilo(fig, 400), width="stretch")
        tt = r[r["grupo"] == "total"]
        fig = px.bar(tt, x="nombre", y="seg_enlace_por_muestra", color="nombre", text_auto=".1f",
                     color_discrete_map=colores,
                     labels={"seg_enlace_por_muestra": "segundos de enlace por muestra", "nombre": ""})
        fig.update_traces(textposition="outside", marker_line_width=0)
        fig.update_layout(title="Tiempo de enlace por muestra")
        c2.plotly_chart(estilo(fig, 400, leyenda=False), width="stretch")
        c2.caption("La detección es la misma para los dos modelos (~1 min por muestra completa); aquí solo se compara "
                   "el enlace.")

        a_, c_ = (tt.set_index("modelo").loc[m] for m in "AC")
        hallazgo(f"El modelo A supera al C por {a_['jaccard_ajustado'] - c_['jaccard_ajustado']:.3f} y enlaza "
                 f"~{c_['seg_enlace_por_muestra'] / a_['seg_enlace_por_muestra']:.0f} veces más rápido. Con las mismas "
                 f"detecciones, el enlace simple con corrección de deriva (guiado por el EDA) funciona mejor que el "
                 f"filtro de Kalman con optimización global: el movimiento entre instantes es pequeño y la deriva del "
                 f"tejido, que A descuenta explícitamente, pesa más que la inercia que modela btrack.")
        with st.expander("Tabla"):
            st.dataframe(r.drop(columns=["nombre"]).round(4), hide_index=True, width="stretch")
    st.caption("Referencia externa: el modelo base de los organizadores (U-Net 3D + transformer, con GPU) obtuvo 0.812 "
               "en el conjunto de prueba oficial de Kaggle (incluye el término de divisiones). No se grafica junto a A "
               "y C porque se evaluó sobre otras muestras.")

# --- Ajuste del modelo A ----------------------------------------------------------------
if "Ajuste del modelo A" in secciones:
    st.header("Ajuste del modelo A")
    res, hist, sig = (tabla(RESULTADOS, f) for f in
                      ["resumen_modelo_A.csv", "historial_modelo_A.csv", "sigma_por_embrion_A.csv"])
    c1, c2 = st.columns(2)
    fig = px.bar(res, x="version", y="jaccard_ajustado", color="grupo", barmode="group", text_auto=".3f",
                 color_discrete_map=GRUPO, category_orders={"grupo": ["total", "6bba", "44b6"]},
                 labels={"jaccard_ajustado": "Jaccard de aristas ajustado", "version": "versión", "grupo": ""})
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_yaxes(range=[0, 1])
    fig.update_layout(title="Tres versiones, 16 muestras de validación")
    c1.plotly_chart(estilo(fig, 400), width="stretch")
    s = sig.melt(id_vars=["sigma_um"], value_vars=["total", "6bba", "44b6"], var_name="grupo", value_name="j")
    fig = px.line(s, x="sigma_um", y="j", color="grupo", markers=True, color_discrete_map=GRUPO,
                  category_orders={"grupo": ["total", "6bba", "44b6"]},
                  labels={"sigma_um": "σ del filtro (µm) ≈ tamaño del núcleo", "j": "Jaccard de aristas ajustado", "grupo": ""})
    fig.update_traces(line_width=2, marker_size=9)
    fig.update_layout(title="Cada embrión prefiere un tamaño de núcleo distinto")
    c2.plotly_chart(estilo(fig, 400), width="stretch")
    hallazgo("La v2 cambió la regla de supresión de máximos y bajó a 0.741; la v3 volvió a la regla estricta y confirmó "
             "la configuración de la v1 como la mejor (σ = 2.5 µm). Con un σ fijo, 44b6 rinde mucho menos que 6bba: "
             "sus núcleos son más pequeños, y como la prueba usa embriones nuevos, esta es la principal limitación.")

    st.subheader("Efecto de cada parámetro (v3)")
    h = hist[hist["version"] == "v3"]
    nombres = {"umbral": "umbral de detección", "separacion": "vecindario del máximo local",
               "radio_um": "radio de enlace (µm)", "deriva": "corrección de deriva", "divisiones": "divisiones"}
    c1, c2 = st.columns([1, 3])
    par = c1.radio("Parámetro", [p for p in nombres if p in set(h["parametro"])], format_func=nombres.get)
    g = h[h["parametro"] == par]
    if par in ("umbral", "separacion"):
        sig_opc = sorted(g["sigma_um"].dropna().unique())
        sigma = c1.selectbox("σ (µm)", sig_opc, index=sig_opc.index(2.5) if 2.5 in sig_opc else 0)
        g = g[g["sigma_um"] == sigma]
    g = g.melt(id_vars=["valor"], value_vars=["jaccard_ajustado", "recall_nodos"], var_name="métrica", value_name="v")
    g["métrica"] = g["métrica"].map({"jaccard_ajustado": "Jaccard de aristas ajustado",
                                     "recall_nodos": "núcleos anotados encontrados"})
    fig = px.line(g, x="valor", y="v", color="métrica", markers=True, line_dash="métrica",
                  color_discrete_sequence=[TEXTO, TEXTO_2], labels={"valor": nombres[par], "v": "", "métrica": ""})
    fig.update_traces(line_width=2, marker_size=9)
    fig.update_yaxes(range=[0, 1])
    if par == "umbral":
        fig.update_xaxes(type="log")
    c2.plotly_chart(estilo(fig, 360), width="stretch")
    with st.expander("Tabla completa del ajuste"):
        st.dataframe(hist, hide_index=True, width="stretch")

# --- Ajuste del modelo C -----------------------------------------------------------------
if "Ajuste del modelo C" in secciones:
    st.header("Ajuste del modelo C")
    aj = tabla(RESULTADOS, "ajuste_modelo_C.csv")
    if aj is None:
        st.info("Pendiente: falta `app/resultados_modelos/ajuste_modelo_C.csv` (corrida de `modelo_C_btrack.ipynb`).")
    else:
        aj = aj.assign(configuracion=aj["sigma_mov"].astype(str) + " µm · " +
                       aj["divisiones"].map({True: "con divisiones", False: "sin divisiones"}))
        fig = px.bar(aj, x="configuracion", y="jaccard_ajustado", text_auto=".3f",
                     color_discrete_sequence=[COLOR["C"]],
                     labels={"configuracion": "ruido de movimiento · divisiones", "jaccard_ajustado": "Jaccard de aristas ajustado"})
        fig.update_traces(textposition="outside", marker_line_width=0)
        fig.update_yaxes(range=[0, 1])
        st.plotly_chart(estilo(fig, 360, leyenda=False), width="stretch")
        hallazgo("Con la hipótesis de división, la optimización global de btrack no converge dentro de su límite de "
                 "tiempo en algunas muestras densas, y el resultado empeora.")
