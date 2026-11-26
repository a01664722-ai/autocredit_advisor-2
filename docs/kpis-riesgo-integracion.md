# Ajuste solicitado por el profesor · KPIs de riesgo crediticio · Equipo 3

**Objetivo:** reemplazar el predominio de productividad por **tres KPI de riesgo y uno de productividad**, conservando el modelo XGBoost, la política crediticia, la bitácora, los colores y los controles existentes. Este ajuste está conectado entre P1 (Bandeja), Mis indicadores de Adrián/Sofía, y las dos pantallas de Mariana.

## Cuatro indicadores principales (riesgo primero)

| Orden | KPI | Fórmula / origen | Interpretación | ¿Meta? |
|---|---|---|---|---|
| **1** | **Exposición de alto riesgo evaluada (u.m.)** | Suma de `LOAN_AMOUNT` de los Loan ID cuya **última decisión registrada durante el mes** conserva `suggested = "Rechazar"`. El monto se enlaza con `M.scores` (TEST) por `LOAN_ID` y `ANALISTA_ID`. | Valor nominal de solicitudes de alto riesgo **evaluadas**, sea cual sea la decisión humana final. **NO** es cartera desembolsada, pérdidas evitadas, pérdida esperada ni utilidad. | **Sin meta**, porque una exposición mayor no equivale a mejor trabajo. |
| **2** | **Casos de alto riesgo atendidos** | Número de solicitudes con decisión mensual cuya recomendación XGBoost guardada fue `Rechazar`. | Casos de alta PD revisados por el analista. El modelo anticipa riesgo; no certifica incumplimiento real. | Meta operativa de revisión editable por Mariana (15 casos iniciales por analista). |
| **3** | **PD promedio evaluada** | Promedio aritmético de `pd_xgb` guardadas en decisiones del mes. | Perfil de riesgo de los casos revisados. **No** es porcentaje de créditos que incumplieron ni una calificación de desempeño individual. | **Sin meta**, porque no conviene aumentar artificialmente la PD promedio. |
| **4** | **Decisiones del mes · productividad** | Número de préstamos diferentes cuya última decisión registrada pertenece al mes actual, en horario CDMX. | Volumen operativo de trabajo documentado. | Meta editable por Mariana (50 casos iniciales por analista). |

### Reglas para evitar cifras engañosas

- Se usa la decisión más reciente de cada Loan ID en SQLite y se filtra el mes en zona `America/Mexico_City`. Una edición **no duplica** los conteos.
- El riesgo se determina por la `suggested` y `pd_xgb` **guardadas al decidir**. Cambiar luego el corte gerencial no reescribe la historia.
- El importe procede de `LOAN_AMOUNT` de TEST, nunca de una moneda inventada. Se identifica como **u.m.** (unidad monetaria no especificada).
- Si falta un Loan ID o corresponde a otro analista, la exposición indica **«—»**, no `0`. Si no hay casos de alto riesgo revisados sí corresponde `0 u.m.`.
- Con cero decisiones, la **PD promedio** muestra **«—»**, no 0% ni una estimación inventada.
- **No se utiliza `DEFAULT` observado** para puntuar a Adrián o Sofía. Con créditos sintéticos de TEST no se puede afirmar que un analista evitó pérdidas, detectó incumplimientos realizados o generó ganancias.
- Los dos KPI informativos carecen de metas; solo los de revisión y productividad comparten la configuración de gerencia. Cambiar una meta en Mariana notifica a ambos analistas.

## Conexión entre pantallas (sin una fórmula distinta para cada perfil)

| Vista | Código | Mismo cálculo compartido |
|---|---|---|
| P1 · Bandeja Adrián/Sofía | `app_v3.py` | `monthly_summary(store.decisions_map(analyst_id), analyst_id, scored=M.scores)` |
| Mis indicadores de Adrián/Sofía | `src/kpi_views.py` | `monthly_summary(..., scored=score_df)`; cuatro tarjetas principales y antiguos indicadores complementarios desplegables |
| Gerencia · Métricas del área | `src/manager_overview.py` | `build_team_metrics(store.decisions(), targets, scores=M.scores)`; suma de exposiciones, conteos y PD ponderada por decisiones |
| Gerencia · Analistas y KPI | `src/kpi_views.py` | El mismo `monthly_summary` para cada analista; Mariana puede comparar por cualquiera de los cuatro KPI y conserva las metas editables |

**Fuente única de definición:** `src/monthly_kpis.py` (incluye `RISK_HEADLINES`, `monthly_summary` y `fmt_risk`).

## Menú «Decisión rápida»

El desplegable del `st.data_editor` conservó sus opciones y reglas para aceptar, condicionar, rechazar y abrir detalle; solo se añadió **un contorno y halo verde neón** con el verde existente `#52dc9a` a portales/listbox de Streamlit y Glide Data Grid. No cambió el sistema de colores de riesgo.

## Pruebas

**`tests/test_risk_kpi_integration.py`** comprueba:

- Los cuatro KPI, el orden correcto y su cálculo exacto por Loan ID.
- Consistencia entre Adrián, Sofía y consolidado de Mariana.
- Que invertir `DEFAULT` no altera los KPI del personal.
- Identificación faltante/ajena: exposición no evaluable, nunca cero inventado.
- Persistencia SQLite sin doble conteo y avisos al modificar metas.
- Que P1, las páginas de analistas y gerencia usan la misma función y que el contorno neón aparece en CSS.

**CI existente:** `.github/workflows/check_dashboard.yml` ejecuta compilación Python, contraste WCAG y `pytest`. Un CI verde verifica código y reglas; la prueba definitiva de que el contorno se aprecia al desplegar es **visual, en el navegador**, y no puede certificarse solo por el script.

**Alcance:** es una aplicación académica con datos sintéticos y login demostrativo. Los KPI no deben usarse para aprobar créditos reales ni para calcular incentivos laborales.
