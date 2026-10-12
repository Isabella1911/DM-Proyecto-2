# Proyecto 2 — Biohub: Cell Tracking During Development

**CC3084 Data Science · Universidad del Valle de Guatemala · Semestre II 2026**
Isabella Obando (23074) · Anthony Lou (23410) · Fabian Prado (23427) · Fernando Mendoza (19644)

Seguimiento de células en videos 3D+tiempo de embriones de pez cebra, para la competencia de Kaggle
[Biohub — Cell Tracking During Development](https://www.kaggle.com/competitions/biohub-cell-tracking-during-development).
El objetivo es detectar los núcleos en cada instante y enlazarlos entre instantes para reconstruir sus
trayectorias y divisiones.

## Estructura

```
├── eda/
│   └── proyecto2-ds.ipynb         Análisis exploratorio (199 muestras, ejecutado en Kaggle)
├── modelos/
│   ├── modelo_A/                  Detección clásica (DoG) + asignación lineal
│   │   ├── modelo_A_v1.ipynb      σ ≤ 2.5 µm                         → Jaccard 0.745
│   │   ├── modelo_A_v2.ipynb      supresión de no máximos + bordes   → 0.741
│   │   └── modelo_A_v3.ipynb      regla estricta + vecindarios       → 0.745 (confirma la v1)
│   ├── modelo_B_unet.ipynb        U-Net 3D + transformer (modelo base de los organizadores; referencia)
│   └── modelo_C_btrack.ipynb      Mismas detecciones que A + btrack (Kalman + optimización global)
├── biohub/                        Código compartido de los modelos A y C (lector, detección, enlace, métrica)
├── app/                           Aplicación Streamlit (en construcción)
│   └── exportar_datos_kaggle.ipynb   Genera en Kaggle las muestras demo y las tablas que usa la app
├── docs/                          Documentos de apoyo (cambios al informe del EDA)
└── archivo/                       Versiones anteriores que ya no se usan
```

`biohub/` contiene el mismo código de las notebooks, extraído para reutilizarlo en la aplicación; se
verificó que produce exactamente los mismos resultados.

## Modelos

| Modelo | Detección | Enlace | Entrenamiento | Validación (Jaccard de aristas ajustado) |
|---|---|---|---|---|
| **A** | diferencia de gaussianas 3D + máximos locales | asignación lineal (húngaro) con corrección de deriva | ninguno: parámetros elegidos con el EDA y validación | **0.745** (16 muestras; 6bba 0.785, 44b6 0.557) |
| **B** | U-Net 3D con atención temporal | transformer + ILP | pesos públicos de los organizadores (Royer Lab, 2026) | referencia oficial: 0.812 |
| **C** | la misma del A | btrack: filtro de Kalman 3D + optimización global | ninguno | pendiente |

## Cómo correr las notebooks

Todas están pensadas para **Kaggle**, con la competencia agregada como *Input* (los datos pesan
87.6 GB y se leen montados, sin descargarlos).

| Notebook | Acelerador | Internet | Inputs adicionales |
|---|---|---|---|
| `eda/proyecto2-ds.ipynb` | ninguno | On (instala `zarr>=3`) | — |
| `modelos/modelo_A/*.ipynb` | ninguno | Off | — |
| `modelos/modelo_B_unet.ipynb` | GPU T4 ×2 | Off | dataset `cellmot-baseline-artifacts`; usar *Copy & Edit* de la notebook oficial para heredar su entorno (Python 3.12) |
| `modelos/modelo_C_btrack.ipynb` | ninguno | On (instala y compila `btrack`) | — |

## Aplicación

Ver [app/README.md](app/README.md).
