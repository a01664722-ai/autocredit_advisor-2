# Instrucciones de trabajo · AutoCredit Advisor

## Qué es este proyecto

Tablero de riesgo de crédito en Streamlit. La base que utiliza es `data/Base_SAS_Equipo3.csv` (12 columnas). Se muestra información distinta según rol: analistas, gerencia y soporte/operación.

## Reglas del proyecto

- Mantener la misma navegación, el diseño y los colores de las pantallas. Los cambios de interfaz deben responder a una decisión del usuario.
- Usar la base `data/Base_SAS_Equipo3.csv` como fuente de los datos reales. Cualquier campo creado para la demostración lleva el rótulo SIMULADO.
- No subir secretos, bitácoras personales, credenciales ni información de sesiones.
- Distinguir siempre datos reales, datos calculados y datos simulados. No presentar simulaciones como resultados observados.
- Respetar los controles de acceso por rol y por `ANALISTA_ID`. No mostrar `DEFAULT` individual a analistas ni créditos individuales a gerencia.
- Mantener la regla de mínimo 30 registros antes de mostrar tasas por segmento.
- Cualquier cambio visual futuro requiere revisión humana; no basta con que pasen las pruebas.

## Comandos de verificación

1. Instalar dependencias: `pip install -r requirements-dev.txt`.
2. Validar la base: `python -m scripts.verificar_contrato data/Base_SAS_Equipo3.csv`.
   - Salida sana: `OK: ... filas; 12 columnas numéricas verificadas.`
   - Salida incorrecta: `ERROR: FALLO DEL CONTRATO DE DATOS` y código de salida 1.
3. Ejecutar pruebas: `python -m pytest -q`. Todas deben aprobarse.
4. Iniciar localmente: `streamlit run app.py`.

Un cambio no está terminado hasta que se ejecuten las verificaciones y se reporte su resultado real. Si aparece un error, primero escribir una prueba que lo reproduzca; después corregir la causa, sin debilitar la prueba para hacerla pasar.

## Reglas que requieren criterio

Preferir lenguaje sencillo, gráficos con una sola escala y alertas con texto e ícono además del color. Una revisión humana determina si una pantalla es legible y si ayuda a su usuario a decidir; estas decisiones no se sustituyen por un test.

## Ubicación de la entrega

- `investigacion/claude.md`: resumen del curso y tres cambios de proceso.
- `contrato-datos.md`: tipos, unidades, origen y tratamiento de huecos.
- `scripts/verificar_contrato.py`, `tests/test_contrato_datos.py` y `.github/workflows/pruebas.yml`: controles automáticos.
- `prompts/B2.md`: prompts usados.
- `ideas/A01664722.md`: propuesta individual.
