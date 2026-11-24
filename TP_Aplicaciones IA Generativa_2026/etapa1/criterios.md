# Hornero · Decisiones de diseño de la Etapa 1

## Paso 1 · Entorno y arquitectura (24/11/2026)

Usamos el entorno virtual compartido de la materia con Python 3.11.15. Consideramos crear uno exclusivo para el TP. La simulación de instalación conjunta resolvió los requisitos sin reemplazar versiones existentes. Después de instalar Streamlit, los 196 paquetes pasaron la comprobación de compatibilidad. En la app base, la pregunta sobre la fecha produjo una llamada a fecha_de_hoy y una respuesta. Queda por probar la ejecución independiente desde etapa1/ una vez armada.

### Flujo acordado

| Agente | Información disponible | Responsabilidad |
| --- | --- | --- |
| Estratega | Pedido, guía e historial editorial | Elaborar un brief con público, canal, objetivo, hechos autorizados, reglas y antecedentes relevantes. |
| Redactor | Brief y, en una segunda pasada, borrador y observación | Escribir la pieza y realizar la corrección solicitada. |
| Revisor | Borrador, requisitos del pedido, antecedente relevante y acceso a la guía | Evaluar la pieza, explicar el ajuste necesario o identificar el dato faltante. |

El StateGraph ejecuta los tres roles en secuencia. Cada nodo selecciona los campos que incorpora al contexto del agente. Para evaluar la originalidad de un push, por ejemplo, el revisor necesita conocer el enfoque del push anterior. Alcanza con pasarle ese antecedente.

El revisor puede aprobar, solicitar una corrección o indicar que falta información comercial. El código lleva la cuenta de las correcciones por pedido. La primera observación devuelve el borrador al redactor. Una segunda observación cierra la ejecución con la pieza pendiente. Un dato comercial faltante da lugar a una consulta al usuario desde la primera revisión. Solo las piezas aprobadas pueden guardarse.

Consideramos que el revisor editara directamente. Elegimos mantener la autoría en el redactor y hacer visible qué observó el revisor y cómo se corrigió. El costo máximo de esa decisión es una ejecución adicional de cada uno de esos dos nodos. Una prueba prevista consiste en forzar dos pedidos de ajuste consecutivos y comprobar que el flujo finalice sin escribir en el CSV.

### Contrato de entrega

La carpeta etapa1/ debe poder ejecutarse con streamlit run main.py. La interfaz invoca responder(pregunta) y recibe respuesta y detalle. Cada entrada de detalle contiene titulo y contenido. El diseño del grafo está acordado y su implementación y validación quedan pendientes.

## Próxima decisión · Recuperación de reglas de marca

Evaluar chunks por sección y por fila de canal frente a ventanas de tamaño fijo. Usar como caso de prueba un WhatsApp con descuento. La evidencia recuperada debe permitir identificar tanto las reglas de WhatsApp como los legales de la promoción.

## Paso 2 · Primera prueba de recuperación

Extrajimos 26 fragmentos de la guía, conservando encabezados en las filas de las tablas. Usamos el modelo multilingüe de Clase 1 con vectores normalizados e IndexFlatIP para buscar por similitud coseno. Guardamos el índice y los textos juntos. La segunda ejecución reutilizó el índice y reprodujo el orden de resultados. En este entorno macOS se usó un hilo OpenMP tras un fallo de ejecución con la configuración por defecto.

Para el WhatsApp de Nuevos con descuento en Cocina, el segmento quedó primero, el canal segundo y el legal de descuentos quinto, después del legal de cuotas. Un top 3 omitiría una regla obligatoria. Antes de fijar la cantidad de fragmentos, queda evaluar las demás consultas del TP y comparar con búsquedas específicas por tipo de regla.

## Comparación sobre las cuatro consultas oficiales

Con el mismo índice, comparamos el pedido completo con subconsultas manuales por canal, segmento explícito y situación aplicable. En la segunda estrategia intercalamos los resultados por puesto y quitamos duplicados. Ambas entregaron cinco fragmentos. Contamos como acierto recuperar el bloque específico de referencia.

| Caso | Bloques de referencia | Pedido completo | Subconsultas |
|---|---|---:|---:|
| Instagram | Instagram, Premium, tono de lanzamiento | 1/3 | 2/3 |
| Email | Email, recuperación, plazos de entrega | 1/3 | 3/3 |
| WhatsApp | WhatsApp, Nuevos, descuentos | 3/3 | 2/3 |
| Push | Push, Recurrentes | 1/2 | 2/2 |

En total se recuperaron 6 y 9 de las 11 referencias respectivamente. Los fragmentos fuera de esa selección ocuparon 4111 y 2592 caracteres. Pueden aportar contexto complementario. La estrategia por subconsultas perdió el legal de descuentos y omitió el tono de lanzamiento. La prueba mide recuperación con subconsultas formuladas a mano, sin evaluar la capacidad de un agente para derivarlas ni la calidad del texto final. Para el push, la verificación de repetición requiere además el historial editorial.

## Prueba de recuperación híbrida

Sobre los mismos cuatro pedidos y referencias, detectamos menciones explícitas de los cinco canales, tres segmentos y tres tipos de promoción mediante coincidencia de palabras. Seleccionamos las filas o reglas correspondientes por encabezado y completamos hasta cinco fragmentos únicos con el ranking FAISS del pedido completo. No hubo clasificación por LLM.

En orden Instagram, Email, WhatsApp y Push, la cobertura fue 2/3, 2/3, 3/3 y 2/2. Total 9/11, con 3266 caracteres fuera de las referencias elegidas. Faltaron el tono de lanzamiento y la regla sobre plazos. Se recuperó el legal de descuentos ausente en la estrategia por subconsultas. La detección literal se evaluó solo en pedidos con menciones afirmativas. Quedan sin evaluar sinónimos, negaciones y ambigüedades. La prueba se ejecutó sin integrar una tool al agente.

## Tool de consulta de la guía

consultar_guia_marca recibe situación, canal, segmento y promoción aplicable. Selecciona fragmentos por encabezado y completa hasta cinco con FAISS. Los legales promocionales entran por el campo promoción para evitar activar un beneficio por mera similitud. Esto hace que la interpretación del pedido por el agente sea decisiva. El contrato actual admite un beneficio por llamada.

Prueba aislada mediante invoke, reutilizando el índice guardado. Para WhatsApp y Nuevos con descuento devolvió tres reglas obligatorias y dos fragmentos complementarios. Con promoción ninguna devolvió dos reglas obligatorias y tres complementarios. Verificamos que el legal de descuento solo se seleccionó en el primer caso. La interpretación autónoma de ambos pedidos por el LLM queda pendiente.

## Prueba de argumentos generados por el modelo

Probamos dos pedidos independientes con create_agent, Groq openai/gpt-oss-20b, temperatura 0 y reasoning_effort bajo. El prompt pidió consultar la guía para producir un brief. En una corrida por pedido, el modelo hizo una llamada exitosa a consultar_guia_marca con WhatsApp y Nuevos en ambos casos. Para el 15 % en Cocina indicó descuento y se recuperó el legal. Para la variante sin descuento indicó ninguna y se recuperaron las reglas de canal y segmento. En el primer caso usó el pedido entero como situación y en el segundo solo “Cocina”. Esta prueba verifica selección de argumentos en esos dos ejemplos. La calidad del brief y la estabilidad entre corridas quedan por evaluar.

## Historial editorial de lectura

consultar_historial lee el CSV en cada llamada para ver nuevas aprobaciones. Filtra por canal y segmento opcionales e incluye piezas dirigidas a Todos cuando busca para un segmento concreto. Devuelve hasta tres antecedentes por fecha descendente, con título y hasta 320 caracteres de texto para acotar el contexto. Una campaña anterior puede quedar fuera de esa ventana.

En una prueba aislada con Groq, el modelo eligió Push y Recurrentes, recuperó el push del 20/10 e identificó su título y llamado a la acción como elementos a evitar. Sugirió como alternativa una oferta exclusiva sin sustento en el pedido. En el brief final habrá que controlar que las ideas respeten los hechos autorizados. Se comprobó también una búsqueda sin coincidencias y la inclusión de comunicaciones a Todos.
