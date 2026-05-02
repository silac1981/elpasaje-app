"""utils/mike.py — integración con el agente Mike (Claude)."""
import streamlit as st
from ep_agente import get_alertas_dashboard as _get_alertas_raw


@st.cache_data(ttl=120)
def get_alertas_dashboard() -> list:
    try:
        return _get_alertas_raw()
    except Exception:
        return []


def preguntar_mike(pregunta: str, contexto_extra: str = "") -> str:
    try:
        from anthropic import Anthropic
        from context_elpasaje import SYSTEM_PROMPT, get_data_context
        _c = Anthropic()
        _sys = SYSTEM_PROMPT + "\n\n" + get_data_context()
        if contexto_extra:
            _sys += f"\n\nCONTEXTO DEL FORMULARIO ACTUAL:\n{contexto_extra}"
        hist = st.session_state.get("mike_history", [])
        hist.append({"role": "user", "content": pregunta})
        r = _c.messages.create(model="claude-sonnet-4-6", max_tokens=800, system=_sys, messages=hist)
        resp = r.content[0].text
        hist.append({"role": "assistant", "content": resp})
        st.session_state["mike_history"] = hist[-20:]
        return resp
    except Exception as e:
        return f"No pude conectarme con Mike ahora mismo ({e})"
