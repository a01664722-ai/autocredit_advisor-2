https://autocreditadvisor-2-f2ww6wn7nnrysa43edznfp.streamlit.app/

# AutoCredit Advisor · Equipo 3 · Entregables 1–3

**App de la presentación:** `app_v3.py` de la rama `v3-integracion-xgboost-12v`, con XGBoost de 12 variables, TRAIN/TEST y perfiles de Adrián, Sofía, Mariana y Soporte. **Verifica en Streamlit Cloud que el despliegue apunte a esa rama y archivo**; el repositorio conserva `app.py` de una versión previa.

| Entrega | Evidencia de este repositorio |
|---|---|
| **B1 · Plan / Design** | [Contrato del prompt](contrato-prompt.md), [registro B1](prompts/B1.md), [observaciones del profesor](docs/entregable-1.md) |
| **B2 · Build / Test** | [Contrato de datos](contrato-datos.md), [investigación de Anthropic](investigacion/claude.md), [registro B2](prompts/B2.md), [pruebas y evidencia](docs/entregable-2.md) |
| **B3 · Accesibilidad y roles** | [Ficha con seis secciones](docs/entregable-3.md), [investigación 1](investigacion/1-user-persona.md), [investigación 3](investigacion/B3.md), [registro B3](prompts/B3.md) |

**Automatización de B3:** `python scripts/check_contrast_b3.py` (contrastes de paleta V3) y `python -m pytest -q` (pruebas). Se ejecutan en [GitHub Actions](.github/workflows/check_dashboard.yml). Los colores, umbrales, modelos, datos y decisiones permanecen sin cambios.

**Última retroalimentación de gerencia del curso:** se priorizan **tres indicadores de riesgo crediticio y uno de productividad**, en el mismo orden y con la misma fórmula para Adrián, Sofía y Mariana. El primer KPI expresa el **porcentaje de casos con sugerencia de rechazo que tienen DEFAULT = 1 en TEST**, calculado de forma retrospectiva entre las decisiones del mes: no implica incumplimiento posterior al rechazo. El KPI de productividad muestra **atendidas del mes / asignadas TEST** y conserva la meta editable de Mariana. [Consultar metodología, integración entre pantallas y pruebas](docs/kpis-riesgo-integracion.md). El selector de **Decisión rápida** recibe únicamente un contorno verde neón con el color actual, sin modificar su función.

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

Los valores de color existentes se mantuvieron; el ajuste del menú de decisión rápida reutiliza la paleta. La auditoría CSS de la versión oscura es una prueba automática acotada y no equivale a certificación universal de todos los modos de navegador.
