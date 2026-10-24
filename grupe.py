"""
CAKI testovi v2 — `grupe.py`
Grupe i kante iz kojih se bira **kome ide test**.

Dva izvora (kao i u starom sustavu, ali ovdje odvojeno i testirano):
  · **Upisi** — tabovi `Grupe` i `Rezervacije` (status „Potvrđeno")
  · **Matura** — tab `Raspored_Matura_<sezona>` (dan × termin × učionica = „kanta")

Vraća se isti oblik za oba: [{"kod", "naziv", "izvor", "ucenici": [{"ucenik_id", "ime_djeteta"}]}].
"""
from __future__ import annotations

import model
import tablice

TAB_GRUPE = "Grupe"
TAB_REZERVACIJE = "Rezervacije"
PREFIKS_MATURA = "Raspored_Matura"


def grupe_upisa(sheet, status: str = "Potvrđeno") -> list[dict]:
    """Grupe Upisa s učenicima (samo zadani status)."""
    grupe = {model.tekst(g.get("grupa_id")): g for g in tablice.ucitaj(sheet, TAB_GRUPE)
             if model.tekst(g.get("grupa_id"))}
    po = {}
    for r in tablice.ucitaj(sheet, TAB_REZERVACIJE):
        gid = model.tekst(r.get("grupa_id"))
        if gid not in grupe:
            continue
        if status and model.tekst(r.get("status")) != status:
            continue
        uid = model.tekst(r.get("ucenik_id")).upper()
        if not uid:
            continue
        stavka = po.setdefault(gid, {"kod": gid, "naziv": _naziv_grupe(grupe[gid]),
                                     "izvor": "Upisi", "ucenici": [], "_videno": set()})
        if uid in stavka["_videno"]:
            continue
        stavka["_videno"].add(uid)
        stavka["ucenici"].append({"ucenik_id": uid,
                                  "ime_djeteta": model.tekst(r.get("ime_djeteta"))})
    return _ocisti(po)


def _naziv_grupe(g: dict) -> str:
    dijelovi = [model.tekst(g.get("predmet")), model.tekst(g.get("naziv")),
                model.tekst(g.get("program")), model.tekst(g.get("skolska_godina"))]
    naziv = " · ".join(d for d in dijelovi if d)
    return naziv or model.tekst(g.get("grupa_id"))


def tabovi_mature(sheet) -> list[str]:
    """Svi tabovi rasporeda Mature (može ih biti više po sezoni)."""
    try:
        naslovi = [w.title for w in sheet.worksheets()]
    except Exception:                                   # noqa: BLE001
        return []
    return [n for n in naslovi if n.startswith(PREFIKS_MATURA)]


def kante_mature(sheet, tab: str | None = None) -> list[dict]:
    """Kante Mature: dan × termin × učionica, s učenicima iz tog termina."""
    tabovi = [tab] if tab else tabovi_mature(sheet)
    izlaz = []
    for ime_taba in tabovi:
        po = {}
        for r in tablice.ucitaj(sheet, ime_taba):
            dan = model.tekst(r.get("dan"))
            termin = model.tekst(r.get("termin"))
            ucionica = model.tekst(r.get("ucionica"))
            uid = model.tekst(r.get("ucenik_id")).upper()
            if not dan or not termin or not uid:
                continue
            kod = f"{ime_taba}|{dan}|{termin}|{ucionica}"
            stavka = po.setdefault(kod, {
                "kod": kod, "izvor": "Matura", "ucenici": [], "_videno": set(),
                "naziv": " · ".join(x for x in (dan, f"T{termin} {model.tekst(r.get('vrijeme'))}".strip(),
                                                f"uč. {ucionica}" if ucionica else "") if x),
            })
            if uid in stavka["_videno"]:
                continue                            # isti učenik u istoj kanti s dva predmeta
            stavka["_videno"].add(uid)
            stavka["ucenici"].append({"ucenik_id": uid,
                                      "ime_djeteta": model.tekst(r.get("ime_djeteta"))})
        izlaz += _ocisti(po)
    return izlaz


def sve_grupe(sheet) -> list[dict]:
    """Sve grupe i kante (Upisi + Matura), bez duplikata, sortirano po nazivu."""
    return sorted(grupe_upisa(sheet) + kante_mature(sheet), key=lambda g: g["naziv"])


def ucenici_iz_grupa(grupe: list[dict], kodovi) -> list[dict]:
    """Spoji učenike odabranih grupa bez dvostrukih (učenik može biti u dvije kante)."""
    if kodovi is None:
        return []
    izlaz, videno = [], set()
    for g in grupe or []:
        if kodovi and model.tekst(g.get("kod")) not in kodovi:
            continue
        for u in g.get("ucenici") or []:
            uid = model.tekst((u or {}).get("ucenik_id")).upper()
            if not uid or uid in videno:
                continue
            videno.add(uid)
            izlaz.append({"ucenik_id": uid, "ime_djeteta": model.tekst((u or {}).get("ime_djeteta"))})
    return izlaz


def _ocisti(po: dict) -> list[dict]:
    """Makni pomoćni `_videno` i preskoči grupe bez učenika."""
    izlaz = []
    for g in po.values():
        g.pop("_videno", None)
        if g.get("ucenici"):
            izlaz.append(g)
    return izlaz
