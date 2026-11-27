"""
main_ejemplo.py: aplicación original de ejemplo, con una tool de fecha.

Cómo correrla (desde esta carpeta, con el venv activado):
    streamlit run main_ejemplo.py
"""

import streamlit as st

from agentes_ejemplo import responder

st.set_page_config(page_title="Hornero · Ejemplo básico", page_icon="📚")
st.title("📚 Hornero · Ejemplo básico")
st.caption("Material de referencia: agente con fecha_de_hoy. Para Marketing, ejecutá etapa1/main.py.")

if "historial" not in st.session_state:
    st.session_state.historial = []


def mostrar_detalle(detalle: list[dict]):
    if not detalle:
        return
    with st.expander("Ver detalle (agentes y tools)"):
        for paso in detalle:
            st.markdown(f"**{paso['titulo']}**")
            st.text(paso["contenido"])


# Mostrar la conversación
for mensaje in st.session_state.historial:
    with st.chat_message(mensaje["rol"]):
        st.markdown(mensaje["contenido"])
        mostrar_detalle(mensaje.get("detalle", []))

# Nueva pregunta
if pregunta := st.chat_input("Escribí tu consulta..."):
    st.session_state.historial.append({"rol": "user", "contenido": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            resultado = responder(pregunta)
        st.markdown(resultado["respuesta"])
        mostrar_detalle(resultado.get("detalle", []))

    st.session_state.historial.append({
        "rol": "assistant",
        "contenido": resultado["respuesta"],
        "detalle": resultado.get("detalle", []),
    })
