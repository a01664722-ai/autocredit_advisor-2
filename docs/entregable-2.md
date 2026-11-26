# Entregable 2 · Verificación del cierre de B1 y continuidad de Build / Test

**Resultado comunicado por el profesor:** partes 1 y 2 completas (**80/80**) y descuento de **10 puntos** por usar dos repositorios sin historia común. El equipo obtuvo **90/100** en B2. No reabrimos pantallas ni cambiamos la base/modelo por esta observación.

| Exigencia / comentario | Evidencia actual en `main` | Estatus |
|---|---|---|
| Investigación de Anthropic y tres mejoras | `investigacion/claude.md` | Documentado |
| Contrato de datos, tipo, unidad, procedencia y ausencias | `contrato-datos.md` | Documentado |
| Dato validado antes de mostrar la pantalla | `scripts/verificar_contrato.py`, `src/datos.py`, `app.py` | Implementado |
| Pruebas automáticas (casos positivos y negativos) | `tests/` y `.github/workflows/pruebas.yml` | Implementado |
| Corrida que falla ante dato inválido | https://github.com/a01664722-ai/autocredit_advisor-2/actions/runs/43777208621 | Evidencia histórica |
| Corrida en verde de Build/Test | https://github.com/a01664722-ai/autocredit_advisor-2/actions/runs/43804791814 | Evidencia histórica |
| Prompt de B2 y decisiones humanas | `prompts/B2.md` | Existente, sin modificar |
| Todos los requisitos documentales de B1 | `contrato-prompt.md`; `prompts/B1.md`; `docs/entregable-1.md` | Añadidos, con límites históricos declarados |
| **Una misma historia de Git de B1 a B4** | Dos repositorios de origen diferentes; `main` definitivo en `autocredit_advisor-2` | **PENDIENTE: NO RESUELTO POR DOCUMENTARLO** |

## Origen de la historia partida (comentario del profesor)

1. Entregable 1: https://github.com/a01659312-iis/autocredit_advisor---9nov
2. Entregable 2 y repositorio definitivo: https://github.com/a01664722-ai/autocredit_advisor-2

El profesor pidió quedarse con el segundo e incorporar la **historia real** del primero, no copiar sus archivos. Eso requiere un merge de historias no relacionadas, resolución de conflictos y revisión de la app antes de hacer `push`, y posteriormente avisarle en Canvas cuál es el repositorio definitivo. **No se ejecuta un merge automático aquí** porque el usuario pidió conservar íntegro el dashboard y no introducir operaciones de alto riesgo. La falta de ancestro común sigue siendo una observación vigente.

## Acreditación de avances individuales

El repositorio contiene ideas en `ideas/` (A01659312, A01659305, A01665592, A01657471, A01664722, A01658354) y `avance/A01664722.md`. La hoja del profesor identifica para A01664722 la «interfaz para consultar predicciones por perfil». La retroalimentación proporcionada de B2 es **del equipo**, no un comentario individual para cada persona. No se atribuyen calificaciones individuales ni intervenciones que no estén documentadas.

## Regla de continuidad

Los archivos originales de B2, el flujo de datos, los tests, la política de acceso y los módulos Streamlit permanecen intactos. La documentación incorporada es incremental, no una app alterna.
