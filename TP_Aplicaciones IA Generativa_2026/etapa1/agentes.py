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
from validaciones import reglas_formato, validar_formato


POLITICA_FUENTES = (
    "La guía de marca es la fuente de verdad para las reglas y los beneficios explícitos "
    "de cada segmento. Los prompts y el pedido no deben contradecirla. "
    "La guía establece acceso anticipado a lanzamientos para Premium: podés mencionarlo "
    "en una pieza para ese segmento sin pedir que el usuario lo confirme otra vez. "
    "Un beneficio autorizado no obliga a incluirlo: respetá el foco del pedido. "
    "El pedido aporta los hechos particulares de la campaña, como qué colección se anuncia. "
    "No inventes porcentajes, precios, fechas, horas de anticipación, códigos ni condiciones. "
    "La sección de legales explica cómo comunicar una promoción; no autoriza a ofrecerla. "
    "Los ejemplos de la guía y el historial son referencias, no autorizaciones para "
    "copiar promociones o características de productos a una campaña nueva. "
)


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
        system_prompt=POLITICA_FUENTES + (
            "Sos el estratega de Marketing de Hornero. Prepará un brief breve en español "
            "rioplatense para que otro agente redacte la pieza. El código te proporciona "
            "la guía y el historial como evidencia. Usá el canal y segmento del pedido "
            "cuando estén indicados. Identificá qué enfoque anterior evitar y proponé un "
            "ángulo concreto que no lo repita. Separá hechos de campaña, reglas y beneficios "
            "de la guía, y antecedentes del historial. "
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


class AjusteTexto(BaseModel):
    fragmento: str = Field(min_length=1, description="Cita literal del texto actual que debe cambiar.")
    reemplazo: str = Field(description="Texto corregido para ese fragmento, sin explicaciones.")


class RevisionEditorial(BaseModel):
    ortografia: list[AjusteTexto] = Field(description="Todos los ajustes de ortografía, tildes y gramática; [] si no hay.")
    tono: list[AjusteTexto] = Field(description="Todos los ajustes de voseo y tono; [] si no hay.")
    respaldo: list[str] = Field(description="Todas las afirmaciones sin respaldo que se pueden quitar o corregir; [] si no hay.")
    repeticion: list[str] = Field(description="Repeticiones de antecedentes reales; [] si no hay antecedentes o no se repiten.")
    contenido: list[str] = Field(description="Otros incumplimientos editoriales: mensaje, CTA o reglas de marca; [] si no hay.")
    datos_faltantes: list[str] = Field(description="Preguntas por todos los datos indispensables ausentes; [] si no faltan.")


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
    entrada["controles_formato"] = reglas_formato(estado["pedido"].canal)
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
        POLITICA_FUENTES +
        "Redactá una pieza de Hornero en voseo usando el pedido y la guía según la política de fuentes. "
        "La estrategia es orientativa: omití toda oferta, prestación o promesa sugerida "
        "que no esté respaldada por el pedido o por una regla explícita de la guía. "
        "No inventes frecuencias de mantenimiento, fechas, enlaces ni códigos. "
        "Cumplí controles_formato. Los emojis son opcionales: no tienen mínimo. "
        "En una corrección resolvé todas las observaciones juntas, conservando lo que ya cumple. "
        "Entregá el título y el texto sin etiquetas ni comentarios editoriales." + formato,
        entrada,
    )
    return {"pieza": pieza, "detalle": _detalle(estado, "Redactor", f"{pieza.titulo}\n{pieza.texto}")}


def _revisor(estado):
    brief, pedido, pieza = estado["brief"], estado["pedido"], estado["pieza"]
    formato = validar_formato(pedido.canal, pieza.titulo, pieza.texto)
    if pedido.canal == "Push":
        patron = r"\b\d+\s+(?:horas?|días?|semanas?|mes(?:es)?|años?)\b"
        plazos_pedido = set(re.findall(patron, estado["pregunta"].casefold()))
        plazos_pieza = set(re.findall(patron, f"{pieza.titulo} {pieza.texto}".casefold()))
        if plazos_pieza - plazos_pedido:
            formato.append("Quitá las frecuencias o plazos numéricos que el pedido no respalda.")
        if re.search(r"\babre la app\b", f"{pieza.titulo} {pieza.texto}", re.IGNORECASE):
            formato.append("Quitá «Abre la app». La apertura es una acción del push.")
    editorial = _consultar(
        RevisionEditorial,
        POLITICA_FUENTES +
        "Revisá la pieza con la guía, el pedido original y el antecedente editorial. "
        "Completá TODAS las categorías del esquema en una sola revisión. No te detengas "
        "en el primer error. Evaluá ortografía y tildes, gramática, tono, repetición, "
        "respaldo y contenido, incluso si Python ya detectó errores de formato o faltan datos. "
        "En cada lista incluí todos los ajustes de esa categoría; usá [] si no hay. "
        "Cada entrada debe describir un error vigente y un ajuste concreto. No incluyas "
        "razonamiento, comprobaciones correctas ni frases como ‘no hay errores’. "
        "No repitas el mismo problema en dos categorías. "
        "En ortografia y tono citá el fragmento literal y su reemplazo corregido, "
        "sin explicaciones. Si el fragmento ya está bien, no lo incluyas. "
        "Los conteos de caracteres, palabras, hashtags y emojis ya los resuelve Python: "
        "no los vuelvas a medir ni los agregues a tus categorías. No hay mínimo de emojis: "
        "cero es válido en todos los canales. No conviertas recomendaciones en requisitos. "
        "La guía pide voseo. ‘Elegí’, ‘abrí’ y ‘mirá’ son correctos. "
        "‘Descubrí’ y ‘tenés’ también son voseo correcto. No los reportes como tuteo. "
        "‘Elegi’ sin tilde es un error de ortografía, no de tuteo: señalalo en ortografia "
        "desde la primera revisión, sin repetirlo en tono. "
        "Pedí corregir el tuteo (‘elige’, ‘abre’, ‘mira’). Evaluá el respaldo contra "
        "el pedido y las reglas explícitas de la guía, respetando su prioridad. "
        "No inventes datos en la observación. Si la guía exige un beneficio de recuperación "
        "y el pedido no indica cuál está autorizado, preguntá cuál es en datos_faltantes. "
        "El historial sirve para evitar repetición. Sus promociones no autorizan ofertas nuevas. "
        "Un ejemplo de la guía no es un antecedente del historial. Si no hay antecedentes, "
        "devolvé repeticion=[]. "
        "Si se puede quitar una afirmación inventada conservando el pedido, pedí corregir. "
        "Si falta un dato indispensable, como vigencia o enlace de bases para un descuento "
        "solicitado, preguntá por él en datos_faltantes. No reescribas la pieza.",
        {"pedido": brief["pedido"], "reglas": brief["reglas_aplicables"],
         "antecedente": brief["historial"][:1], "pieza": pieza.model_dump(),
         "errores_formato": formato},
    )
    lenguaje = {"Ortografía": [], "Tono": []}
    cambios = set()
    texto_actual = f"{pieza.titulo}\n\n{pieza.texto}"
    for categoria, ajustes in (("Ortografía", editorial.ortografia), ("Tono", editorial.tono)):
        for ajuste in ajustes:
            cambio = (ajuste.fragmento, ajuste.reemplazo)
            if ajuste.fragmento == ajuste.reemplazo or cambio in cambios:
                continue
            cambios.add(cambio)
            if ajuste.fragmento not in texto_actual:
                lenguaje[categoria].append(
                    f"La corrección cita «{ajuste.fragmento}», que no aparece en la pieza; requiere revisión.")
            else:
                lenguaje[categoria].append(f"Reemplazá «{ajuste.fragmento}» por «{ajuste.reemplazo}».")
    categorias = {"Formato": formato, **lenguaje,
                  "Respaldo": editorial.respaldo, "Repetición": editorial.repeticion,
                  "Contenido": editorial.contenido, "Datos faltantes": editorial.datos_faltantes}
    observaciones = [f"- {categoria}: {error}" for categoria, errores in categorias.items()
                     for error in dict.fromkeys(errores)]
    veredicto = "pedir_datos" if editorial.datos_faltantes else "corregir" if observaciones else "aprobar"
    revision = Revision(veredicto=veredicto,
                        observacion="\n".join(observaciones) or "Sin observaciones de formato ni editoriales.")
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
