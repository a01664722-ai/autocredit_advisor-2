https://github.com/a01664722-ai/autocredit_advisor-2/actions/runs/45742128624

# Entregable 3 · Evidencia de la versión XGBoost V3

**Aplicación:** https://autocreditadvisor-2-f2ww6wn7nnrysa43edznfp.streamlit.app/  
**Código auditado:** rama `v3-integracion-xgboost-12v`, entrada `app_v3.py`. **Primera línea:** corrida verde real del workflow de V3 que ejecuta contraste WCAG y pytest. La evidencia deberá volver a comprobarse antes de entregar si se modifica el código.

## 1. Gráficas y preguntas visibles

| Persona / gráfico V3 | Pregunta mostrada en la propia gráfica o arriba | Archivo |
|---|---|---|
| Analista · indicador de PD | ¿La PD de este caso supera el corte de la política crediticia? | `app_v3.py` |
| Analista · histograma TEST | ¿Dónde se ubica la PD del caso frente a las solicitudes de TEST? | `app_v3.py` |
| Analista · endeudamiento | ¿Cómo se compara el endeudamiento del caso con los grupos de TRAIN? | `app_v3.py` |
| Analista · perfil relativo | ¿Qué indicadores superan la mediana de buenos pagadores? | `app_v3.py` |
| Analista · percentiles | ¿Qué percentil ocupa cada indicador del caso dentro de TRAIN? | `app_v3.py` |
| Gerencia · escenarios de corte | ¿Cómo cambian los casos condicionados y rechazados al mover el corte? | `app_v3.py` |
| Gerencia · default condicional | ¿Qué incumplimiento se observó en la zona condicional de TEST? | `app_v3.py` |
| Gerencia · cumplimiento individual | ¿Qué tan cerca está cada analista de su meta individual? | `src/manager_overview.py` |
| Gerencia · evolución | ¿Cómo avanzan las decisiones de los analistas frente a la meta? | `src/manager_overview.py` |
| Gerencia · incidencias | ¿Qué categorías concentran las incidencias de Soporte? | `src/manager_overview.py` |
| Gerencia · estados | ¿Cuáles son los estados de los casos de Soporte? | `src/manager_overview.py` |
| Analistas · evolución mensual | ¿Cómo evolucionan las decisiones del mes frente a la meta? | `src/kpi_views.py` |
| Analistas · composición | ¿Qué proporción de decisiones fue aceptar, condicionar o rechazar? | `src/kpi_views.py` |
| Analistas · riesgos atendidos | ¿Cuántos casos se atendieron por nivel de riesgo frente a la meta? | `src/kpi_views.py` |
| Analistas · procedimientos | ¿Qué tan cerca están los indicadores de procedimiento de sus metas? | `src/kpi_views.py` |
| Gerencia · indicador elegido | ¿Qué nivel de riesgo o cumplimiento presenta cada analista? | `src/kpi_views.py` |
| Gerencia · acumulado mensual | ¿Cómo evoluciona el número de decisiones por analista durante el mes? | `src/kpi_views.py` |
| Gerencia · riesgo XGBoost | ¿Qué niveles de riesgo atiende cada analista? | `src/kpi_views.py` |
| Soporte · ROC | ¿Qué tan bien distinguen los modelos el incumplimiento? | `src/support_views.py` |
| Soporte · precisión/recall | ¿Qué precisión obtiene cada modelo al aumentar la detección de incumplimientos? | `src/support_views.py` |
| Soporte · matriz | ¿Cuántos casos clasifica correcta e incorrectamente XGBoost? | `src/support_views.py` |
| Soporte · PD por clase | ¿Cómo se distribuye la PD entre créditos cumplidos e incumplidos? | `src/support_views.py` |
| Soporte · importancia | ¿Qué variables tienen mayor importancia interna en XGBoost? | `src/support_views.py` |
| Soporte · calibración | ¿Coinciden las probabilidades estimadas con el incumplimiento observado? | `src/support_views.py` |

Se conserva el cálculo y la geometría de cada gráfica; solo cambia el título por una pregunta. La tabla «Resumen visual de decisión» también tiene una pregunta, aunque no cuenta como gráfica.

## 2. Paleta y contraste calculado

WCAG 2.2 AA: **4.5:1** texto normal y **3:1** texto grande/elementos informativos. Ejemplos con la paleta original: KPI `#b8c5bd` sobre `#161b18` **9.77:1**; chip rojo `#f47b87` sobre `#4b2027` **5.23:1**; ámbar `#f5c65b` sobre `#423011` **7.89:1**; verde `#52dc9a` sobre `#103a2a` **7.26:1**. **No se cambiaron los colores**; el menú rápido reutiliza los existentes.

Pipeline: `.github/workflows/check_dashboard.yml`, ejecuta `python scripts/check_contrast_b3.py` y `python -m pytest -q`. Si la combinación auditada no cumple, el CI falla. Ver [investigación 3](../investigacion/B3.md) para método y alcance; no se declara auditoría integral del DOM.

## 3. Jerarquía justificada con investigación 1

El estudio original del equipo *User Persona Riesgo Crediticio v2 (1).pdf*, pp. 4–5 y 15–17, explica que Adrián debe decidir un caso en menos de 5 minutos; Mariana necesita comparar segmentos y políticas. De ahí que P1 muestre KPIs, filtros y conteo antes de la tabla y P2 muestre PD y recomendación antes de comparaciones; la gerencia ve primero métricas y después simulador. [Síntesis y evidencia de la investigación 1](../investigacion/1-user-persona.md). La V3 añadió Sofía y Soporte; esta evolución se documenta.

## 4. Estado «nada seleccionado» y `st.stop()`

En `app_v3.py` (Bandeja, aprox. líneas 399–439), quitar todas las recomendaciones o usar filtros sin coincidencias muestra **«No hay solicitudes para esta combinación»**, ofrece Restablecer y ejecuta `st.stop()`. En Ficha (aprox. líneas 665–680), si el Loan ID no coincide con solicitudes autorizadas, muestra aviso y `st.stop()`. No se procesan ni grafican casos inexistentes.

## 5. Dos controles y decisión con conteo visible

| Control | Selección | Decisión que habilita |
|---|---|---|
| **Estado de la solicitud** (P1) | Pendiente, Resuelta, Todas | Adrián/Sofía prioriza los casos por trabajar o verificar |
| **Recomendación XGBoost** (P1) | Aceptar, Condicionar y Rechazar (selección múltiple) | Adrián/Sofía elige qué nivel de recomendación revisar antes de decidir |

Ambos filtros realmente actualizan `filtrada`. La interfaz muestra **«N resultados · datos de TEST · N páginas · Orden: ...»**, junto con los filtros y el botón Restablecer. Evidencia: `app_v3.py`, líneas aproximadas 362–466.

## 6. Matriz de acceso por rol y limitación de autenticación

| Perfil | Pantallas / permisos | Restricción |
|---|---|---|
| Adrián, analista A-017 | Bandeja, Ficha, Mis indicadores, Mensajes | Solo sus Loan ID; no controla política ni accede a Soporte |
| Sofía, analista A-022 | Bandeja, Ficha, Mis indicadores, Mensajes | Solo sus Loan ID; no ve casos asignados a Adrián |
| Mariana, gerencia | Métricas del área, Analistas y KPI, Mensajes, Auditoría de accesos | No registra decisiones de préstamos como analista |
| Especialista de Soporte | Centro de soporte, Validación del modelo, Mensajes | No aprueba ni rechaza solicitudes |

**Mecanismo:** `app_v3.py` crea navegación distinta por perfil, separa los préstamos con `ANALISTA_ID`, y `send_decision` comprueba propiedad del préstamo antes de guardarlo. Se borra el estado de navegación al cambiar de perfil; pruebas `tests/test_analyst_isolation.py`, `tests/test_demo_login.py` y `tests/test_v3.py`.

**Limitación explícita:** selección de perfiles **sin verificar identidad**; es una rebanada funcional de demostración, no autenticación institucional ni RBAC seguro para datos reales. La URL es pública y los datos son sintéticos. No hay contraseñas en GitHub.

**Defensa en vivo:** entrar como Adrián, mostrar P1/P2; salir y entrar como Mariana para mostrar pantallas distintas; repetir con Sofía para observar separación de Loan ID; vaciar filtros en P1 para mostrar el estado y `st.stop()`.


### Anexo · Última observación del profesor: riesgo crediticio por encima de productividad

Se preservan **las seis secciones obligatorias anteriores** y sus evidencias. La última retroalimentación se atendió sin reentrenar el modelo ni modificar la política, con **tres KPI de riesgo y uno de productividad** que aparecen y se calculan igual en P1, Mis indicadores y gerencia: (1) exposición monetaria evaluada en casos de alto riesgo, (2) casos de alto riesgo atendidos, (3) PD promedio de las solicitudes revisadas y (4) decisiones del mes.

Los dos indicadores de riesgo que aumentan con volumen/PD no se consideran metas de desempeño; son señales para gestionar exposición. El conteo de riesgo y productividad mantiene metas de gerencia, sincronizadas en SQLite. No se utiliza incumplimiento observado `DEFAULT` para puntuar analistas.

**Metodología, fórmulas, limitaciones, enlaces de código y pruebas:** [`docs/kpis-riesgo-integracion.md`](kpis-riesgo-integracion.md), y [`tests/test_risk_kpi_integration.py`](../tests/test_risk_kpi_integration.py).

**Menú de Decisión rápida:** contorno neón con `#52dc9a` existente, sin cambiar valores ni categorías de decisión. El aspecto desplegado debe comprobarse visualmente en Streamlit tras el despliegue.
