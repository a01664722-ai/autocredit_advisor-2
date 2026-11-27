# Entregable 2 · Evidencia de Build / Test

**Repositorio de referencia:** https://github.com/a01664722-ai/autocredit_advisor-2

## Entrega documental y pruebas

En la retroalimentación compartida, el profesor acreditó completamente **las partes 1 y 2 (80/80 puntos de esos criterios)**: las tres mejoras justificadas, la distinción entre pruebas deterministas e instrucciones, la investigación y las preguntas del curso, el contrato de datos, el pipeline y el orden de las tablas. Este documento reúne en un solo lugar las piezas disponibles en el repositorio.

| Requisito | Evidencia verificable | Estado documental |
|---|---|---|
| Investigación de Anthropic y mejoras elegidas | [`investigacion/claude.md`](../investigacion/claude.md) | Incluida |
| Instrucciones del proyecto y revisión | [`CLAUDE.md`](../CLAUDE.md) | Incluido |
| Contrato de datos: tipo, unidad, procedencia y ausencias | [`contrato-datos.md`](../contrato-datos.md) | Incluido |
| Validación automática del dataset | [`scripts/verificar_contrato.py`](../scripts/verificar_contrato.py) y pruebas en [`tests/`](../tests/) | Implementada |
| Pipeline sobre `main` | [`.github/workflows/pruebas.yml`](../.github/workflows/pruebas.yml) | Implementado |
| Evidencia de corrida incorrecta detectada | https://github.com/a01664722-ai/autocredit_advisor-2/actions/runs/43777208621 | Corrida registrada |
| Evidencia de corrida exitosa | https://github.com/a01664722-ai/autocredit_advisor-2/actions/runs/45739300997 | CI de datos y pruebas en verde |
| Registro de prompts B2 | [`prompts/B2.md`](../prompts/B2.md) | Incluido |
| Contrato y registro del bloque 1 | [`contrato-prompt.md`](../contrato-prompt.md), [`prompts/B1.md`](../prompts/B1.md), [`docs/entregable-1.md`](entregable-1.md) | Incluidos |

## Verificación de resultados

- El CSV está sujeto a revisión de esquema, tipos, ausencias, valores inválidos y consistencia antes de su uso en las pantallas.
- El workflow instala dependencias, ejecuta la validación del CSV y después la suite `pytest` en GitHub Actions.
- Las tablas se configuran con `column_order` y `hide_index=True` para respetar el orden y la lectura del dato.
- Se documentan por separado las decisiones del equipo y las recomendaciones del asistente en los registros de prompts.

## Evidencia de aportaciones individuales

Las aportaciones se registran en [`ideas/`](../ideas/) y [`avance/A01664722.md`](../avance/A01664722.md). No se asignan calificaciones individuales no documentadas.

## Conclusión de B2

**La evidencia de datos, Build/Test y pruebas queda organizada en el repositorio indicado.** Esta ficha no modifica el producto, sus pantallas, la base de datos ni el modelo. La corrida verde citada comprueba el workflow de datos y `pytest`, **no sustituye las verificaciones de accesibilidad de B3**.
