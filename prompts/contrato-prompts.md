# Contrato del prompt — Equipo 3 · AutoCredit Advisor

**Bloque:** Entregable 1 (Plan / Design). **Repositorio definitivo:** https://github.com/a01664722-ai/autocredit_advisor-2

**Alcance documental:** reconstruye el contrato con la evidencia del profesor, el prompt aportado por el equipo y el código existente. El registro histórico literal está **incompleto**: no se inventan fragmentos ni respuestas de IA que no fueron conservados. Ver `prompts/B1.md`.

## 1. Qué debe mostrar el tablero y qué decisión habilita

| Pantalla | Persona | Qué muestra | Decisión |
|---|---|---|---|
| P0 · Acceso | Equipo de prueba | Cuenta/perfil y límites del modo demostración | Entrar únicamente a vistas autorizadas |
| P1 · Bandeja | Adrián, analista | KPIs, filtro de estado F1, riesgo F2 y solicitudes | Elegir qué caso atender primero |
| P2 · Ficha | Adrián | PD, datos válidos, comparación, explicación y registro | Aprobar, condicionar o rechazar, con motivo en excepción |
| P3 · Cartera | Mariana, gerente | Segmentos, tasas, umbrales y simulación del corte | Endurecer o relajar política por segmento |
| P4 · Monitor | Luis, operación | Alertas, tendencia, distribución, vigilancia y bitácora | Escalar o descartar con justificación |
| P5 · Estados | Roles autorizados | Bifurcaciones de error y recuperación | Recuperarse de datos erróneos y estados vacíos |
| P6 · Gobierno de datos | Roles autorizados | Matriz persona × pantalla y persona × dato | Saber qué información se permite mostrar |
| P7 · Indicadores | Varios perfiles | KPIs específicos por perfil | Dar seguimiento a su trabajo o a la calidad de información |

**Estados que deben existir:** sin sesión, sin rol, filtro sin resultados, dato ausente o fuera de rango, segmento con muestra insuficiente, sesión expirada y excepción a la recomendación. La simulación y los límites de seguridad se rotulan como tales.

**Objetivo de negocio:** permitir que Adrián apruebe, condicione o rechace una solicitud con información de riesgo y evidencia de revisión. **Meta:** menos de 5 minutos por decisión; **línea base:** el profesor propuso 14 minutos con 20 casos manuales, pero no hay evidencia en este repositorio de que esos 20 tiempos se hayan medido. Es **referencia pendiente de validación**, no resultado observado. Para medir mejora se requiere una muestra de decisiones manuales con cronometraje, criterio uniforme y comparación posterior sin aumentar errores de clasificación.

## 2. Diseño de la salida: columnas, orden, unidades y jerarquía

**P1, en el orden implementado:** Folio (identificador simulado), Recibida (tiempo simulado), PD (porcentaje calculado), Nivel (categoría calculada), Datos (estado validado), Sugerencia del modelo (categoría calculada), DTI (%), LTV (%) y Ahorro (unidad monetaria de la fuente, sin moneda declarada). Fuente: `vistas/p1_bandeja.py`, `column_order` y `hide_index=True`.

**Distribución:** arriba cabecera, KPIs y filtros; después corte activo y conteo; enseguida tabla priorizada y acción para abrir ficha; al final procedencia y límites. P2 presenta primero datos y estado de riesgo, luego comparación, intervención humana y registro. P3/P4 ponen filtros y semáforos antes del detalle analítico.

**Cifras:** REAL = columna del CSV; CALCULADO = resultado derivado o PD; SIMULADO = folio, fecha y condiciones no presentes en la base; POLÍTICA = umbral acordado. Cada pantalla debe distinguirlas. Dato protegido no aparece por la sola existencia de una columna. DTI/LTV/PD se muestran con unidad %, no como texto libre; montos con unidad no especificada, sin suponer MXN.

## 3. Prompt de apoyo al código y auditoría de vistas (versión consolidada)

**Objetivo de la solicitud:** pedir apoyo técnico para **revisar, organizar y auditar el código de GitHub que el equipo ya estaba trabajando**, especialmente la creación y funcionamiento de cada vista de Streamlit. **No se solicitó delegar a la IA el diseño del negocio ni presentar la app como una creación autónoma de la IA.**

> **Rol y objetivo**
>
> Actúa como especialista en Python, Streamlit, ciencia de datos y revisión de código. Necesitamos que nos ayudes a **revisar y organizar el código existente** de nuestro repositorio de GitHub de AutoCredit Advisor. Verifica que las pantallas estén correctamente separadas, funcionen y correspondan al diseño y a las decisiones de las personas usuarias. No queremos que inventes otro producto ni que reconstruyas desde cero el dashboard.
>
> **Contexto**
>
> - Repositorio del equipo: `a01664722-ai/autocredit_advisor-2`.
> - Base de trabajo del entregable: `Base_SAS_Equipo3.csv`, con 80,000 registros sintéticos y 12 columnas, incluida `DEFAULT`.
> - Prototipo de referencia: *User Persona Riesgo Crediticio v2.pdf*.
> - Perfiles: Adrián (analista, revisa y decide solicitudes), Mariana (gerencia, revisa cartera y política) y Luis (operación, supervisa resultados y alertas).
> - Tecnologías: Python, Streamlit, Pandas y Plotly; código versionado en GitHub.
>
> **Qué necesitamos que revises y nos ayudes a ordenar**
>
> 1. **Estructura del repositorio:** comprobar que `app.py` organice la navegación, `vistas/` contenga las pantallas, `src/` concentre funciones compartidas y `tests/` permita probarlas. Evitar lógica repetida.
> 2. **Pantallas P0–P7:** verificar para cada vista quién la utiliza, qué información muestra, cómo llega el usuario, qué filtros o botones funcionan y qué decisión puede tomar. Identificar vistas incompletas, controles sin efecto y errores de navegación.
> 3. **Roles y datos sensibles:** revisar las restricciones por perfil y la matriz persona × dato, de manera que el analista solo acceda a sus solicitudes y cada rol vea únicamente lo autorizado.
> 4. **Flujo de análisis:** comprobar que las solicitudes puedan abrirse, que los datos se validen antes de registrar una decisión, que existan estados vacíos y rutas de recuperación ante errores y que las excepciones requieran justificación.
> 5. **Indicadores y visualizaciones:** comprobar que cada KPI y gráfica responda a una pregunta concreta; que las cifras sean correctas y se identifique su origen como REAL, CALCULADO, SIMULADO o POLÍTICA.
> 6. **Interfaz:** revisar jerarquía visual, contraste, etiquetas, colores acompañados de texto y que los filtros tengan resultados visibles. No alterar pantallas que ya cumplen sin justificarlo.
> 7. **Pruebas y calidad:** identificar qué funciones necesitan pruebas; revisar el funcionamiento por rol, los errores dentro del proceso y la consistencia con el dataset; indicar qué está verificado y qué falta comprobar.
>
> **Cómo queremos la respuesta**
>
> Devuélvenos una **propuesta de organización por carpetas**, una **tabla por pantalla** (vista, persona, funcionalidad, decisión y estado de revisión), una **lista de observaciones técnicas con archivo relacionado**, y **cambios puntuales de código o pruebas que podamos revisar antes de integrar**. Explica por qué sugieres cada cambio. **No sustituyas nuestras decisiones de diseño, negocio, permisos ni política crediticia.**

**Trazabilidad:** este es el **prompt consolidado conforme a la aclaración actual del equipo** y al enfoque de revisión del repositorio. **No se presenta como transcripción literal del mensaje histórico original.** En el fragmento inicial que se había conservado aparecía la frase «diseñar y construir un tablero»; el equipo aclara que, en la práctica, pidió apoyo sobre el código y las vistas del producto en desarrollo. El registro original permanece consultable en el historial del archivo; el prompt literal íntegro aún debe recuperarse si el profesor lo exige.

## 4. Qué devolvió la IA

La IA **nos ayudó a estructurar y revisar el desarrollo del dashboard existente**. Su aportación se centró en organizar el código y señalar qué revisar en cada pantalla; **no sustituyó el trabajo del equipo ni decidió por nosotros cómo debía operar el negocio**.

- **Organización del código:** propuso separar la entrada y navegación en `app.py`, las pantallas por perfil en `vistas/`, la lógica compartida en `src/` y las verificaciones en `tests/`. Esto facilita revisar cada parte sin mezclar la interfaz con los cálculos.
- **Revisión de las vistas:** ayudó a establecer qué debía comprobarse en P0 (acceso), P1 (bandeja), P2 (ficha), P3 (cartera), P4 (monitor), P5 (errores y recuperación), P6 (gobierno de datos) y P7 (indicadores). La revisión debía relacionar **persona, información, botón o filtro y decisión**.
- **Auditoría funcional:** aportó criterios para identificar controles sin efecto, información que un rol no debe ver, datos faltantes, falta de justificación al contradecir una recomendación y pantallas sin una salida clara.
- **Revisión de calidad:** orientó la separación de pruebas y comprobaciones de acceso, integridad de datos y flujo antes de aceptar cambios en GitHub.
- **Mejoras posteriores por iteración:** también hubo respuestas relativas a la pantalla P7 y los KPI por perfil; esos entregables se documentan como **iteraciones posteriores**, no como prueba de que la IA creó por sí sola la aplicación inicial. Su evidencia se describe en `prompts/B1.md` (P-003).

**Resumen en dos líneas:** la IA aportó una propuesta para **organizar el código de GitHub por vistas y módulos** y una guía para **auditar pantallas, funciones, permisos y pruebas**. El equipo revisó esas propuestas y decidió qué correcciones correspondían al producto.

**Evidencia verificable:** `app.py`, `vistas/`, `src/`, `tests/`, `src/seguridad.py` y `vistas/p6_gobierno.py`; las carpetas y los controles existen en el repositorio. **La lista anterior describe el apoyo y el resultado observable; no es una transcripción palabra por palabra de la primera respuesta de la IA.**

## 5. Qué cambiamos de lo que devolvió la IA

**No integramos las sugerencias automáticamente.** Contrastamos la organización y las observaciones propuestas con el prototipo, los comentarios del profesor y el comportamiento del código. En particular:

1. **Revisamos pantalla por pantalla** que las vistas correspondieran al rol y a la decisión definida por el equipo; mantuvimos la separación entre navegación, pantallas, cálculos y pruebas.
2. **Corregimos el flujo de errores:** el profesor señaló que no bastaba con mostrar errores en el inicio de sesión. La revisión incorporó situaciones de información faltante, datos inválidos y recuperación **dentro de la ficha y del proceso de análisis**. Evidencia: `vistas/p2_ficha.py` y `vistas/p5_estados.py`.
3. **Aplicamos los permisos, no solo los dibujamos:** la matriz persona × dato y los controles por rol se reflejan en `src/seguridad.py`, `vistas/p6_gobierno.py` y `tests/test_seguridad.py`.
4. **Ajustamos la lectura de las cifras:** orden de columnas, unidades y notas de procedencia (REAL, CALCULADO, SIMULADO y POLÍTICA); documentación en `src/ui.py`, `vistas/p1_bandeja.py` y `contrato-datos.md`.
5. **Conservamos las decisiones del equipo:** ningún cambio de la IA se consideró aprobado sin revisión; se mantuvieron la intervención humana, el objetivo de negocio y los controles relacionados con la información disponible.

Los archivos citados permiten comprobar **qué funciona y dónde quedó**. No se atribuye a una respuesta histórica específica una línea de código si no se cuenta con la comparación de versiones correspondiente. Más detalle en `docs/entregable-1.md`.

## 6. Qué decidimos nosotros y no la IA

El equipo determinó **las tres personas usuarias y sus decisiones**, los datos que necesita cada pantalla, los permisos de acceso, el significado de los datos faltantes, los criterios de riesgo, el objetivo de resolver una solicitud en menos de cinco minutos, las acciones disponibles para el analista y la necesidad de justificar las excepciones. También **auditamos las propuestas técnicas y decidimos cuáles integrar**; la IA actuó como apoyo para organizar y revisar el código, no como responsable de validar el producto ni de tomar decisiones crediticias.

**Continuidad pendiente:** el repositorio histórico de B1 `a01659312-iis/autocredit_advisor---9nov` y el definitivo `a01664722-ai/autocredit_advisor-2` tienen historias Git independientes. Actualizar el contrato no fusiona esas historias.


> **Nota de ruta:** esta versión se publica también en `prompts/contrato-prompts.md`, la ruta alternativa solicitada en la rúbrica; el contenido principal se mantiene en `contrato-prompt.md`.
