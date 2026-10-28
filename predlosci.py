"""
CAKI testovi v2 — `predlosci.py`
📁 PREDLOŠCI TESTA i NACRT — **isti tabovi i isti format kao v1** (`TestBuilder_predlosci`,
`TestBuilder_draft`), da Caki može spremiti u jednoj aplikaciji i učitati u drugoj.

ZA SLJEDEĆEG AGENTA:
  · `sadrzaj_json` je popis **zamrznutih zadataka** (isti oblik koji drži `definicije.zadaci`).
  · Predložak = imenovani odabir; nacrt = jedan automatski zapis (nastavlja se gdje se stalo).
  · Sve funkcije su čiste (bez Streamlita) — UI ih samo zove.
"""
from __future__ import annotations

import json

import model
import tablice

TAB_PREDLOSCI = "TestBuilder_predlosci"
TAB_NACRT = "TestBuilder_draft"

# PREUZETO iz v1 (`2_test_builder.py`) — zaglavlja MORAJU biti identična
PREDLOSCI_HEADERS = ["predlozak_id", "naziv", "datum_spremanja", "naslov_dokumenta",
                     "tip_dokumenta", "prikazi_rjesenja", "broj_zadataka", "sadrzaj_json"]
DRAFT_HEADERS = ["draft_id", "zadnja_izmjena", "naslov_dokumenta", "tip_dokumenta",
                 "prikazi_rjesenja", "broj_zadataka", "sadrzaj_json"]


def _svi(sheet, tab: str) -> list[dict]:
    try:
        return tablice.ucitaj(sheet, tab)
    except Exception:                                  # noqa: BLE001 — taba još nema
        return []


def _json(zadaci) -> str:
    return json.dumps(list(zadaci or []), ensure_ascii=False)


def _iz_jsona(tekst) -> list:
    try:
        podaci = json.loads(model.tekst(tekst) or "[]")
        return podaci if isinstance(podaci, list) else []
    except Exception:                                  # noqa: BLE001
        return []


# ------------------------------------------------------------------ predlošci

def predlosci(sheet) -> list[dict]:
    """Svi spremljeni predlošci, najnoviji prvi."""
    redci = _svi(sheet, TAB_PREDLOSCI)
    return sorted(redci, key=lambda r: model.tekst(r.get("datum_spremanja")), reverse=True)


def novi_id(predlosci_: list[dict]) -> str:
    return tablice.novi_id([model.tekst(r.get("predlozak_id")) for r in predlosci_ or []], "P26-")


def spremi_predlozak(sheet, *, naziv: str, zadaci: list[dict], naslov_dokumenta: str = "",
                     tip_dokumenta: str = "", prikazi_rjesenja: bool = False) -> dict:
    """Spremi odabir kao imenovani predložak (isti oblik kao v1)."""
    naziv = model.tekst(naziv)
    if not naziv:
        raise ValueError("Predložak treba naziv.")
    if not zadaci:
        raise ValueError("Predložak ne može biti prazan.")
    postojeci = predlosci(sheet)
    red = {
        "predlozak_id": novi_id(postojeci),
        "naziv": naziv,
        "datum_spremanja": model.sada_iso(),
        "naslov_dokumenta": model.tekst(naslov_dokumenta),
        "tip_dokumenta": model.tekst(tip_dokumenta),
        "prikazi_rjesenja": "da" if prikazi_rjesenja else "ne",
        "broj_zadataka": len(zadaci),
        "sadrzaj_json": _json(zadaci),
    }
    tablice.dodaj(sheet, TAB_PREDLOSCI, [red])
    return red


def ucitaj_predlozak(sheet, predlozak_id: str) -> dict:
    """Vrati {"zadaci", "naslov_dokumenta", "tip_dokumenta", "prikazi_rjesenja"} ili prazno."""
    for r in predlosci(sheet):
        if model.tekst(r.get("predlozak_id")) == model.tekst(predlozak_id):
            return {
                "naziv": model.tekst(r.get("naziv")),
                "zadaci": _iz_jsona(r.get("sadrzaj_json")),
                "naslov_dokumenta": model.tekst(r.get("naslov_dokumenta")),
                "tip_dokumenta": model.tekst(r.get("tip_dokumenta")),
                "prikazi_rjesenja": model.tekst(r.get("prikazi_rjesenja")).lower() in ("da", "1", "true"),
            }
    return {}


def obrisi_predlozak(sheet, predlozak_id: str) -> bool:
    return tablice.obrisi(sheet, TAB_PREDLOSCI, "predlozak_id", model.tekst(predlozak_id))


# ------------------------------------------------------------------ nacrt (jedan zapis)

def nacrt(sheet) -> dict:
    """Zadnji spremljeni nacrt (nastavak rada) ili prazno."""
    redci = _svi(sheet, TAB_NACRT)
    if not redci:
        return {}
    zadnji = max(redci, key=lambda r: model.tekst(r.get("zadnja_izmjena")))
    return {
        "draft_id": model.tekst(zadnji.get("draft_id")),
        "zadaci": _iz_jsona(zadnji.get("sadrzaj_json")),
        "naslov_dokumenta": model.tekst(zadnji.get("naslov_dokumenta")),
        "tip_dokumenta": model.tekst(zadnji.get("tip_dokumenta")),
        "prikazi_rjesenja": model.tekst(zadnji.get("prikazi_rjesenja")).lower() in ("da", "1", "true"),
    }


def spremi_nacrt(sheet, *, zadaci: list[dict], naslov_dokumenta: str = "",
                 tip_dokumenta: str = "", prikazi_rjesenja: bool = False) -> bool:
    """Jedan upis nacrta (kao v1 `_spremi_nacrt`) — nikad ne blokira rad ako padne."""
    try:
        redci = _svi(sheet, TAB_NACRT)
        red = {
            "draft_id": model.tekst((redci[0] if redci else {}).get("draft_id")) or "D26-0001",
            "zadnja_izmjena": model.sada_iso(),
            "naslov_dokumenta": model.tekst(naslov_dokumenta),
            "tip_dokumenta": model.tekst(tip_dokumenta),
            "prikazi_rjesenja": "da" if prikazi_rjesenja else "ne",
            "broj_zadataka": len(zadaci or []),
            "sadrzaj_json": _json(zadaci),
        }
        if redci:
            tablice.azuriraj(sheet, TAB_NACRT, "draft_id", red["draft_id"], red)
        else:
            tablice.dodaj(sheet, TAB_NACRT, [red])
        return True
    except Exception:                                  # noqa: BLE001 — nacrt ne ruši rad
        return False
