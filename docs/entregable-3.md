https://github.com/a01664722-ai/autocredit_advisor-2/actions/runs/45754353334

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

## 2. Paleta inclusiva, protanopía/deuteranopía y contraste verificado

**Corrección respecto al avance:** no basta con conservar el color original, y el tema claro de la versión anterior no resultaba legible. La V3 ahora ofrece **controles visibles desde la pantalla de acceso y también en la barra lateral de cada perfil**: **Oscuro / Claro** y **Modo daltónico · símbolos y paleta**. Son preferencias de presentación independientes de los datos y se mantienen al cambiar de perfil.

**Señal no cromática obligatoria:** `✓ Aceptar`, `◇ Condicionar`, `✕ Rechazar` se muestran en la tabla de Bandeja, el resumen y la ficha sin cambiar las decisiones almacenadas. Alto/medio/bajo se acompañan de texto. Las metas incluyen estado escrito (meta lograda, en progreso, por debajo del 50%) además del color. En modo daltónico, las barras usan tramas y las líneas/series emplean trazos y marcadores diferentes. Así una persona puede reconocer la categoría aunque las tonalidades converjan.

**Método reproducible:** `scripts/check_cvd_b3.py` transforma RGB sRGB linealizado mediante las matrices de severidad 1.0 de Machado, Oliveira y Fernandes (2009). Para cada uno de **2 temas × 3 categorías × 3 escenarios** (visión habitual, protanopía y deuteranopía) calcula contraste relativo contra su fondo. La compuerta exige **mínimo 4.5:1** para los tonos usados en texto (criterio WCAG 2.2, 1.4.3); las marcas y patrones se evalúan como señales adicionales (1.4.1). Los resultados siguientes se obtuvieron con el mismo algoritmo; la acción CI vuelve a calcularlos:

| Tema | Señal | Visión habitual | Protanopía | Deuteranopía | Umbral |
|---|---|---:|---:|---:|---|
| Oscuro | ✓ Aceptar · azul `#74D5FF` | 11.47:1 | 12.53:1 | 10.80:1 | ≥4.5 |
| Oscuro | ◇ Condicionar · ámbar `#FFD166` | 13.14:1 | 12.25:1 | 13.74:1 | ≥4.5 |
| Oscuro | ✕ Rechazar · rosa `#F7A3CF` | 10.01:1 | 9.15:1 | 10.64:1 | ≥4.5 |
| Claro | ✓ Aceptar · azul `#005A8C` | 7.39:1 | 6.66:1 | 7.95:1 | ≥4.5 |
| Claro | ◇ Condicionar · ámbar `#815000` | 6.82:1 | 7.59:1 | 6.41:1 | ≥4.5 |
| Claro | ✕ Rechazar · violeta `#8E285C` | 8.05:1 | 9.73:1 | 7.22:1 | ≥4.5 |

**Resultado de la simulación:** los 18 pares previstos superan 4.5:1, con mínimo **6.41:1**. Esto comprueba los **tokens** auditados, **no** certifica todos los píxeles del dashboard ni sustituye una inspección en navegador. La distinción sigue respaldada por palabras, símbolos y patrones, incluso cuando dos colores simulados se parecen.

**Evidencia visual:** [muestras de las paletas simuladas (SVG)](evidencia-daltonismo.svg). **Código:** [control de accesibilidad](../src/accessibility_theme.py), [verificador de daltonismo](../scripts/check_cvd_b3.py), [verificador de contraste](../scripts/check_contrast_b3.py), [pruebas](../tests/test_accessibility_entrega4.py). Para ejecutar: `python -m scripts.check_cvd_b3`, `python scripts/check_contrast_b3.py` y `python -m pytest -q`.

**Pipeline real:** `.github/workflows/check_dashboard.yml` se utiliza en V3. Para no dejar sin cobertura la rama que evalúa el profesor, `.github/workflows/contraste-v3.yml` en **main** debe ejecutar checkout del mismo commit de **main**, nunca fijar `ref: v3-integracion-xgboost-12v`. La sincronización de assets V3 a main debe preservarlos junto a los originales de B1/B2. Ver [seguimiento de Entrega 4](entregable-4.md).

**Referencias:** Machado, G. M., Oliveira, M. M., & Fernandes, L. A. F. (2009). *A physiologically-based model for simulation of color vision deficiency*. IEEE TVCG, 15(6), 1291–1298, https://doi.org/10.1109/TVCG.2009.113; W3C (2023), [WCAG 2.2](https://www.w3.org/TR/WCAG22/) y [Use of Color, criterio 1.4.1](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html).

## 3. Jerarquía visual: investigación 1 del curso + user persona del equipo

**Dos fuentes diferentes, no intercambiables:**

1. **Investigación 1 del curso:** el material bibliográfico específico (título, autoría y enlace/página) **no está identificado ni adjunto al repositorio**. Para no inventar una referencia, queda señalado como **pendiente de incorporar la cita literal de la investigación 1 asignada por el profesor**. No se presenta el user persona como esa fuente ni se afirma que el criterio documental está plenamente cerrado sin ella.
2. **Investigación del equipo (fuente independiente):** *User Persona Riesgo Crediticio v2 (1).pdf*, pp. 4–5 y 15–17 (Equipo 3, 2026); [síntesis documentada](../investigacion/1-user-persona.md). Explica que Adrián decide un caso en menos de cinco minutos, Mariana compara segmentos y políticas, y los flujos difieren por perfil.

**Aplicación a la jerarquía:** P1 muestra señales de riesgo y productividad, filtros y conteo **antes** de la tabla para decidir qué solicitud revisar. P2 presenta PD, recomendación y nivel de riesgo **antes** de las comparaciones. Mariana ve primero panorama y cumplimiento del equipo y después el simulador. El flujo V3 incorpora a Sofía y Soporte sin atribuirlos a la investigación inicial.

**Apoyo externo adicional, no presentado como investigación 1 del curso:** W3C, [Headings and Labels](https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels.html), explica el valor de encabezados descriptivos para orientar acciones. La aplicación mantiene las 24 preguntas de negocio previamente aceptadas.

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

Se preservan **las seis secciones obligatorias anteriores**. Los cuatro KPI sincronizados actualmente son: **(1) Atención prioritaria de riesgo alto / meta porcentual editable**, (2) casos de alto riesgo atendidos / meta, (3) PD promedio estimada (informativa) y (4) Atendidas vs meta mensual editable. Las cifras provienen de SQLite y se agregan correctamente en las dos vistas gerenciales sin reentrenar XGBoost. El resultado `DEFAULT` de TEST no se usa para calificar al personal.

**Metodología, fórmulas, limitaciones, enlaces de código y pruebas:** [`docs/kpis-riesgo-integracion.md`](kpis-riesgo-integracion.md), y [`tests/test_risk_kpi_integration.py`](../tests/test_risk_kpi_integration.py).

**Menú de Decisión rápida:** contorno neón con `#52dc9a` existente, sin cambiar valores ni categorías de decisión. El aspecto desplegado debe comprobarse visualmente en Streamlit tras el despliegue.
