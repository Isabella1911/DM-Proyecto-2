"""Enlace del modelo A: asignación lineal entre instantes consecutivos, con corrección de deriva."""
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist

from .constantes import VOXEL_UM
from .deteccion import columna


def asignar(D, radio):
    if D.size == 0:
        return np.empty((0, 2), int)
    C = np.where(D <= radio, D, 1e6)
    f, c = linear_sum_assignment(C)
    ok = C[f, c] < 1e6
    return np.column_stack([f[ok], c[ok]])


def enlazar(det, n_t, p):
    """det: detecciones (t, z, y, x, resp, max_*) -> (nodos con node_id, aristas source/target)."""
    ok = det["resp"] >= p["umbral"]
    if columna(p["separacion"]) in det:
        ok &= det[columna(p["separacion"])]
    det = det[ok].reset_index(drop=True)
    det["node_id"] = np.arange(1, len(det) + 1)
    pos = det[["z", "y", "x"]].to_numpy() * VOXEL_UM
    por_t = {t: g.index.to_numpy() for t, g in det.groupby("t")}
    vacio = np.empty(0, int)
    src, dst = [], []
    for t in range(n_t - 1):
        a, b = por_t.get(t, vacio), por_t.get(t + 1, vacio)
        if len(a) == 0 or len(b) == 0:
            continue
        P0, P1 = pos[a], pos[b]
        D = cdist(P0, P1)
        pares = asignar(D, p["radio_um"])
        if p["deriva"] == "dos_pasos" and len(pares) >= 5:
            deriva = np.median(P1[pares[:, 1]] - P0[pares[:, 0]], axis=0)
            D = cdist(P0 + deriva, P1)
            pares = asignar(D, p["radio_um"])
        src += list(a[pares[:, 0]]); dst += list(b[pares[:, 1]])

        if p["divisiones"] and len(pares):
            hijo = dict(zip(pares[:, 0], pares[:, 1]))
            libres = np.setdiff1d(np.arange(len(b)), pares[:, 1])
            usadas = set()
            for j in libres:
                cand = [(D[i, j], i) for i in hijo if i not in usadas and D[i, j] <= p["radio_div_um"]]
                if cand:
                    _, i = min(cand)
                    usadas.add(i)
                    src.append(a[i]); dst.append(b[j])

    aristas = pd.DataFrame({"source_id": det["node_id"].to_numpy()[src],
                            "target_id": det["node_id"].to_numpy()[dst]})
    return det, aristas
