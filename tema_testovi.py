"""
CAKI testovi v2 — `tema_testovi.py`
Dodatne komponente izgleda za ekrane koji postoje SAMO u ovom repou (kartica 🧪 Testovi).

**Zašto zasebna datoteka, a ne dopuna `caki_tema.py`:** `caki_tema.py` je po vlastitom opisu
ista datoteka u `caki-testovi`, `caki-evidencija-dolazaka`, `caki-booking-termina` i CRM adminu.
Kad bi se proširila ovdje, četiri kopije bi se razišle i sljedeća sinkronizacija bi pregazila
dopunu. Ovdje stoji samo ono što drugi portali nemaju.

Koristi se uz nju, ne umjesto nje:

    caki_tema.primijeni()       # zajednička tema (font, boje, gumbi, kartice)
    tema_testovi.primijeni()    # dodatak za ovaj repo

Boje i razmaci namjerno su isti kao u `caki_tema.py` (`--kc-*` varijable), da se ekran ne
raspadne na dva stila. Ovdje se NE dira nikakav podatak — samo izgled.
"""
from __future__ import annotations

import html

import streamlit as st

# Narančasta i crvena nisu u `caki_tema.py` jer ih drugi portali ne trebaju.
# Crvena je `#b42318` — provjereno da zadovoljava kontrast 4.5:1 na bijeloj podlozi.
CSS = """
<style>
:root{ --tt-crvena:#b42318; --tt-crvena-t:#8f1d14; --tt-crvena-p:#fdeceb; --tt-crvena-r:#f1c4bf;
  --tt-naranca:#8a4207; --tt-naranca-p:#fff0e0; --tt-naranca-r:#e8cba6; }

/* ---------- stavka popisa testova ---------- */
.tt-stavka{ display:flex; flex-direction:column; gap:6px; }
.tt-stavka .nm{ display:flex; align-items:flex-start; justify-content:space-between; gap:10px; }
.tt-stavka .nm b{ font-size:14.5px; font-weight:600; line-height:1.3; color:var(--kc-ink); }
.tt-stavka .meta{ font-size:12px; color:var(--kc-muted); }
.tt-stavka .st{ font-size:12px; font-weight:500; }
.tt-stavka .st.g{ color:#1b6b3d; } .tt-stavka .st.o{ color:var(--tt-naranca); }
.tt-stavka .st.m{ color:var(--kc-muted); }

/* odabrana kartica u popisu: plavi obrub + blagi prsten, bez lijeve crte */
.stApp [class*="st-key-box_tt_odabran"]{ border-color:var(--kc-blue) !important;
  box-shadow:0 0 0 2px #dbeafd; background:#f8fbff !important; }
.stApp [class*="st-key-box_tt_stavka"]{ padding:13px 14px !important; gap:8px !important; }
.stApp [class*="st-key-box_tt_stavka"] button{ min-height:38px; }

/* ---------- zaglavlje detalja ---------- */
.tt-naslov{ display:flex; flex-wrap:wrap; align-items:flex-start; justify-content:space-between; gap:14px; }
.tt-naslov h2{ font-size:22px !important; font-weight:600 !important; margin:0 0 6px !important; line-height:1.25; }
.tt-id{ font-size:12.5px; font-weight:500; color:var(--kc-muted); font-variant-numeric:tabular-nums; }

/* pločice brojeva (zadaci / bodovi / pokušaji) */
.tt-brojevi{ display:flex; gap:20px; flex-wrap:wrap; }
.tt-brojevi div{ display:flex; flex-direction:column; }
.tt-brojevi b{ font-size:23px; font-weight:600; letter-spacing:-0.4px; color:var(--kc-ink);
  font-variant-numeric:tabular-nums; line-height:1.15; }
.tt-brojevi span{ font-size:11.5px; color:var(--kc-muted); margin-top:1px; }

/* ---------- poruke u kartici (bez st.info/st.warning, da stanu u karticu) ---------- */
.tt-poruka{ display:flex; gap:11px; border-radius:10px; padding:13px 15px; font-size:13.5px; line-height:1.55; }
.tt-poruka .ik{ flex:0 0 auto; font-size:15px; line-height:1.4; }
.tt-poruka p{ margin:0 !important; font-size:13.5px !important; }
.tt-poruka.b{ background:#e6effb; border:1px solid #c3d8f2; color:#174f92; }
.tt-poruka.o{ background:var(--tt-naranca-p); border:1px solid var(--tt-naranca-r); color:#7a3b06; }
.tt-poruka.c{ background:var(--tt-crvena-p); border:1px solid var(--tt-crvena-r); color:var(--tt-crvena-t); }
.tt-poruka code{ font-family:inherit; font-weight:600; }

/* ---------- traka radnji ---------- */
.stApp [class*="st-key-box_tt_radnje"]{ padding:16px 20px !important; }
.stApp [class*="st-key-tt_opasno"] button{ border-color:#e8b4ae !important; color:var(--tt-crvena) !important; }
.stApp [class*="st-key-tt_opasno"] button:hover{ border-color:var(--tt-crvena) !important;
  background:#fffafa !important; }

/* ---------- Student View: red po resursu ---------- */
.tt-sv{ font-size:13px; font-weight:600; color:var(--kc-ink); margin:0 0 2px; }
.tt-sv-opis{ font-size:12px; color:var(--kc-muted); margin:0 0 10px; }

/* ---------- prazno stanje ---------- */
.tt-prazno{ background:#fff; border:1px dashed var(--kc-in); border-radius:12px; padding:26px 22px;
  text-align:center; }
.tt-prazno b{ display:block; font-size:15px; font-weight:600; margin-bottom:5px; }
.tt-prazno span{ font-size:13.5px; color:var(--kc-muted); }
</style>
"""

# status iz `definicije.STANJA` → (natpis za čovjeka, vrsta čipa iz caki_tema.chip)
# UX pravilo 5: nikad sirovi podaci korisniku — `zatvoren` nije natpis, „Zatvoren" jest.
STATUS_CHIP = {
    "nacrt": ("Nacrt", ""),
    "objavljen": ("Objavljen", "g"),
    "zatvoren": ("Zatvoren", "b"),
    "arhiviran": ("Arhiviran", "o"),
}


def primijeni() -> None:
    """Ubaci dodatni CSS. Zove se odmah nakon `caki_tema.primijeni()`."""
    st.markdown(CSS, unsafe_allow_html=True)


def status_natpis(status: str) -> tuple[str, str]:
    """`('zatvoren')` → `('Zatvoren', 'b')`. Nepoznat status vraća sam sebe, sivo."""
    kljuc = (status or "").strip().lower()
    return STATUS_CHIP.get(kljuc, (status or "—", ""))


def stavka(naziv: str, oznaka: str, status_html: str, meta: str,
           dodatak: str = "", dodatak_boja: str = "m") -> str:
    """Jedna kartica u popisu testova: naziv + čip statusa, pa redak s podacima.

    `dodatak_boja`: 'g' zeleno (gotovo), 'o' narančasto (traži pažnju), 'm' sivo (neutralno).
    """
    red_dodatka = (f'<span class="st {html.escape(dodatak_boja)}">{html.escape(dodatak)}</span>'
                   if dodatak else "")
    return (
        '<div class="tt-stavka">'
        f'<span class="nm"><b>{html.escape(naziv or "—")}</b>{status_html}</span>'
        f'<span class="meta">{html.escape(oznaka)} · {html.escape(meta)}</span>'
        f'{red_dodatka}'
        '</div>'
    )


def naslov(naziv: str, oznaka: str, cipovi_html: str, brojevi_html: str = "") -> str:
    """Zaglavlje detalja: naziv testa, njegova oznaka i čipovi lijevo, brojevi desno."""
    return ('<div class="tt-naslov"><div>'
            f'<h2>{html.escape(naziv or "—")}</h2>'
            f'<div class="kc-chips"><span class="tt-id">{html.escape(oznaka)}</span>'
            f'{cipovi_html}</div></div>'
            f'{brojevi_html}</div>')


def brojevi(*parovi) -> str:
    """Pločice brojeva: `brojevi(("24", "zadatka"), ("48", "bodova"))`."""
    unutra = "".join(
        f'<div><b>{html.escape(str(v))}</b><span>{html.escape(str(o))}</span></div>'
        for v, o in parovi)
    return f'<div class="tt-brojevi">{unutra}</div>'


def poruka(vrsta: str, tekst_html: str, ikona: str = "") -> str:
    """Poruka unutar kartice. `vrsta`: 'b' plava (info), 'o' narančasta (pažnja), 'c' crvena.

    Prima HTML jer tekst redovito sadrži podebljanja i `code` nazive stupaca; pozivatelj je
    dužan escapirati ono što dolazi od korisnika.
    """
    v = vrsta if vrsta in ("b", "o", "c") else "b"
    ik = f'<span class="ik">{html.escape(ikona)}</span>' if ikona else ""
    return f'<div class="tt-poruka {v}">{ik}<p>{tekst_html}</p></div>'


def prazno(naslov: str, uputa: str) -> str:
    """Prazno stanje — UX pravilo 6: mora reći što napraviti, ne samo da je prazno."""
    return (f'<div class="tt-prazno"><b>{html.escape(naslov)}</b>'
            f'<span>{html.escape(uputa)}</span></div>')
