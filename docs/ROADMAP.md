# Hoja de ruta del TP Hornero

Fuente única del estado actual. Última revisión: 26/11/2026. Los responsables quedan sin asignar hasta acuerdo del equipo. `Implementado` no significa validado editorialmente.

| ID | Tarea / criterio de cierre | Estado | Responsable | Evidencia o dependencia |
| --- | --- | --- | --- | --- |
| G-01 | Ignorar secretos, entornos y cachés | Hecho | Sin asignar | `.gitignore`; `.env` no estaba versionado |
| G-02 | Documentar instalación, arquitectura y trabajo con IA | Hecho | Sin asignar | README, AGENTS, arquitectura y bitácoras |
| G-03 | Instalar y verificar entorno Windows | Hecho | Sin asignar | Python 3.12.10, 121 paquetes fijados, `pip check` sin conflictos; ver bitácora |
| G-04 | Acordar responsables, ramas, PR y protección de main | Pendiente | Sin asignar | Flujo propuesto en README; configuración remota no verificada |
| G-05 | Separar y renombrar ejemplos para evitar ejecutar el agente básico por error | Hecho | Sin asignar | `ejemplos/`; títulos distintos; seis tests y script funcional OK; ver bitácora |
| E1-01 | Tres roles con StateGraph y una ronda de corrección | Implementado | Sin asignar | `etapa1/agentes.py`; falta evaluación editorial final |
| E1-02 | RAG persistente y herramientas de historial | Implementado | Sin asignar | `etapa1/rag_guia.py`, `tools.py` |
| E1-03 | Pruebas técnicas reproducibles, UI y Groq | Hecho | Sin asignar | Seis tests OK; RAG real, AppTest en ambas entradas, Groq real y HTTP 200; ver bitácora |
| E1-04 | Evaluar cuatro consultas oficiales contra guía y pedido | Pendiente | Sin asignar | Bitácora contiene pruebas parciales; no repetir como evaluación técnica |
| E1-05 | Guardar y revisar piezas de entrega | Pendiente | Sin asignar | CSV conserva las ocho filas originales |
| E2-01 | Acordar orquestador, contratos y reutilización de Marketing | Propuesto | Sin asignar | `docs/ARQUITECTURA.md`; resolver imports sin duplicar código |
| E2-02 | RAG de políticas RRHH | Pendiente | Sin asignar | Manual provisto |
| E2-03 | Entrenar/validar attrition y tools de predicción, interpretación y simulación | Pendiente | Sin asignar | `empleados.csv`; definir partición y métrica |
| E2-04 | Entrenar/validar ventas y tools generales | Pendiente | Sin asignar | `ventas.csv`; separar temporalmente entrenamiento y validación |
| E2-05 | Agentes SQL empleados/ventas con BD solo lectura | Pendiente | Sin asignar | SQLDatabaseToolkit; verificar rechazo de escritura |
| E2-06 | MCP clima y agregación para pronóstico de ventas | Pendiente | Sin asignar | CSV alternativo solo con explicación del intento MCP |
| E2-07 | App única, mínimo privilegio, rechazo fuera de alcance y tiempos | Pendiente | Sin asignar | Depende de especialistas y orquestador |
| E2-08 | Ocho consultas oficiales y dos propias con tiempos | Pendiente | Sin asignar | Medición real de punta a punta |
| D-01 | Informe PDF de ambas etapas con diagramas y evidencia | Pendiente | Sin asignar | Máximo 10 páginas sin carátula; anexo opcional hasta 5 |
| D-02 | Empaquetar ambas apps, CSV e informe; excluir secretos/venv | Pendiente | Sin asignar | Probar ambas apps desde sus carpetas |
| D-03 | Confirmar fecha de entrega en campus | Pendiente | Sin asignar | PDF contradice 29/11 con tabla hasta 6/12 sin descuento |
| X-01 | A2A | Opcional | Sin asignar | Solo después de cerrar requisitos mínimos |

## Orden sugerido

1. Cerrar instalación y pruebas técnicas de Etapa 1.
2. Acordar contratos de Etapa 2 y responsables. Desarrollar RRHH y Supply por frentes.
3. Integrar Marketing, orquestador, límites y mediciones.
4. Ejecutar consultas oficiales, consolidar CSV, informe y paquete final.

Al cambiar un estado, enlazar evidencia en la bitácora de la etapa. Evitar duplicar esta tabla en otros documentos.
