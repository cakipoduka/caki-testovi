"""
CAKI testovi v2 — `galerija_radova.py`
🖼️ Pregled priloženih radova (slike/PDF postupka) UZ ocjenjivanje — 24.11.2026.

Caki: „Može li se učitana slika/pdf pregledavati kao u nekom pretpregledu / galeriji u desnoj
polovici prozora, dok se na lijevoj strani vide odgovori na zadatke, pa da profesor u jednom
prozoru može ocjenjivati i pregledavati učitane slike?"

Kako: radovi su na Driveu (dijeljeni disk, mapa `02_Radovi_ucenika`). Google za svaku datoteku
nudi stranicu za pregled (`…/file/d/<id>/preview`) koja prikazuje i sliku i PDF, s
povećavanjem i listanjem stranica. Ugrađuje se u aplikaciju kao okvir (iframe). Prikazuje se
jer je profesor u pregledniku prijavljen Google računom koji je član dijeljenog diska —
aplikacija sama ništa ne preuzima.

Poveznica koja nije s Drivea (npr. Google Photos s mobitela): izravna slika (.jpg/.png…) se
prikaže, za ostalo je gumb „Otvori u novoj kartici".
"""
from __future__ import annotations

import re

import model

_DRIVE_ID = (
    re.compile(r"drive\.google\.com/file/d/([A-Za-z0-9_-]{10,})"),
    re.compile(r"drive\.google\.com/(?:open|uc)\?(?:.*&)?id=([A-Za-z0-9_-]{10,})"),
    re.compile(r"docs\.google\.com/\w+/d/([A-Za-z0-9_-]{10,})"),
)
_SLIKA = re.compile(r"\.(jpe?g|png|gif|webp|bmp)(\?.*)?$", re.IGNORECASE)


def drive_id(veza) -> str:
    """ID datoteke iz Drive poveznice ('' ako nije Drive)."""
    tekst = model.tekst(veza)
    for uzorak in _DRIVE_ID:
        m = uzorak.search(tekst)
        if m:
            return m.group(1)
    return ""


def nacin_prikaza(veza) -> tuple[str, str]:
    """('drive', url_pregleda) · ('slika', url) · ('poveznica', url) · ('', '')."""
    tekst = model.tekst(veza)
    if not tekst:
        return "", ""
    fid = drive_id(tekst)
    if fid:
        return "drive", f"https://drive.google.com/file/d/{fid}/preview"
    if _SLIKA.search(tekst):
        return "slika", tekst
    return "poveznica", tekst


def oznaka(rad: dict, redni: int) -> str:
    naziv = model.tekst(rad.get("naziv")) or "rad"
    stanje = "✅" if model.tekst(rad.get("potvrdjeno")) else "⏳"
    return f"{redni}. {naziv} {stanje}"


def prikazi(st, radovi_: list[dict], *, kljuc: str, visina: int = 820, potvrdi=None) -> None:
    """Desna strana: odabir rada + pregled. `potvrdi(rad_id)` — gumb „✅ Potvrdi pregled"."""
    s_vezom = [r for r in (radovi_ or []) if model.tekst(r.get("veza"))]
    bez_veze = len(radovi_ or []) - len(s_vezom)
    if not s_vezom:
        st.info("Učenik nije priložio rad (sliku ili PDF postupka).")
        if bez_veze:
            st.caption(f"{bez_veze} zapis(a) bez datoteke — slanje tada nije uspjelo.")
        return

    kljuc_i = f"{kljuc}_gal_i"
    i = int(st.session_state.get(kljuc_i, 0) or 0) % len(s_vezom)
    if len(s_vezom) > 1:
        c1, c2, c3 = st.columns([1, 6, 1])
        if c1.button("◀", key=f"{kljuc}_gal_prev", help="Prethodni rad"):
            i = (i - 1) % len(s_vezom)
        if c3.button("▶", key=f"{kljuc}_gal_next", help="Sljedeći rad"):
            i = (i + 1) % len(s_vezom)
        izbor = c2.selectbox("Rad", list(range(len(s_vezom))), index=i,
                             format_func=lambda n: oznaka(s_vezom[n], n + 1),
                             key=f"{kljuc}_gal_sel_{i}", label_visibility="collapsed")
        i = int(izbor)
    st.session_state[kljuc_i] = i
    rad = s_vezom[i]

    nacin, url = nacin_prikaza(rad.get("veza"))
    if nacin == "drive":
        st.components.v1.iframe(url, height=visina, scrolling=True)
    elif nacin == "slika":
        st.image(url, width="stretch")
    st.link_button("↗ Otvori u novoj kartici", model.tekst(rad.get("veza")))
    if nacin == "poveznica":
        st.caption("Ova poveznica nije s Drivea pa se ne može prikazati ovdje.")
    if bez_veze:
        st.caption(f"+ {bez_veze} zapis(a) bez datoteke (slanje nije uspjelo).")

    if potvrdi is not None and not model.tekst(rad.get("potvrdjeno")):
        if st.button("✅ Potvrdi pregled ovog rada", key=f"{kljuc}_gal_ok_{rad.get('rad_id')}"):
            potvrdi(model.tekst(rad.get("rad_id")))
