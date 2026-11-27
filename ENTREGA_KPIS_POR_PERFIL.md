# AutoCredit Advisor · KPI iniciales por perfil

**Responsable del trabajo:** Yexalén Quetzalli Lozano Gaytán · A01664722  
**Base:** `data/Base_SAS_Equipo3.csv`  
**Propósito:** cada usuario autenticado ve indicadores adecuados a su decisión y permisos.

## Alcance implementado

P7 (`vistas/p7_kpis.py`) se muestra en el menú de los perfiles **Adrián, Sofía, Mariana y Luis**. Mantiene el control de acceso por rol de `src/seguridad.py`.

| Cuenta | Perfil | KPI 1 | KPI 2 | KPI 3 | Fuente |
|---|---|---|---|---|---|
| Adrián Pérez | Analista | Solicitudes asignadas | Pendientes de atender | Casos con datos por revisar | Bandeja de DEMOSTRACIÓN filtrada por A-017 |
| Sofía Reyes | Analista | Solicitudes asignadas | Pendientes de atender | Casos con datos por revisar | Bandeja de DEMOSTRACIÓN filtrada por A-022 |
| Mariana Torres | Gerente | Registros crediticios | Tasa histórica de default | DTI promedio | CSV REAL, agregados |
| Luis Ramírez | Operación | Registros revisados | Porcentaje con variables críticas completas | Filas fuera de límites | CSV REAL, agregados |

Los dos analistas comparten el **tipo de KPI**, no los casos ni las asignaciones. Estas dos bandejas son simuladas, construidas con filas del holdout. Los totales de créditos de la institución, la producción real y las fechas de originación no están en el CSV.

## Fórmulas y procedencia

- `Registros crediticios = número de filas del CSV`. Esto **no prueba** que se trate de 80,000 créditos o clientes únicos.
- `Tasa histórica de default = número de DEFAULT=1 / número de DEFAULT con dato válido`.
- `DTI promedio = media de DEBT_TO_INCOME` (presentada como porcentaje).
- `Campos críticos completos = registros con todos los valores de VARIABLES_CLAVE no nulos / registros totales`.
- `Fuera de límites = filas con al menos una entrada fuera de LIMITES_VALIDOS`.
- `Solicitudes asignadas = filas de la bandeja de demo del analista autenticado`.
- `Pendientes = filas de SU bandeja con ESTADO_SOLICITUD='Pendiente'`.
- `Datos por revisar = filas de SU bandeja con CALIDAD!='Completo'`.

## Límites y siguiente etapa

1. Las métricas de Mariana y Luis son resultados históricos de una base estática, no mediciones de producción en tiempo real.
2. Los indicadores de Adrián y Sofía representan **escenarios simulados** para probar el flujo de la aplicación, no casos reales de clientes actuales.
3. Existe una regresión logística preliminar en `src/modelo.py`, con una partición train/holdout, pero **no** hay aún una comparación concluyente de tres modelos ni un campeón validado con el protocolo de Entrega 4.
4. No se crea todavía un perfil adicional para evaluación de modelos. En la siguiente fase se definirá si Luis necesita ese módulo o si existe realmente un rol distinto de validación independiente.
5. La matriz TP/FP/FN/TN, ROC, AUC, KS, precision y recall se incluirán cuando haya modelos, partición y umbrales documentados; no se usarán cifras inventadas ni métricas del conjunto de entrenamiento como prueba final.
6. Para prevenir sesgo y fuga de información, la evaluación debe hacerse sobre una partición reservada, con preprocesamiento ajustado **solo en entrenamiento**, y reportar resultados por segmentos únicamente cuando la base y los permisos lo permitan. Ocultar KPI por rol no elimina el sesgo estadístico.

## Evidencia sugerida

- Captura de P7 como Adrián y como Sofía (sin mostrar folios en la entrega).
- Captura de P7 como Mariana y como Luis.
- Metodología de cada grupo de KPI desplegada desde el panel explicativo.
- Pruebas: `pytest -q tests/test_kpis.py tests/test_kpis_por_perfil.py tests/test_seguridad.py`.
