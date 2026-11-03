"""
CAKI testovi v2 — `raspodjela.py`  (PLAN 14 — raspodjela bodova)
⚠️ PRIPREMA izvan gita (`_proba_tmp/prep/`) — kopira se u `caki-testovi/` kad Claude završi.

Daje: histograme po rasponima (0–20, 20–40, …), medijan, prosjek, percentil 25/75,
najbolji/najslabiji, udio prolaznih (>= 50 %) i tablicu za prikaz.
"""
from __future__ import annotations

RASPONI = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 101)]


def _postotak(bodovi, maks) -> int | None:
    try:
        b, m = float(bodovi), float(maks)
    except (TypeError, ValueError):
        return None
    if not m:
        return None
    return int(round(100 * b / m))


def postoci(dodjele, pokusaji) -> list[int]:
    """Postoci svih predanih pokušaja (0–100)."""
    po_dodjeli = {p.get("dodjela_id"): p for p in pokusaji or []}
    izlaz = []
    for d in dodjele or []:
        p = po_dodjeli.get(d.get("dodjela_id"))
        if not p:
            continue
        post = _postotak(p.get("bodovi"), p.get("bodovi_max"))
        if post is not None:
            izlaz.append(post)
    return sorted(izlaz)


def _percentil(uredjeno: list[int], q: float) -> int:
    """Percentil (q između 0 i 1) — linearna interpolacija."""
    if not uredjeno:
        return 0
    if len(uredjeno) == 1:
        return uredjeno[0]
    poz = q * (len(uredjeno) - 1)
    donji = int(poz)
    gornji = min(donji + 1, len(uredjeno) - 1)
    tezina = poz - donji
    return int(round(uredjeno[donji] * (1 - tezina) + uredjeno[gornji] * tezina))


def histogram(postoci_: list[int]) -> list[dict]:
    """Raspodjela po rasponima (uvijek svih 5 redaka, i kad je 0)."""
    izlaz = []
    for donji, gornji in RASPONI:
        n = sum(1 for p in postoci_ if donji <= p < gornji)
        izlaz.append({"raspon": f"{donji}–{min(gornji, 100)} %", "ucenika": n})
    return izlaz


def sazetak(postoci_: list[int], *, prag_prolaza: int = 50) -> dict:
    """Brojevi za karticu: prosjek, medijan, P25, P75, min, max, prolaznost."""
    if not postoci_:
        return {"ucenika": 0, "prosjek": 0, "medijan": 0, "p25": 0, "p75": 0,
                "najbolji": 0, "najslabiji": 0, "prolazno": 0, "prolazno_postotak": 0}
    n = len(postoci_)
    prolazno = sum(1 for p in postoci_ if p >= prag_prolaza)
    return {
        "ucenika": n,
        "prosjek": int(round(sum(postoci_) / n)),
        "medijan": _percentil(postoci_, 0.5),
        "p25": _percentil(postoci_, 0.25),
        "p75": _percentil(postoci_, 0.75),
        "najbolji": postoci_[-1],
        "najslabiji": postoci_[0],
        "prolazno": prolazno,
        "prolazno_postotak": int(round(100 * prolazno / n)),
    }
