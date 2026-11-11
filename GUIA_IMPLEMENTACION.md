# AutoCredit Advisor · rediseño de 12 variables (equipo 3)

## Instalación sin romper la aplicación original

1. Genera una rama de respaldo desde `main` antes de modificar la aplicación. Para poder editar en el repositorio de José Carlos, el propietario debe dar permisos de escritura a la conexión de GitHub elegida.
2. Descarga y descomprime este paquete. Copia `app_v2.py`, `src/engine.py`, `src/store.py`, `data/Base_SAS_Equipo3_TRAIN_12V.csv`, `data/Base_SAS_Equipo3_TEST_12V.csv`, `requirements.txt` en el repositorio conservando las rutas. Deja las demás carpetas existentes sin cambios.
3. En Streamlit Cloud, configura el archivo de entrada `app_v2.py` de la rama de prueba. El dashboard anterior mantiene su `app.py` original: este paquete NO lo reemplaza. Se recomienda trabajar en una rama nueva antes de cambiar la ruta de entrada de Streamlit Cloud.
4. Para correr localmente: `pip install -r requirements.txt && streamlit run app_v2.py`. Para ejecutar pruebas: `pip install pytest && pytest -q tests/test_v2.py`.

## Datos y metodología (verificable)

- Base sintética de crédito automotriz: TRAIN = 80,000; TEST = 20,000; no comparten `LOAN_ID`.
- 12 predictores numéricos, incluido `LOAN_AMOUNT`. `LOAN_ID` sirve solo para identificar; `DEFAULT` es objetivo. No se usa ninguna de ellas como predictor.
- La validación para fijar un corte de clasificación parte **exclusivamente** de TRAIN (60,000 ajuste / 20,000 validación, estratificado). Se elige el umbral que maximiza F2 para favorecer sensibilidad de detección.
- Se reentrena XGBoost con todo TRAIN y después se calculan predicciones de TEST sin utilizar TEST en entrenamiento. Logit es comparador con las mismas 12 variables. Los parámetros de XGBoost se mantienen como en el notebook de Colab (200 árboles, profundidad 4, eta 0.05, submuestreo 0.8).
- Regla propuesta: `PD_XGB >= corte_vigente -> Rechazar`; en caso contrario `Aprobar`. No se recomienda imponer arbitrariamente una condición Logit >= 60% sin validación empírica de los costos de los errores; se muestra Logit como referencia, nunca como causal de cambio automático.
- La gerente ajusta el corte por segmento de DTI; los analistas reciben mensajes, y la recomendación se recalcula a partir del corte vigente. Este umbral de decisión no es límite legal ni regulatorio.
- La tabla inicial muestra Loan ID auténticos provenientes de TEST, clase pronosticada XGBoost, PD XGBoost, PD Logit, DTI y monto. Se excluye el objetivo DEFAULT del flujo del analista para impedir que se filtre la etiqueta que se desea pronosticar.
- Las asignaciones a Adrián/Sofía, perfiles de demostración, inbox y decisiones operativas son simulaciones. Los créditos son de una base sintética (no expedientes de clientes reales). Las medidas ROC-AUC, Accuracy, recall, precision, F1, KS, matriz de confusión, distribución y calibración se calculan sobre TEST.
- `FINANCIAL_LITERACY_SCORE` entra al benchmark técnico por solicitud de 12 variables, pero se oculta al analista por riesgo de proxy socioeconómico. Para producción requiere auditoría de equidad.

## Controles de negocio

**P1 Bandeja.** KPIs antes del título, filtrado por riesgo/estado/búsqueda, paginación y acción en cada fila. Una decisión alineada con el modelo se registra sin abrir P2. Si discrepa, P2 abre diálogo obligatorio de confirmación y motivo.

**P2 Ficha.** Los KPI de predicción, corte y comparación aparecen primero. Semáforos suaves, comparaciones gráficas contra pagadores sin incumplimiento del TRAIN y decisión visible. No se revela DEFAULT individual.

**P3 Gerencia.** Corte global o específico de DTI, trade-off real sobre TEST, cambios visibles por los analistas, KPI con metas editables, comparaciones solo cuando existen decisiones registradas, mensajes por excepciones.

**P4 Operación.** Identifica la falta de flujo productivo y no inventa SLA o drift. Los modelos se validan en la pantalla técnica DTI.

**P8 DTI.** ROC, matriz de confusión, KS, accuracy, F1, recall, precisión, PR-AUC, calibración, importancias y distribución de scores, con interpretación de falsos positivos.

**P5 y P6.** Solo visibles para gerencia/DTI; fuera del perfil del analista.

## Límites que impiden uso productivo

- El selector de perfiles sirve únicamente como demo. NO es autenticación real, no hay SSO/RLS ni control de permisos de backend de producción.
- SQLite en el disco de Streamlit Cloud es efímero: los cambios se comparten durante la vida de una instancia, pero pueden perderse al reiniciarse o reescalarse. Migrar la bitácora a PostgreSQL gestionado, con permisos por fila y transacciones.
- Las asignaciones simuladas de TEST no representan nuevas solicitudes reales. No se conoce fecha real de entrada ni tiempos de resolución; los KPI que dependerían de ellas se mantienen sin observación.
- La etiqueta `DEFAULT` en TEST es histórica y se usa únicamente en evaluación agregada. No es legítimo ajustar el corte mirando repetidamente TEST y reportarlo como evaluación independiente: antes de producción habrá que usar nuevo holdout temporal.
- El corte F2 protege recall, pero no prueba rentabilidad; faltan costos de falsos aprobados/rechazados, LGD, EAD, desempeño por segmentos y validación regulatoria. En una decisión real de crédito también se requiere cumplimiento legal, explicación y revisión humana.
- La unidad monetaria de origen no está documentada: se usa «u.m.» y no se afirma MXN o USD.

## Archivos de auditoría incluidos

`data/SCORES_TEST_XGBOOST_LOGIT_12V.csv` incluye las predicciones calculadas de 20,000 observaciones TEST con su `LOAN_ID` original, clase prevista y recomendación con corte inicial. `DEFAULT` en este archivo es la etiqueta histórica para evaluar; **no mostrar en la pantalla del analista**. `data/METRICAS_TEST_MODELOS_12V.csv` permite cotejar las métricas de ambos modelos sin inventar resultados.
