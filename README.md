https://autocreditadvisor-2-f2ww6wn7nnrysa43edznfp.streamlit.app/

# AutoCredit Advisor · Equipo 3 · Entregables 1–3

**App de la presentación:** `app_v3.py` de la rama `v3-integracion-xgboost-12v`, con XGBoost de 12 variables, TRAIN/TEST y perfiles de Adrián, Sofía, Mariana y Soporte. **Verifica en Streamlit Cloud que el despliegue apunte a esa rama y archivo**; el repositorio conserva `app.py` de una versión previa.

| Entrega | Evidencia de este repositorio |
|---|---|
| **B1 · Plan / Design** | [Contrato del prompt](contrato-prompt.md), [registro B1](prompts/B1.md), [observaciones del profesor](docs/entregable-1.md) |
| **B2 · Build / Test** | [Contrato de datos](contrato-datos.md), [investigación de Anthropic](investigacion/claude.md), [registro B2](prompts/B2.md), [pruebas y evidencia](docs/entregable-2.md) |
| **B3 · Accesibilidad y roles** | [Ficha con seis secciones](docs/entregable-3.md), [investigación 1](investigacion/1-user-persona.md), [investigación 3](investigacion/B3.md), [registro B3](prompts/B3.md) |

**Automatización B3/B4:** `python scripts/check_contrast_b3.py` (contraste original), `python -m scripts.check_cvd_b3` (simulación de protanopía/deuteranopía, 18 pares) y `python -m pytest -q`. Ver [workflow V3](.github/workflows/check_dashboard.yml), [ficha B3](docs/entregable-3.md), [investigación de accesibilidad](investigacion/B3.md) y [auditoría de Entrega 4](docs/entregable-4.md). **Tema claro y modo daltónico** se activan explícitamente desde el acceso y la barra lateral; las decisiones, modelos, datos y umbrales originales no se modificaron.

**Última retroalimentación de gerencia del curso:** se priorizan **tres indicadores de riesgo crediticio y uno de productividad**, en el mismo orden y con la misma fórmula para Adrián, Sofía y Mariana. El primer KPI mide **atención prioritaria de riesgo alto (casos de alto riesgo atendidos / todas las solicitudes atendidas del mes)** y tiene meta porcentual editable por Mariana (60% inicial); no mide incumplimientos ni fuerza rechazos. El KPI de productividad muestra **atendidas vs meta mensual gerencial** (50 casos iniciales por analista) sin usar solicitudes asignadas como denominador. Las cuatro pantallas comparten cálculo y metas. [Consultar metodología, integración entre pantallas y pruebas](docs/kpis-riesgo-integracion.md). El selector de **Decisión rápida** recibe únicamente un contorno verde neón con el color actual, sin modificar su función.

**Seguridad:** acceso por perfiles **de demostración**, no autenticación institucional; la URL pública y el conjunto sintético no deben usarse para evaluar solicitantes reales.


## Cómo ejecutar exactamente la V3

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
streamlit run app_v3.py
```

El código usa los archivos `data/Base_SAS_Equipo3_TRAIN_12V.csv` y `data/Base_SAS_Equipo3_TEST_12V.csv`; entrena XGBoost y Logit con TRAIN, utiliza los cortes calibrados en validación y evalúa TEST. La demo no realiza decisiones reales de crédito.

### Quién ve qué (versión implementada)

| Perfil | Vistas permitidas | Decisión / función |
|---|---|---|
| **Adrián A-017** | Bandeja, Ficha, Mis indicadores, Mensajes | Sus solicitudes, decisiones y motivos |
| **Sofía A-022** | Bandeja, Ficha, Mis indicadores, Mensajes | Sus solicitudes, decisiones y motivos |
| **Mariana, gerencia** | Métricas del área, Analistas y KPI, Mensajes, Auditoría de accesos | Metas, política y revisión |
| **Especialista de Soporte** | Centro de soporte, Validación del modelo, Mensajes | Incidencias y evaluación técnica |

**Integridad de la demo:** se filtran préstamos por `ANALISTA_ID`; una excepción a la recomendación necesita motivo y notificación; la bitácora usa SQLite temporal. El usuario puede seleccionar perfiles de prueba sin autenticar una identidad, por lo que es un prototipo académico.

### Verificación

- `python scripts/check_contrast_b3.py` calcula y comprueba razones de contraste de los tokens de texto y series de las gráficas de V3.
- `python -m pytest -q` valida reglas de negocio, aislamiento de casos, KPI, preguntas de gráficas, estados y filtros.
- [Workflow V3 y resultado de CI](.github/workflows/check_dashboard.yml) (el estado de cada corrida se consulta en [Actions](https://github.com/a01664722-ai/autocredit_advisor-2/actions)).

La paleta operativa oscura original se conserva. Se añadió **paleta inclusiva opcional** con etiquetas, símbolos y patrones, y estilos específicos de tema claro. La simulación y las comprobaciones estáticas no sustituyen pruebas visuales en navegador. **Falta recibir la referencia exacta de la investigación 1 del curso** (distinta del PDF del user persona) para cerrar ese criterio documental sin inventar fuentes.
