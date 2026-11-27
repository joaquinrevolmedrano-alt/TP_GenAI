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

## 26/11/2026 · Evaluación manual de Instagram Premium · E1-04

Fuente: salida y detalle compartidos por el usuario desde la aplicación de Etapa 1; no es una nueva ejecución ni una prueba simulada. Pedido: anunciar la nueva colección de muebles de exterior para Premium en Instagram.

El recorrido observado fue estratega, redactor, revisión con corrección, redactor y segunda revisión con corrección. Terminó pendiente al agotarse la única ronda permitida, de acuerdo con el diseño. La primera versión no tenía hashtags y ambas versiones escribieron «Elegi» sin tilde. El revisor pidió los hashtags en la primera revisión, pero detectó la tilde recién en la segunda. Se desperdició la oportunidad de corregir todos los errores juntos.

La exigencia de agregar emojis fue un falso requisito: la tabla de Instagram dice «hasta 3» y las reglas de voz fijan un máximo, no un mínimo. Sí corresponde exigir de tres a cinco hashtags e incluir `#HorneroEnCasa`. La segunda versión cumplía esos conteos, pero conservó la falta de tilde.

Hay una inconsistencia de fuentes que requiere decisión: la sección 7 de la guía menciona acceso anticipado para Premium y la sección 9 lo usa en un ejemplo; en cambio, los prompts de redactor y revisor exigen respaldo en el pedido para esa afirmación. El estratega la propuso y el revisor afirmó que no había datos sin respaldo. Hay que acordar si esas reglas de segmento autorizan un beneficio permanente o si cada campaña debe confirmarlo y aplicar el mismo criterio en los tres roles.

El estratega colocó el ejemplo negativo de la guía en `antecedentes_a_evitar`. Eso no es una pieza histórica. La consulta al CSV actual con los mismos filtros de canal Instagram y segmento Premium/Todos no devuelve filas; ese caso debe representar explícitamente ausencia de antecedentes, sin transformar ejemplos de la guía en historial.

Próximo trabajo: alinear política de fuentes; separar controles objetivos de formato y revisión semántica; recoger todas las observaciones en la primera revisión y evaluar de nuevo. No se modificaron prompts ni se relajó el límite de correcciones en esta evaluación. E1-04 sigue en curso.

## 26/11/2026 · Controles de formato y revisión conjunta · E1-06, E1-07

El usuario autorizó implementar controles objetivos y consolidar las observaciones. La decisión sobre beneficios de segmento se mantiene pendiente en E1-08: puede tratarse el acceso anticipado como derecho permanente de Premium o como beneficio que se confirma por lanzamiento. No se cambió automáticamente esa política.

`validaciones.py` centraliza los límites de la sección 4 de la guía para Instagram, Email, WhatsApp, Push y LinkedIn. Controla largos, palabras del email, cantidad de hashtags, `#HorneroEnCasa` y máximos de emojis. Cero emojis es válido. Para Instagram, WhatsApp y LinkedIn cuenta título y cuerpo publicados; para Push y Email aplica límites separados. Los caracteres se cuentan en Unicode NFC con `len`; los emojis por secuencias visibles, sin contar por separado tonos de piel, banderas o familias. `regex` se declara como dependencia directa; ya estaba instalado y fijado en el lock. Si cambia la guía, revisar también esta tabla de reglas.

El redactor recibe la misma configuración que usa Python. El revisor devuelve todas las categorías en una respuesta estructurada: ortografía, tono, respaldo, repetición, contenido y datos faltantes. Python reúne esa respuesta con los hallazgos objetivos y calcula el veredicto. Un dato faltante conserva los otros hallazgos y termina pendiente. Se mantiene una ronda de corrección y el guardado exclusivo de piezas aprobadas a pedido del usuario.

Las primeras pruebas reales detectaron la tilde y los hashtags juntos, pero el modelo produjo explicaciones contradictorias en tono. Por eso ortografía y tono ahora requieren citas literales con reemplazo concreto. Se eliminan cambios idénticos y duplicados; una cita que no aparece en la pieza se marca para revisión. Los demás juicios editoriales siguen dependiendo del modelo: la estructura no garantiza detectar todos los errores.

Alternativa descartada: aumentar rondas para compensar revisiones parciales.

Validación final: `python -m unittest discover -s tests -v` pasó 16/16 y `pip check` no detectó conflictos. En una revisión real del primer borrador del usuario, Groq devolvió juntos los dos hallazgos de hashtags y el reemplazo «Elegi» por «Elegí», sin exigir emojis ni agregar observaciones de tono. `python scripts/verificar_funcionamiento.py --live` comprobó ambas interfaces, RAG, CSV temporal y el grafo con el nuevo esquema editorial (cinco pasos de detalle, 5,4 s del bloque de grafo). CSV original intacto. Pruebas ejecutadas en Windows; el código no usa rutas ni lógica específicas del sistema operativo. Los cambios quedan locales, sin commit/push en esta tarea. E1-04 y la política de negocio E1-08 siguen pendientes de cierre.

## 26/11/2026 · Prioridad de la guía de marca · E1-08

Decisión del usuario: debe primar la guía. La sección 7 declara el acceso anticipado como beneficio de Premium; no exige confirmarlo por lanzamiento. La condición de reconfirmación había sido agregada en prompts y se retiró. Las entradas anteriores conservan la discusión previa; esta decisión la resuelve.

Se agregó `POLITICA_FUENTES` compartida por estratega, redactor y revisor: la guía determina reglas y beneficios explícitos del segmento; el pedido determina los detalles de la campaña. Un beneficio permitido no obliga a incluirlo. Ejemplos, historial y textos de legales no autorizan promociones nuevas. El acceso anticipado no permite inventar cuántas horas o días de ventaja hay, porcentajes, códigos ni fechas. La misma política queda indicada en AGENTS para evitar que futuros cambios la contradigan.

Validación: 16/16 tests técnicos OK. En dos consultas reales al revisor, una pieza Premium con «la ves antes que nadie» fue aprobada y otra que agregaba 10 % de descuento y código PREMIUM10 fue marcada para corregir por falta de respaldo. Ambas usaron la guía recuperada y el pedido original, sin guardar piezas. E1-08 se cierra; E1-04 requiere repetir las cuatro consultas oficiales con la versión actual.

La verificación completa `python scripts/verificar_funcionamiento.py --live` también pasó con la política compartida: ambas interfaces, RAG y persistencia temporal OK; estratega, redactor y revisor completaron tres pasos de detalle en 5,2 s del bloque de grafo. CSV original intacto.

## 27/11/2026 · Reinicio para pruebas manuales · E1-03, E1-04

Al reiniciar la app se observó que el navegador conectaba y mostraba «Stop», pero no llegaba a renderizar el título mientras se importaban dependencias de IA. `main.py` importaba `agentes` antes de mostrar la interfaz. Se movió ese import al bloque de la primera consulta, dentro del indicador «Pensando...», para mostrar el título y el chat sin esperar esa carga. No cambia la lógica de agentes ni los datos.

Tras reiniciar de nuevo, Chromium confirmó título de Marketing y entrada de chat visibles en `127.0.0.1:8502`. Se abrió la aplicación en el navegador del usuario para repetir las cuatro consultas oficiales. Esta comprobación de arranque no invocó Groq ni modificó el CSV.

Regresión del cambio de arranque: `python -m unittest discover -s tests -p test_funcionamiento.py -v` pasó 9/9, incluida la interacción con el chat y la presentación de respuesta y detalle con el agente simulado.
