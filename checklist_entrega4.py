"""Checklist colaborativo de Entrega 4. App independiente de AutoCredit Advisor."""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Entrega 4 · Equipo 3", layout="wide")

# Estilos de lectura: estados visibles completos y colores semánticos.
st.markdown("""
<style>
    .block-container {max-width: 1380px; padding-top: 2rem;}
    h1 {font-size: clamp(1.65rem, 3vw, 2.35rem) !important; line-height: 1.2 !important;}
    h4 {font-size: 1.15rem !important; line-height: 1.4 !important; overflow-wrap: anywhere;}
    .resumen-card {
        border: 1px solid rgba(160, 160, 160, .23);
        border-radius: 12px;
        padding: 14px 18px;
        min-height: 92px;
    }
    .resumen-label {font-size: .95rem; color: #A4A4A4; margin-bottom: 6px;}
    .resumen-valor {font-size: 2.1rem; font-weight: 750; line-height: 1.1;}
    .resumen-pendiente {color: #F87171;}
    .resumen-parcial {color: #FBBF24;}
    .resumen-completado {color: #4ADE80;}
    .estado-etiqueta {
        display: inline-block;
        border-radius: 9px;
        padding: 7px 12px;
        font-size: .93rem;
        line-height: 1.35;
        font-weight: 700;
        white-space: normal;
        overflow-wrap: anywhere;
        max-width: 100%;
    }
    .estado-pendiente {color: #FCA5A5; border: 1px solid #B91C1C; background: rgba(185,28,28,.15);}
    .estado-parcial {color: #FCD34D; border: 1px solid #B45309; background: rgba(180,83,9,.15);}
    .estado-completado {color: #86EFAC; border: 1px solid #15803D; background: rgba(21,128,61,.15);}
</style>
""", unsafe_allow_html=True)

REPO = "a01664722-ai/autocredit_advisor-2"
BRANCH = "entrega4-seguimiento"
PATH = "checklist_entrega4.json"
API = f"https://api.github.com/repos/{REPO}/contents/{PATH}"
ESTADOS = ["Pendiente", "Parcial", "Completado"]


def secreto(nombre: str) -> str:
    try:
        return str(st.secrets[nombre])
    except (KeyError, FileNotFoundError, AttributeError):
        return ""


def solicitud(metodo: str = "GET", contenido: dict | None = None, token: str = "") -> dict:
    url = f"{API}?ref={quote(BRANCH)}" if metodo == "GET" else API
    encabezados = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Equipo3-Entrega4",
    }
    if token:
        encabezados["Authorization"] = f"Bearer {token}"
    datos = None
    if contenido is not None:
        datos = json.dumps(contenido, ensure_ascii=False).encode("utf-8")
        encabezados["Content-Type"] = "application/json"
    peticion = Request(url, headers=encabezados, data=datos, method=metodo)
    with urlopen(peticion, timeout=15) as respuesta:
        return json.load(respuesta)


def leer_documento() -> tuple[dict, str]:
    import base64
    respuesta = solicitud(token=secreto("GITHUB_TOKEN"))
    texto = base64.b64decode(respuesta["content"]).decode("utf-8")
    return json.loads(texto), respuesta["sha"]


def guardar_tarea(indice: int, cambios: dict, autor: str) -> None:
    import base64
    # Leer el SHA actual antes de escribir para evitar sobrescribir cambios ajenos.
    documento, sha = leer_documento()
    tarea = documento["tareas"][indice]
    if tarea["id"] != cambios["id"]:
        raise ValueError("El orden de las tareas cambió; actualiza la página.")
    tarea.update({
        "estado": cambios["estado"],
        "nota": cambios["nota"],
        "enlace": cambios["enlace"],
        "actualizado_por": autor,
        "actualizado_en": datetime.now(ZoneInfo("America/Mexico_City")).strftime("%Y-%m-%d %H:%M"),
    })
    cadena = json.dumps(documento, ensure_ascii=False, indent=2) + "\n"
    solicitud("PUT", {
        "message": f"Entrega 4: seguimiento de {tarea['id']} por {autor}",
        "content": base64.b64encode(cadena.encode("utf-8")).decode("ascii"),
        "branch": BRANCH,
        "sha": sha,
    }, token=secreto("GITHUB_TOKEN"))


st.title("Entrega 4 · Seguimiento del Equipo 3")
st.caption("Riesgo crediticio automotriz · 8 criterios de evidencia · Estado compartido en GitHub")

token = secreto("GITHUB_TOKEN")
pin_configurado = secreto("EQUIPO_PIN")
puede_editar = bool(token and pin_configurado)

with st.sidebar:
    st.header("Equipo 3")
    st.write("José Carlos · Valeria · Marcos · Edwin · Yexalén · Emiliano")
    st.divider()
    st.subheader("Edición colaborativa")
    if puede_editar:
        nombre = st.text_input("Tu nombre", key="nombre_integrante")
        pin = st.text_input("PIN del equipo", type="password", key="pin_equipo")
        autorizado = bool(nombre.strip() and pin == pin_configurado)
        if autorizado:
            st.success("Edición habilitada")
        else:
            st.info("Escribe tu nombre y el PIN para actualizar tareas.")
    else:
        autorizado = False
        nombre = ""
        st.info("Vista de consulta. Para activar edición compartida configura GITHUB_TOKEN y EQUIPO_PIN en los secretos de esta app.")
    st.divider()
    if st.button("Actualizar estados desde GitHub", use_container_width=True):
        st.rerun()

try:
    documento, _ = leer_documento()
except (HTTPError, URLError, ValueError, KeyError, json.JSONDecodeError) as error:
    st.error("No se pudo cargar el checklist desde GitHub. Intenta actualizar la página.")
    st.caption(f"Detalle técnico: {type(error).__name__}")
    st.stop()

tareas = documento["tareas"]
conteo = {estado: sum(t["estado"] == estado for t in tareas) for estado in ESTADOS}
total = len(tareas)
c1, c2, c3, c4 = st.columns(4)
for columna, etiqueta, valor, clase in [
    (c1, "Criterios", total, ""),
    (c2, "Completados", conteo["Completado"], "resumen-completado"),
    (c3, "En proceso", conteo["Parcial"], "resumen-parcial"),
    (c4, "Pendientes", conteo["Pendiente"], "resumen-pendiente"),
]:
    with columna:
        st.markdown(
            f'<div class="resumen-card"><div class="resumen-label">{etiqueta}</div>'
            f'<div class="resumen-valor {clase}">{valor}</div></div>',
            unsafe_allow_html=True,
        )
st.progress(conteo["Completado"] / total, text=f"{conteo['Completado']} de {total} criterios completados")
st.caption("El progreso refleja los estados declarados por el equipo; las evidencias deben revisarse antes de entregar.")

filtro = st.segmented_control(
    "Filtrar criterios", ["Todos", "Pendiente", "Parcial", "Completado"], default="Todos"
)
visible = [(i, tarea) for i, tarea in enumerate(tareas)
           if filtro == "Todos" or tarea["estado"] == filtro]

for indice, tarea in visible:
    with st.container(border=True):
        columna_izq, columna_der = st.columns([5, 1.8], vertical_alignment="top")
        with columna_izq:
            st.markdown(f"#### {indice + 1}. {tarea['titulo']}")
            st.markdown(f"**Responsable:** {tarea['responsable']}")
            st.write(f"**Evidencia:** {tarea['evidencia']}")
        with columna_der:
            estado_actual = tarea["estado"] if tarea["estado"] in ESTADOS else "Pendiente"
            clase_estado = {
                "Pendiente": "estado-pendiente",
                "Parcial": "estado-parcial",
                "Completado": "estado-completado",
            }[estado_actual]
            st.markdown(
                f'<div class="estado-etiqueta {clase_estado}">{estado_actual}</div>',
                unsafe_allow_html=True,
            )
        if tarea.get("nota"):
            st.caption(f"Nota: {tarea['nota']}")
        if tarea.get("enlace"):
            st.link_button("Abrir evidencia", tarea["enlace"])
        if tarea.get("actualizado_en"):
            st.caption(f"Última actualización: {tarea.get('actualizado_en')} · {tarea.get('actualizado_por', '')}")
        # Cambios rápidos: un clic guarda el estado compartido y actualiza el progreso.
        if autorizado:
            st.caption("Cambiar estado rápidamente")
            botones = st.columns(3, gap="small")
            for columna, nuevo_estado in zip(botones, ESTADOS):
                with columna:
                    if st.button(
                        f"Marcar {nuevo_estado.lower()}",
                        key=f"rapido_{tarea['id']}_{nuevo_estado}",
                        use_container_width=True,
                        disabled=(tarea["estado"] == nuevo_estado),
                        type="primary" if nuevo_estado == "Completado" else "secondary",
                    ):
                        try:
                            guardar_tarea(indice, {
                                "id": tarea["id"],
                                "estado": nuevo_estado,
                                "nota": tarea.get("nota", ""),
                                "enlace": tarea.get("enlace", ""),
                            }, nombre.strip())
                        except HTTPError as error:
                            if error.code in (409, 422):
                                st.warning("Otro integrante guardó cambios. Actualiza y vuelve a intentar.")
                            else:
                                st.error(f"No se pudo guardar (HTTP {error.code}).")
                        except (URLError, ValueError, KeyError) as error:
                            st.error(f"No se pudo guardar: {type(error).__name__}")
                        else:
                            st.rerun()

        with st.expander("Editar detalle, nota y enlace"):
            if not autorizado:
                st.info("Para guardar, ingresa tu nombre y el PIN del equipo en la barra lateral.")
            else:
                with st.form(f"editar_{tarea['id']}"):
                    estado = st.selectbox("Estado", ESTADOS, index=ESTADOS.index(tarea["estado"]))
                    nota = st.text_area("Avances o pendientes", value=tarea.get("nota", ""), height=85)
                    enlace = st.text_input("Enlace a evidencia (opcional)", value=tarea.get("enlace", ""))
                    enviar = st.form_submit_button("Guardar para todo el equipo", type="primary")
                    if enviar:
                        enlace = enlace.strip()
                        if enlace and not enlace.startswith(("https://", "http://")):
                            st.error("El enlace debe empezar por https:// o http://.")
                        else:
                            try:
                                guardar_tarea(indice, {
                                    "id": tarea["id"], "estado": estado,
                                    "nota": nota.strip(), "enlace": enlace,
                                }, nombre.strip())
                            except HTTPError as error:
                                if error.code in (409, 422):
                                    st.warning("Otra persona guardó cambios. Actualiza la página y vuelve a intentarlo.")
                                else:
                                    st.error(f"No se pudo guardar (HTTP {error.code}). Revisa los permisos del token.")
                            except (URLError, ValueError, KeyError) as error:
                                st.error(f"No se pudo guardar: {type(error).__name__}")
                            else:
                                st.success("Actualización guardada en GitHub.")
                                st.rerun()

st.divider()
st.subheader("Exportar seguimiento")
tabla = pd.DataFrame([{
    "Criterio": t["titulo"],
    "Responsable": t["responsable"],
    "Evidencia": t["evidencia"],
    "Estado": t["estado"],
    "Nota": t.get("nota", ""),
    "Enlace": t.get("enlace", ""),
    "Actualizó": t.get("actualizado_por", ""),
    "Fecha": t.get("actualizado_en", ""),
} for t in tareas])
st.download_button("Descargar checklist CSV", tabla.to_csv(index=False).encode("utf-8-sig"),
                   "Checklist_Entrega4_Equipo3.csv", mime="text/csv")
st.caption("Entrega final: PDF en Canvas, capturas SAS, dashboard, conclusiones, APA y declaración de IA.")
