"""
tools.py: acá van TODAS las tools que usan los agentes.

Por ahora hay una sola tool de ejemplo (fecha_de_hoy). Para el TP tienen que sumar
tools para buscar en documentos (RAG), escribir datos, usar los modelos de machine
learning (predecir, interpretar, simular), etc. Las consultas exploratorias sobre los
datos las resuelve un agente SQL (SQLDatabaseToolkit), no una tool por pregunta.

Recordatorios (Clase 4):
- El docstring de cada tool es lo que el LLM lee para decidir cuándo usarla.
- Que cada tool reciba al menos un parámetro: los modelos chicos (gpt-oss-20b) a veces
  generan mal la llamada a una tool sin parámetros.
- Lo que devuelve una tool entra entero en el contexto del LLM: devuelvan resúmenes, no tablas enteras.
"""

from datetime import date
from pathlib import Path
from typing import Literal

from langchain_core.tools import tool

# Carpeta con los datos del TP (datos/etapa1 y datos/etapa2)
RUTA_DATOS = Path(__file__).parent / "datos"

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


@tool
def fecha_de_hoy(formato: Literal["numerico", "texto"]) -> str:
    """Devuelve la fecha de hoy. formato='numerico' devuelve AAAA-MM-DD;
    formato='texto' devuelve, por ejemplo, 'sábado 7 de noviembre de 2026'."""
    hoy = date.today()
    if formato == "texto":
        return f"{DIAS[hoy.weekday()]} {hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"
    return hoy.isoformat()
