# Hornero · Bitácora de la Etapa 2

## 26/11/2026 · Propuesta inicial · E2-01

Estado: diseño propuesto, sin código ejecutable ni modelos entrenados. El estado de tareas se mantiene en `../../docs/ROADMAP.md`.

Se propone un orquestador con especialistas Marketing, RRHH y Supply. Marketing reutilizará el grafo de Etapa 1. RRHH tendrá herramientas de políticas, SQL empleados y attrition. Supply tendrá SQL ventas, modelo predictivo y clima. Cada especialista tendrá acceso solo a sus fuentes.

Se prefiere delegación por área frente a aplicar una secuencia fija a todas las consultas, para cumplir la estructura distinta de Etapa 1 y evitar llamadas innecesarias. El detalle de módulos y colaboración está en `../../docs/ARQUITECTURA.md`.

Antes de implementar: acordar contratos, particiones de validación de modelos, variables permitidas en simulación y adaptación de imports para reutilizar Marketing sin copiarlo.

Registrar aquí avances de RRHH, Supply e integración con fecha, tarea, decisión, alternativa, pruebas y siguiente paso. No usar esta bitácora como lista duplicada de pendientes.
