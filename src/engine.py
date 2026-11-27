"""Motor reproducible: 12 predictores, TRAIN 80k / TEST 20k sin fuga.
Los datos son sintéticos de crédito, no decisiones financieras reales.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import (roc_auc_score, average_precision_score, accuracy_score,
    precision_score, recall_score, f1_score, confusion_matrix, roc_curve, brier_score_loss, fbeta_score)

ROOT = Path(__file__).resolve().parents[1]
COLS = ["REVOLVING_UTILIZATION", "DEBT_TO_INCOME", "MISSED_PAYMENTS_12M", "SAVINGS_BALANCE",
        "DOWN_PAYMENT_PCT", "FINANCIAL_LITERACY_SCORE", "LOAN_TO_VALUE", "DELINQ_90",
        "YEARS_CREDIT_HISTORY", "PAYMENT_TO_INCOME", "BANKRUPTCY_FLAG", "LOAN_AMOUNT"]
LABELS = {"REVOLVING_UTILIZATION":"Uso revolvente", "DEBT_TO_INCOME":"Deuda/ingreso",
          "MISSED_PAYMENTS_12M":"Pagos omitidos (12 m)", "SAVINGS_BALANCE":"Ahorro (MXN*)",
          "DOWN_PAYMENT_PCT":"Enganche", "FINANCIAL_LITERACY_SCORE":"Educación financiera",
          "LOAN_TO_VALUE":"Préstamo/valor", "DELINQ_90":"Atrasos 90+ días",
          "YEARS_CREDIT_HISTORY":"Historial (años)", "PAYMENT_TO_INCOME":"Pago/ingreso",
          "BANKRUPTCY_FLAG":"Bancarrota", "LOAN_AMOUNT":"Préstamo (MXN*)"}
# * Unidad monetaria debe verificarse en diccionario de datos de origen; no afirmar MXN.
LABELS["SAVINGS_BALANCE"] = "Saldo de ahorro (u.m.)"
LABELS["LOAN_AMOUNT"] = "Monto del crédito (u.m.)"
PERCENT = {"REVOLVING_UTILIZATION","DEBT_TO_INCOME","DOWN_PAYMENT_PCT","LOAN_TO_VALUE","PAYMENT_TO_INCOME"}


def bases(path=ROOT / "data"):
    train = pd.read_csv(Path(path)/"Base_SAS_Equipo3_TRAIN_12V.csv", dtype={"LOAN_ID":str})
    test = pd.read_csv(Path(path)/"Base_SAS_Equipo3_TEST_12V.csv", dtype={"LOAN_ID":str})
    expected = set(COLS + ["DEFAULT","LOAN_ID"])
    for name,df in (("TRAIN",train),("TEST",test)):
        if not expected.issubset(df.columns): raise ValueError(f"{name}: faltan {sorted(expected-set(df.columns))}")
        df["LOAN_ID"] = df["LOAN_ID"].astype("string").str.strip()
        if df["LOAN_ID"].isna().any() or df["LOAN_ID"].eq("").any() or not df["LOAN_ID"].is_unique:
            raise ValueError(f"LOAN_ID vacío o duplicado en {name}")
        if not df["DEFAULT"].isin([0,1]).all(): raise ValueError(f"DEFAULT distinto de 0/1 en {name}")
        if df[COLS].isna().any().any(): raise ValueError(f"Predictores faltantes en {name}; no imputar con información TEST")
        if not all(pd.api.types.is_numeric_dtype(df[c]) for c in COLS): raise ValueError("Predictores deben ser numéricos")
    if not set(train.LOAN_ID).isdisjoint(test.LOAN_ID): raise ValueError("Fuga: LOAN_ID compartido TRAIN/TEST")
    if len(train) != 80000 or len(test) != 20000:
        raise ValueError("Particiones inesperadas: se requieren 80,000 TRAIN y 20,000 TEST")
    return train,test


def resumen(y,prob,cut):
    yy = np.asarray(y, dtype=int)
    pr = np.asarray(prob, dtype=float)
    pred = (pr>=cut).astype(int)
    fpr,tpr,_ = roc_curve(yy,pr)
    tn,fp,fn,tp = confusion_matrix(yy,pred,labels=[0,1]).ravel()
    return {"ROC-AUC":float(roc_auc_score(yy,pr)), "PR-AUC":float(average_precision_score(yy,pr)),
            "KS":float(max(tpr-fpr)),"Accuracy":float(accuracy_score(yy,pred)),
            "Precision":float(precision_score(yy,pred,zero_division=0)),
            "Recall":float(recall_score(yy,pred,zero_division=0)),
            "F1":float(f1_score(yy,pred,zero_division=0)),
            "Brier":float(brier_score_loss(yy,pr)),
            "TN":int(tn),"FP":int(fp),"FN":int(fn),"TP":int(tp)}


def umbrales_validacion(y, prob):
    """Reproduce la celda 9 del notebook: máximo F2 y zona con >=95% del F2 máximo.

    Solo utiliza la porción VALIDACIÓN de TRAIN. TEST no interviene para
    seleccionar los umbrales. Los dos cortes sirven para la política de tres vías.
    """
    yy = np.asarray(y, dtype=int)
    pp = np.asarray(prob, dtype=float)
    candidatos = np.linspace(0.05, 0.60, 112)  # sin redondear: idéntico al notebook
    f2 = np.array([fbeta_score(yy, pp >= u, beta=2, zero_division=0) for u in candidatos])
    idx = int(np.argmax(f2))
    fin = idx
    limite = 0.95 * f2[idx]
    for i in range(idx + 1, len(candidatos)):
        if f2[i] < limite:
            break
        fin = i
    if fin == idx:
        raise ValueError("No se encontró segundo umbral F2 (95% del máximo)")
    return float(candidatos[idx]), float(candidatos[fin])


def umbral_validacion(y, prob):
    """Compatibilidad con consumidores anteriores; corte inferior F2."""
    return umbrales_validacion(y, prob)[0]


@dataclass
class Modelos:
    train:pd.DataFrame
    test:pd.DataFrame
    xgb:object
    logit:object
    corte_base:float
    corte_rechazo:float
    scores:pd.DataFrame
    validacion:pd.DataFrame
    metricas:pd.DataFrame
    comparacion:pd.DataFrame
    auc_roc:dict


def entrenar(train:pd.DataFrame,test:pd.DataFrame)->Modelos:
    # Selección del umbral SOLO en TRAIN/validación. TEST no participa.
    a,b=train_test_split(train,test_size=.25,stratify=train.DEFAULT,random_state=42)
    def nuevo_xgb():return XGBClassifier(n_estimators=200,max_depth=4,learning_rate=.05,
        subsample=.8,colsample_bytree=.8,objective='binary:logistic',eval_metric='logloss',
        random_state=42,n_jobs=4,tree_method='hist')
    mval=nuevo_xgb().fit(a[COLS],a.DEFAULT)
    pval=mval.predict_proba(b[COLS])[:,1]
    cut,cut_reject=umbrales_validacion(b.DEFAULT,pval)
    # Reentrenamiento final con todo TRAIN, nunca con TEST.
    xgb=nuevo_xgb().fit(train[COLS],train.DEFAULT)
    logit=Pipeline([('standard',StandardScaler()),('classifier',LogisticRegression(penalty=None,solver='lbfgs',max_iter=2000,random_state=42))]).fit(train[COLS],train.DEFAULT)
    px=xgb.predict_proba(test[COLS])[:,1]
    pl=logit.predict_proba(test[COLS])[:,1]
    scored=test.copy()
    scored['PD_XGB']=px;scored['PD_LOGIT']=pl
    scored['PRED_XGB']=(px>=cut).astype(int)
    scored['SEG_DTI']=segmentar_dti(scored, train['DEBT_TO_INCOME'])
    scored['ANALISTA_ID']=np.where(pd.util.hash_pandas_object(scored['LOAN_ID'], index=False)%2==0,'A-017','A-022')
    rows=[]
    for nombre,p in [('XGBoost',px),('Logit',pl)]:
        rows.append({'Modelo':nombre,'Conjunto':'TEST', 'Umbral':cut, **resumen(test.DEFAULT,p,cut)})
    mt=pd.DataFrame(rows)
    fpr_x,tpr_x,_=roc_curve(test.DEFAULT,px)
    fpr_l,tpr_l,_=roc_curve(test.DEFAULT,pl)
    return Modelos(train,test,xgb,logit,cut,cut_reject,scored,b.assign(PD_VALID=pval).copy(),mt,mt,
        {'XGBoost':(fpr_x,tpr_x),'Logit':(fpr_l,tpr_l)})


def segmentar_dti(df:pd.DataFrame,serie_train:pd.Series):
    q1,q2=np.quantile(serie_train,[1/3,2/3])
    return np.select([df.DEBT_TO_INCOME<=q1,df.DEBT_TO_INCOME<=q2],['DTI bajo','DTI medio'],default='DTI alto')


def sugerencia(pdx, corte, corte_rechazo=None, calidad_ok=True):
    """Política de tres decisiones basada SOLO en PD XGBoost.

    Se conserva la llamada binaria previa para compatibilidad con la V2:
    sugerencia(PD, corte) -> Aprobar/Rechazar. En la V3 deben pasarse ambos
    umbrales: Aceptar, Condicionar o Rechazar.
    """
    if isinstance(corte_rechazo, (bool, np.bool_)):
        calidad_ok, corte_rechazo = bool(corte_rechazo), None
    if not calidad_ok:
        return 'Revisar'
    pd = float(pdx)
    if corte_rechazo is None:
        return 'Rechazar' if pd >= float(corte) else 'Aprobar'
    if not 0 <= float(corte) < float(corte_rechazo) <= 1:
        raise ValueError('Cortes inconsistentes: el rechazo debe superar al de aceptación')
    if pd < float(corte):
        return 'Aceptar'
    if pd < float(corte_rechazo):
        return 'Condicionar'
    return 'Rechazar'


def formato(col,val):
    if pd.isna(val):return '—'
    if col in PERCENT:return f'{float(val):.1%}'
    if col in ('LOAN_AMOUNT','SAVINGS_BALANCE'):return f'{float(val):,.0f} u.m.'
    if col=='BANKRUPTCY_FLAG':return 'Sí' if int(val)==1 else 'No'
    return str(round(float(val),1)) if pd.api.types.is_number(val) else str(val)
