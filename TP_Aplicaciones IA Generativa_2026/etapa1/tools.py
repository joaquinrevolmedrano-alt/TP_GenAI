import csv
from pathlib import Path
from functools import lru_cache
from typing import Literal

from rag_guia import MODELO, SentenceTransformer, abrir_indice
from langchain_core.tools import tool


@lru_cache(maxsize=1)
def _cargar_guia():
    modelo = SentenceTransformer(MODELO, device="cpu")
    indice, chunks = abrir_indice(modelo)
    return modelo, indice, chunks


@tool
def consultar_guia_marca(
    situacion: str,
    canal: Literal["Instagram", "Email", "WhatsApp", "Push", "LinkedIn"] | None = None,
    segmento: Literal["Nuevos", "Recurrentes", "Premium", "Todos"] | None = None,
    promocion: Literal["descuento", "cuotas", "envío sin cargo", "ninguna"] = "ninguna",
) -> dict:
    """Consulta la guía antes de redactar o revisar. Describí el objetivo en situacion.
    Omití canal o segmento si el pedido no los indica. En promocion indicá solo
    el beneficio ofrecido. Para 'sin descuento' usá 'ninguna' si no hay otro beneficio.
    Devuelve reglas seleccionadas por los campos y contexto adicional por similitud.
    """
    modelo, indice, chunks = _cargar_guia()
    etiquetas = {"descuento": "Descuentos", "cuotas": "Cuotas", "envío sin cargo": "Envío sin cargo"}
    prefijos = []
    if canal:
        prefijos.append(f"Reglas por canal — Canal: {canal} ")
    if segmento:
        prefijos.append(f"Segmentos de clientes y cómo hablarles — {segmento}:")
    if promocion in etiquetas:
        prefijos.append(f"Promociones y legales obligatorios — {etiquetas[promocion]}:")
    obligatorias = [c for c in chunks if c.startswith(tuple(prefijos))]
    vector = modelo.encode([situacion], normalize_embeddings=True)
    _, vecinos = indice.search(vector, len(chunks))
    contexto = []
    for posicion in vecinos[0]:
        fragmento = chunks[posicion]
        if fragmento in obligatorias or fragmento.startswith("Promociones y legales obligatorios —"):
            continue
        contexto.append(fragmento)
        if len(obligatorias) + len(contexto) >= 5:
            break
    return {"obligatorias": obligatorias, "contexto": contexto}


HISTORIAL = Path(__file__).resolve().parent.parent / "datos/etapa1/contenidos_aprobados.csv"


@tool
def consultar_historial(
    segmento: Literal["Nuevos", "Recurrentes", "Premium", "Todos"] | None = None,
    canal: Literal["Instagram", "Email", "WhatsApp", "Push", "LinkedIn"] | None = None,
) -> list[dict]:
    """Consultá las tres últimas piezas aprobadas antes de elegir un enfoque.
    Indicá el segmento del pedido y el canal si querés limitar la búsqueda a ese canal.
    Un segmento concreto incluye comunicaciones dirigidas a Todos. Omití un filtro
    para buscar sin esa restricción. Devuelve fecha, canal, segmento, título y extracto.
    """
    with HISTORIAL.open(encoding="utf-8-sig", newline="") as archivo:
        piezas = [fila for fila in csv.DictReader(archivo)
                  if (not segmento or fila["segmento"] in (segmento, "Todos"))
                  and (not canal or fila["canal"] == canal)]
    piezas.sort(key=lambda pieza: pieza["fecha"], reverse=True)
    return [{**{k: fila[k] for k in ("fecha", "canal", "segmento", "titulo")},
             "extracto": fila["texto"][:320]} for fila in piezas[:3]]
