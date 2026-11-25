"""Agente estratega de Marketing de Hornero."""

import json
import re
from functools import lru_cache
from typing import Literal, TypedDict

from dotenv import load_dotenv
from groq import APIError, RateLimitError
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from tools import consultar_guia_marca, consultar_historial, guardar_pieza


class BriefEstrategico(BaseModel):
    objetivo: str
    enfoque: str
    antecedentes_a_evitar: list[str]
    datos_faltantes: list[str] = Field(description="Datos necesarios que el pedido no proporciona.")


def crear_estratega():
    load_dotenv()
    return create_agent(
        model=ChatGroq(model="openai/gpt-oss-20b", temperature=0, reasoning_effort="low", timeout=25, max_retries=1),
        tools=[],
        response_format=ToolStrategy(BriefEstrategico),
        system_prompt=(
            "Sos el estratega de Marketing de Hornero. Prepará un brief breve en español "
            "rioplatense para que otro agente redacte la pieza. El código te proporciona "
            "la guía y el historial como evidencia. Usá el canal y segmento del pedido "
            "cuando estén indicados. Identificá qué enfoque anterior evitar y proponé un "
            "ángulo concreto que no lo repita. El pedido es la fuente para los hechos "
            "comerciales. La guía aporta reglas y el historial aporta antecedentes. "
            "Las ofertas pasadas no están autorizadas para una pieza nueva. "
            "En objetivo y enfoque evitá inventar precios, beneficios, plazos o prestaciones. "
            "Cuando el pedido solo menciona una categoría, proponé una acción útil "
            "que el cliente pueda realizar sin depender de prestaciones o ventajas no confirmadas. "
            "Si un dato indispensable para cumplir el pedido falta, registralo en datos_faltantes."
        ),
    )


def preparar_brief(pedido: str, *, canal=None, segmento=None, promocion="ninguna"):
    """Carga la evidencia para los campos del pedido ya identificados."""
    guia = consultar_guia_marca.invoke({
        "situacion": pedido, "canal": canal, "segmento": segmento, "promocion": promocion,
    })
    historial = consultar_historial.invoke({"canal": canal, "segmento": segmento})
    entrada = {"pedido": pedido, "guia": guia, "historial": historial}
    resultado = crear_estratega().invoke(
        {"messages": [{"role": "user", "content": json.dumps(entrada, ensure_ascii=False)}]},
        {"recursion_limit": 12},
    )
    return {
        "pedido": pedido,
        "canal": canal,
        "segmento": segmento,
        "promocion": promocion,
        "reglas_aplicables": guia,
        "historial": historial,
        "estrategia": resultado["structured_response"].model_dump(),
    }


class Pedido(BaseModel):
    canal: Literal["Instagram", "Email", "WhatsApp", "Push", "LinkedIn"] | None
    segmento: Literal["Nuevos", "Recurrentes", "Premium", "Todos"] | None
    promocion: Literal["descuento", "cuotas", "envío sin cargo", "ninguna"]
    guardar: bool
    es_marketing: bool


class Pieza(BaseModel):
    titulo: str
    texto: str


class Revision(BaseModel):
    veredicto: Literal["aprobar", "corregir", "pedir_datos"]
    observacion: str


class Estado(TypedDict, total=False):
    pregunta: str
    pedido: Pedido
    brief: dict
    pieza: Pieza
    revision: Revision
    correcciones: int
    respuesta: str
    detalle: list[dict]


@lru_cache(maxsize=None)
def _agente(esquema, instrucciones):
    load_dotenv()
    return create_agent(
        ChatGroq(model="openai/gpt-oss-20b", temperature=0, reasoning_effort="low", timeout=25, max_retries=1),
        tools=[], response_format=ToolStrategy(esquema), system_prompt=instrucciones,
    )


def _consultar(esquema, instrucciones, entrada):
    return _agente(esquema, instrucciones).invoke(
        {"messages": [{"role": "user", "content": json.dumps(entrada, ensure_ascii=False)}]},
        {"recursion_limit": 12},
    )["structured_response"]


def _detalle(estado, titulo, contenido):
    return [*estado.get("detalle", []), {"titulo": titulo, "contenido": contenido}]


def _estratega(estado):
    pregunta = estado["pregunta"]
    pedido = _consultar(
        Pedido,
        "Identificá los datos explícitos de un pedido de contenido de Marketing para Hornero. "
        "Usá null para canal o segmento omitidos. Si se pide recuperar clientes por una entrega, "
        "eso es Marketing. Marcá guardar solo si el usuario lo solicita expresamente. "
        "Sin descuento significa ninguna si no hay otro beneficio.",
        pregunta,
    )
    if not pedido.es_marketing or pedido.canal is None:
        mensaje = ("¿Para qué canal querés la pieza?" if pedido.es_marketing
                   else "Puedo ayudarte a generar piezas de marketing para Hornero.")
        return {"pedido": pedido, "respuesta": mensaje}
    if pedido.promocion == "descuento":
        if pedido.canal == "WhatsApp":
            patron = r"(?:https?://|\bwww\.)[^\s<>]+|\b[\w.-]+\.com\.ar/[^\s<>]+"
            pregunta_faltante = (
                "¿Cuál es el enlace oficial a las bases y condiciones del descuento? "
                "Para continuar, reenviá el pedido original con ese enlace."
            )
        else:
            patron = r"\d{1,2}/\d{1,2}.*\d{1,2}/\d{1,2}"
            pregunta_faltante = "¿Entre qué fechas aplica el descuento? Reenviá el pedido con la vigencia."
        if not re.search(patron, pregunta):
            respuesta = pregunta_faltante
            if pedido.canal == "WhatsApp":
                porcentaje = re.search(r"(?<![\d.,+-])(\d{1,3}(?:[.,]\d+)?)\s*%\s+de\s+descuento\b", pregunta, re.IGNORECASE)
                categoria = re.search(r"\bdescuento en (Cocina|Electro|Muebles|Jardín)\b", pregunta, re.IGNORECASE)
                if porcentaje:
                    rubro = f" en {categoria[1].capitalize()}" if categoria else ""
                    borrador = f"Tenés un {porcentaje[1]} % de descuento{rubro}. "
                else:
                    borrador = "Tenés un descuento. "
                borrador += "Consultá las bases y condiciones: [enlace oficial]"
                respuesta = f"**Borrador pendiente de aprobación**\n\n{borrador}\n\n{pregunta_faltante}"
            return {"pedido": pedido, "respuesta": respuesta,
                    "detalle": _detalle(estado, "Estratega · faltan datos", pregunta_faltante)}
    brief = preparar_brief(pregunta, canal=pedido.canal, segmento=pedido.segmento,
                           promocion=pedido.promocion)
    return {"pedido": pedido, "brief": brief, "correcciones": 0,
            "detalle": _detalle(estado, "Estratega · guía e historial",
                                json.dumps(brief["estrategia"], ensure_ascii=False, indent=2))}


def _redactor(estado):
    brief = estado["brief"]
    entrada = {k: brief[k] for k in ("pedido", "reglas_aplicables", "estrategia")}
    if estado["correcciones"]:
        entrada.update(borrador=estado["pieza"].model_dump(),
                       observacion=estado["revision"].observacion)
    formato = " Usá imperativos rioplatenses como elegí, abrí y mirá."
    if estado["pedido"].canal == "Push":
        formato += (" Para push, escribí un título de hasta 40 caracteres y una sola frase "
                   "de hasta 90 caracteres, incluidos espacios. El push abre la app por "
                   "su funcionamiento. No agregues la etiqueta «Abre la app».")
    pieza = _consultar(
        Pieza,
        "Redactá una pieza de Hornero en voseo. Usá el pedido como fuente de hechos "
        "comerciales y la guía como fuente de reglas. La estrategia es orientativa: "
        "omití toda oferta, prestación o promesa sugerida que el pedido no respalde. "
        "El segmento Premium orienta el tono. Solo el pedido puede confirmar acceso anticipado. "
        "No inventes frecuencias de mantenimiento, fechas, enlaces ni códigos. "
        "Entregá el título y el texto sin etiquetas ni comentarios editoriales." + formato,
        entrada,
    )
    return {"pieza": pieza, "detalle": _detalle(estado, "Redactor", f"{pieza.titulo}\n{pieza.texto}")}


def _revisor(estado):
    brief, pedido, pieza = estado["brief"], estado["pedido"], estado["pieza"]
    revision = _consultar(
        Revision,
        "Revisá la pieza con la guía, el pedido original y el antecedente editorial. "
        "Evaluá tono, formato, repetición y respaldo de todas las afirmaciones. "
        "La guía pide voseo. ‘Elegí’, ‘abrí’ y ‘mirá’ son correctos. "
        "Pedí corregir el tuteo (‘elige’, ‘abre’, ‘mira’) y el acceso anticipado sin respaldo. "
        "No inventes datos en la observación. Si la guía exige un beneficio de recuperación "
        "y el pedido no indica cuál está autorizado, usá pedir_datos y preguntá cuál es. "
        "El historial sirve para evitar repetición. Sus promociones no autorizan ofertas nuevas. "
        "Si se puede quitar una afirmación inventada conservando el pedido, pedí corregir. "
        "Si falta un dato indispensable, como vigencia o enlace de bases para un descuento "
        "solicitado, pedí datos. Aprobá solo una pieza lista para usar. No la reescribas.",
        {"pedido": brief["pedido"], "reglas": brief["reglas_aplicables"],
         "antecedente": brief["historial"][:1], "pieza": pieza.model_dump()},
    )
    if pedido.canal == "Push" and revision.veredicto != "pedir_datos":
        patron = r"\b\d+\s+(?:horas?|días?|semanas?|mes(?:es)?|años?)\b"
        plazos_pedido = set(re.findall(patron, estado["pregunta"].casefold()))
        plazos_pieza = set(re.findall(patron, f"{pieza.titulo} {pieza.texto}".casefold()))
        observaciones = []
        if plazos_pieza - plazos_pedido:
            observaciones.append("Quitá las frecuencias o plazos numéricos que el pedido no respalda.")
        if re.search(r"\babre la app\b", f"{pieza.titulo} {pieza.texto}", re.IGNORECASE):
            observaciones.append("Quitá «Abre la app». La apertura es una acción del push.")
        if observaciones:
            if revision.veredicto == "corregir":
                observaciones.append(revision.observacion)
            revision = Revision(veredicto="corregir", observacion=" ".join(observaciones))
    limites = {"Push": (40, 90), "Instagram": (None, 2200),
               "WhatsApp": (None, 300), "LinkedIn": (None, 1300), "Email": (50, None)}
    titulo, cuerpo = limites.get(pedido.canal, (None, None))
    if revision.veredicto != "pedir_datos" and (
        (titulo and len(pieza.titulo) > titulo) or (cuerpo and len(pieza.texto) > cuerpo)
        or (pedido.canal == "Email" and len(pieza.texto.split()) > 150)
    ):
        revision = Revision(veredicto="corregir",
                            observacion=(f"Ajustá los límites de {pedido.canal} según la guía. "
                                         f"Título actual: {len(pieza.titulo)} caracteres. "
                                         f"Texto actual: {len(pieza.texto)} caracteres. "
                                         + (revision.observacion if revision.veredicto == "corregir" else "")))
    return {"revision": revision,
            "detalle": _detalle(estado, f"Revisor · {revision.veredicto}", revision.observacion)}


def _terminar(estado):
    revision, pieza, pedido = estado["revision"], estado["pieza"], estado["pedido"]
    if revision.veredicto != "aprobar":
        return {"respuesta": f"Pieza pendiente. {revision.observacion}"}
    respuesta = f"**{pieza.titulo}**\n\n{pieza.texto}"
    if pedido.guardar:
        resultado = guardar_pieza.invoke({"canal": pedido.canal, "segmento": pedido.segmento or "Todos",
                                         **pieza.model_dump()})
        respuesta = f"{respuesta}\n\n{resultado}"
        return {"respuesta": respuesta, "detalle": _detalle(estado, "Historial", resultado)}
    return {"respuesta": respuesta}


def _contar_correccion(estado):
    return {"correcciones": estado["correcciones"] + 1}


@lru_cache(maxsize=1)
def _grafo():
    grafo = StateGraph(Estado)
    for nodo in (_estratega, _redactor, _revisor, _contar_correccion, _terminar):
        grafo.add_node(nodo.__name__, nodo)
    grafo.add_edge(START, "_estratega")
    grafo.add_conditional_edges("_estratega", lambda e: END if "respuesta" in e else "_redactor",
                               [END, "_redactor"])
    grafo.add_edge("_redactor", "_revisor")
    grafo.add_conditional_edges(
        "_revisor",
        lambda e: "_contar_correccion" if e["revision"].veredicto == "corregir" and not e["correcciones"]
        else "_terminar",
        ["_contar_correccion", "_terminar"],
    )
    grafo.add_edge("_contar_correccion", "_redactor")
    grafo.add_edge("_terminar", END)
    return grafo.compile()


def responder(pregunta: str) -> dict:
    try:
        estado = _grafo().invoke({"pregunta": pregunta})
    except RateLimitError:
        return {"respuesta": "Groq alcanzó su límite temporal. Probá de nuevo más tarde.", "detalle": []}
    except APIError:
        return {"respuesta": "Groq no pudo completar el pedido. Probá de nuevo.", "detalle": []}
    return {"respuesta": estado["respuesta"], "detalle": estado.get("detalle", [])}
