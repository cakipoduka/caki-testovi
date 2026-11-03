"""
CAKI testovi v2 — `usporedba.py`  (PLAN 13 — usporedba dva testa)
⚠️ PRIPREMA izvan gita (`_proba_tmp/prep/`) — kopira se u `caki-testovi/` kad Claude završi.

Pitanje na koje odgovara: **je li razred napredovao između dva testa?**
Uspoređuje iste učenike na dva testa i daje: prosjek prije/poslije, razliku u postotnim
bodovima, broj učenika koji su napredovali / nazadovali / isto, te po učeniku tablicu.
"""
from __future__ import annotations

import model


def _postotak(bodovi, maks) -> int | None:
    try:
        b = float(bodovi)
        m = float(maks)
    except (TypeError, ValueError):
        return None
    if not m:
        return None
    return int(round(100 * b / m))


def po_uceniku(dodjele_a, pokusaji_a, dodjele_b, pokusaji_b) -> list[dict]:
    """Vrati [{ucenik, sifra, prije, poslije, razlika}] za učenike prisutne na OBA testa."""
    def mapa(dodjele, pokusaji):
        po_dodjeli = {model.tekst(p.get("dodjela_id")): p for p in pokusaji or []}
        izlaz = {}
        for d in dodjele or []:
            u = model.tekst(d.get("ucenik_id")).upper()
            p = po_dodjeli.get(model.tekst(d.get("dodjela_id")))
            if not u or not p or not model.je_predan(p):   # 4.11.: samo PREDANI pokušaji
                continue
            post = _postotak(p.get("bodovi"), p.get("bodovi_max"))
            if post is None:
                continue
            ime = model.tekst(d.get("ime_djeteta")) or u
            izlaz[u] = {"ime": ime, "postotak": post}
        return izlaz

    a = mapa(dodjele_a, pokusaji_a)
    b = mapa(dodjele_b, pokusaji_b)

    redci = []
    for u in sorted(set(a) & set(b)):
        prije, poslije = a[u]["postotak"], b[u]["postotak"]
        redci.append({
            "ucenik": a[u]["ime"] or b[u]["ime"],
            "sifra": u,
            "prije": prije,
            "poslije": poslije,
            "razlika": poslije - prije,
        })
    redci.sort(key=lambda r: -r["razlika"])
    return redci


def sazetak(redci: list[dict]) -> dict:
    """Prosjeci, razlika i broj napredovanja — za tri broja na vrhu kartice."""
    if not redci:
        return {"ucenika": 0, "prije": 0, "poslije": 0, "razlika": 0,
                "napredovalo": 0, "nazadovalo": 0, "isto": 0}
    n = len(redci)
    prije = sum(r["prije"] for r in redci) / n
    poslije = sum(r["poslije"] for r in redci) / n
    return {
        "ucenika": n,
        "prije": int(round(prije)),
        "poslije": int(round(poslije)),
        "razlika": int(round(poslije - prije)),
        "napredovalo": sum(1 for r in redci if r["razlika"] > 0),
        "nazadovalo": sum(1 for r in redci if r["razlika"] < 0),
        "isto": sum(1 for r in redci if r["razlika"] == 0),
    }
