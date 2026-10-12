"""Compila el núcleo C++ de btrack si su binario precompilado no carga en este equipo (solo Linux).

El binario de btrack 0.7.0 exige GLIBCXX_3.4.32 (GCC 13 o más nuevo). En sistemas más antiguos, por
ejemplo Ubuntu 22.04, no carga y la app desactiva el modelo C. Este script lo compila desde el código
fuente con el compilador del sistema, enlazando la librería de C++ de forma estática.

Requiere: g++, make, git e internet.   Uso:  python app/reparar_btrack.py
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


def btrack_carga():
    r = subprocess.run([sys.executable, "-c", "from btrack import libwrapper; libwrapper.get_library()"],
                       capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr)[-600:]


def correr(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.exit(f"Falló: {' '.join(map(str, cmd))}\n{(r.stdout + r.stderr)[-1500:]}")


def main():
    if importlib.util.find_spec("btrack") is None:
        sys.exit("btrack no está instalado: correr primero  pip install -r requirements.txt")
    ok, detalle = btrack_carga()
    if ok and "--forzar" not in sys.argv:
        print("btrack ya carga correctamente; no hace falta compilar.")
        return
    if sys.platform != "linux":
        sys.exit(f"btrack no carga y este script solo compila en Linux.\n{detalle}")
    for prog in ("g++", "make", "git"):
        if shutil.which(prog) is None:
            sys.exit(f"Falta '{prog}'. En Ubuntu/Debian: sudo apt install build-essential git")

    print("Compilando el núcleo de btrack desde el código fuente (≈1 minuto)...")
    tmp = Path(tempfile.mkdtemp())
    correr([sys.executable, "-m", "pip", "download", "-q", "--no-deps", "--no-binary", ":all:",
            "btrack==0.7.0", "-d", str(tmp)])
    with tarfile.open(next(tmp.glob("btrack-*.tar.gz"))) as tar:
        tar.extractall(tmp, filter="data")
    fuente = next(p for p in tmp.glob("btrack-*") if p.is_dir())
    correr(["git", "clone", "-q", "--depth", "1", "--branch", "3.3.9",
            "https://gitlab.com/libeigen/eigen.git", str(fuente / "btrack" / "include" / "eigen")])
    for d in ("libs", "obj"):
        (fuente / "btrack" / d).mkdir(exist_ok=True)
    correr(["make", f"-j{os.cpu_count() or 1}", "XLDFLAGS=-Wl,--no-undefined -static-libstdc++ -static-libgcc"],
           cwd=fuente)
    destino = Path(importlib.util.find_spec("btrack").origin).parent / "libs" / "libtracker.so"
    shutil.copy(fuente / "btrack" / "libs" / "libtracker.so", destino)
    ok, detalle = btrack_carga()
    if not ok:
        sys.exit(f"btrack sigue sin cargar después de compilarlo:\n{detalle}")
    print(f"Listo: {destino}")


if __name__ == "__main__":
    main()
