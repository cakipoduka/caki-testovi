"""
CAKI testovi v2 — `provjera_ocjena.py`
🧑‍🏫 RED ČEKANJA ZA PROFESORA (G4) — zadaci koje automatska provjera nije mogla odlučiti.

Zašto: `ceka_profesora` se prije samo izračunao i bacio. Sada postoji popis:
`Ocjene_zadataka` s `izvor_ocjene = "?"` (sumnja) ili `izvor_ocjene = "ai"` (AI predložio, čeka potvrdu).

Ne mijenja ništa — samo čita i grupira. Potvrda ide kroz `provedba.ocijeni_rucno()`
(trag u `Izmjene_ocjena`, preračun ukupnih bodova — G5).
"""
from __future__ import annotations

import model
import tablice

IZVOR_SUMNJA = "?"
IZVOR_AI = "ai"


def _svi(sheet, tab: str) -> list[dict]:
    try:
        return tablice.ucitaj(sheet, tab) or []
    except Exception:                                   # noqa: BLE001
        return []


def red_cekanja(sheet, definicija_id: str = "") -> list[dict]:
    """Zadaci koji čekaju profesora: [{pokusaj_id, zadatak_id, odgovor, izvor, bodovi, max}]."""
    did = model.tekst(definicija_id)
    pokusaji_testa = set()
    if did:
        dodjele_testa = {model.tekst(d.get("dodjela_id")) for d in _svi(sheet, tablice.TAB_DODJELE)
                         if model.tekst(d.get("definicija_id")) == did}
        pokusaji_testa = {model.tekst(p.get("pokusaj_id")) for p in _svi(sheet, tablice.TAB_POKUSAJI)
                          if model.tekst(p.get("dodjela_id")) in dodjele_testa}

    izlaz = []
    for r in _svi(sheet, tablice.TAB_OCJENE):
        izvor = model.tekst(r.get("izvor_ocjene")).lower()
        if izvor not in (IZVOR_SUMNJA, IZVOR_AI):
            continue
        pid = model.tekst(r.get("pokusaj_id"))
        if pokusaji_testa and pid not in pokusaji_testa:
            continue
        izlaz.append({
            "pokusaj_id": pid,
            "zadatak_id": model.tekst(r.get("zadatak_id")),
            "odgovor": model.tekst(r.get("odgovor")),
            "izvor": izvor,
            "bodovi": model.broj(r.get("bodovi"), 0),
            "max": model.broj(r.get("max"), 0),
            "komentar": model.tekst(r.get("komentar")),
        })
    izlaz.sort(key=lambda x: (x["pokusaj_id"], x["zadatak_id"]))
    return izlaz


def grupirano(sheet, definicija_id: str = "") -> dict[str, list[dict]]:
    """Isti odgovor → isti redak (profesor jednom odluči za sve identične)."""
    izlaz: dict[str, list[dict]] = {}
    for r in red_cekanja(sheet, definicija_id):
        kljuc = f"{r['zadatak_id']} :: {r['odgovor']}"
        izlaz.setdefault(kljuc, []).append(r)
    return izlaz


def broj_cekanja(sheet, definicija_id: str = "") -> int:
    return len(red_cekanja(sheet, definicija_id))


def potvrdi(sheet, pokusaj_id: str, zadatak_id: str, *, tocno: bool, bodovi=None,
            komentar: str = "", profesor: str = "") -> bool:
    """Profesor potvrđuje/ispravlja zadatak iz reda čekanja (trag + preračun, G5)."""
    import provedba

    return provedba.ocijeni_rucno(sheet, pokusaj_id, zadatak_id, tocno=tocno, bodovi=bodovi,
                                  komentar=komentar, profesor=profesor)
