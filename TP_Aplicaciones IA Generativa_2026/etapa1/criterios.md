# Hornero · Decisiones de diseño de la Etapa 1

Bitácora histórica compartida del equipo. El estado vigente y los responsables se
mantienen en `../../docs/ROADMAP.md`; las notas anteriores pueden describir pasos
que luego se completaron o decisiones que se reemplazaron. Agregar nuevas entradas
con fecha, tarea, decisión, alternativa y evidencia de pruebas.

## Verificación técnica del 26/11/2026 · E1-03

Se verificó en Windows/Python 3.12.10 con entorno en una ruta corta. Seis pruebas
reproducibles en `../tests/test_funcionamiento.py` pasaron sin API, con respuestas
simuladas y CSV temporal. `../scripts/verificar_funcionamiento.py --live` comprobó
imports, arranque de ambas interfaces, extracción del PDF, 26 chunks, embeddings,
construcción/recarga FAISS y lectura/escritura temporal. Una consulta real a Groq
completó estratega, redactor y revisor en 4,7 s. Se corrigió UTF-8 explícito en el
JSON del índice. El CSV original quedó intacto con ocho filas.

También se comprobó HTTP 200 del servidor Streamlit y se detuvo el proceso de prueba.
Esta verificación no evalúa tono, hechos ni calidad editorial y no cierra E1-04.
El detalle del entorno y los límites está en `../../docs/BITACORA.md`.

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

## Prototipo del estratega

Implementamos un brief validado con Pydantic y ToolStrategy para pasar campos específicos al redactor. En el push oficial, la primera corrida consultó guía e historial, recuperó «Preparate para el calor» y los límites 40/90, pero propuso una línea nueva, eficiencia energética y garantía de postventa sin respaldo. Tras reforzar el prompt, la segunda corrida mantuvo los límites y consignó tema, canal y segmento, pero omitió la consulta al historial y sugirió control inteligente y eficiencia energética. El esquema asegura la forma del brief. La obligatoriedad de las consultas y el respaldo de las afirmaciones quedan pendientes antes de integrar el redactor.

## Evidencia obligatoria antes de elaborar el brief

preparar_brief invoca ambas tools desde Python y entrega el pedido y sus resultados al estratega. Por ahora el llamador suministra canal, segmento y promoción. En la primera prueba con evidencia precargada se recuperó el antecedente del 20/10, pero el brief todavía sugirió ahorro y facilidad de instalación. Pedimos una sola acción útil y dimos como ejemplo medir el espacio disponible. La segunda prueba conservó el antecedente y los límites 40/90 y elaboró ese consejo sin afirmar prestaciones. Es una prueba con un ejemplo explícito en el prompt. El modelo todavía mezcló reglas de canal en hechos_autorizados. Quedan por validar otros pedidos y el tratamiento de hechos antes de pasar el brief al redactor.

## Separación de fuentes en el brief

Python conserva el pedido original, los filtros, la guía recuperada y el historial en campos separados. El modelo genera únicamente objetivo, enfoque, antecedentes a evitar y datos faltantes. Así, los datos comerciales se contrastan con el pedido original y las reglas conservan el texto de la guía. Se mantiene el alcance de la materia: RAG, tools, prompts y transferencia explícita de contexto entre agentes.

Probamos el push y el email de recuperación con Groq y con filtros suministrados por el llamador. Ambos conservaron el pedido y las reglas obligatorias del canal. Al generalizar el prompt y quitar el ejemplo de aires, el push volvió a sugerir cuotas y ahorro sin respaldo. En el email, el agente propuso un cupón y un destino de enlace sin registrarlos como datos faltantes. La separación de fuentes permite revisar esas afirmaciones contra el pedido, pero la estrategia generada sigue requiriendo revisión. Antes de aprobar o guardar, el flujo debe tratar como pendiente cualquier beneficio o dato indispensable sin respaldo.

## Integración en Streamlit

La Etapa 1 usa StateGraph para ejecutar estratega, redactor y revisor. El estratega identifica los campos del pedido y carga guía e historial. El redactor recibe el pedido, las reglas y la estrategia. El revisor recibe el borrador, el pedido, las reglas y un antecedente. Un contador de Python limita la devolución al redactor a una ronda. El código comprueba los largos del canal y solo invoca la escritura si hay veredicto favorable y pedido de guardado.

En un CSV temporal, verificamos que dos pedidos de corrección terminan sin agregar filas, que corrección seguida de aprobación agrega una fila y que pedir datos termina sin agregar filas. En Streamlit, el primer push quedó pendiente tras dos revisiones por largo. Después de precisar el máximo y las observaciones, otro push y un post de Instagram obtuvieron aprobación del modelo. La revisión humana detectó tuteo en el push y acceso anticipado sin sustento en Instagram. Se reforzaron ambos prompts en esos puntos. El email terminó pendiente y su observación llegó a sugerir un cupón sin respaldo. El caso WhatsApp encontró un error del proveedor durante la tanda. Se agregó manejo de errores de Groq en la interfaz. Las aprobaciones del modelo siguen necesitando contraste con la guía y el pedido.

En la corrida posterior, el revisor confundió «Elegí» con tuteo. Añadimos formas correctas y formas a corregir al prompt del revisor. La calidad lingüística sigue pendiente de validación con el prompt actualizado. La app responde en localhost:8502 y la prueba de escritura usó un archivo temporal.

## Correcciones a partir de la prueba manual en Streamlit

El push aprobado incluyó «cada 15 días» y «Abre la app». El WhatsApp quedó pendiente sin pedir claramente el enlace. Adelantamos la comprobación de datos del descuento al estratega: para WhatsApp sin enlace, pide el enlace y termina antes de redactar o guardar. En push, el código marca para corregir duraciones numéricas ausentes del pedido y la etiqueta literal «Abre la app». Son controles acotados y no validan todas las afirmaciones posibles. Ambas rutas se comprobaron con respuestas simuladas del modelo.

## Borrador visible cuando falta el enlace de WhatsApp

En una prueba manual, el chat mostró solo el veredicto y dejó en el detalle un borrador con fechas y URL ficticias. El caso WhatsApp con descuento sin enlace ahora muestra en el mensaje principal una plantilla pendiente de aprobación con un marcador de enlace. Python reutiliza el porcentaje y las categorías reconocidas cuando aparecen explícitamente. AppTest verificó el pedido del 15 % en Cocina con clasificación simulada, sin escritura en el CSV.
