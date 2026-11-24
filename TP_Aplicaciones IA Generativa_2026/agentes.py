"""
agentes.py: acá se definen los agentes y cómo se conectan entre sí.

Por ahora hay un único agente muy simple, con un system prompt trivial y una sola
tool. Para el TP lo tienen que reemplazar por el sistema multiagente que diseñen.

main.py solo usa la función responder(): mientras respeten lo que devuelve,
pueden cambiar todo lo que hay detrás sin tocar la app de Streamlit.
"""

import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_groq import ChatGroq

from tools import fecha_de_hoy

load_dotenv()

MODELO = "openai/gpt-oss-20b"
# reasoning_effort="low": con el valor por defecto, gpt-oss-20b a veces razona hasta agotar los
# tokens de salida y devuelve una respuesta vacía. Además gasta muchos menos tokens.
llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model=MODELO, temperature=0.0, max_retries=5,
               reasoning_effort="low")


# --------------------------------------------------------------------------
# Helpers (los mismos de la notebook de la Clase 4)
# --------------------------------------------------------------------------

def preguntar(agente, texto: str, verbose: bool = False) -> str:
    # Invoca un agente y devuelve su respuesta final.
    # Con verbose=True muestra qué tools llamó.
    resultado = agente.invoke({"messages": [{"role": "user", "content": texto}]})
    if verbose:
        mostrar_pasos(resultado)
    return resultado["messages"][-1].content


def mostrar_pasos(resultado) -> list:
    # Imprime las tools que llamó el agente, en orden, y devuelve sus nombres.
    nombres = []
    print("  [PASOS INTERMEDIOS]")
    for msg in resultado["messages"]:
        for tc in getattr(msg, "tool_calls", None) or []:
            print(f"  → Llama tool: {tc['name']}({tc['args']})")
            nombres.append(tc["name"])
    print()
    return nombres


def pasos_para_la_app(resultado) -> list[dict]:
    # Igual que mostrar_pasos, pero devuelve los pasos en el formato que muestra main.py
    return [{"titulo": f"Tool llamada: {tc['name']}", "contenido": str(tc["args"])}
            for msg in resultado["messages"] for tc in (getattr(msg, "tool_calls", None) or [])]


# --------------------------------------------------------------------------
# Agente de ejemplo
# --------------------------------------------------------------------------

agente_simple = create_agent(
    model=llm,
    tools=[fecha_de_hoy],
    system_prompt="Sos un asistente amable de Hornero. Respondé en forma breve.",
)


def responder(pregunta: str) -> dict:
    """Punto de entrada que usa main.py.

    Devuelve un diccionario con:
      - "respuesta": el texto final que se muestra en el chat.
      - "detalle": lista de pasos intermedios para mostrar en la app, cada uno como
        {"titulo": str, "contenido": str}. Sirve para ver qué agente o tool actuó.
    """
    resultado = agente_simple.invoke({"messages": [{"role": "user", "content": pregunta}]})
    return {"respuesta": resultado["messages"][-1].content, "detalle": pasos_para_la_app(resultado)}


if __name__ == "__main__":
    print(preguntar(agente_simple, "¿Qué día es hoy?", verbose=True))
