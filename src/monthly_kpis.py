"""Indicadores operativos mensuales de la demo; nunca usan DEFAULT real ni TEST para puntuar analistas.

Solo cuentan préstamos distintos cuya última decisión está fechada en el mes actual.
SQLite guarda el estado más reciente, NO un log histórico de múltiples acciones.
"""
from __future__ import annotations
from calendar import monthrange
from datetime import datetime, timezone
from math import isfinite
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("America/Mexico_City")

KPI_SPECS = (
    ("Decisiones mensuales", "Decisiones del mes", "count", 50, "Solicitudes con decisión registrada"),
    ("Riesgo alto atendido", "Riesgo alto atendido", "count", 15, "Casos con sugerencia Rechazar revisados"),
    ("Riesgo medio atendido", "Riesgo medio atendido", "count", 10, "Casos con sugerencia Condicionar revisados"),
    ("Riesgo bajo atendido", "Riesgo bajo atendido", "count", 15, "Casos con sugerencia Aceptar revisados"),
    ("Coincidencia con sugerencia", "Coincidencia con XGBoost", "rate", 0.80, "Proporción de decisiones que coinciden"),
    ("Con justificación", "Excepciones justificadas", "rate", 1.00, "Excepciones con motivo y detalle válido"),
)
# Los cuatro indicadores que abren P1, Mis indicadores y la supervisión de gerencia.
# Exposición y PD son señales informativas de riesgo, no cuotas de rendimiento:
# NO se incentiva elevar la PD ni el importe de créditos peligrosos.
RISK_HEADLINES = (
    ("Exposición alto riesgo evaluada", "Exposición de alto riesgo", "risk_amount",
     "Importe de préstamos con recomendación Rechazar que tuvieron decisión este mes; en u.m., NO pérdida evitada"),
    ("Riesgo alto atendido", "Casos de alto riesgo", "risk_count",
     "Solicitudes evaluadas cuyo XGBoost recomendó Rechazar al decidir"),
    ("PD promedio evaluada", "PD promedio evaluada", "risk_pd",
     "Probabilidad de incumplimiento promedio de las solicitudes con decisión este mes; NO tasa de default observada"),
    ("Decisiones mensuales", "Decisiones del mes", "productivity",
     "Número de solicitudes con decisión registrada este mes"),
)
RISK_MAP = {spec[0]: spec for spec in RISK_HEADLINES}
KPI_MAP = {spec[0]: spec for spec in KPI_SPECS}
MONTHS_ES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
             "agosto", "septiembre", "octubre", "noviembre", "diciembre")
IDS = tuple(spec[0] for spec in KPI_SPECS)


def local_now():
    return datetime.now(LOCAL_TZ)


def as_local(value):
    """Timestamps persistidos en UTC; un timestamp antiguo sin zona se interpreta UTC."""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(LOCAL_TZ)
    except (TypeError, ValueError, OverflowError):
        return None


def monthly_summary(records, analyst_id=None, reference=None, scored=None):
    """Resumen del mes por analista; exposición solo desde LOAN_ID en TEST.

    scored es la tabla de TEST ya puntuada que recibe la pantalla, no DEFAULT
    ni una predicción reentrenada. La sugerencia y PD se leen de la decisión
    guardada: se respeta la política que estaba activa al decidir. Para una
    exposición sin Loan ID verificable devuelve None, nunca un cero inventado.
    """
    reference = (reference or local_now()).astimezone(LOCAL_TZ)
    candidates = list(records.values()) if isinstance(records, dict) else list(records)
    current = []
    for row in candidates:
        if analyst_id is not None and row.get("analyst_id") != analyst_id:
            continue
        t = as_local(row.get("updated_at"))
        if t is not None and (t.year, t.month) == (reference.year, reference.month):
            current.append({**row, "_local_dt": t})

    n = len(current)
    high_rows = [r for r in current if r.get("suggested") == "Rechazar"]
    amounts = None
    if scored is not None:
        # Coincidir por identidad del préstamo y por el analista, no por
        # posición ni por la sugerencia vigente, que puede cambiar con política.
        amounts = {
            str(loan): (str(aid), float(amount))
            for loan, aid, amount in scored[["LOAN_ID", "ANALISTA_ID", "LOAN_AMOUNT"]]
                .itertuples(index=False, name=None)
        }
    if not high_rows:
        risk_amount = 0.0
    elif amounts is None:
        risk_amount = None
    else:
        matched = [
            amounts.get(str(row.get("loan_id"))) for row in high_rows
        ]
        valid = all(
            item is not None
            and isfinite(item[1]) and item[1] >= 0
            and item[0] == str(row.get("analyst_id"))
            for row, item in zip(high_rows, matched)
        )
        risk_amount = sum(item[1] for item in matched) if valid else None

    pd_values = []
    for row in current:
        try:
            v = float(row.get("pd_xgb"))
            if not isfinite(v) or not 0 <= v <= 1:
                break
            pd_values.append(v)
        except (TypeError, ValueError, OverflowError):
            break
    avg_pd = (sum(pd_values) / n) if n and len(pd_values) == n else None
    overrides = [x for x in current if bool(x.get("override"))]
    n_justified = sum(bool(str(x.get("motivo") or "").strip()) and
                      len(str(x.get("text_detail") or "").strip()) >= 8 for x in overrides)
    n_match = n - len(overrides)
    counts = {
        "Aceptar": sum(x.get("decision") in ("Aceptar", "Aprobar") for x in current),
        "Condicionar": sum(x.get("decision") == "Condicionar" for x in current),
        "Rechazar": sum(x.get("decision") == "Rechazar" for x in current),
    }
    metrics = {
        "Exposición alto riesgo evaluada": risk_amount,
        "PD promedio evaluada": avg_pd,
        "Decisiones mensuales": n,
        "Riesgo alto atendido": sum(x.get("suggested") == "Rechazar" for x in current),
        "Riesgo medio atendido": sum(x.get("suggested") == "Condicionar" for x in current),
        "Riesgo bajo atendido": sum(x.get("suggested") in ("Aceptar", "Aprobar") for x in current),
        "Coincidencia con sugerencia": n_match / n if n else None,
        "Con justificación": n_justified / len(overrides) if overrides else None,
    }
    days = monthrange(reference.year, reference.month)[1]
    daily = [0] * days
    for row in current:
        daily[row["_local_dt"].day - 1] += 1
    running = []
    total = 0
    for count in daily:
        total += count
        running.append(total)
    return {
        "metrics": metrics,
        "rows": current,
        "count": n,
        "overrides": len(overrides),
        "justified": n_justified,
        "matches": n_match,
        "decisions": counts,
        "daily": daily,
        "cumulative": running,
        "month_days": days,
        "day": reference.day,
        "period": f"{MONTHS_ES[reference.month - 1]} de {reference.year}",
        "month_id": f"{reference.year:04d}-{reference.month:02d}",
        "reference": reference,
    }


def level(value, goal):
    if value is None:
        return "na"
    if goal <= 0:
        return "na"
    ratio = float(value) / float(goal)
    return "met" if ratio >= 1 else "mid" if ratio >= 0.5 else "low"


def fmt(metric, value):
    if value is None:
        return "—"
    return f"{float(value):.1%}" if KPI_MAP[metric][2] == "rate" else f"{int(value):,}"


def fmt_risk(metric, value):
    """Una sola etiqueta y formato de riesgo para P1, analistas y gerencia."""
    if value is None:
        return "—"
    if metric == "Exposición alto riesgo evaluada":
        return f"{float(value):,.0f} u.m."
    if metric == "PD promedio evaluada":
        return f"{float(value):.1%}"
    return fmt(metric, value)


def progress(value, target):
    if value is None or float(target) <= 0:
        return None
    return max(0.0, float(value) / float(target))


def validate_target(metric, value):
    if metric not in KPI_MAP:
        raise ValueError(f"Indicador no autorizado: {metric}")
    v = float(value)
    if not (0 < v < float("inf")):
        raise ValueError("Todas las metas deben ser positivas y finitas")
    if KPI_MAP[metric][2] == "rate":
        if v > 1:
            raise ValueError("La meta porcentual debe estar entre 0 y 100%")
    elif int(v) != v or v > 100000:
        raise ValueError("Las metas de conteo deben ser enteros entre 1 y 100,000")
    return v
