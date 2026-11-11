import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from src import store
from src.engine import bases, entrenar, sugerencia, COLS

@pytest.fixture(scope='module')
def context():
    a,b=bases()
    return a,b,entrenar(a,b)

def test_data_integrity(context):
    a,b,m=context
    assert len(a)==80000 and len(b)==20000
    assert len(COLS)==12
    assert set(a.LOAN_ID).isdisjoint(b.LOAN_ID)
    assert m.scores.LOAN_ID.nunique()==20000
    assert m.scores.PD_XGB.between(0,1).all()
    assert m.scores.PD_LOGIT.between(0,1).all()
    assert m.scores.PRED_XGB.equals((m.scores.PD_XGB>=m.corte_base).astype(int))

def test_model_measured_only_on_test(context):
    a,b,m=context
    assert len(m.metricas)==2 and set(m.metricas.Modelo)=={'XGBoost','Logit'}
    assert (m.metricas['ROC-AUC']>.7).all()
    assert m.metricas.iloc[0]['TN'] + m.metricas.iloc[0]['FP'] + m.metricas.iloc[0]['FN'] + m.metricas.iloc[0]['TP']==len(b)

def test_positive_label_is_reject():
    assert sugerencia(.8,.5)=='Rechazar'
    assert sugerencia(.1,.5)=='Aprobar'
    assert sugerencia(.1,.5,False)=='Revisar'

def test_policy_and_override(tmp_path,monkeypatch):
    monkeypatch.setattr(store,'DB',tmp_path/'test.sqlite3')
    store.initialize(.15)
    assert store.policy('General')['threshold']==.15
    assert store.update_policy('General',.17,'Mariana',{'A-017':3,'A-022':5})
    assert store.policy('General')['threshold']==.17
    assert store.unread('analista','A-017')==1
    assert store.unread('analista','A-022')==1
    with pytest.raises(ValueError):
        store.save_decision('7654','A-017','Aprobar','Rechazar',.9,.8,.17)
    is_override=store.save_decision('7654','A-017','Aprobar','Rechazar',.9,.8,.17,'Otro','Un documento fue corregido')
    assert is_override
    assert store.unread('gerente')==1
    assert len(store.decisions_map('A-017'))==1
    with pytest.raises(PermissionError):
        store.save_decision('7654','A-022','Aprobar','Aprobar',.1,.1,.17)
    msg=store.messages('gerente')[0]
    store.mark_read(msg['id'],'gerente')
    assert store.unread('gerente')==0
