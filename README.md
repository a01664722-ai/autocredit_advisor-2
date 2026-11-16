# AutoCredit Advisor · Build y Test

Dashboard de riesgo de crédito en Streamlit. La base `data/Base_SAS_Equipo3.csv` contiene 80,000 registros y 12 columnas. La información se organiza por perfil: analistas, gerencia y soporte.

## Archivos de la entrega

| Criterio | Evidencia |
|---|---|
| Investigación de Anthropic y tres cambios | [investigacion/claude.md](investigacion/claude.md) |
| Instrucciones al asistente | [CLAUDE.md](CLAUDE.md) |
| Contrato por columna, tipos, unidad, origen y ausencias | [contrato-datos.md](contrato-datos.md) |
| Verificación de números y ausencias | [scripts/verificar_contrato.py](scripts/verificar_contrato.py) |
| Pruebas de datos, interfaz y tablas | [tests/test_contrato_datos.py](tests/test_contrato_datos.py) y [tests/test_integracion_contrato.py](tests/test_integracion_contrato.py) |
| Pipeline | [.github/workflows/pruebas.yml](.github/workflows/pruebas.yml) |
| Prompts de la semana | [prompts/B2.md](prompts/B2.md) |
| Idea y evidencia individual | [ideas/A01664722.md](ideas/A01664722.md) y [avance/A01664722.md](avance/A01664722.md) |

## Cómo ejecutar y verificar

Requiere Python 3.11 y las dependencias indicadas:

```bash
python -m pip install -r requirements-dev.txt
python -m scripts.verificar_contrato data/Base_SAS_Equipo3.csv
python -m pytest -q
streamlit run app.py
```

La lectura de datos revisa las 12 columnas, sus tipos numéricos, las banderas 0/1, los valores ausentes y el tamaño mínimo. Si hay un error, la aplicación lo muestra antes de cargar información financiera. Cuando todo está correcto, la barra lateral indica **12/12 columnas verificadas**.

Las tablas tienen orden de columnas definido, no muestran el índice y conservan numéricos los importes, los porcentajes y la PD. El ahorro en la bandeja se puede ordenar haciendo clic en su encabezado.

GitHub Actions repite la validación del CSV y las pruebas en cada cambio a `main` o en un pull request hacia esa rama.

- [Corrida exitosa en `main`](https://github.com/a01664722-ai/autocredit_advisor-2/actions/runs/43777067259): **80,000 filas y 12 columnas numéricas validadas**, sin marcadores de ausencia; la suite de pruebas terminó correctamente.
- [Corrida de control con dato incorrecto](https://github.com/a01664722-ai/autocredit_advisor-2/actions/runs/43777208621): GitHub Actions detectó `NO_ES_UN_NUMERO` en `SAVINGS_BALANCE` y detuvo el proceso con código 1.
- [Todas las ejecuciones del workflow](https://github.com/a01664722-ai/autocredit_advisor-2/actions/workflows/pruebas.yml).
- **Protección de `main`:** para bloquear también una fusión, el administrador debe configurar el check como obligatorio en las reglas de protección de la rama.

## Acceso y origen de cifras

Repositorio: https://github.com/a01664722-ai/autocredit_advisor-2

**URL pública de Streamlit:** el enlace del despliegue no está registrado. Para comprobar el acceso se requiere abrirlo en una ventana privada; `localhost` solo sirve para ejecución local.

La app ofrece cuentas de demostración para analistas (Adrián y Sofía), gerencia (Mariana) y soporte/operación (Luis), con permisos según el rol.

- **REAL:** dato del CSV o decisión registrada realmente en bitácora.
- **CALCULADO:** resultado derivado de esos datos o del modelo.
- **SIMULADO:** folios, asignaciones, fechas y escenarios creados para demostrar la pantalla.
- **POLÍTICA:** umbrales definidos por el equipo.

La base no incluye un identificador de crédito ni fechas de solicitudes. Esos campos se señalan como simulados. La tasa de incumplimiento y el DTI promedio se calculan a partir de la fuente real.
