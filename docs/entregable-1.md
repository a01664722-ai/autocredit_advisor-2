# Entregable 1 · Corrección documental de la retroalimentación

**Repositorio definitivo:** https://github.com/a01664722-ai/autocredit_advisor-2  
**Dashboard público informado:** https://autocreditadvisor-2-f2ww6wn7nnrysa43edznfp.streamlit.app/  
**Puntaje de la primera entrega:** 28/100. El profesor confirmó que la URL en ventana privada, la aplicación por perfiles y sus pantallas **sí funcionaban**: la principal penalización fue por documentación faltante.

## Comprobación por criterio del profesor

| Criterio B1 | Evidencia y estado |
|---|---|
| URL accesible en ventana privada | Confirmación del profesor en la retroalimentación B1. En `README.md` la primera línea es la URL. |
| Dos observaciones del 21 de octubre cerradas | Ver O-1 y O-2 abajo; `vistas/p2_ficha.py`, `vistas/p5_estados.py`, `src/seguridad.py` y `vistas/p6_gobierno.py` |
| Contrato del prompt personalizado, literal y cambios | `contrato-prompt.md`: pantallas, salida, texto original disponible, resultado verificable, cambios y autoría. **Literal histórico no completo:** se declara en vez de inventarlo. |
| Objetivo de negocio: decisión, línea base y meta | Adrián: aprobar, condicionar o rechazar; meta ≤ 5 minutos. **14 min / 20 casos** fue sugerencia del profesor, no medición documentada: **línea base empírica pendiente**. |
| Registro de prompts sin campos mudos y con revisión humana | `prompts/B1.md`: formato requerido, decisiones humanas, archivo y commit. Los prompts/respuestas no preservados se identifican como tales. |
| Un repositorio y continuidad de los cuatro bloques | `autocredit_advisor-2` es el repositorio definitivo. La unificación histórica real del repositorio B1 original **no está resuelta**; ver `docs/entregable-2.md`. |

## O-1 — exposición del 21 de octubre · bifurcación de error

**Qué observó el profesor:** la experiencia de error no puede limitarse al login; debe haber recuperación dentro del análisis.  
**Qué cambió:** la ficha y los recorridos contemplan folio ajeno, información faltante, datos inválidos y sesión expirada, con controles para recuperar y evitar decisiones sin validar.  
**Dónde quedó:** `vistas/p2_ficha.py` (estados, interrupciones `st.stop()`), `vistas/p5_estados.py` (recorridos), `tests/test_seguridad.py` y `tests/test_app.py`. Estado verificable en `main@6f3a4b12736e66e1bd99a5d1c02930dee50e642d`. Este SHA es **evidencia del estado**, no se presenta como autoría exclusiva del cambio.

## O-2 — exposición del 21 de octubre · matriz persona × dato sensible

**Qué observó el profesor:** faltaba la matriz aplicada de permisos, no únicamente una descripción.  
**Qué cambió:** se documentó y programó acceso por analista, gerente y operación, con protección de datos de solicitudes e imposibilidad de consultar permisos no declarados (denegación por defecto).  
**Dónde quedó:** `src/seguridad.py` (`MATRIZ_DATOS`, `aplicar_politica_fila`, `puede_ver`), `vistas/p6_gobierno.py` y `tests/test_seguridad.py`. Estado verificable en `main@6f3a4b12736e66e1bd99a5d1c02930dee50e642d`.

## Evidencia adicional de criterios de diseño

- Jerarquía y filtros: `vistas/p1_bandeja.py` y `src/ui.py`.
- Rótulos de origen REAL / CALCULADO / SIMULADO / POLÍTICA: `src/ui.py`.
- Unidades y orden de columnas: `vistas/p1_bandeja.py`; contrato por columna: `contrato-datos.md`.
- Preguntas de gráficas y alcance por perfil: `docs/entregable-3.md`.
- Registro de revisión individual: consultar `ideas/` y `avance/`.

**No se reescribe historia Git ni se declara recuperado un prompt original que no está disponible.**
