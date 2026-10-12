"""Lectura de arreglos Zarr v3 y grafos .geff sin depender de la librería zarr."""
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd


def _blosc(b):
    try:
        import numcodecs
        return numcodecs.Blosc().decode(b)
    except ImportError:
        pass
    try:
        import blosc2
        return blosc2.decompress(b)
    except ImportError:
        import blosc
        return blosc.decompress(b)


def _zstd(b):
    try:
        import numcodecs
        return numcodecs.Zstd().decode(b)
    except ImportError:
        import zstandard
        return zstandard.ZstdDecompressor().stream_reader(io.BytesIO(b)).read()


def _gzip(b):
    import gzip
    return gzip.decompress(b)


DECODIFICADORES = {"blosc": _blosc, "zstd": _zstd, "gzip": _gzip, "crc32c": lambda b: bytes(b)[:-4]}


class ArregloZarr:
    """Lector mínimo de arreglos Zarr v3 (solo lectura, sin depender de la librería zarr)."""

    def __init__(self, ruta):
        self.ruta = Path(ruta)
        m = json.loads((self.ruta / "zarr.json").read_text())
        assert m.get("node_type") == "array", f"{ruta} no es un arreglo"
        self.shape = tuple(m["shape"])
        self.chunks = tuple(m["chunk_grid"]["configuration"]["chunk_shape"])
        self.fill = m.get("fill_value") or 0
        enc = m.get("chunk_key_encoding", {"name": "default"})
        self.sep = enc.get("configuration", {}).get("separator", "/" if enc["name"] == "default" else ".")
        self.prefijo = ["c"] if enc["name"] == "default" else []
        endian = "<"
        self.codecs = []
        for c in m["codecs"]:
            n = c["name"]
            if n == "bytes":
                endian = "<" if c.get("configuration", {}).get("endian", "little") == "little" else ">"
            elif n in DECODIFICADORES:
                self.codecs.append(n)
            else:
                raise NotImplementedError(f"códec no soportado: {n}")
        self.dtype = np.dtype(m["data_type"]).newbyteorder(endian)

    def _chunk(self, idx):
        f = self.ruta / self.sep.join(self.prefijo + [str(i) for i in idx])
        if not f.exists():
            return np.full(self.chunks, self.fill, dtype=self.dtype)
        b = f.read_bytes()
        for n in reversed(self.codecs):
            b = DECODIFICADORES[n](b)
        return np.frombuffer(b, dtype=self.dtype).reshape(self.chunks)

    def leer(self):
        """Arreglo completo."""
        grid = [range(-(-s // c)) for s, c in zip(self.shape, self.chunks)]
        out = np.empty(self.shape, dtype=self.dtype.newbyteorder("="))
        for idx in np.ndindex(*[len(g) for g in grid]):
            sl = tuple(slice(i * c, min((i + 1) * c, s)) for i, c, s in zip(idx, self.chunks, self.shape))
            out[sl] = self._chunk(idx)[tuple(slice(0, x.stop - x.start) for x in sl)]
        return out

    def instante(self, t):
        """Volumen (Z, Y, X) del instante t, asumiendo chunks de un instante en el eje 0."""
        assert self.chunks[0] == 1 and self.chunks[1:] == self.shape[1:], "se esperan chunks (1, Z, Y, X)"
        return self._chunk((t, 0, 0, 0))[0].astype(self.dtype.newbyteorder("="))



def leer_grafo(geff):
    """Grafo de referencia .geff -> (DataFrame de nodos, arreglo de aristas, nodos estimados)."""
    geff = Path(geff)
    ids = ArregloZarr(geff / "nodes" / "ids").leer()
    nodos = pd.DataFrame({"node_id": ids.astype(np.int64)})
    for c in "tzyx":
        nodos[c] = ArregloZarr(geff / "nodes" / "props" / c / "values").leer().astype(float)
    aristas = ArregloZarr(geff / "edges" / "ids").leer().astype(np.int64).reshape(-1, 2)
    attrs = json.loads((geff / "zarr.json").read_text()).get("attributes", {})

    def buscar(d, k):
        if isinstance(d, dict):
            if k in d:
                return d[k]
            for v in d.values():
                r = buscar(v, k)
                if r is not None:
                    return r
        return None

    return nodos, aristas, buscar(attrs, "estimated_number_of_nodes")
