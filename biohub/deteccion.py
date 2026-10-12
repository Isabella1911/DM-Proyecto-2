"""Detección de núcleos (modelo A): normalización, diferencia de gaussianas y máximos locales."""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import ndimage

from .constantes import VOXEL_UM
from .lector import ArregloZarr


def normalizar(v):
    lo, hi = np.percentile(v[::2, ::4, ::4], [1, 99.9])
    return np.clip((v.astype(np.float32) - lo) / max(hi - lo, 1e-6), 0, 1)


def reducir_xy(v, f):
    if f == 1:
        return v
    Z, Y, X = v.shape
    return v[:, :Y // f * f, :X // f * f].reshape(Z, Y // f, f, X // f, f).mean(axis=(2, 4))


def filtro_maximo(dog, separacion, vox):
    """Máximo en el vecindario 'elipsoide D' o 'caja D' (D en micras)."""
    forma, d = separacion.split()
    r = np.maximum(1, np.round(float(d) / vox)).astype(int)
    if forma == "caja":
        return ndimage.maximum_filter(dog, size=2 * r + 1, mode="nearest")
    zz, yy, xx = np.ogrid[-r[0]:r[0] + 1, -r[1]:r[1] + 1, -r[2]:r[2] + 1]
    huella = (zz / r[0]) ** 2 + (yy / r[1]) ** 2 + (xx / r[2]) ** 2 <= 1
    return ndimage.maximum_filter(dog, footprint=huella, mode="nearest")


def columna(separacion):
    return "max_" + separacion.replace(" ", "_")


def detectar_volumen(v, p, umbral, separaciones):
    """Máximos locales estrictos para el primer vecindario de la lista (el más permisivo), con una
    columna por vecindario que indica si el candidato también es máximo en él."""
    f = p["reduccion_xy"]
    vr = reducir_xy(normalizar(v), f)
    vox = VOXEL_UM * np.array([1, f, f])
    s1 = p["sigma_um"] / vox
    dog = ndimage.gaussian_filter(vr, s1) - ndimage.gaussian_filter(vr, s1 * p["k_dog"])
    pico = (dog == filtro_maximo(dog, separaciones[0], vox)) & (dog > umbral)
    idx = np.argwhere(pico)
    marcas = {columna(s): dog[pico] == filtro_maximo(dog, s, vox)[pico] for s in separaciones}
    pos = idx.astype(float)
    pos[:, 1:] = pos[:, 1:] * f + (f - 1) / 2          # volver a la rejilla original
    return pos, dog[pico], marcas


def detectar_muestra(zarr_dir, p, umbral, separaciones=None):
    """Detecciones de todos los instantes -> (DataFrame t, z, y, x, resp, max_*; n_t)."""
    separaciones = separaciones or [p["separacion"]]
    arr = ArregloZarr(Path(zarr_dir) / "0")
    filas = []
    for t in range(arr.shape[0]):
        pos, resp, marcas = detectar_volumen(arr.instante(t), p, umbral, separaciones)
        filas.append(pd.DataFrame({"t": t, "z": pos[:, 0], "y": pos[:, 1], "x": pos[:, 2], "resp": resp, **marcas}))
    return pd.concat(filas, ignore_index=True), arr.shape[0]
