# Investigación · El ciclo de desarrollo con un asistente

**Proyecto:** AutoCredit Advisor (tablero de riesgo crediticio en Streamlit)
**Curso revisado:** Anthropic, *The AI-native SDLC playbook*, Claude Academy. Lecciones leídas: Introducción; Test (*Give Claude a feedback loop* y *Continuous evals in CI*); Build (*The CLAUDE.md*); y, como apoyo, Deploy (*Hooks as approval gates*).
**Etapa de esta semana:** Build y Test (entregable 2).

---

## Resumen

### 1. ¿En qué etapas del ciclo ya usamos el asistente y en cuáles no?

Revisamos uno por uno los prompts de la conversación con la que construimos el tablero, del 2 al 11 de noviembre. Este es el registro:

| Fecha | Prompt (resumido) | Etapa |
|---|---|---|
| 2 nov | «Ayúdame a construir un dashboard en Streamlit, estructurado en Visual Code… incluye estas mejoras» (con el CSV, el PDF del prototipo y la retroalimentación de los bloques A–F) | Build |
| 3 nov | «¿Me recomiendas generar un link público o qué debería hacer?» · «Los pasos para subirlo a GitHub, que sea seguro» · «No veo el botón Share» · «¿El tablero se puede ver desde el compartido?» | Deploy |
| 9 nov | Cinco grupos de recomendaciones: notación, layout, semáforo, lógica de negocio y cartera | Design + Build |
| 11 nov | «Actúa como responsable de calidad (QA)…»: inventario, pruebas del dato, revisión de flujos y pipeline | Test |

No encontramos en estos prompts evidencia clara de uso del asistente en **Plan** ni en **Maintain**. En **Deploy** sí se pidió orientación para publicar, pero eso no demuestra que existieran controles automáticos de revisión.

### 2. ¿Qué práctica concreta del curso podemos adoptar esta semana?

La lección *Give Claude a feedback loop* propone siete pasos. Tres se pueden adoptar esta semana sin infraestructura nueva:

1. **Una sola orden de verificación que falle si algo está mal.** Ya la tenemos: `pytest`, que sale con código distinto de cero cuando una prueba falla. Falta usarla siempre.
2. **Documentar esa orden en `CLAUDE.md` y hacerla parte de «terminado».** El archivo reúne los comandos, el resultado esperado y la regla de verificarlos antes de dar por concluida una tarea.
3. **Corregir errores con la prueba primero.** Cuando aparezca un error, primero se escribe una prueba que lo reproduce y falla. Esa prueba se guarda, y después se le pide al asistente que la haga pasar sin editarla.

La pregunta de la semana era cómo separar las reglas que no pueden depender de que el asistente haga caso de las que sí, porque tienen excepciones. El curso da el criterio en la lección de Test: **las garantías van en controles deterministas (hooks o CI); la guía sobre cómo trabajar va en instrucciones (`CLAUDE.md`)**. Aplicado a nuestro proyecto:

- **No pueden depender del asistente.** No tienen excepciones y su falla expone datos o da una cifra falsa:
  - Un analista nunca recibe incumplimiento (DEFAULT) ni casos de otro ANALISTA_ID.
  - La gerente nunca recibe un crédito individual.
  - Ninguna tasa se muestra con n menor de 30.
  - Todo filtro tiene persona y decisión.
  - FINANCIAL_LITERACY_SCORE no entra al modelo.
  - El AUC no baja de 0.75.
  - `secrets.toml` y la bitácora `.db` no se suben.

  Varias cuentan con pruebas; las nuevas verificaciones de tipos y del CSV deben añadirse al pipeline.
- **Pueden depender del asistente.** Tienen excepciones o requieren criterio:
  - Minúsculas salvo en nombres de columna.
  - Color siempre con ícono y texto.
  - No usar doble eje Y.
  - Qué dimensión mostrar primero.

  Una prueba no sabe juzgar si una cifra es «propia» o si un título es legible. Estas van en `CLAUDE.md` y se revisan en el *pull request*.

### 3. ¿Qué esperábamos encontrar en el curso y no estaba?

- **Un criterio explícito para decidir qué regla va en un control y cuál en una instrucción.** La lección de `CLAUDE.md` nunca dice que sus instrucciones son orientativas y que el asistente puede ignorarlas. La de hooks dice que los hooks son controles obligatorios, pero no las contrasta con las instrucciones ni habla de excepciones. El único lugar donde aparece la división es una tabla en la lección de *feedback loop*. La pregunta de esta semana («¿la regla tiene excepciones?») tuvimos que construirla nosotros.
- **Pruebas sobre datos, no solo sobre código.** El curso prueba el código y la configuración del agente (los *evals* corren cuando cambian `CLAUDE.md` o los *skills*). No habla de validar que el dato es correcto: esquema de la base, fuga de la variable objetivo, tamaño mínimo de muestra o *drift*. En un tablero de riesgo, el error más caro es una cifra equivocada que se ve bien, y eso no aparece.
- **Una versión para equipos pequeños.** Las prácticas suponen infraestructura de empresa: *managed settings* que el ingeniero no puede apagar, exportación a OpenTelemetry y presupuesto de API para correr *evals* en CI. Esperábamos una versión mínima para un repositorio de un equipo de estudiantes. La más cercana es la nuestra: `pytest` en GitHub Actions como verificación obligatoria.
- **Cómo probar legibilidad y accesibilidad de una interfaz.** Para UI, el curso solo propone comparar una captura contra un *mock*. No dice cómo verificar que un semáforo no depende solo del color o que un número lleva su rótulo de origen, que es lo que más nos evaluaron.

---

## Tres cambios propuestos

| # | Qué cambiamos | Dónde | Por qué ahí |
|---|---|---|---|
| 1 | La suite `pytest` y el validador del CSV corren en cada *push* o *pull request*; un resultado incorrecto deja el check en rojo. Para bloquear la fusión a `main` se requiere configurar ese check como obligatorio. | **Dentro del pipeline:** GitHub Actions (`.github/workflows/pruebas.yml`) + regla de protección de `main` que exige ese check. | Las reglas sin excepción (acceso por rol, n ≥ 30, filtros amarrados, AUC ≥ 0.75) no pueden depender de que alguien se acuerde de correr las pruebas, y un despliegue no debería aceptar un dato que rompe el contrato. |
| 2 | Escribimos qué órdenes existen, las convenciones con excepción (`*`/`**`, minúsculas, ícono + texto) y dos reglas de trabajo: «corre `pytest` y pega la salida antes de decir terminado» y «un error se corrige con la prueba primero, sin editar la prueba». | **Fuera del pipeline:** `CLAUDE.md` en la raíz del repositorio, de menos de una página. | Son reglas que requieren criterio o tienen excepciones; el asistente las lee al iniciar cada sesión y una prueba automática no las podría juzgar. |
| 3 | Proponemos evitar el *push* directo a `main`: cada cambio pasaría por una rama, un *pull request* y una lista de revisión (origen, legibilidad, captura). | **Fuera del pipeline:** revisión humana en GitHub, con `.github/pull_request_template.md`. | Ahí el revisor ve el resultado del check del cambio 1 y se concentra en lo que ninguna prueba mide: si la pantalla se entiende y si sirve a la decisión de su persona. |


---

## Fuentes

- [Introduction · The AI-native SDLC playbook](https://academy.claude.com/courses/ai-native-sdlc-playbook/introduction)
- [Give Claude a feedback loop](https://academy.claude.com/courses/ai-native-sdlc-playbook/give-claude-a-feedback-loop)
- [Continuous evals in CI](https://academy.claude.com/courses/ai-native-sdlc-playbook/continuous-evals-in-ci)
- [The CLAUDE.md](https://academy.claude.com/courses/ai-native-sdlc-playbook/claude-md)
- [Hooks as approval gates](https://academy.claude.com/courses/ai-native-sdlc-playbook/hooks-as-approval-gates)

**Evidencia de prompts:** `prompts/B2.md`. Las reglas automáticas están en `scripts/verificar_contrato.py`, `tests/` y `.github/workflows/pruebas.yml`.
