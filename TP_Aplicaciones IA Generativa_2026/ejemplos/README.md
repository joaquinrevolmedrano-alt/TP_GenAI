# Ejemplos originales

Material de referencia provisto con la consigna, separado de la implementación del equipo.

- `main_ejemplo.py`: chat de Streamlit para el agente básico.
- `agentes_ejemplo.py`: agente original con una herramienta de fecha.
- `tools_ejemplo.py`: implementación de `fecha_de_hoy`.
- `ejemplo_mcp.py`: demo independiente de DeepWiki, con llamadas externas al ejecutarse.

Con el entorno activo, desde esta carpeta:

```sh
python -m streamlit run main_ejemplo.py
```

La configuración sigue en `../.env`, sin copiar secretos a esta carpeta. Los datos siguen en `../datos/`. Las rutas se calculan con `pathlib`, compatibles con Windows y macOS.

Para probar el trabajo desarrollado de Marketing, ejecutar `python -m streamlit run main.py` desde `../etapa1/`.
