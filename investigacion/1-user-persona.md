# Investigación 1 aplicada a la jerarquía del producto

**Fuente primaria del equipo:** *User Persona Riesgo Crediticio v2 (1).pdf* (28 páginas), presentación original de Design Thinking y arquitectura de información. Se citan páginas para que el evaluador identifique las decisiones originales. Esta síntesis no reemplaza al PDF.

## Observaciones de la investigación original

- **Página 4, bloque Design Thinking:** el analista carecía de PD y explicación por solicitud; la gerencia necesitaba conocer riesgo por segmento; operación requería monitoreo de datos y modelo.
- **Página 5, personas y tarea crítica:** Adrián debe aprobar, condicionar o rechazar un crédito en menos de cinco minutos; necesita leer DTI, enganche, atraso y PD. Mariana debe localizar segmentos por encima de la tolerancia y estimar el efecto de cambiar políticas. Luis, en el prototipo inicial, vigila métricas, alertas y datos.
- **Página 15, arquitectura:** P1 pone solicitudes y filtros antes del detalle; P2 muestra PD frente a política y comparaciones; P3 pone segmentación antes de política; P5 muestra causa y recuperación ante error en lugar de una gráfica vacía.
- **Página 16, recorrido de Adrián:** entra, filtra, abre ficha, lee riesgo y variables, decide y documenta una excepción; si falla un dato, necesita un camino de recuperación.
- **Página 17, recorrido de Mariana:** revisa, filtra, detecta el segmento con riesgo, estudia el impacto de un corte y prepara su decisión de gerencia.

## Jerarquía resultante en la V3

| Hallazgo de la investigación | Decisión de jerarquía de la app | Dónde se implementa |
|---|---|---|
| El analista quiere decidir un caso en pocos minutos | KPIs, filtros y conteo antes de la bandeja; la ficha prioriza PD, recomendación y botones | `app_v3.py` · Bandeja/Ficha |
| El riesgo necesita explicación y contexto | Las preguntas encabezan las gráficas; TRAIN y TEST se distinguen; se muestran porcentajes y referencias | `app_v3.py` · Gráficas de ficha |
| La gerente necesita comparar antes de cambiar una política | Estado del área, comparación por perfil, metas y después simulador de corte | `src/manager_overview.py`, `src/kpi_views.py`, `app_v3.py` |
| Un estado vacío no equivale a riesgo cero | Mensaje, restablecer filtro y `st.stop()` para impedir que continúe el cálculo | `app_v3.py` |
| Acceso por persona | Vistas distintas para analistas, gerencia y soporte y separación de Loan ID entre analistas | `app_v3.py`, `src/login_view.py`, `src/access_audit.py` |

**Evolución declarada:** la investigación original describe a Adrián, Mariana y Luis; la implementación V3 presentada agrega a Sofía y sustituye la vista de operación por Especialista de Soporte. Esta diferencia se explica expresamente; no se presenta la V3 como copia literal del mockup.

**Referencia interna:** Equipo 3. (2026). *User Persona Riesgo Crediticio v2* [Presentación académica en PDF], pp. 4–5 y 15–17.
