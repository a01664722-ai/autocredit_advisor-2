# Entrega 4 · Equipo 3 · Auditoría de continuidad B1–B4

**Fecha límite comunicada por el profesor:** lunes **30 de noviembre de 2026, 23:59 (CDMX)**. En ese corte se reevaluarán los cuatro entregables; el avance del 25 de noviembre no es la calificación final.

## Preservación obligatoria de B1 y B2

**No se borran ni se reemplazan** los contratos, prompts y evidencias de B1/B2:

- B1: [contrato del prompt](../contrato-prompt.md), [registro original](../prompts/B1.md), [evidencia](entregable-1.md).
- B2: [contrato de datos](../contrato-datos.md), [registro original](../prompts/B2.md), [evidencia](entregable-2.md), [investigación Anthropic](../investigacion/claude.md).
- La versión antigua `app.py` y las vistas originales se preservan para trazabilidad. La interfaz final de presentación es `app_v3.py`; se debe validar su despliegue en Streamlit Cloud.

## Revisión de observaciones de la Evidencia 3

| Requisito del profesor | Implementación / evidencia | Estado verificable |
|---|---|---|
| 24 gráficas con pregunta | `docs/entregable-3.md`, secciones 1 y 4; `tests/test_b3_rubric.py` | Conservado y probado |
| Estado vacío y `st.stop()` | Bandeja y Ficha de `app_v3.py` | Conservado y probado |
| Dos controles activos y conteo visible | Estado / Recomendación, contador en P1 | Conservado y probado |
| Aislamiento de Adrián/Sofía | Filtro `ANALISTA_ID`, autorización de registro, `tests/test_analyst_isolation.py` | Conservado y probado |
| Registro de prompts | `prompts/B1.md`, `prompts/B2.md`, `prompts/B3.md` | Conservado; se agrega nota del ajuste |
| Contraste + simulación bajo protanopía y deuteranopía | `scripts/check_contrast_b3.py`, `scripts/check_cvd_b3.py`, `investigacion/B3.md`, `docs/evidencia-daltonismo.svg` | Contraste de tokens y simulación reproducibles |
| Estado de riesgo independiente del color | Símbolos ✓/◇/✕, leyendas y etiquetas, patrones/trazos de gráficas | Código implementado; revisión visual final requerida |
| Tema claro legible | `src/accessibility_theme.py`: fondos y tipografía explícitos, controles desde acceso y sidebar | Código y tests; revisión visual final requerida |
| Investigación 1 del curso Y estudio de user persona | La ficha distingue ambas referencias sin sustituirlas | **Pendiente: referencia bibliográfica exacta de Investigación 1 del curso** |
| CI verifica commit de `main` | `.github/workflows/contraste-v3.yml`: checkout sin `ref` fijo a V3, incorpora tests V3 y daltonismo | Ver corrida de GitHub Actions sobre `main` |
| B1/B2 sin borrar | No eliminar archivos `docs/entregable-{1,2}.md`, `prompts/B{1,2}.md`, contratos, `app.py` | Confirmar en diff del PR |

## Pasos de verificación funcional en la app

Entrar como Adrián desde Pantalla 0; cambiar **Oscuro → Claro**, activar **Modo daltónico**, comprobar que ✓/◇/✕ acompañan Aceptar/Condicionar/Rechazar. Revisar Bandeja, Ficha y Mis indicadores, incluidos gráfico, leyendas, menú de Decisión rápida y estado vacío con filtros sin resultados. Cambiar a Sofía (verificar que no accede a Loan ID de Adrián), luego Mariana (Métricas del área y Analistas y KPI, metas y diagramas), y Soporte (gráficos y tarjetas). Confirmar que al volver al acceso permanecen preferencias pero se borra el perfil anterior.

**No declarar completada la inspección visual hasta realizarla en navegador.** Esta ficha de evidencia y los scripts son trazabilidad, no una captura de prueba de cada estado.

## Criterios técnicos y métodos

`python -m compileall -q app.py app_v2.py app_v3.py src vistas scripts`  
`python scripts/check_contrast_b3.py`  
`python -m scripts.check_cvd_b3`  
`python -m pytest -q`

El pipeline debe ejecutar estos comandos con checkout del **commit evaluado** en main y el de la rama V3. Los modelos y sus parámetros no deben modificarse para cumplir requisitos de accesibilidad.

**Importante:** el checklist colaborativo `checklist_entrega4.json` contiene también tareas de SAS / modelo / conclusiones que requieren evidencia del equipo. **No declarar completado el Entregable 4 global basándose solo en los cambios de accesibilidad.**
