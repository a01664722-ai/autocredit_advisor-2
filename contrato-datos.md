# Contrato de datos · AutoCredit Advisor

La fuente del dashboard es `data/Base_SAS_Equipo3.csv`, con 80,000 registros y 12 columnas. **REAL** significa que la cifra viene del CSV, **CALCULADO** que se obtuvo de esos datos o del modelo, y **SIMULADO** que sirve para mostrar una función que la fuente no incluye. **POLÍTICA** identifica las reglas del equipo.

## 1. Columnas del archivo original

El tipo indicado es el tipo esperado **después de convertir el CSV**. Aunque el archivo CSV guarda caracteres, todos estos campos deben convertirse a números; una celda no numérica causa error. La ausencia nunca se interpreta automáticamente como cero.

| Columna | Tipo esperado | Unidad | Origen | Si está vacía |
|---|---|---|---|---|
| REVOLVING_UTILIZATION | decimal | proporción (1 = 100 %) | REAL · CSV | Desconocido; se conserva como nulo. |
| DEBT_TO_INCOME | decimal | proporción deuda/ingreso | REAL · CSV | Falta dato crítico; se bloquea la validación. |
| MISSED_PAYMENTS_12M | entero | número de pagos fallidos en 12 meses | REAL · CSV | Falta dato crítico; se bloquea la validación. |
| SAVINGS_BALANCE | decimal | unidades monetarias de origen* | REAL · CSV | Falta dato crítico; se bloquea la validación. |
| DOWN_PAYMENT_PCT | decimal | proporción del enganche | REAL · CSV | Desconocido; se conserva como nulo. |
| FINANCIAL_LITERACY_SCORE | decimal | puntos (escala por confirmar) | REAL · CSV | Desconocido; se conserva como nulo; excluido del modelo. |
| LOAN_TO_VALUE | decimal | proporción préstamo/valor | REAL · CSV | Falta dato crítico; se bloquea la validación. |
| DELINQ_90 | entero | número de atrasos de 90+ días | REAL · CSV | Desconocido; se conserva como nulo. |
| YEARS_CREDIT_HISTORY | decimal | años de historial | REAL · CSV | Desconocido; se conserva como nulo. |
| PAYMENT_TO_INCOME | decimal | proporción pago/ingreso | REAL · CSV | Falta dato crítico; se bloquea la validación. |
| BANKRUPTCY_FLAG | entero 0/1 | indicador (0=no; 1=sí) | REAL · CSV | Desconocido; nunca se interpreta como 0. |
| DEFAULT | entero 0/1 | resultado histórico (0=no; 1=sí) | REAL · CSV | Falta variable objetivo; se bloquea la validación. |

*El archivo no acredita por sí solo una moneda. La interfaz usa el símbolo $, pero no se debe afirmar que es MXN o USD sin comprobar la fuente. Este campo debe mantenerse numérico para ordenar correctamente importes.

**Privacidad:** `DEFAULT` histórico no se presenta en expedientes individuales del analista; gerencia solo recibe agregados. La matriz de permisos de la aplicación sigue vigente.

## 2. Columnas y cifras construidas para las pantallas

En estas columnas también debe constar el origen. Cuando no existe dato suficiente, la interfaz debe mostrar «Sin dato» o «—», no un cero inventado. Se incluye el nombre interno cuando existe.

| Columna o cifra publicada | Tipo | Unidad | Origen | Si está vacía |
|---|---|---|---|---|
| FOLIO / Folio | texto | identificador | SIMULADO | No se puede abrir el expediente. |
| ANALISTA_ID | texto | identificador del analista | SIMULADO | No se asigna una solicitud. |
| RECIBIDA_MIN / Recibida | número o texto de visualización | minutos desde recepción | SIMULADO | Se muestra «Sin hora»; no se supone cero. |
| PD | decimal | probabilidad (0 a 1; en pantalla %) | CALCULADO · modelo | Sin recomendación hasta tener datos suficientes. |
| NIVEL | categoría | Bajo, Medio, Alto | CALCULADO · PD + POLÍTICA | Sin clasificación. |
| CALIDAD / Datos | categoría | Completo, Incompleto, Fuera de rango | CALCULADO | Se solicita revisar el expediente. |
| SUGERENCIA / Sugerencia del modelo | categoría | Aprobar, Condicionar, Rechazar | CALCULADO + POLÍTICA | Sin sugerencia; requiere revisión. |
| ESTADO_SOLICITUD | categoría | Pendiente, En espera, Resuelta | SIMULADO / bitácora | Pendiente solo por regla explícita de la demo. |
| SEG_DTI | categoría | tercil de DTI | CALCULADO · DEBT_TO_INCOME | Sin segmento si falta DTI. |
| SEG_ENGANCHE | categoría | banda de enganche | CALCULADO · DOWN_PAYMENT_PCT | Sin segmento. |
| SEG_PAGOS | categoría | banda de pagos fallidos | CALCULADO · MISSED_PAYMENTS_12M | Sin segmento. |
| SEG_BANCARROTA | categoría | Sí / No | CALCULADO · BANKRUPTCY_FLAG | Sin segmento. |
| SEG_LTV | categoría | banda de LTV | CALCULADO · LOAN_TO_VALUE | Sin segmento. |
| n / Registros crediticios | entero | registros | CALCULADO · conteo de REAL | Cero solo cuando efectivamente no hay filas. |
| tasa / Tasa de incumplimiento | decimal | proporción (en pantalla %) | CALCULADO · DEFAULT | No se publica con n menor de 30. |
| DTI promedio | decimal | proporción (en pantalla %) | CALCULADO · DEBT_TO_INCOME | Se muestra «—» si no hay valores válidos. |
| Campos críticos completos | decimal | proporción (en pantalla %) | CALCULADO · campos críticos | Se muestra «—» sin filas válidas. |
| Registros fuera de límites | entero | registros | CALCULADO · límites de src/config.py | Cero solo si se revisaron datos y no hubo casos. |
| Alertas y series del monitor | número / categoría | según métrica | SIMULADO, salvo bitácora indicada | No se presenta como monitoreo productivo. |

### Otras columnas que se muestran en las tablas

| Columna publicada | Tipo | Unidad | Origen | Si está vacía |
|---|---|---|---|---|
| DTI y LTV (bandeja) | decimal | porcentaje (0 a 100) | REAL · DEBT_TO_INCOME y LOAN_TO_VALUE | Sin porcentaje; se revisa la calidad de datos. |
| Ahorro (bandeja) | decimal | dinero de la fuente* | REAL · SAVINGS_BALANCE | Celda vacía; requiere documento. |
| Variable (expediente) | texto | nombre de la variable | REAL · esquema y etiquetas | La fila no se presenta. |
| Valor (expediente) | decimal | indicada en Unidad | REAL · dato de la solicitud | Vacío; el Estado indica si falta o fue imputado. |
| Unidad (expediente) | texto | %, años, pagos, 0/1 o dinero | POLÍTICA · FORMATO | Se muestra «sin unidad». |
| Típico buen pagador | decimal | la misma que Valor | CALCULADO · mediana del entrenamiento | Sin referencia disponible. |
| Estado (expediente) | categoría | REAL, IMPUTADO, FUERA DE RANGO | CALCULADO · revisión del dato | Requiere verificación. |
| Variable (coeficientes) | texto | nombre del factor | REAL · esquema del modelo | Se omite la fila. |
| Dirección | categoría | sube o baja el riesgo | CALCULADO · coeficiente del modelo | Sin conclusión. |
| Efecto de +1 desv. estándar | decimal | razón de momios | CALCULADO · modelo | Sin estimación. |
| Hora (bitácora) | fecha-hora | hora local registrada | REAL · bitácora | Sin fecha confirmada. |
| Métrica (alerta) | texto | nombre del indicador | SIMULADO / bitácora | Sin indicador. |
| Valor (alerta) | texto descriptivo | la indicada en cada alerta | SIMULADO / bitácora | Sin lectura. |
| Acción (alerta) | categoría | escalada o descartada | REAL · bitácora | Pendiente de atender. |
| Tipo (alerta) | categoría | clase de incidente | REAL · bitácora | No clasificado. |
| Nota (alerta) | texto | explicación | REAL · bitácora | Se solicita una nota antes de guardar. |
| Responsable | texto | nombre del operador | REAL · bitácora | Sin responsable registrado. |
| Folio (decisión) | texto enmascarado | identificador parcial | SIMULADO + bitácora | No se muestra una solicitud identificable. |
| Decisión | categoría | aprobar, condicionar, rechazar | REAL · decisión guardada | Sin decisión. |
| Categoría (decisión) | categoría | tipo de acuerdo o contradicción | CALCULADO · decisión frente al modelo | Sin clasificación. |
| Motivo (catálogo) | texto | motivo seleccionado | REAL · bitácora | Se muestra «—» si no aplica. |
| PD (bitácora) | decimal | porcentaje | CALCULADO · modelo | Sin estimación. |
| Qué vigila | texto | nombre del indicador | POLÍTICA · registro del monitor | No se publica. |
| Umbral / banda | texto | límites y unidades de cada métrica | POLÍTICA · registro del monitor | Sin umbral definido. |
| Frecuencia | texto | minutos, horas o días | POLÍTICA · registro del monitor | Sin periodicidad. |
| Si se sale | texto | acción sugerida | POLÍTICA · registro del monitor | Revisión manual. |
| Origen | categoría | REAL, CALCULADO, SIMULADO, POLÍTICA | CALCULADO · clasificación del equipo | Se exige identificarlo. |
| Estado (catálogo de excepciones) | texto | nombre del estado | POLÍTICA · recorridos | Sin caso registrado. |
| Pantalla · persona | texto | rol y pantalla | POLÍTICA · recorrido | Sin responsable. |
| Disparador | texto | condición que provoca el estado | POLÍTICA · recorrido | Sin disparador. |
| Qué ve la persona | texto | resultado de interfaz | POLÍTICA · recorrido | Sin información para mostrar. |
| Recuperación | texto | acción de recuperación | POLÍTICA · recorrido | Revisión manual. |
| Cómo verlo | texto | instrucción de prueba | POLÍTICA · recorrido | No hay escenario reproducible. |
| Dato / Campo | texto | nombre de columna o dato | POLÍTICA · matriz de acceso | Sin regla se oculta por defecto. |
| Adrián, Mariana y Luis (matriz) | categoría | nivel de acceso | POLÍTICA · seguridad | Sin permiso. |
| Tratamiento | categoría | ocultar, agregar, enmascarar, restringir | POLÍTICA · seguridad | Se oculta por defecto. |
| Sensibilidad | categoría | clasificación del dato | POLÍTICA · seguridad | Se restringe hasta clasificar. |
| Nota (gobierno) / Razón | texto | explicación de regla | POLÍTICA · registro | Sin justificación. |
| Nivel (resumen de acceso) | categoría | individual, agregado, oculto, etc. | CALCULADO · matriz de acceso | Sin nivel. |
| ID (filtro o control) | texto | identificador F o C | POLÍTICA · registro | No se presenta. |
| Filtro / Control | texto | nombre del elemento | POLÍTICA · registro | No se presenta. |
| Pantalla / Persona | texto | pantalla y responsable | POLÍTICA · registro | No se presenta. |
| Decisión que cambia | texto | decisión del usuario | POLÍTICA · registro | La regla se considera incompleta. |
| Por defecto | texto / categoría | valor inicial | POLÍTICA · registro | Sin selección inicial. |
| Tipo / Qué habilita | texto | clase y uso del dato propuesto | POLÍTICA · catálogo | No se incorpora al tablero. |
| KPI | texto | nombre del indicador | CALCULADO · registro del tablero | No se presenta. |
| Fórmula | texto | operación que produce el KPI | CALCULADO · metodología | No se publica sin definición. |

Las columnas que contienen importes, porcentajes, PD y coeficientes se mantienen numéricas. Streamlit les da formato para mostrarlas y permite ordenarlas por su valor. Los textos de alertas, catálogos y notas se mantienen como texto porque describen un evento, no una medida comparable.

## 3. Convención de ausencias y errores

| Marcador leído | Conversión | Interpretación |
|---|---|---|
| Celda vacía, `NA`, `N/A`, `NULL`, `NONE`, `NAN`, `?`, `-`, `S/D` | `None` en la validación | No se conoce el valor; **no** equivale a cero. |
| `0` | Número cero | Dato presente y válido; en `DEFAULT` significa no incumplimiento. |
| `1` | Número uno | Dato presente y válido; en `DEFAULT` significa incumplimiento. |
| Texto como `NO_ES_UN_NUMERO` en una columna numérica | Error | Se rechaza el archivo en el pipeline. |
| Infinito o `DEFAULT` diferente de 0/1 | Error | Se rechaza el archivo. |
| Valor no aplicable | Nulo documentado | Solo se usa si una regla de negocio lo determina; no se infiere del cero. |

Estos son los marcadores que reconoce la lectura del CSV. La base actual no contiene valores ausentes en las doce columnas.

**Resultado comprobado en CI:** en la [corrida del 15 de noviembre de 2026](https://github.com/a01664722-ai/autocredit_advisor-2/actions/runs/43777067259), las 80,000 filas superaron la verificación de las 12 columnas y no aparecieron marcadores de ausencia. En una [corrida negativa independiente](https://github.com/a01664722-ai/autocredit_advisor-2/actions/runs/43777208621), el pipeline sí rechazó un valor de texto en `SAVINGS_BALANCE`.

## 4. Cómo se comprueba

- `python -m scripts.verificar_contrato data/Base_SAS_Equipo3.csv` revisa encabezados, que las 12 columnas sean numéricas, enteros donde corresponde, banderas 0/1, ausencias críticas y al menos 30 registros.
- `tests/test_contrato_datos.py` prueba un CSV correcto y casos con texto en una columna numérica, `DEFAULT=2`, ausencia de DTI y ausencia no crítica.
- `.github/workflows/pruebas.yml` corre la verificación y `pytest` en los cambios del repositorio.
- `src/datos.py` aplica el mismo contrato al cargar la base, antes de mostrar información financiera. Si falla, la app presenta el error y detiene la navegación de datos. Si pasa, la barra lateral indica que se verificaron las 12 columnas numéricas.
- Las tablas usan `column_order` y `hide_index=True`. Los campos numéricos de la bandeja, la ficha y los indicadores del monitor se presentan como números para que el ordenamiento sea correcto.
