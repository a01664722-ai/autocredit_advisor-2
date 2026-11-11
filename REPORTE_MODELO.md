# Reporte técnico breve · Equipo 3 — Dashboard V2

## Fuente y separación

Archivo ZIP adjunto **Bases_SAS_Equipo3_12V(2).zip**. Datos sintéticos de crédito, no solicitudes reales ni información bancaria productiva.

| Partición | Registros | DEFAULT=1 | Predictores | Uso |
|---|---:|---:|---:|---|
| TRAIN | 80,000 | 13.48% | 12 | Ajuste, validación y selección de corte |
| TEST | 20,000 | 13.48% | 12 | Evaluación final; nunca en fit |

`LOAN_ID` es identificador (no predictor) y `DEFAULT` es el objetivo (no predictor). Los ID son únicos y disjuntos y los predictores carecen de nulos.

## Modelos entrenados en TRAIN y evaluados en TEST

XGBoost sigue los parámetros base del notebook: 200 árboles, profundidad 4, tasa de aprendizaje 0.05, submuestreo 80% por filas y columnas. Logit estándar como modelo complementario; ambas opciones usan 12 variables, incorporando `LOAN_AMOUNT`. A diferencia de la notebook de 11 variables, este cálculo corresponde exactamente a las bases nuevas.

El umbral inicial se obtiene en una subpartición 75/25 de TRAIN mediante máximo F2, sin mirar TEST, y después se ajustan ambos modelos con los 80,000 registros TRAIN.

| Modelo | ROC-AUC | KS | PR-AUC | Accuracy | Recall default | Precision default | F1 | TN | FP | FN | TP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| XGBoost | 0.7858 | 0.4343 | 0.4048 | 66.14% | 77.26% | 25.28% | 0.3809 | 11146 | 6158 | 613 | 2083 |
| Logit | 0.7838 | 0.4267 | 0.4043 | 65.25% | 77.41% | 24.76% | 0.3752 | 10963 | 6341 | 609 | 2087 |

**Corte de demostración seleccionado por F2:** 10.95%. Los resultados se muestran a ese umbral.

**Interpretación:** `DEFAULT = 1` significa incumplimiento. Cuando `PD_XGB ≥ corte`, la regla académica **sugiere rechazar**; de lo contrario **sugiere aprobar**. El analista puede decidir distinto si justifica y avisa a la gerente. El pronóstico de Logit es complementario, nunca una condición fija de ≥60%% sin calibración.

XGBoost obtuvo un ROC-AUC apenas 0.0020 superior a Logit. El resultado es compatible con seleccionarlo como campeón de esta comparación, pero requiere contrastes de incertidumbre y validación posterior; no es evidencia de superioridad fuerte.

**Costo de error:** Al priorizar recall con F2, XGBoost genera **6,158 falsos positivos** en TEST, es decir, créditos sin incumplimiento que la regla sugiere rechazar, y **613 falsos negativos**. Sin LGD, EAD, margen, pérdida por cliente rechazado, controles de sesgo y aprobación institucional, ningún corte es financieramente óptimo ni apto para producción.

## Referencia y gobierno

- El **corte de revisión** es el umbral de PD fijado por Mariana para formular una recomendación. Su cambio en la demo se guarda en SQLite, modifica recomendaciones en P1/P2 y notifica a los analistas afectados. No modifica el modelo entrenado.
- Los resultados de TEST y sus etiquetas históricas solo se exponen agregados al perfil de gerente/DTI. Las vistas individuales del analista no muestran `DEFAULT` real.
- La vista DTI incluye matriz de confusión, ROC-AUC, KS, Accuracy, F1, Precision, Recall, PR-AUC, calibración, importancia y distribución de scores.
- Los identificadores de solicitudes son **`LOAN_ID` originales**. Los nombres de analistas, asignación y bandeja de mensajes son elementos operativos simulados (*).
- La unidad monetaria de origen no está verificada; en la UI se indica `u.m.` en lugar de inventar MXN o USD.

## Reproducibilidad (SHA256)

- TRAIN: `43a8cbe535247540d4638dd13a18ce99051bbe269c9577768efbc9dd76ac5492`
- TEST: `bd7b97de2aaf187aeaec8a96816e75a0cbbe0b485715796f032f018c5703f215`

## Límites de esta entrega

Este paquete incorpora un prototipo técnicamente funcional en el motor y las reglas, pero la interfaz Streamlit aún requiere verificación visual/de interacción al desplegarse. El selector de personas es una demo, no login institucional. SQLite en Streamlit Cloud no ofrece persistencia garantizada entre reinicios ni entre varias instancias. No se debe usar para decisiones reales de crédito.
