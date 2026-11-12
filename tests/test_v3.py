"""Pruebas de integración del motor académico de 12 variables y la política de tres vías."""
import numpy as np
import pytest

from src.engine import COLS, bases, entrenar, sugerencia, umbrales_validacion
from src import store


@pytest.fixture(scope="module")
def resultado():
    train, test = bases()
    return train, test, entrenar(train, test)


def test_conserva_loan_ids_y_12_variables(resultado):
    train, test, m = resultado
    assert len(COLS) == 12 and "LOAN_AMOUNT" in COLS
    assert "LOAN_ID" not in COLS and "DEFAULT" not in COLS
    assert len(train) == 80000 and len(test) == 20000
    assert len(m.scores) == len(test)
    assert m.scores.LOAN_ID.astype(str).tolist() == test.LOAN_ID.astype(str).tolist()
    assert set(train.LOAN_ID).isdisjoint(test.LOAN_ID)
    assert m.scores.PD_XGB.between(0, 1).all()
    assert m.scores.PD_LOGIT.between(0, 1).all()


def test_umbrales_identicos_a_metodologia_del_notebook(resultado):
    train, test, m = resultado
    assert .05 <= m.corte_base < m.corte_rechazo <= .60
    inferior, superior = umbrales_validacion(m.validacion.DEFAULT, m.validacion.PD_VALID)
    assert m.corte_base == pytest.approx(inferior)
    assert m.corte_rechazo == pytest.approx(superior)
    assert m.corte_base == pytest.approx(.1144, abs=.005)
    assert m.corte_rechazo == pytest.approx(.1590, abs=.01)


def test_recomendaciones_tres_vias(resultado):
    _, _, m = resultado
    a, b = m.corte_base, m.corte_rechazo
    assert sugerencia(a / 2, a, b) == "Aceptar"
    assert sugerencia((a + b) / 2, a, b) == "Condicionar"
    assert sugerencia(b, a, b) == "Rechazar"
    assert sugerencia(b, a, b, False) == "Revisar"
    assert m.scores.PRED_XGB.equals((m.scores.PD_XGB >= a).astype(int))


def test_matriz_test_independiente(resultado):
    _, test, m = resultado
    k = m.metricas.loc[m.metricas.Modelo == "XGBoost"].iloc[0]
    assert sum(int(k[x]) for x in ("TN", "FP", "FN", "TP")) == len(test)
    assert np.isfinite(k["ROC-AUC"])
    assert k["ROC-AUC"] > .7


def test_corte_gerente_y_excepcion_condicionar(tmp_path, monkeypatch, resultado):
    monkeypatch.setattr(store, "DB", tmp_path / "credit.sqlite3")
    _, _, m = resultado
    store.initialize(m.corte_rechazo)
    assert store.policy("General")["threshold"] == pytest.approx(m.corte_rechazo)
    assert store.update_policy("DTI alto", m.corte_rechazo + .02, "Mariana", {"A-017": 2})
    assert store.unread("analista", "A-017") == 1
    with pytest.raises(ValueError):
        store.save_decision("123", "A-017", "Rechazar", "Condicionar", .18, .13, .17)
    assert store.save_decision("123", "A-017", "Rechazar", "Condicionar", .18, .13, .17,
                               "Capacidad de pago", "Verificada en el expediente")
    assert store.unread("gerente") == 1
    with pytest.raises(PermissionError):
        store.save_decision("123", "A-022", "Condicionar", "Condicionar", .18, .13, .17)
