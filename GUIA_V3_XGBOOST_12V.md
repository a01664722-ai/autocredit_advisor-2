# AutoCredit Advisor V3 · implementación auditable (12 variables)

## Arranque de la versión nueva

La pantalla V3 es **`app_v3.py`**, creada sin sobrescribir `app.py` ni `app_v2.py`.

```bash
pip install -r requirements.txt -r requirements-dev.txt
streamlit run app_v3.py
python -m pytest -q tests/test_v3.py tests/test_v2.py
```

En Streamlit Community Cloud se debe seleccionar **la rama V3** y el archivo principal **`app_v3.py`**. Si Cloud apunta a `app.py` o `app_v2.py`, mostrará el sistema anterior. Los archivos CSV ya están versionados en `data/` de la rama de origen.

## Procedencia y unidad de observación

- TRAIN: `data/Base_SAS_Equipo3_TRAIN_12V.csv` (80,000 filas).
- TEST: `data/Base_SAS_Equipo3_TEST_12V.csv` (20,000 filas).
- Son datos del proyecto, **sintéticos**, no créditos de originación bancaria.
- Identificador original **`LOAN_ID`**, visible como **Loan ID**; se lee como cadena, se eliminan espacios periféricos y se validan duplicados. No se genera un identificador de préstamo.
- Se usan exactamente 12 predictores: `REVOLVING_UTILIZATION`, `DEBT_TO_INCOME`, `MISSED_PAYMENTS_12M`, `SAVINGS_BALANCE`, `DOWN_PAYMENT_PCT`, `FINANCIAL_LITERACY_SCORE`, `LOAN_TO_VALUE`, `DELINQ_90`, `YEARS_CREDIT_HISTORY`, `PAYMENT_TO_INCOME`, `BANKRUPTCY_FLAG` y `LOAN_AMOUNT`. Ni `DEFAULT` ni `LOAN_ID` entran al entrenamiento.
- La unidad monetaria de `LOAN_AMOUNT` y `SAVINGS_BALANCE` no consta en el notebook: `u.m.` hasta recibir un diccionario de origen.
- `DEFAULT` observado se utiliza solo en las métricas técnicas agregadas, no en las fichas para analistas.
- `ANALISTA_ID`, fecha/tiempo de operación, personas, bandeja y mensajes son simulaciones de trabajo. No hay expedientes humanos reales.

## Modelo y partición: equivalencia metodológica con el notebook adjunto

El notebook `MODELOSCOMPARACION_12_VARIABLES (3).ipynb` usa:
1. TRAIN (80,000) y TEST (20,000) sin préstamos compartidos.
2. Partición estratificada interna de TRAIN: 60,000 ajuste, 20,000 validación, `random_state=42`.
3. `XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, objective="binary:logistic", eval_metric="logloss", random_state=42)`.
4. Regresión logística comparadora con `StandardScaler`, `penalty=None`, `solver="lbfgs"` y 2,000 iteraciones.
5. **XGBoost campeón adoptado por el equipo**. En la salida de validación del notebook, XGBoost alcanza ROC-AUC 0.7790, F1 0.2481 y KS 0.4189; Random Forest registra KS 0.4190. La elección no debe describirse como un triunfo en absolutamente todas las métricas.

El motor V3 emplea los parámetros anteriores. Selecciona los cortes únicamente en la validación de TRAIN y **reentrena con todo TRAIN antes de pronosticar TEST**. Las métricas mostradas en DTI se computan sobre TEST. Los valores de TEST pueden diferir de las cifras de validación impresas en Colab: es un conjunto distinto y un modelo reentrenado.

## Política de tres decisiones

El notebook, celda 9, optimiza **F2** sobre `np.linspace(0.05, 0.60, 112)` y define un segundo umbral avanzando hacia mayores PD hasta antes del primer valor con F2 inferior al 95% del máximo. En la ejecución adjunta:
- **Aceptar** si PD XGBoost < 11.44% (umbral F2 inferior).
- **Condicionar** si 11.44% ≤ PD XGBoost < 15.90%.
- **Rechazar** si PD XGBoost ≥ 15.90%.

La aplicación obtiene estos valores por cálculo reproducible, no por copiar cifras fijas. El clasificador binario de la matriz de confusión usa el corte **inferior**: 1 significa predicción de incumplimiento y 0 de no incumplimiento. **No significa que la recomendación final deba ser binaria.** Logit aparece como PD comparadora, no impone una regla de rechazo adicional de 60% sin análisis de pérdidas crediticias.

La gerente puede editar **el corte superior (rechazo)**, manteniéndolo mayor que el inferior F2. La zona condicional se amplía o reduce y la bandeja de analistas lee el corte de la misma tabla SQLite. Los cambios emiten avisos por analista según los cambios de sugerencia. Esta es una simulación de escenarios sobre TEST: toda política afinada después de inspeccionar TEST requerirá un conjunto independiente nuevo para evaluar su desempeño sin sesgo de selección.

## Pantallas y trazabilidad

| Persona | Vistas | Observaciones |
|---|---|---|
| Adrián/Sofía (analistas demo) | Bandeja, Ficha, Mis indicadores, Mensajes | Solo la partición TEST asignada en el prototipo; decisiones rápidas y ficha con confirmación motivada para discrepancias |
| Mariana (gerente demo) | Política, Analistas y KPI, Mensajes, Gobierno | Ajusta corte superior y metas; compara decisiones registradas y recibe excepciones |
| Especialista DTI (demo) | Validación, Gobierno | ROC, KS, Accuracy, F1, Recall, Precision, PR-AUC, Brier, matriz de confusión y distribuciones |
| Luis (operación demo) | Operación, Validación | Datos y métricas técnicas agregadas |

El ranking gerencial mide volumen y cumplimiento de procedimiento registrados en la bitácora; **no** representa habilidad crediticia o rendimiento laboral definitivo. Sin decisiones registradas no se inventan porcentajes. Los avatares de iniciales evitan atribuir fotografías no provistas a personas.

Las vistas de gobierno están fuera del menú del analista. La bandeja muestra solo predictores seleccionados para la decisión rápida: Loan ID, selección, recomendación, clase XGBoost, PD XGBoost, PD Logit, DTI, monto y pagos omitidos. Es una tabla compacta; según el ancho físico de pantalla, Streamlit puede seguir generando scroll horizontal. La ficha expande el resto de variables, con comparación de referencia TRAIN.

## Lo que queda fuera de producción

Este es un prototipo académico con **selector de identidades**, no identidad verificable ni autorización por backend. La base SQLite de Streamlit Cloud no garantiza persistencia entre reinicios. Para producción se requieren autenticación SSO, permisos efectivos de consulta, base de datos compartida persistente, auditoría de cambios, validación temporal externa, calibración, costos de FP/FN, LGD/EAD, análisis de equidad (incluyendo `FINANCIAL_LITERACY_SCORE`) y revisión humana/documental. Los campos `DEFAULT` y `LOAN_ID` nunca se incorporan como predictores.

## Bibliografía metodológica

- Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. *Proceedings of KDD 2016*, 785–794. https://doi.org/10.1145/2939672.2939785
- Basel Committee on Banking Supervision. (2000). *Principles for the management of credit risk*. Bank for International Settlements. https://www.bis.org/publ/bcbs75.htm
- Fawcett, T. (2006). An introduction to ROC analysis. *Pattern Recognition Letters, 27*(8), 861–874. https://doi.org/10.1016/j.patrec.2005.10.010

Las referencias respaldan los enfoques técnicos; **no** atribuyen a esos autores los umbrales o resultados específicos de estas bases.
