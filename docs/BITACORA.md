# Bitácora general

El estado vigente vive en [ROADMAP.md](ROADMAP.md). Esta bitácora registra decisiones transversales y evidencia, sin sustituir la historia de cada etapa.

## 26/11/2026 · Organización y entorno · G-01, G-02, G-03

- Autor: asistencia de IA en el checkout local; responsables humanos por acordar.
- Se agregó `.gitignore`. `.env` y `.venv` eran archivos/directorios no versionados y ahora quedan ignorados. `.env.example` se conserva compartible. No se leyó ni imprimió la clave.
- Se mantuvo la arquitectura por etapas exigida por la consigna. Los ejemplos originales permanecen donde estaban; README distingue la entrada real.
- Se creó una sola guía `AGENTS.md`, un roadmap global y bitácoras por etapa. Alternativa descartada por ahora: varias skills y reglas locales que duplicaran estado.
- Se detectó que instalar PyTorch dentro de la ruta larga de OneDrive falla con `OSError: [Errno 2]` en un header interno. Se eligió recrear un entorno en `%USERPROFILE%\.venvs\hornero-tp312`, sin borrar el entorno previo ni cambiar configuración global de Windows.
- Se corrigió `etapa1/rag_guia.py` para leer/escribir JSON en UTF-8 explícito; evita depender de la página de códigos de Windows.

### Resultado de la verificación funcional

Entorno instalado: `C:\Users\matia\.venvs\hornero-tp312`, Python 3.12.10. El `.venv` de la carpeta larga quedó incompleto tras el primer intento: usar el entorno corto, también en el IDE. No se borraron carpetas del usuario.

| Verificación | Comando / mecanismo | Resultado |
| --- | --- | --- |
| Instalación | `python -m pip install -r requirements.txt` en entorno corto | Completa; versiones guardadas en `requirements-lock.txt` (121 paquetes) |
| Compatibilidad declarada | `python -m pip check` | `No broken requirements found` |
| Flujo, escritura e interfaz | `python -m unittest discover -s tests -v` | 6/6 OK; modelo simulado y CSV temporal |
| Imports | `python scripts/verificar_funcionamiento.py --live` | Dependencias de app, agentes, RAG, SQL, MCP y ML importan |
| Interfaces | AppTest en procesos separados para raíz del TP y `etapa1/` | Ambas inician sin excepción y muestran entrada de chat |
| RAG real | Mismo script; extracción, embeddings y FAISS | 26 chunks; construcción y recarga de índice OK; tres reglas obligatorias en WhatsApp/Nuevos/descuento; 4,3 s del bloque RAG en esta corrida |
| CSV | Mismo script y tests | Lectura/escritura temporal OK; original intacto con ocho filas |
| Groq real Marketing | Mismo script | Estratega, redactor y revisor completados; 3 pasos de detalle, 4 llamadas observadas al proveedor, 4,7 s del bloque de grafo |
| Groq real ejemplo | Invocar `responder('¿Qué día es hoy?')` desde raíz del TP y comprobar tool en detalle | Respuesta no vacía y llamada a `fecha_de_hoy` |
| Servidor HTTP | Proceso Streamlit de Etapa 1 en puerto local disponible; GET `/` y `/_stcore/health` | HTTP 200 en ambos; proceso detenido al terminar |
| Higiene Git | `git check-ignore`, `git diff --check` | `.env`/venv ignorados, `.env.example` versionado y diff sin errores de espacios |

Alcance: funcionamiento técnico, sin evaluación editorial. Los tiempos son observaciones de esta máquina y no la tabla exigida para Etapa 2. Importar MCP/SQL/ML no equivale a tener integraciones de Etapa 2 implementadas. No se ejecutó `ejemplo_mcp.py` porque es un demo externo independiente. No se configuró GitHub ni se hicieron commits/push.

Referencias: [entornos virtuales de Python](https://docs.python.org/3/library/venv.html) y [reglas de gitignore](https://git-scm.com/docs/gitignore). Los entornos se recrean localmente; ignorar un archivo no elimina archivos ya versionados. En este checkout `.env` aún no estaba versionado.

## 26/11/2026 · Separación de ejemplos · G-05

- La prueba manual se había hecho sobre el agente básico de fecha por la duplicación de nombres e interfaces. Se trasladaron los cuatro scripts originales a `TP_Aplicaciones IA Generativa_2026/ejemplos/`.
- La interfaz original ahora es `main_ejemplo.py`, con módulos `agentes_ejemplo.py` y `tools_ejemplo.py`. El demo `ejemplo_mcp.py` también se movió. Se ajustaron imports y rutas a `datos/` y `.env` con `pathlib`, sin duplicar configuración ni agregar rutas específicas de Windows.
- Las pantallas ahora se identifican como «Hornero · Ejemplo básico» y «Hornero · Etapa 1 · Marketing». Alternativa descartada: mantener el ejemplo como `main.py` en la raíz, que ya había causado confusión.
- README, AGENTS, arquitectura y script de verificación reflejan las nuevas ubicaciones. Las entradas anteriores de esta bitácora conservan las rutas que existían cuando se hicieron aquellas pruebas.
- Verificación: `python -m unittest discover -s tests -v` pasó 6/6; `python scripts/verificar_funcionamiento.py` pasó imports, arranque y títulos de ambas interfaces, PDF, embeddings, recarga FAISS de 26 chunks y lectura/escritura temporal. Se comprobó además `fecha_de_hoy` y la ruta de datos desde `ejemplos/`. El CSV original quedó intacto y el servidor de Marketing sigue respondiendo HTTP 200 en 8502.
- No se volvieron a consumir llamadas a Groq ni a ejecutar el demo MCP: el cambio afecta organización, imports, rutas y títulos. Código compatible por construcción con Windows/macOS; la ejecución de esta verificación fue en Windows.

## Formato de entradas futuras

Fecha / autor o rama / ID de tarea / decisión y alternativa / archivos afectados / comando y resultado / limitación o próximo paso. No registrar secretos ni copiar conversaciones completas.
