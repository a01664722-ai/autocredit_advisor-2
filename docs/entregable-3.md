https://github.com/a01664722-ai/autocredit_advisor-2/actions/runs/43804791814

# Entregable 3 · Evidencia de despliegue, jerarquía y acceso

**Advertencia sobre primera línea:** la URL superior corresponde a un **CI verde de validación del CSV y pytest** previo a este documento. **No demuestra el contraste WCAG**: ese control todavía NO forma parte del pipeline y permanece como pendiente. No se etiqueta indebidamente una corrida anterior como prueba de accesibilidad.

**Repositorio definitivo:** https://github.com/a01664722-ai/autocredit_advisor-2  
**Dashboard público:** https://autocreditadvisor-2-f2ww6wn7nnrysa43edznfp.streamlit.app/

**Alcance:** la documentación audita `main`, la base de Build/Test de B1–B2. El dashboard de XGBoost presentado por el equipo tiene código adicional en la rama `v3-integracion-xgboost-12v`; `main` aún usa el modelo `PD-logit v1.0` en `src/config.py`. No se afirma que sean idénticos ni se cambian componentes para ocultar esa diferencia.

## 1. Gráficas: pregunta que responde cada visualización

| Visualización | Persona / pantalla | Pregunta de negocio | Evidencia |
|---|---|---|---|
| G1 · Barra de PD/corte | Adrián, P2 | ¿La PD está arriba o abajo del corte? | `vistas/p2_ficha.py`; `src/graficas.py:g1_barra_corte` |
| G2 · Contribuciones | Adrián, P2 | ¿Qué variables suben o bajan el riesgo de este caso? | `vistas/p2_ficha.py`; `g2_contribuciones` |
| G3 · Barras pareadas | Adrián, P2 | ¿En qué difiere de un buen pagador? | `vistas/p2_ficha.py`; `g3_pareadas` |
| G4 · Bandeja con barra de PD | Adrián, P1 | ¿Qué solicitud reviso primero? | `vistas/p1_bandeja.py` |
| G5 · Mapa de calor | Mariana, P3 | ¿Qué combinación de segmentos supera la tolerancia? | `vistas/p3_cartera.py`; `g5_mapa_calor` |
| G6 · Barras de pagos | Mariana, P3 | ¿Qué historial de pagos concentra más incumplimiento? | `vistas/p3_cartera.py`; `g6_barras_grupo` |
| G7 · Curva de cambio de corte | Mariana, P3 | Si cambio el corte, ¿cuánta aprobación pierdo y cuánto incumplimiento evito? | `vistas/p3_cartera.py`; `g7_tradeoff` |
| G8 · Tendencia/banda | Luis, P4 | ¿La aprobación sigue dentro de su banda esperada? | `vistas/p4_monitor.py`; `g8_linea_banda` |
| G9 · Distribuciones | Luis, P4 | ¿Cambió la población de solicitudes que llega? | `vistas/p4_monitor.py`; `g9_histogramas` |
| G10 · Acuerdo modelo/analista | Luis, P4 | ¿Las decisiones de analistas y recomendaciones del modelo se están separando? | `vistas/p4_monitor.py`; `g10_apiladas` |
| Discriminación, calibración y coeficientes | Luis, P4 | ¿El modelo separa los grupos?, ¿predice tasas cercanas a las observadas? y ¿qué variables pesan más? | `vistas/p4_monitor.py` |
| Cuatro gráficas de DTI / incumplimiento | KPI P7 | ¿Cómo se distribuye DTI?, ¿cuánto incumplió la cartera?, ¿DTI promedio?, ¿qué ocurre con DTI alto? | `vistas/p7_kpis.py` |

Cada título o comentario de código declara su pregunta; los colores se acompañan de leyendas, unidades y textos donde están implementados. Una gráfica no documentada en esta tabla no se considera automáticamente cubierta.

## 2. Paleta y razones calculadas

Se revisó `.streamlit/config.toml` y `src/graficas.py` siguiendo WCAG 2.2: **4.5:1** texto normal, **3:1** texto grande y elementos informativos no textuales. Ejemplos auditados: negro `#0b0b0b` / blanco `#ffffff` = **19.68:1**, gris de texto `#52514e` / blanco = **7.94:1**, texto claro `#f0efec` / fondo oscuro `#0f1110` = **16.48:1**. Sin embargo, gris tenue `#898781` / blanco = **3.59:1** y blanco / verde principal `#0f8a4f` = **4.40:1**; si se usan como texto normal sobre esas superficies, **no llegan a 4.5:1**. Cálculos, límites y reserva sobre pares renderizados: `investigacion/visual-jerarquia.md`.

**Estado del criterio CI de contraste:** **PENDIENTE.** El workflow actual verifica datos y tests, no paleta; por ello no se promete bloqueo automático de regresiones de color. No se cambió el código visual ni el workflow sin autorización.

## 3. Jerarquía visual justificada

El objetivo manda la prioridad: Adrián decide una solicitud, Mariana define política por segmento y Luis resuelve alertas. En P1 los KPIs y filtros se ven antes de la tabla y el botón de acción; en P3 aparecen filtros y conteo activo antes de mapas y curvas; en P4 el estado y las alertas aparecen antes de las gráficas de diagnóstico. Estas relaciones están respaldadas por `src/config.py`, `src/seguridad.py`, `vistas/` y por la respuesta del profesor sobre la exposición de octubre, no por preferencias arbitrarias.

**Fuente de apoyo:** `investigacion/visual-jerarquia.md` y W3C WCAG 2.2. **Investigación 1 original:** no localizada en `main`; queda pendiente anexarla si el profesor exige esa pieza histórica concreta.

## 4. Estado «nada seleccionado» y uso de `st.stop()`

**P3, `vistas/p3_cartera.py`:** cuando el corte no tiene muestra válida, se muestra explicación y **`st.stop()`** impide continuar al resto del cálculo. **P2, `vistas/p2_ficha.py`:** existen bloqueos de folio inexistente/ajeno y situaciones inválidas, también con `st.stop()`. **P1:** si F2 no tiene niveles seleccionados, ofrece estado vacío y restablecer sin mostrar una tabla válida. Los tres casos no deben confundirse: el `st.stop()` exigido es comprobable específicamente en P3/P2.

## 5. Dos controles y la decisión que habilitan

| Control | Valor / visualización | Decisión y efecto |
|---|---|---|
| **F1: Estado de solicitud (P1)** | Pendiente, En espera de documento, Resuelta hoy | Adrián selecciona qué tipo de tarea atiende; la tabla se filtra y se ve el conteo activo |
| **F2: Nivel de riesgo por PD (P1)** | Alto, Medio, Bajo (selección múltiple) | Adrián prioriza los casos por nivel de riesgo; se actualizan tabla y conteo |
| C2 adicional (P3) | Corte de PD propuesto por gerencia | Mariana evalúa aprobación que se sacrifica y riesgo que se reduce al mover corte |

Evidencia: `src/config.py` (filtro con persona y decisión), `src/ui.py` (`corte_activo` imprime filtro + n/total y permite restablecer), `vistas/p1_bandeja.py` y `vistas/p3_cartera.py`.

## 6. Matriz de acceso por rol, mecanismo y limitación

| Rol | Acceso permitido | Acceso restringido |
|---|---|---|
| **Adrián / Sofía, analistas** | P1 y P2, únicamente sus propias solicitudes; pueden registrar decisiones | No consultan cartera P3, monitor P4 ni DEFAULT de su solicitud |
| **Mariana, gerencia** | P3, agregados de segmentos con n suficiente | No recibe una fila de préstamo ni P2 |
| **Luis, operación** | P4, métricas y folios enmascarados | No recibe P1 ni la ficha nominal P2 |
| **Sin rol** | Solicitud de acceso | No ve información de créditos |

P5, P6 y P7 tienen alcance definido para cada rol. El servidor comprueba `puede_ver` y `exigir_acceso`; las funciones de entrega filtran además columnas/datos. Evidencia: `src/auth.py`, `src/seguridad.py`, `tests/test_seguridad.py`.

**Limitación obligatoria:** en modo demostración los perfiles se seleccionan sin verificación de identidad: **no es autenticación real**. `src/auth.py` admite configuración con OIDC y asignación de roles fuera del repositorio, pero no se presenta el modo demo como protección suficiente de datos sensibles. El enlace de Streamlit Cloud es público. No se publican secretos ni datos personales reales.

## Estado de los ocho criterios de la rúbrica

| Criterio | Evaluación documental |
|---|---|
| Pregunta por gráfica | Documentado según código de `main` |
| Contraste AA y CI que bloquea | **PENDIENTE: no existe verificación de contraste en workflow** |
| Jerarquía ligada a investigación 1 | Parcial: jerarquía respaldada por código y observaciones; fuente exacta de investigación 1 ausente |
| Paleta sin depender solo del color | Evidencia de semáforos con texto e íconos; no equivale a auditoría de daltonismo global |
| Nada seleccionado y `st.stop()` | Evidenciado en P3/P2; P1 tiene estado vacío |
| Dos controles + decisión + corte visible | F1 y F2 en P1 documentados |
| Acceso por rol + limitación | Matriz y pruebas presentes; autenticación de demo no verifica identidad |
| `prompts/B3.md` e investigación 3 | `prompts/B3.md` y `investigacion/visual-jerarquia.md`, con límites históricos explicitados |

**La entrega 3 no se declara 100 % aprobada sin evidencia de CI WCAG y la fuente original de investigación 1.** Esta es una comprobación fiel sin modificar un dashboard que ya fue presentado.
