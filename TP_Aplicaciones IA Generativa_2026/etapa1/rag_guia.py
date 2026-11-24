"""Construcción y consulta del índice local de la guía de Hornero."""
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile

import os
# PyTorch y FAISS comparten OpenMP en el entorno de la materia (macOS).
os.environ.setdefault("OMP_NUM_THREADS", "1")

import faiss
import pdfplumber
from sentence_transformers import SentenceTransformer

BASE = Path(__file__).resolve().parent
GUIA = BASE.parent / "datos/etapa1/guia_de_marca.pdf"
MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def extraer_chunks():
    partes = []
    with pdfplumber.open(GUIA) as pdf:
        for pagina in pdf.pages:
            tablas = pagina.find_tables()
            def fuera_de_tabla(obj):
                return all(not (x <= obj["x0"] < derecha and y <= obj["top"] < abajo)
                           for x, y, derecha, abajo in (t.bbox for t in tablas))
            texto = pagina.filter(fuera_de_tabla).extract_text()
            texto = texto.split("Hornero: Guía de marca y comunicación. Uso interno. Página")[0]
            for tabla in tablas:
                headers, *filas = tabla.extract()
                lineas = [" | ".join(f"{h}: {v}" for h, v in zip(headers, fila)).replace("\n", " ")
                          for fila in filas]
                marcador = "Reglas generales:" if headers[0] == "Canal" else "El tono se ajusta"
                texto = texto.replace(marcador, "\n".join("§" + l for l in lineas) + "\n" + marcador)
            partes.append(texto)
    secciones = re.split(r"(?m)^\d+\. ([^\n]+)\n", "\n".join(partes))
    chunks = []
    for titulo, cuerpo in zip(secciones[1::2], secciones[2::2]):
        if titulo.startswith("Promociones"):
            cuerpo, ubicacion = cuerpo.split("En Instagram", 1)
            bloques = [b + " En Instagram" + ubicacion for b in cuerpo.split("•")[1:]]
        elif titulo.startswith("Segmentos"):
            bloques = cuerpo.split("•")[1:]
        else:
            bloques = re.split(r"§|(?=Reglas generales:|El tono se ajusta)", cuerpo)
        chunks.extend(titulo + " — " + " ".join(b.split()) for b in bloques if b.strip())
    return chunks


def abrir_indice(modelo):
    firma = hashlib.sha256(GUIA.read_bytes() + MODELO.encode() + Path(__file__).read_bytes()).hexdigest()[:16]
    raiz = BASE / "indices"
    destino = raiz / firma
    if not destino.exists():
        raiz.mkdir(exist_ok=True)
        chunks = extraer_chunks()
        vectores = modelo.encode(chunks, normalize_embeddings=True)
        indice = faiss.IndexFlatIP(vectores.shape[1])
        indice.add(vectores)
        with tempfile.TemporaryDirectory(dir=raiz) as tmp:
            carpeta = Path(tmp) / "guia"
            carpeta.mkdir()
            faiss.write_index(indice, str(carpeta / "guia.faiss"))
            (carpeta / "chunks.json").write_text(json.dumps(chunks, ensure_ascii=False, indent=2))
            try:
                carpeta.rename(destino)
            except OSError:
                if not destino.is_dir():
                    raise
        print("Índice construido")
    else:
        print("Índice reutilizado")
    return faiss.read_index(str(destino / "guia.faiss")), json.loads((destino / "chunks.json").read_text())


if __name__ == "__main__":
    modelo = SentenceTransformer(MODELO, device="cpu")
    indice, chunks = abrir_indice(modelo)
    consulta = " ".join(sys.argv[1:]) or "Armá un WhatsApp para clientes Nuevos con un 15% de descuento en Cocina"
    vector = modelo.encode([consulta], normalize_embeddings=True)
    _, ids = indice.search(vector, min(8, len(chunks)))
    print(len(chunks), "fragmentos")
    for puesto, i in enumerate(ids[0], 1):
        print(puesto, chunks[i][:150])
