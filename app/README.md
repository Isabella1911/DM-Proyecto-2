# Aplicación — plan

Aplicación en **Streamlit** donde el usuario elige una muestra de demostración, la procesa con los
modelos **A** y/o **C**, y explora los datos y el rendimiento de cada modelo con gráficas interactivas
(Plotly).

## Secciones previstas y criterio de la guía que cubren

| Sección | Contenido | Criterio (puntos) |
|---|---|---|
| Inicio | el problema, los datos y cómo usar la app | — |
| Explorar los datos | hallazgos del EDA en gráficas interactivas: esparcidad de la anotación, desplazamientos, deriva, divisiones, diferencias entre embriones | Presentación de resultados (20): "explorar de forma dinámica los datos" |
| Probar los modelos | elegir muestra demo y modelo (A, C o ambos); la app normaliza, detecta y enlaza sin intervención del usuario; muestra detecciones sobre la imagen, trayectorias en 3D y, si la muestra tiene anotación, su puntaje | Preprocesamiento de la entrada (15) y Presentación de resultados (20) |
| Rendimiento | métricas de validación de cada modelo (total y por embrión), historial v1 → v3, tiempos; con opción de ocultar | Eficiencia de los modelos (15) |

## Datos que necesita

Todo debe salir de corridas en Kaggle, porque el conjunto completo pesa 87.6 GB:

- `datos_demo/`: 2 – 3 muestras recortadas (pocos instantes) en formato `.zarr` + `.geff`, de unos MB
  cada una, para correr los modelos en vivo.
- Tablas resumen del EDA y resultados de validación de cada modelo (CSV), para las secciones de
  exploración y rendimiento.

## Código

La app usa el paquete `biohub/` (en la raíz del repositorio), que contiene el mismo código de las
notebooks de los modelos A y C.

## Pendiente a tener en cuenta

- El binario precompilado de `btrack` 0.7.0 requiere `GLIBCXX_3.4.32`. Si la app se publica en un
  servidor con una versión de C++ más antigua (por ejemplo, Streamlit Community Cloud), habrá que
  compilarlo como se hace en `modelos/modelo_C_btrack.ipynb`.
