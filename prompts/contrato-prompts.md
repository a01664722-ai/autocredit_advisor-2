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

## 3. Prompt literal disponible

Se transcribe **solo el fragmento literal** aportado al equipo. El texto recibido termina cortado; no se completa artificialmente:

> Rol y objetivo
>
> Actúa como especialista en ciencia de datos, diseño de tableros (UX/UI) y desarrollo en Python. Necesito tu ayuda para diseñar y construir un tablero (dashboard) de riesgo crediticio en Streamlit, estructurado como proyecto de Visual Studio Code, para la materia de Analítica de Datos y Herramientas de Inteligencia Artificial.
>
> Contexto
>
> - Base de datos: [Base_SAS_Equipo3.csv] — datos sintéticos de crédito automotriz (80,000 registros, 12 variables, incluida la variable objetivo DEFAULT).
> - Prototipo previo: [User Persona Riesgo Crediticio v2.pdf] — contiene las personas usuarias, el mapa de pantallas y el diseño inicial del tablero.
> - Personas usuarias:
> - Adrián, analista de crédito: aprueba, condiciona o rechaza solicitudes individuales en menos de 5 minutos.
> - Mariana, gerente de riesgo: ajusta la política de crédito por segmento con base en el incumplimiento.
> - Luis, operación del modelo: vigila métricas operativas y escala alertas cuando algo sale de su banda.
>
> Requerimientos funcionales
>
> 1. Una pantalla por decisión de cada persona, con acceso por rol (principio de menor privilegio) y una matriz completa persona × dato sensible.
> 2. Modelo de probabilidad de incumplimiento (PD) entrenado con la base, interpretable y con métricas de desempeño (AUC, KS, calibración).
> 3. Cada filtro y control debe estar vinculado explícitamente a la decisión de una persona.
> 4. Notación de origen de cada cifra: dato real, dato propio () y dato simulado (*), con su aclaración al pie de cada pantalla.
> 5. Semáforo verde / amarillo / rojo, íconos de tendencia (▲/▼) y comparación de cada solicitud contra la media de la cartera.
> 6. Flujo operativo que primero valide la información y después registre la decisión; notificación al analista cuando la gerencia cambie el corte de un segmento.
> 7. Estados de error y recuperación dentro del flujo de análisis (datos faltantes, filtros sin resultados, muestra insuficiente, sesión expirada, datos desactualizados).
>
> Retroalimentación por atender
>
> [Pega aquí la retroalimentación recibida, organizada por bloque o criterio.]
>
> Criterios de diseño
>
> - Jerarquía visual clara: métricas y filtros clave en la parte superior, mínimo desplazamiento vertical.
> - Uso moderado de mayúsculas; protagonismo para los nombres de secciones y variables.
> - Accesibilidad: el color siempre acompañado de texto o ícono; modo claro y oscuro.
> - Una sola escala por gráfica; nada de gráficas de doble ej

**Nota de autenticidad:** el fragmento se recibió sin la parte final y con el marcador «Pega aquí...». No se afirma que esa sección haya sido completada ni que se conserve el prompt histórico íntegro.

## 4. Qué devolvió el asistente (evidencia verificable)

**La respuesta textual exacta de la IA no está archivada.** El resultado del desarrollo sí puede comprobarse: en el repositorio original de B1 se construyeron `app.py`, `vistas/p0_login.py` a `p6_gobierno.py`, `src/` y `tests/`; la aplicación se publicó en Streamlit. Esa es evidencia de *producto*, no transcripción de la salida del asistente.

## 5. Qué cambió el equipo frente al resultado

La retroalimentación del 21 de octubre exigía (i) error **dentro** del flujo de análisis, no solo en login, y (ii) matriz persona × dato sensible aplicada, no solo dibujada. En el repositorio definitivo existen `vistas/p2_ficha.py`, `vistas/p5_estados.py`, `src/seguridad.py`, `vistas/p6_gobierno.py` y `tests/test_seguridad.py` para comprobar estos controles. También se incorporaron rótulos REAL/CALCULADO/SIMULADO/POLÍTICA, mensajes de error y restricciones por perfil. Los cambios concretos se documentan en `docs/entregable-1.md`; no se inventan fechas de autoría de cada cambio.

## 6. Qué decidimos nosotros y no el modelo

El equipo definió a Adrián, Mariana y Luis y sus decisiones; el umbral operativo y la meta de 5 minutos; qué columnas se ven por rol; el significado de un dato ausente; qué cifras se rotulan SIMULADAS; la necesidad de registrar excepciones; y la decisión de no usar la salida predictiva como aprobación automática.

**Riesgo pendiente:** el repositorio original `a01659312-iis/autocredit_advisor---9nov` y `a01664722-ai/autocredit_advisor-2` tienen historias Git independientes. Este documento no las fusiona ni afirma que los commits del primero pertenezcan a `main` del segundo.

> **Nota de ruta:** esta versión completa se publica también en `prompts/contrato-prompts.md` para cubrir la ruta explícita de la rúbrica; el contenido canónico se mantiene en `contrato-prompt.md`.
