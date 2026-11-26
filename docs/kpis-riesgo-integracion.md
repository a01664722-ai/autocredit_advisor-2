# Indicadores de riesgo y productividad · AutoCredit Advisor V3

**Alcance:** ajuste únicamente de KPI en Bandeja (P1), Mis indicadores, Analistas y KPI y Métricas del área de Mariana; corrección puntual de la gráfica de metas en gerencia y legibilidad de sus leyendas. Se conserva intacta la política, la selección F2 del modelo XGBoost, TRAIN/TEST, datos fuente, decisiones, autorizaciones y notificaciones.

## Cuatro KPI principales, en orden

| Orden | KPI visible | Fórmula y fuente | Uso |
|---|---|---|---|
| 1 | **Rechazos con default (TEST)** | Entre las solicitudes con **decisión registrada este mes** cuya recomendación **guardada al decidir** fue `Rechazar`, proporción con `DEFAULT = 1` en el archivo **TEST**, cruzado por **Loan ID + analista**. Numerador / denominador verificables. | Revisión **retrospectiva** de la capacidad de las recomendaciones de rechazo para identificar incumplimientos etiquetados. **No** implica que el crédito incumpliera *después* de rechazarse: un crédito realmente rechazado no tiene desempeño posterior observable en la institución. |
| 2 | **Casos de alto riesgo** | Conteo de decisiones del mes cuyo `suggested = Rechazar` (independiente de la decisión final humana). | Carga de revisión de casos riesgosos. Meta mensual editable por Mariana: 15 casos iniciales por analista. |
| 3 | **PD promedio evaluada** | Promedio de `pd_xgb` guardada en las decisiones mensuales del analista; en consolidado, promedio ponderado por decisiones. | Riesgo **estimado**, no tasa de default realizado. No se fija meta para aumentar la PD. |
| 4 | **Atendidas / asignadas TEST** | Numerador: decisiones distintas registradas **este mes** en SQLite. Denominador: solicitudes **TEST asignadas** a ese analista, según `ANALISTA_ID`; en gerencia ambos numeradores y denominadores se **suman**. | Productividad demostrativa. La **meta mensual editable** permanece en `Decisiones mensuales` (50 casos iniciales por analista), no en el total de TEST. |

## Definiciones y restricciones

- Todas las pantallas usan `src/monthly_kpis.py:monthly_summary` y las mismas filas de TEST, `LOAN_ID`, `ANALISTA_ID` y bitácora SQLite. No se realiza un entrenamiento nuevo.
- El KPI 1 usa **solo casos con recomendación de rechazo revisados** durante el mes. Por tanto, no debe leerse como tasa general de default, recall de XGBoost, ni porcentaje de **rechazos finales** incumplidos. La revisión humana puede decidir distinto sin alterar la sugerencia histórica guardada.
- `DEFAULT` proviene del conjunto TEST etiquetado, que es sintético. **No** es una observación posterior a la decisión simulada del analista ni permite calificar laboralmente a Adrián/Sofía. Es una comparación retrospectiva sobre ese conjunto.
- Si no hubo sugerencias de rechazo revisadas en el mes, la tasa muestra **«—»**, no 0%. Si falta el Loan ID de un caso o corresponde a un analista diferente, toda la tasa afectada aparece **«—»**, no un 0% engañoso. Si hay casos válidos pero ninguno tuvo DEFAULT=1, se muestra 0%.
- Los registros de decisiones se guardan por `loan_id` único y conservan solo el estado más reciente. La edición de una decisión no duplica los conteos y la fecha se interpreta en horario de Ciudad de México.
- La meta de productividad la edita Mariana en **Analistas y KPI** y se notifica a ambos analistas a través del mecanismo existente. Cambiar un corte gerencial no reescribe recomendaciones de decisiones históricas ya guardadas. La bandeja usa la política vigente para nuevos casos.
- En la gerencia, el porcentaje de rechazos con default se calcula con **suma de casos DEFAULT=1 / suma de rechazos sugeridos válidos**, no el promedio simple de las tasas de Adrián y Sofía; la PD también se pondera por número de decisiones. Si los datos del cruce de cualquiera de los perfiles son insuficientes, la tasa global es no evaluable.
- El denominador de productividad corresponde a la asignación total **TEST**, no a solicitudes reales recibidas o a operaciones originadas. Las decisiones son del mes en curso; el avance de la meta usa el número de decisiones del mes.

## Conexión entre las cuatro pantallas

| Pantalla | Función compartida o composición |
|---|---|
| P1 · Bandeja de Adrián / Sofía | `app_v3.py` obtiene `monthly_summary(decisiones, analyst_id, scored=M.scores)`, y muestra tasa TEST y atendidas/asignadas |
| Mis indicadores de ambos analistas | `src/kpi_views.py` obtiene `monthly_summary(records, analyst_id, scored=score_df)` |
| Gerencia · Analistas y KPI | `src/kpi_views.py` agrega `monthly_summary` para cada analista y mantiene la edición, confirmación y notificación de metas |
| Gerencia · Métricas del área | `src/manager_overview.py:build_team_metrics` consolida numeradores, denominadores, PD y productividad desde los mismos resúmenes |

## Error gerencial y legibilidad

La curva de evolución de **decisiones vs meta** debe utilizar siempre `Decisiones mensuales` y su meta, incluso cuando el ranking de Mariana selecciona un KPI informativo sin meta. Esto evita dividir o graficar un `goal=None`. Las dos funciones de formateo de Plotly reservan espacio inferior y distribuyen las leyendas en columnas sin superposición. Las tarjetas KPI conservan altura flexible para que sus textos no se corten.

## Verificación

`tests/test_risk_kpi_integration.py` cubre cruces correctos, ponderación gerencial, cero denominador, fallos de identidad, SQLite y metas con avisos, más las llamadas compartidas de la UI. `tests/test_manager_layout.py` revisa disposición de leyendas y preservación de la pregunta de negocio de B3. `scripts/check_contrast_b3.py` permanece sin alteraciones.

**Limitación:** las pruebas de código y CI no reemplazan una revisión visual en un navegador con cada perfil. El despliegue Streamlit Cloud debe apuntar a `app_v3.py` de la rama que contiene los cambios; `main/app.py` es la app histórica B1–B2.