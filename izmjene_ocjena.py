"""
CAKI testovi v2 — `izmjene_ocjena.py`
📝 IZMJENE OCJENA (append-only) — trag svake promjene ocjene, uključujući žalbu.

Cakijeva/Claudeova odluka 30.10.2026. (MASTER §12.10 + §12.11.2): `_upisi_rucno` je **prepisivao**
automatsku ocjenu i brisao trag (izvor: string/SymPy/AI). Ova tablica čuva **svaku** izmjenu.

Shema (sve novo, nijedna postojeća tablica se ne dira):
    izmjena_id · pokusaj_id · zadatak_id · ocjena_prije · ocjena_poslije
    bodovi_prije · bodovi_poslije · izvor_prije · razlog · povod · tko · kada

  · ključ je **`zadatak_id`** (ne `redni_broj`) — isto kako `provedba._upisi_rucno` traži redak,
  · `izvor_prije` čuva odakle je ocjena došla PRIJE ispravke (GDPR čl. 22 trag),
  · `povod` = `zalba` | `profesor_sam_primijetio` (§12.10).
"""
from __future__ import annotations

import model
import tablice

TAB_IZMJENE = "Izmjene_ocjena"

ZAGLAVLJE = [
    "izmjena_id", "pokusaj_id", "zadatak_id",
    "ocjena_prije", "ocjena_poslije",
    "bodovi_prije", "bodovi_poslije",
    "izvor_prije", "razlog", "povod", "tko", "kada",
]

POVOD_ZALBA = "zalba"
POVOD_PROFESOR = "profesor_sam_primijetio"


def _svi(sheet) -> list[dict]:
    try:
        return tablice.ucitaj(sheet, TAB_IZMJENE) or []
    except Exception:                                   # noqa: BLE001
        return []


def zapisi(sheet, *, pokusaj_id: str, zadatak_id: str,
           ocjena_prije: bool | None = None, ocjena_poslije: bool | None = None,
           bodovi_prije=None, bodovi_poslije=None,
           izvor_prije: str = "", razlog: str = "", povod: str = POVOD_PROFESOR,
           tko: str = "") -> dict:
    """Upiši JEDNU izmjenu (append-only — nikad se ne mijenja ni briše)."""
    if not model.tekst(pokusaj_id) or not model.tekst(zadatak_id):
        raise ValueError("Izmjena mora imati `pokusaj_id` i `zadatak_id`.")

    red = {
        "izmjena_id": tablice.novi_id([model.tekst(r.get("izmjena_id")) for r in _svi(sheet)],
                                      "I26-"),
        "pokusaj_id": model.tekst(pokusaj_id),
        "zadatak_id": model.tekst(zadatak_id),
        "ocjena_prije": "" if ocjena_prije is None else ("da" if ocjena_prije else "ne"),
        "ocjena_poslije": "" if ocjena_poslije is None else ("da" if ocjena_poslije else "ne"),
        "bodovi_prije": "" if bodovi_prije is None else bodovi_prije,
        "bodovi_poslije": "" if bodovi_poslije is None else bodovi_poslije,
        "izvor_prije": model.tekst(izvor_prije),
        "razlog": model.tekst(razlog),
        "povod": model.tekst(povod) or POVOD_PROFESOR,
        "tko": model.tekst(tko),
        "kada": model.sada_iso(),
    }
    tablice.dodaj(sheet, TAB_IZMJENE, [red])
    return red


def za_pokusaj(sheet, pokusaj_id: str) -> list[dict]:
    """Sve izmjene jednog pokušaja, kronološki."""
    pid = model.tekst(pokusaj_id)
    return sorted([r for r in _svi(sheet) if model.tekst(r.get("pokusaj_id")) == pid],
                  key=lambda r: model.tekst(r.get("kada")))


def za_zadatak(sheet, pokusaj_id: str, zadatak_id: str) -> list[dict]:
    """Povijest ocjene jednog zadatka u pokušaju (za žalbu i za obranu od prigovora)."""
    pid, zid = model.tekst(pokusaj_id), model.tekst(zadatak_id)
    return [r for r in za_pokusaj(sheet, pid) if model.tekst(r.get("zadatak_id")) == zid]


def zadnji_izvor(sheet, pokusaj_id: str, zadatak_id: str) -> str:
    """Odakle je ocjena došla prije prve izmjene (npr. `sympy`, `ai`, `string`)."""
    povijest = za_zadatak(sheet, pokusaj_id, zadatak_id)
    return model.tekst(povijest[0].get("izvor_prije")) if povijest else ""


def osiguraj(sheet) -> bool:
    """Napravi tab ako ga nema (samo uz uključeno pisanje)."""
    try:
        tablice.osiguraj(sheet, TAB_IZMJENE)
        return True
    except Exception:                                   # noqa: BLE001
        return False
