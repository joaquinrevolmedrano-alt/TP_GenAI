"""
ejemplo_mcp.py: el ejemplo de MCP de la Clase 4 (server DeepWiki), pero como script de Python.

    python ejemplo_mcp.py

En la notebook escribíamos `await cliente.get_tools()` y `await agente.ainvoke(...)`. Eso funciona
porque Jupyter permite usar `await` directo en una celda. En un archivo .py no se puede: hay que
envolver cada llamada asíncrona en `asyncio.run(...)`. Es lo único que cambia.

¿Por qué hace falta? Las tools que devuelve MultiServerMCPClient son SOLO asíncronas: se llaman con
`ainvoke`, no con `invoke`. Si usan `agente.invoke(...)` con una tool MCP adentro, falla con
"StructuredTool does not support sync invocation".

El script muestra dos formas de usar un server MCP:
  1. Darle las tools MCP directo a un agente y llamarlo con asyncio.run(agente.ainvoke(...)).
  2. Envolver una tool MCP dentro de una tool común (@tool). Así el agente se usa con invoke(),
     como el resto de los agentes del TP (y como lo llama main.py). Es la forma recomendada para el TP.
"""

import asyncio
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="openai/gpt-oss-20b", temperature=0.0,
               max_retries=5, reasoning_effort="low")


# --------------------------------------------------------------------------
# Conectarse al server MCP y ver qué tools ofrece
# --------------------------------------------------------------------------

cliente_mcp = MultiServerMCPClient({
    "deepwiki": {"url": "https://mcp.deepwiki.com/mcp", "transport": "streamable_http"},
})

# En la notebook:   tools_mcp = await cliente_mcp.get_tools()
tools_mcp = asyncio.run(cliente_mcp.get_tools())

print("Tools del server DeepWiki:")
for t in tools_mcp:
    print(f"- {t.name}: parámetros {list(t.args)}")

tools_deepwiki = [t for t in tools_mcp if t.name == "ask_wiki_question"]
pregunta = "En el repo langchain-ai/langgraph, ¿qué es un StateGraph y para qué sirve?"


# --------------------------------------------------------------------------
# Forma 1: agente con las tools MCP, llamado con asyncio.run(agente.ainvoke(...))
# --------------------------------------------------------------------------

agente_mcp = create_agent(
    model=llm,
    tools=tools_deepwiki,
    system_prompt="Respondés preguntas sobre repositorios de GitHub usando tus tools. "
                  "Respondé en español, en 3 o 4 oraciones.",
)

# En la notebook:   resultado = await agente_mcp.ainvoke({...})
resultado = asyncio.run(agente_mcp.ainvoke({"messages": [{"role": "user", "content": pregunta}]}))

print("\n=== Forma 1: agente con tools MCP (ainvoke) ===")
print(resultado["messages"][-1].content)


# --------------------------------------------------------------------------
# Forma 2: la tool MCP envuelta en una tool común
# --------------------------------------------------------------------------
# Ventajas: el agente se llama con invoke() como siempre, y la tool decide qué le devuelve al LLM
# (por ejemplo, puede recortar o resumir una respuesta muy larga del server).

@tool
def preguntar_repo(repo: str, pregunta: str) -> str:
    """Responde una pregunta sobre un repositorio público de GitHub (formato 'dueño/repo')
    usando la documentación que genera DeepWiki."""
    tool_mcp = tools_deepwiki[0]
    respuesta = asyncio.run(tool_mcp.ainvoke({"repoName": repo, "question": pregunta}))
    # Las tools MCP devuelven una lista de bloques de contenido: nos quedamos con el texto
    texto = respuesta[0]["text"] if isinstance(respuesta, list) else str(respuesta)
    return texto[:3000]   # recortamos para no gastar tokens de más


agente_comun = create_agent(
    model=llm,
    tools=[preguntar_repo],
    system_prompt="Respondés preguntas sobre repositorios de GitHub usando tus tools. "
                  "Respondé en español, en 3 o 4 oraciones.",
)

resultado = agente_comun.invoke({"messages": [{"role": "user", "content": pregunta}]})

print("\n=== Forma 2: tool MCP dentro de un @tool (invoke) ===")
print(resultado["messages"][-1].content)
