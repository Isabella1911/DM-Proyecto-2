"""Métrica de aristas de la competencia (coincide con evaluate.py oficial en la parte de aristas)."""
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

from .constantes import VOXEL_UM
from .enlace import asignar


def emparejar(pred, gt, max_um=7.0):
    """Diccionario node_id predicho -> node_id de referencia, por instante."""
    m = {}
    for t, g in gt.groupby("t"):
        pr = pred[pred["t"] == t]
        if len(pr) == 0:
            continue
        D = cdist(pr[["z", "y", "x"]].to_numpy() * VOXEL_UM, g[["z", "y", "x"]].to_numpy() * VOXEL_UM)
        for i, j in asignar(D, max_um):
            m[pr["node_id"].iat[i]] = g["node_id"].iat[j]
    return m


def metrica_aristas(pred_nodos, pred_aristas, gt_nodos, gt_aristas, n_est):
    m = emparejar(pred_nodos, gt_nodos)
    gt_set = set(map(tuple, gt_aristas.tolist()))
    sale, entra = {}, {}
    for s, d in gt_set:
        sale.setdefault(s, set()).add(d)
        entra.setdefault(d, set()).add(s)
    tp_set, fp = set(), 0
    for s, d in zip(pred_aristas["source_id"], pred_aristas["target_id"]):
        ms, md_ = m.get(s), m.get(d)
        if ms is not None and md_ is not None and (ms, md_) in gt_set:
            tp_set.add((ms, md_))
        elif (md_ is not None and entra.get(md_, set()) - {ms}) or \
             (ms is not None and sale.get(ms, set()) - {md_}):
            fp += 1
    tp, fn = len(tp_set), len(gt_set) - len(tp_set)
    j = tp / max(tp + fp + fn, 1)
    n_pred = len(pred_nodos)
    adj = max(0.0, j * (1 - 0.1 * (n_pred - n_est) / n_est)) if n_est else j
    recall_nodos = len(set(m.values())) / max(len(gt_nodos), 1)
    return dict(tp=tp, fp=fp, fn=fn, jaccard=j, jaccard_ajustado=adj, n_pred=n_pred, n_est=n_est,
                recall_nodos=recall_nodos)


def agregar(res):
    r = pd.DataFrame(res)
    w = r["tp"] + r["fp"] + r["fn"]
    return pd.Series({"jaccard_ajustado": (r["jaccard_ajustado"] * w).sum() / w.sum(),
                      "jaccard": r["tp"].sum() / w.sum(),
                      "recall_nodos": r["recall_nodos"].mean(),
                      "pred/estimados": r["n_pred"].sum() / r["n_est"].sum(),
                      "tp": r["tp"].sum(), "fp": r["fp"].sum(), "fn": r["fn"].sum()})
