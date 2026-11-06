"""P2 · Ficha de solicitud · Adrián (analista).
Decisión: aprobar, condicionar o rechazar esta solicitud en menos de 5 minutos."""
import math
import time

import pandas as pd
import streamlit as st

from src import almacen, auth, config as C, datos, graficas as G, servicios, ui
from src.modelo import evaluar, pd_con_enganche
from src.seguridad import MATRIZ_DATOS, OCULTO, aplicar_politica_fila
from src.simulacion import texto_hace

usuario = auth.exigir_acceso("P2")
modelo = servicios.modelo()
cola, originales = servicios.cola_analista(usuario)
ui.cabecera("P2", usuario)


def _ir_bandeja():
    st.session_state.pop("folio_actual", None)


# --- Recorrido de error 1: llegar sin solicitud elegida -------------------------
folio = st.session_state.get("folio_actual")
if not folio:
    ui.estado_vacio("Elige una solicitud en tu bandeja",
                    "La ficha muestra una solicitud a la vez. Ábrela desde P1, donde están ordenadas por PD.",
                    key="p2_sin_folio")
    st.page_link("vistas/p1_bandeja.py", label="Ir a la bandeja", icon=":material/inbox:")
    st.stop()

# --- Recorrido de error 2: folio que no es suyo (autorización por ANALISTA_ID) --
if folio not in set(cola["FOLIO"]):
    st.error(f"La solicitud {folio} no está asignada a tu ANALISTA_ID ({usuario.analista_id}). "
             "No se muestra ningún dato.", icon=":material/lock:")
    st.page_link("vistas/p1_bandeja.py", label="Volver a mi bandeja", icon=":material/inbox:")
    st.stop()

registro = cola[cola["FOLIO"] == folio].iloc[0]
fila = aplicar_politica_fila(usuario.rol, registro.to_dict())  # solo columnas permitidas al analista
ev = evaluar(modelo, fila)
estado = registro["ESTADO_SOLICITUD"]
st.session_state.setdefault(f"inicio_{folio}", time.time())

# --- Encabezado de la solicitud --------------------------------------------------
with st.container(horizontal=True, vertical_alignment="center"):
    if st.button("Bandeja", icon=":material/arrow_back:", on_click=_ir_bandeja, type="tertiary"):
        st.switch_page("vistas/p1_bandeja.py")
    st.markdown(f"### Solicitud {folio}")
    st.badge(f"recibida {texto_hace(registro['RECIBIDA_MIN'])} · SIMULADO", color="orange")
    st.badge(estado, color={"Pendiente": "blue", "En espera de documento": "orange"}.get(estado, "green"))

if st.session_state.pop("aviso_regreso", False):
    st.info("Regresaste a la solicitud que tenías abierta cuando expiró la sesión; lo que habías capturado "
            "está abajo.", icon=":material/history:")


def _pedir_documento():
    almacen.poner_estado(folio, usuario.analista_id, "En espera de documento")
    st.toast(f"{folio} pasó a «En espera de documento».", icon=":material/mail:")


def _llego_documento():
    almacen.registrar_documento(folio)
    almacen.poner_estado(folio, usuario.analista_id, "Pendiente")
    st.toast("Llegó el documento: la PD se recalculó con el dato real.", icon=":material/task_alt:")


demo = not auth.modo_oidc()

# --- Estados de excepción dentro del flujo de análisis ---------------------------
if ev.invalidos:
    st.error(f"Dato imposible en {', '.join(C.ETIQUETAS[v] for v in ev.invalidos)}: está fuera de los límites "
             "válidos, así que **no se calcula PD**. Pide el documento o rechaza con motivo.",
             icon=":material/error:")
if ev.imputados:
    with st.container(border=True):
        st.warning(
            f"**Esta solicitud llegó sin {', '.join(C.ETIQUETAS[v] for v in ev.imputados)}.** Se imputó la mediana "
            "de entrenamiento y la PD puede estar sesgada: el valor imputado no es el del cliente. "
            "«Aprobar» y «Condicionar» quedan deshabilitados mientras un dato clave siga imputado.",
            icon=":material/report:")
        with st.container(horizontal=True):
            st.button("Pedir documento (pasa a En espera)", on_click=_pedir_documento, type="primary",
                      disabled=estado == "En espera de documento", icon=":material/mail:")
            if demo:
                st.button("Simular que llegó el documento", on_click=_llego_documento, icon=":material/science:")
if ev.fuera_rango:
    with st.container(border=True):
        rangos = "; ".join(f"{C.ETIQUETAS[v]} = {datos.formatear(v, fila[v])} (entrenado entre "
                           f"{datos.formatear(v, modelo.rango[v][0])} y {datos.formatear(v, modelo.rango[v][1])})"
                           for v in ev.fuera_rango)
        st.warning(f"**Dato fuera del rango con el que se entrenó el modelo:** {rangos}. La PD es una "
                   "extrapolación, por eso el modelo **no emite recomendación**: decide con revisión manual "
                   "y registra el motivo.", icon=":material/warning:")
        with st.container(horizontal=True):
            st.button("Pedir avalúo / documento", on_click=_pedir_documento, type="primary",
                      disabled=estado == "En espera de documento", icon=":material/mail:")
            if demo:
                st.button("Simular documento corregido", on_click=_llego_documento, icon=":material/science:")
if estado == "En espera de documento":
    st.info("Esta solicitud espera un documento. Cuando llegue, la PD se recalcula y se habilita la decisión.",
            icon=":material/hourglass_top:")

if ev.pd is None:
    st.stop()

# --- Resumen y acciones visibles sin desplazamiento ----------------------------
with st.container(border=True):
    st.markdown("**Decisión crediticia · Solicitud en revisión**")
    a, b, c, d = st.columns(4, gap="small")
    a.metric("Riesgo calculado (logit demo)", f"{ev.pd:.1%}", border=False,
             help="PD del modelo logístico de demostración, no del campeón Gradient Boosting SAS.")
    b.metric("Referencia cartera", f"{modelo.tasa_base:.2%}", border=False)
    dti_actual = fila.get("DEBT_TO_INCOME")
    c.metric("Deuda / ingreso", f"{dti_actual:.1%}" if pd.notna(dti_actual) else "Sin dato",
             border=False)
    d.metric("Corte propuesto", f"{C.CORTE_PD:.0%}", border=False)
    dist = (ev.pd - C.CORTE_PD)*100
    st.caption(f"Diferencia frente al corte: {dist:+.1f} puntos porcentuales. "
               "Corte de política del equipo, sujeto a calibración; no es autorización automática.")
    if ev.bloquea_aprobar or estado == "En espera de documento" or ev.fuera_rango:
        st.error("Revisión obligatoria: datos incompletos, inválidos, en espera o fuera de rango. "
                 "No autorizar sin verificar documentación.", icon=":material/warning:")
    st.markdown("**Elegir rápidamente una decisión**")
    st.markdown("""
    <style>
    div.st-key-p2_aprobar button {background:#103d25!important;color:#72f3a8!important;
        border:2px solid #138b4f!important;border-radius:12px!important;font-weight:750!important;}
    div.st-key-p2_condicionar button {background:#42300e!important;color:#ffd77a!important;
        border:2px solid #a8730d!important;border-radius:12px!important;font-weight:750!important;}
    div.st-key-p2_rechazar button {background:#491b24!important;color:#ff9ba7!important;
        border:2px solid #ac3c53!important;border-radius:12px!important;font-weight:750!important;}
    div.st-key-p2_aprobar button:hover {background:#165a36!important;}
    div.st-key-p2_condicionar button:hover {background:#604610!important;}
    div.st-key-p2_rechazar button:hover {background:#682632!important;}
    </style>""",unsafe_allow_html=True)
    ca, cc, cr = st.columns(3, gap="small")
    k_rapida = f"dec_{folio}"
    for col, etiqueta, clave in ((ca, "Aprobar", "p2_aprobar"),
                                (cc, "Condicionar", "p2_condicionar"),
                                (cr, "Rechazar", "p2_rechazar")):
        with col:
            if st.button(etiqueta, key=clave, use_container_width=True,
                         disabled=etiqueta != "Rechazar" and
                                  (ev.bloquea_aprobar or estado == "En espera de documento" or bool(ev.fuera_rango))
                         ):
                st.session_state[k_rapida] = etiqueta
                st.rerun()
    st.caption("Selecciona una acción y confirma en el formulario siguiente: "
               "no se guarda ningún dictamen al pulsar el botón.")

# --- Decisión ------------------------------------------------------------------
clave = f"{folio}"
k_dec, k_eng, k_mot, k_txt = (f"dec_{clave}", f"eng_{clave}", f"mot_{clave}", f"txt_{clave}")

# Restaurar borrador (p. ej., tras una sesión expirada).
if k_dec not in st.session_state:
    borrador = almacen.leer_borrador(usuario.email, folio)
    if borrador:
        for k, v in zip((k_dec, k_eng, k_mot, k_txt), ("decision", "enganche", "motivo", "texto")):
            if borrador.get(v) is not None:
                st.session_state[k] = borrador[v]
        st.toast("Recuperamos lo que habías capturado en esta solicitud.", icon=":material/history:")


def _guardar_borrador():
    almacen.guardar_borrador(usuario.email, folio, {
        "decision": st.session_state.get(k_dec), "enganche": st.session_state.get(k_eng),
        "motivo": st.session_state.get(k_mot), "texto": st.session_state.get(k_txt)})


if estado == "Resuelta hoy":
    hecho = almacen.decisiones(analista_id=usuario.analista_id)
    hecho = hecho[hecho["folio"] == folio].head(1)
    with st.container(border=True):
        if len(hecho):
            h = hecho.iloc[0]
            st.success(f"Ya resolviste esta solicitud: **{h['decision']}** a las {h['ts'][11:16]}"
                       + (f" · motivo: {h['motivo']}" if h["motivo"] else ""), icon=":material/task_alt:")
        st.page_link("vistas/p1_bandeja.py", label="Volver a la bandeja", icon=":material/inbox:")
    st.stop()

with st.container(border=True):
    st.markdown("#### Tu decisión")
    bloqueado = ev.bloquea_aprobar or estado == "En espera de documento"
    opciones = ["Rechazar"] if bloqueado else C.DECISIONES
    if bloqueado:
        st.caption("Solo «Rechazar» está disponible mientras falte un dato clave o la solicitud espere documento.")
    if st.session_state.get(k_dec) not in opciones:
        st.session_state.pop(k_dec, None)
    decision = st.segmented_control("Decisión", opciones, key=k_dec, on_change=_guardar_borrador,
                                    label_visibility="collapsed")

    pd_final = ev.pd
    enganche = None
    if decision == "Condicionar":
        actual = float(fila["DOWN_PAYMENT_PCT"])
        sugerido = ev.enganche_requerido or min(actual + 0.05, C.ENGANCHE_MAX_CONDICION)
        if k_eng not in st.session_state:
            st.session_state[k_eng] = min(math.ceil(sugerido * 1000) / 10, C.ENGANCHE_MAX_CONDICION * 100)
        enganche_pct = st.slider(f"C3 · {C.CONTROLES['C3']['nombre']}", min_value=round(actual * 100, 1),
                                 max_value=C.ENGANCHE_MAX_CONDICION * 100, step=0.5, format="%.1f%%",
                                 key=k_eng, on_change=_guardar_borrador)
        st.caption(ui.amarre("C3"))
        enganche = enganche_pct / 100
        pd_final = pd_con_enganche(modelo, fila | {v: fila[v] if pd.notna(fila[v]) else modelo.medianas[v]
                                                   for v in modelo.variables}, enganche)
        bajo = pd_final < C.CORTE_PD
        st.markdown(f"Con enganche de **{enganche:.1%}** (hoy {actual:.1%}) la PD queda en **{pd_final:.1%}** "
                    + ("· bajo el corte" if bajo else "· sigue sobre el corte") + ". Escenario CALCULADO: más "
                    "enganche baja el LTV y el pago mensual.")

    contradice = False
    if decision:
        sin_recomendacion = ev.sugerencia == "Revisión manual"
        contradice = sin_recomendacion or (decision == "Aprobar" and ev.pd >= C.CORTE_PD) or \
            (decision == "Rechazar" and ev.pd < C.CORTE_PD) or (decision == "Condicionar" and pd_final >= C.CORTE_PD)
    etiqueta_motivo = "Motivo (obligatorio: tu decisión contradice al modelo o no hay recomendación)" if contradice \
        else "Motivo (opcional cuando coincides con el modelo)"
    m1, m2 = st.columns([1, 1.3])
    with m1:
        motivo = st.selectbox(etiqueta_motivo, C.MOTIVOS_OVERRIDE, index=None, placeholder="Elige un motivo…",
                              key=k_mot, on_change=_guardar_borrador)
    with m2:
        texto = st.text_input("Detalle del motivo" + (" (obligatorio)" if motivo == C.MOTIVO_OTRO else ""),
                              key=k_txt, on_change=_guardar_borrador, max_chars=280,
                              placeholder="Sin datos personales: no escribas nombres ni teléfonos.")

    errores = st.empty()

    def _siguiente_pendiente():
        resto = cola[(cola["ESTADO_SOLICITUD"] == "Pendiente") & (cola["FOLIO"] != folio)]
        resto = resto.sort_values(["PD", "RECIBIDA_MIN"], ascending=[False, False])
        return resto["FOLIO"].iloc[0] if len(resto) else None

    if st.button("Guardar decisión y abrir la siguiente", type="primary", icon=":material/save:"):
        # Recorrido de error 3: guardar sin decisión o contradecir sin motivo.
        problemas = []
        if not decision:
            problemas.append("Elige Aprobar, Condicionar o Rechazar.")
        if contradice and not motivo:
            problemas.append("Tu decisión contradice al modelo (o no hay recomendación): elige un motivo para "
                             "que Luis pueda medir el acuerdo modelo–analista.")
        if motivo == C.MOTIVO_OTRO and not (texto or "").strip():
            problemas.append("Con «Otro» escribe el detalle del motivo.")
        if problemas:
            errores.error("No se guardó:\n\n- " + "\n- ".join(problemas), icon=":material/error:")
        else:
            aprueba = decision in ("Aprobar", "Condicionar")
            categoria = "Coincide con el modelo" if not contradice else (
                "Aprueba lo que el modelo rechaza" if aprueba else "Rechaza lo que el modelo aprueba")
            if ev.sugerencia == "Revisión manual":
                categoria = "Sin recomendación del modelo"
            almacen.guardar_decision({
                "folio": folio, "analista_id": usuario.analista_id, "decision": decision,
                "enganche_condicion": enganche, "motivo": motivo, "motivo_texto": texto or None,
                "pd": ev.pd, "sugerencia": ev.sugerencia, "contradice": contradice, "categoria": categoria,
                "duracion_seg": time.time() - st.session_state.get(f"inicio_{folio}", time.time()),
            })
            siguiente = _siguiente_pendiente()
            st.toast(f"{folio}: {decision} registrada.", icon=":material/task_alt:")
            if siguiente:
                st.session_state["folio_actual"] = siguiente
                st.rerun()
            st.session_state.pop("folio_actual", None)
            st.switch_page("vistas/p1_bandeja.py")
    st.caption("Al guardar se registran decisión, motivo, PD y tiempo (alimentan el acuerdo modelo–analista que "
               "vigila Luis) y se abre la siguiente solicitud pendiente de mayor PD.")



# --- Diagnóstico detallado (tras la decisión visible) --------------------------
# --- Fila 1: G1 (corte) y G3 (buen pagador) -----------------------------------
c1, c2 = st.columns(2, gap="medium")
with c1, st.container(border=True):
    ui.titulo_grafica("¿Está arriba o abajo del corte?", "CALCULADO", "POLÍTICA", codigo="G1 · barra con corte")
    veredicto = {
        "Aprobar": ("El modelo sugiere APROBAR", "green", ":material/check:"),
        "Condicionar": (f"El modelo sugiere CONDICIONAR: enganche ≥ {ev.enganche_requerido:.1%}" if ev.enganche_requerido else "", "orange", ":material/tune:"),
        "Rechazar": ("El modelo sugiere RECHAZAR: ni con 31% de enganche baja del corte", "red", ":material/close:"),
        "Revisión manual": ("Sin recomendación: dato fuera de rango", "gray", ":material/help:"),
    }[ev.sugerencia]
    with st.container(horizontal=True, vertical_alignment="center"):
        st.markdown(f"## PD {ev.pd:.1%}")
        st.badge(veredicto[0], color=veredicto[1], icon=veredicto[2])
    G.mostrar(G.g1_barra_corte(ev.pd, C.CORTE_PD, modelo.tasa_base), key="g1")
    distancia = (ev.pd - C.CORTE_PD) * 100
    st.caption(f"Nivel **{ev.nivel}** · {abs(distancia):.1f} pp {'sobre' if distancia >= 0 else 'bajo'} el corte "
               f"de {C.CORTE_PD:.0%}. Promedio de cartera {modelo.tasa_base:.2%} = DEFAULT REAL de las 80,000 filas.")

with c2, st.container(border=True):
    ui.titulo_grafica("¿En qué se aleja de un buen pagador?", "REAL", "CALCULADO", codigo="G3 · barras pareadas")
    variables = ["DEBT_TO_INCOME", "PAYMENT_TO_INCOME", "LOAN_TO_VALUE", "DOWN_PAYMENT_PCT", "REVOLVING_UTILIZATION"]
    valores_cliente = [float(fila[v]) if pd.notna(fila[v]) else modelo.medianas[v] for v in variables]
    G.mostrar(G.g3_pareadas(variables, valores_cliente, [modelo.mediana_buenos[v] for v in variables]), key="g3")
    st.caption("Mismo eje en % para las cinco razones. Referencia: mediana de los créditos con DEFAULT = 0.")

# --- Fila 2: G2 (contribuciones) y expediente ----------------------------------
c3, c4 = st.columns(2, gap="medium")
with c3, st.container(border=True):
    ui.titulo_grafica("¿Qué sube o baja el riesgo de ESTE caso?", "CALCULADO", codigo="G2 · barras divergentes")
    G.mostrar(G.g2_contribuciones(ev.contribuciones, datos.formatear), key="g2")
    st.caption("Cada barra = cuántos puntos de PD cambiaría si esa variable tomara el valor típico de la cartera "
               "(mediana) y todo lo demás quedara igual. Rojo sube el riesgo; azul lo baja.")

with c4, st.container(border=True):
    ui.titulo_grafica("Expediente: solo lo que la decisión necesita", "REAL")
    exp = pd.DataFrame({
        "Variable": [C.ETIQUETAS[v] for v in modelo.variables],
        "Valor": [datos.formatear(v, fila[v]) + (" · IMPUTADO" if v in ev.imputados else "")
                  + (" · FUERA DE RANGO" if v in ev.fuera_rango else "") for v in modelo.variables],
        "Típico buen pagador": [datos.formatear(v, modelo.mediana_buenos[v]) for v in modelo.variables],
    })
    st.dataframe(exp, hide_index=True, height=388)
    ocultos = [f["dato"] for f in MATRIZ_DATOS if f["analista"] == OCULTO and f["grupo"] != "Calculado"]
    st.caption("Ocultos por política (no cambian la decisión o filtrarían el resultado): " + ", ".join(ocultos) + ".")

ui.pie_origen("Los valores de esta solicitud son una fila REAL del holdout; la PD y las contribuciones se "
              "calculan con el modelo entrenado en el otro 75% de la base.")
