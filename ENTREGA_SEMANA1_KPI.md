# Semana 1 · Componente Streamlit: tres KPI reales

**Proyecto:** AutoCredit Advisor · Riesgo Crediticio (Auto) · Entrega 4

## Evidencia lista

La pantalla nueva **P7 · Indicadores del conjunto crediticio** muestra tres tarjetas construidas con `data/Base_SAS_Equipo3.csv`:

| KPI | Variable | Fórmula | Resultado en CSV adjunto |
|---|---|---|---|
| Registros crediticios | Filas | `len(df)` | 80,000 |
| Tasa histórica de default | DEFAULT | `sum(DEFAULT == 1) / count(DEFAULT válido)` | 13.48% (10,783 de 80,000) |
| DTI promedio | DEBT_TO_INCOME | `mean(DEBT_TO_INCOME) × 100` | 29.61% |

Los resultados se calculan automáticamente; **no son cifras fijadas a mano en la interfaz**. Si cambia el CSV, cambian los indicadores al limpiar la caché de Streamlit y recargar los datos.

## Dónde está el trabajo

- `src/kpis.py` — lógica sencilla y comprobable con pandas.
- `src/servicios.py` — acceso a agregados por rol (gerencia y operación).
- `vistas/p7_kpis.py` — tres tarjetas `st.metric`, fuente, fórmulas y límites.
- `app.py` y `src/seguridad.py` — navegación autorizada a la nueva pantalla.
- `tests/test_kpis.py` — verificaciones contra CSV real y ante nulos.

## Mostrarlo

1. Abrir el proyecto en VS Code y ejecutar `streamlit run app.py`.
2. Iniciar sesión en modo demo como **Mariana Torres** o **Luis Ramírez**.
3. Abrir en la barra lateral **P7 · Indicadores de la base**.
4. Tomar captura de las tres tarjetas y del desplegable **Cómo se calcularon los KPI**.

**Importante:** la app conserva los roles originales. Un analista no tiene permiso para abrir esta pantalla de agregados generales. No se añadió ningún dato simulado ni se modificó el CSV o el modelo.

## Límite de interpretación

Cada fila representa un registro, pero el CSV no trae identificador de crédito, fechas de originación, ni una variable de volumen monetario. Por lo tanto, no se puede afirmar que hay 80,000 clientes únicos ni derivar crecimiento mensual. `DEFAULT` refleja el incumplimiento observado en la base, no PD futura.
