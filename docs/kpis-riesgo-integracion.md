# Ajuste final de KPI · AutoCredit Advisor V3

**Alcance limitado:** únicamente el KPI inicial de riesgo y el KPI de productividad de las cuatro pantallas donde aparecen: P1 Bandeja, Mis indicadores, Analistas y KPI y Métricas del área. Los otros dos KPI principales, la política crediticia, XGBoost/Logit, los datos, la bitácora, autorizaciones, gráficas restantes y mensajería mantienen su implementación anterior.

## Cuatro KPI principales, en el mismo orden para Adrián, Sofía y Mariana

| Orden | KPI visible | Cálculo | Meta de gerencia |
|---|---|---|---|
| 1 | **Atención prioritaria de riesgo alto** | **Casos con recomendación guardada `Rechazar` y decisión registrada en el mes / total de decisiones únicas registradas en el mes.** El contador de riesgo alto coincide con el KPI 2; el denominador es *todo el trabajo atendido del mes*. | **60% inicial** por analista, editable por Mariana en **Analistas y KPI**. Se calcula avance respecto de la meta y semáforo. Si no hay decisiones, mostrar «—», nunca 0%. |
| 2 | **Casos de alto riesgo atendidos** | Casos del mes que XGBoost recomendó rechazar al decidir, independientemente de la decisión humana. | Conteo mensual editable, **15 iniciales** por analista, o la meta que ya haya definido gerencia. |
| 3 | **PD promedio evaluada** | Media de la probabilidad `pd_xgb` almacenada al decidir; en gerencia se pondera por decisiones mensuales. | **Sin meta**: es una descripción de riesgo, no un objetivo de aumento. |
| 4 | **Atendidas vs meta** | **Número de solicitudes distintas con decisión del mes / meta de decisiones del mes.** Ya no se usan solicitudes asignadas como denominador del KPI. | **50 iniciales** por analista (clave interna `Decisiones mensuales`), editable por Mariana; para el área la meta de ambos analistas se suma. |

Ejemplo: si Adrián atendió 10 solicitudes y 8 tuvieron recomendación de alto riesgo, el primer KPI presenta **80.0% / 60.0%** y el último **10 / 50** (si gerencia conserva esas metas). El segundo permanece **8 / meta de casos de alto riesgo**, y el tercero mantiene su PD media.

## Interpretación y controles

La **atención prioritaria** mide *en qué proporción se revisan solicitudes riesgosas* dentro del trabajo mensual, y sirve para supervisar el foco operativo. **No es** tasa de default, precisión de XGBoost, pérdidas evitadas, porcentaje de rechazos finales ni calificación de la decisión humana. Una aprobación o condición justificada distinta de la sugerencia XGBoost sigue contándose como caso de alto riesgo revisado. Como depende de la composición de solicitudes, debe interpretarse junto al volumen y nunca usarse para imponer rechazos ni castigar excepciones justificadas.

Se cuenta la **última decisión por Loan ID** en la misma SQLite por ambos roles. Solo se consideran registros cuyo `updated_at` pertenece al mes en `America/Mexico_City`. Se conserva la sugerencia de XGBoost guardada al decidir (no se recalcula con cambios posteriores en la política). Los Loan ID y las asignaciones son demostrativos y los datos son sintéticos.

El KPI de **productividad** es mensual: `decisiones únicas del mes / meta mensual`. Es independiente de la cantidad de préstamos asignados en TEST. Si no hay decisiones se muestra `0 / meta`; la prioridad de riesgo se muestra `— / meta` porque una proporción sin denominador no es evaluable.

La gerente **Mariana** puede editar la meta porcentual de prioridad (entre 0% y 100%, con mínimo positivo), la meta mensual de atenciones, y las metas preexistentes. Su confirmación utiliza `store.set_targets_batch`: guarda en la misma SQLite, conserva metas existentes, y envía notificación a Adrián y Sofía. Ambos analistas ven las metas actualizadas al recargar/rerun su vista.

## Consistencia entre pantallas

| Pantalla | Fuente |
|---|---|
| P1 · Bandeja de Adrián y Sofía | `app_v3.py` llama `monthly_summary(decisiones,analyst_id,scored=M.scores)`. Las tarjetas primera y cuarta toman `store.targets()`. |
| Mis indicadores de Adrián y Sofía | `src/kpi_views.py:render_analyst_month` llama el mismo `monthly_summary` y `store.targets()`. |
| Gerencia · Analistas y KPI | `src/kpi_views.py:render_manager_month` obtiene el resumen mensual individual por analista y la misma tabla `targets`; allí se editan ambas metas. |
| Gerencia · Métricas del área | `src/manager_overview.py:build_team_metrics` agrega conteos de ambos analistas y calcula prioridad como **suma de casos de riesgo alto / suma de decisiones**, nunca promediando porcentajes individuales sin ponderar. Productividad = suma de atendidas / suma de metas mensuales. |

## Verificación y rúbrica

`tests/test_risk_kpi_integration.py` incluye consistencia de las cuatro pantallas, agregación gerencial ponderada, casos con cero decisiones, independencia de `DEFAULT` y excepciones humanas, persistencia SQLite, validación de meta porcentual, edición de metas y avisos a ambos analistas. Las pruebas anteriores de modelo, permisos y el contraste WCAG B3 se mantienen.

El panel de gerencia mantiene el arreglo previo por el cual la curva de productividad usa siempre la meta de `Decisiones mensuales`, aunque se seleccione un indicador informativo sin meta, para evitar el error de `goal=None`. Se conservan las leyendas con espacio suficiente bajo los gráficos.

**Límite de prueba:** CI verifica cálculos, integración y criterios automatizables, pero no certifica que la app desplegada haya actualizado visualmente todos los perfiles. Streamlit Cloud debe apuntar a `app_v3.py` en la rama `v3-integracion-xgboost-12v` después del merge.
