import streamlit as st

from comun import COLOR, EDA, faltan_datos, tabla

st.title("Seguimiento celular en el desarrollo del pez cebra")
st.markdown(
    "En videos 3D de microscopía de fluorescencia se ven los núcleos de las células de un embrión de pez cebra. "
    "El reto ([Biohub — Cell Tracking During Development](https://www.kaggle.com/competitions/"
    "biohub-cell-tracking-during-development)) es **detectar cada núcleo en cada instante y enlazarlo con su "
    "posición en el instante siguiente**, para reconstruir trayectorias y divisiones celulares."
)

if not faltan_datos():
    m = tabla(EDA, "muestras.csv")
    c = st.columns(4)
    c[0].metric("Videos de entrenamiento", f"{len(m)}")
    c[1].metric("Embriones", f"{m['embryo_id'].nunique()}")
    c[2].metric("Células anotadas", f"{int(m['n_nodos'].sum()):,}")
    c[3].metric("Células anotadas del total estimado",
                f"{100 * m['n_nodos'].sum() / m['n_estimado'].sum():.1f}%")

st.subheader("Cómo usar la aplicación")
st.markdown(f"""
| Sección | Qué encontrarás |
|---|---|
| **Explorar los datos** | las variables del conjunto y los hallazgos del análisis exploratorio que guiaron los modelos |
| **Probar los modelos** | elige una muestra y un modelo; la aplicación prepara la imagen, detecta los núcleos y los enlaza, y compara el resultado con la anotación |
| **Rendimiento** | el desempeño de cada modelo en validación y cómo se ajustaron sus parámetros |
""")

st.subheader("Los modelos")
st.markdown(f"""
Los dos modelos comparten la **detección**: diferencia de gaussianas en 3D sobre la imagen normalizada, con filtros
definidos en micras por la anisotropía del vóxel (1.625 × 0.406 × 0.406 µm). Difieren en el **enlace**:

- <span style='color:{COLOR["A"]};font-weight:600'>■</span> **Modelo A**: asignación lineal (algoritmo húngaro)
  entre instantes consecutivos, con radio de 8.4 µm (el percentil 99 del desplazamiento) y corrección de la deriva
  del tejido.
- <span style='color:{COLOR["C"]};font-weight:600'>■</span> **Modelo C**: btrack (Ulicna et al., 2021), un filtro
  de Kalman 3D con optimización global de las trayectorias.

Como referencia externa, el modelo base de los organizadores (U-Net 3D + transformer, entrenado con GPU) obtuvo
0.812 en el conjunto de prueba oficial.
""", unsafe_allow_html=True)

st.subheader("Cómo se mide")
st.markdown(
    "La **métrica oficial** empareja cada núcleo predicho con uno anotado si están a menos de 7 µm, y cuenta cuántos "
    "**enlaces** anotados se recuperan. El **Jaccard de aristas** es aciertos / (aciertos + errores + omisiones), "
    "ajustado por una penalización si se predicen muchos más núcleos de los que existen. Como solo ~3% de las células "
    "está anotado, una detección sin pareja anotada **no** cuenta como error."
)
st.caption("Colores: paleta categórica validada para daltonismo (cada color identifica siempre la misma entidad), "
           "con leyendas y formas de marcador distintas para no depender solo del color.")
