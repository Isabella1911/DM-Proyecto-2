"""Constantes físicas y parámetros validados de los modelos."""
import numpy as np

# Tamaño del vóxel (Z, Y, X) en micras, documentado por los organizadores de la competencia.
VOXEL_UM = np.array([1.625, 0.40625, 0.40625])

# Modelo A: parámetros validados en modelos/modelo_A (v1 = v3, Jaccard de aristas ajustado 0.745).
PARAMS_A = dict(
    reduccion_xy=2,        # promedio 2x2 en XY: vóxel de 1.625 x 0.81 x 0.81 um (4x más rápido)
    sigma_um=2.5,          # escala del núcleo (v1: mejor σ = 2.5)
    k_dog=1.6,             # razón entre las dos gaussianas de la DoG (aproxima un LoG)
    separacion="elipsoide 3.0",  # vecindario del máximo local: "elipsoide 3.0" (v1) o "caja D" (D en um)
    umbral=0.01,           # respuesta DoG mínima, en unidades de intensidad normalizada
    radio_um=8.4,          # radio máximo de enlace: p99 del desplazamiento (EDA 5.1)
    deriva="dos_pasos",    # "ninguna" | "dos_pasos": restar el desplazamiento mediano del instante
    divisiones=False,      # agregar una segunda hija cuando una detección nueva aparece junto a una madre
    radio_div_um=8.0,      # distancia máxima madre -> segunda hija
)

# Modelo C: mismas detecciones que el A; enlace con btrack (sigma_mov se ajusta en modelo_C_btrack.ipynb).
PARAMS_C = {**PARAMS_A, "sigma_mov": 3.0, "divisiones": False, "max_lost": 1}
