"""Resultados documentados en el memorial de Entrega 4 (SAS Viya).

Importante: son métricas del experimento SAS de la entrega, NO de las
predicciones actualmente generadas en P1/P2 por el modelo logístico de demo.
El PDF mezcla 11/12 predictores; volver a validar con LOAN_AMOUNT antes de
afirmar que el artefacto del campeón incluye esa variable.
"""
NOMBRE = "Incremento de gradiente (SAS)"
METRICA = "KS de validación"
KS = 0.4215
COMPARACION_KS = {
    "Incremento de gradiente": 0.4215,
    "Regresión logística": 0.3876,
    "Red neuronal": 0.3767,
    "Árbol de decisión": 0.3012,
    "Bosque aleatorio": 0.2488,
}
IMPORTANTES = [
    "REVOLVING_UTILIZATION",
    "DEBT_TO_INCOME",
    "SAVINGS_BALANCE",
    "FINANCIAL_LITERACY_SCORE",
    "MISSED_PAYMENTS_12M",
]
AVISO = (
    "El campeón validado en SAS no es todavía el motor de scoring de esta aplicación: "
    "las fichas y la bandeja usan regresión logística demostrativa. "
    "El informe SAS no acredita que la versión evaluada contenga LOAN_AMOUNT; "
    "las métricas deberán recalcularse después de incorporar esa variable al modelo."
)
