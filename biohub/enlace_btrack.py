"""Enlace del modelo C: filtro de Kalman 3D + optimización global de hipótesis (btrack).

Usa las mismas detecciones que el modelo A; solo cambia el método de enlace.
"""
import logging

import numpy as np
import pandas as pd

from .constantes import VOXEL_UM
from .deteccion import columna


def config_btrack(p):
    I, Z0 = np.eye(3), np.zeros((3, 3))
    hip = ["P_FP", "P_init", "P_term", "P_link"] + (["P_branch"] if p["divisiones"] else [])
    return {
        "name": "biohub", "max_search_radius": p["radio_um"], "verbose": False,
        "motion_model": {
            "name": "velocidad_constante_3d", "measurements": 3, "states": 6, "dt": 1.0,
            "accuracy": 2.0, "max_lost": p["max_lost"], "prob_not_assign": 0.1,
            "A": np.block([[I, I], [Z0, I]]).ravel().tolist(),                  # x' = x + v
            "H": np.hstack([I, Z0]).ravel().tolist(),                          # se observa la posición
            "P": {"sigma": 10.0, "matrix": np.eye(6).ravel().tolist()},
            "G": {"sigma": p["sigma_mov"], "matrix": [0.5, 0.5, 0.5, 1, 1, 1]},  # ruido del movimiento
            "R": {"sigma": 1.0, "matrix": np.eye(3).ravel().tolist()},         # ruido de medición (~1 µm)
        },
        "hypothesis_model": {
            "name": "hipotesis", "hypotheses": hip, "lambda_time": 5.0, "lambda_dist": 3.0,
            "lambda_link": 5.0, "lambda_branch": 20.0, "eta": 1e-10, "theta_dist": 5.0, "theta_time": 3.0,
            "dist_thresh": p["radio_um"], "time_thresh": 2, "apop_thresh": 5,
            "segmentation_miss_rate": 0.1, "apoptosis_rate": 0.001, "relax": True,
        },
    }


def enlazar_btrack(det, n_t, forma, p):
    """Mismo filtrado de detecciones que el modelo A; enlace con btrack. -> (nodos, aristas)."""
    import btrack
    from btrack.utils import objects_from_dict

    logging.getLogger("btrack").setLevel(logging.WARNING)
    ok = det["resp"] >= p["umbral"]
    if columna(p["separacion"]) in det:
        ok &= det[columna(p["separacion"])]
    det = det[ok].reset_index(drop=True)
    det["node_id"] = np.arange(1, len(det) + 1)
    vacio = pd.DataFrame({"source_id": pd.Series(dtype=np.int64), "target_id": pd.Series(dtype=np.int64)})
    if len(det) == 0:
        return det, vacio
    um = det[["z", "y", "x"]].to_numpy() * VOXEL_UM
    objetos = objects_from_dict({"ID": np.arange(len(det)), "t": det["t"].to_numpy().astype(int),
                                 "x": um[:, 2], "y": um[:, 1], "z": um[:, 0]})
    lim = np.array(forma) * VOXEL_UM
    with btrack.BayesianTracker(verbose=False) as tr:
        tr.configure(config_btrack(p))
        tr.volume = ((0, lim[2]), (0, lim[1]), (0, lim[0]))
        tr.append(objetos)
        tr.track(step_size=100)
        tr.optimize(msg_lev="GLP_MSG_OFF", tm_lim=60_000)   # conserva el límite de 60 s por defecto
        tracks = tr.tracks

    t_obj = det["t"].to_numpy()
    src, dst, primero, ultimo = [], [], {}, {}
    for trk in tracks:
        refs = [r for r in trk.refs if r >= 0]           # refs < 0: objetos de relleno de btrack
        for a, b in zip(refs[:-1], refs[1:]):
            if t_obj[b] - t_obj[a] == 1:
                src.append(a); dst.append(b)
        if refs:
            primero[trk.ID], ultimo[trk.ID] = refs[0], refs[-1]
    if p["divisiones"]:
        for trk in tracks:
            for hija in trk.children:
                a, b = ultimo.get(trk.ID), primero.get(hija)
                if a is not None and b is not None and t_obj[b] - t_obj[a] == 1:
                    src.append(a); dst.append(b)
    ids = det["node_id"].to_numpy()
    return det, (pd.DataFrame({"source_id": ids[src], "target_id": ids[dst]}) if src else vacio)
