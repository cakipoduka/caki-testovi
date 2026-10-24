"""
CAKI testovi v2 — `veza.py`
Otvara Sheetove (baza zadataka + CRM). Ovo je **jedino mjesto** koje zna za vjerodajnice.

`tablice.py` zna gdje su tabovi, `veza.py` zna kako se dolazi do dokumenta. Kad dođe Supabase,
mijenja se `tablice.py`; ako se promijeni način prijave, mijenja se ovdje.
"""
from __future__ import annotations

import streamlit as st

import secrets_json as _sj


def _klijent():
    """gspread klijent iz servisnog računa (tolerantno čitanje JSON-a — v. secrets_json)."""
    from gspread import authorize

    return authorize(_sj.ucitaj(st, "GOOGLE_SERVICE_ACCOUNT_JSON"))


@st.cache_resource(show_spinner=False)
def sheet_crm():
    """CRM Sheet — testovi, dodjele, pokušaji, ocjene."""
    return _klijent().open_by_key(str(st.secrets["CRM_SHEET_ID"]))


@st.cache_resource(show_spinner=False)
def sheet_baze():
    """Baza zadataka (20.000+ zadataka) — samo čitanje."""
    return _klijent().open_by_key(str(st.secrets["SHEET_ID"]))
