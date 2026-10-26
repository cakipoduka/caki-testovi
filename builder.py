"""
CAKI testovi v2 — `builder.py`
SLAGANJE TESTA: filtri, stranice po 20/30/40 zadataka i prikaz koji se **stvarno vidi**.

Cakijeva napomena 26.10.2026. (tri stvari koje su falile):
  1. u popisu se vidio **LaTeX kao kod** — mora se prikazati kao formula, sa slikama;
  2. **ne učitavati sve odjednom** (usporava) — učitava se 20/30/40 po stranici;
  3. nedostaju filtri **potpoglavlje** i **biblioteka izvora** (zbirka/udžbenik).

Zato je ovdje sve čisto (bez Streamlita) — pa se testira, a sučelje samo crta.
"""
from __future__ import annotations

import model

VELICINE_STRANICE = (20, 30, 40)
ZADANA_VELICINA = 20


# ------------------------------------------------------------------ filtri

def _kao_lista(vrijednost) -> list[str]:
    """Filter može biti string, lista ili prazno — uvijek vrati listu nepraznih stringova."""
    if vrijednost is None:
        return []
    if isinstance(vrijednost, (list, tuple, set)):
        return [model.tekst(v) for v in vrijednost if model.tekst(v)]
    return [model.tekst(vrijednost)] if model.tekst(vrijednost) else []


def _odgovara(vrijednost, filteri) -> bool:
    """Prazan filter propušta sve; inače vrijednost mora biti među odabranima."""
    odabrano = _kao_lista(filteri)
    if not odabrano:
        return True
    return model.tekst(vrijednost) in odabrano


def filtriraj(zadaci: list[dict], *, tekst: str = "", cjelina="", potpoglavlje="",
              tezina="", tip="", izvor="") -> list[dict]:
    """Filtrira zadatke; svaki filter može biti **jedna vrijednost ili lista** (višestruki izbor).

    Primjer: `filtriraj(zadaci, cjelina=["Linearne", "Razlomci"], tezina=["lako"])`.
    """
    trazeno = model.tekst(tekst).lower()
    izlaz = []
    for z in (zadaci or []):
        if not _odgovara(z.get("cjelina"), cjelina):
            continue
        if not _odgovara(z.get("potpoglavlje"), potpoglavlje):
            continue
        if not _odgovara(z.get("tezina"), tezina):
            continue
        if not _odgovara(z.get("tip"), tip):
            continue
        if not _odgovara(z.get("izvor"), izvor):
            continue
        if trazeno:
            polje = " ".join([model.tekst(z.get("id")), model.tekst(z.get("tekst")),
                              model.tekst(z.get("cjelina")), model.tekst(z.get("potpoglavlje"))])
            if trazeno not in polje.lower():
                continue
        izlaz.append(z)
    return izlaz


def vrijednosti(zadaci: list[dict], polje: str) -> list[str]:
    """Sortirane jedinstvene vrijednosti nekog polja (za padajuće izbornike)."""
    return sorted({model.tekst(z.get(polje)) for z in (zadaci or []) if model.tekst(z.get(polje))})


def potpoglavlja_za(zadaci: list[dict], cjelina="") -> list[str]:
    """Potpoglavlja unutar odabranih cjelina (ili sva, ako cjelina nije odabrana)."""
    odabrane = _kao_lista(cjelina)
    izvor = [z for z in (zadaci or [])
             if not odabrane or model.tekst(z.get("cjelina")) in odabrane]
    return vrijednosti(izvor, "potpoglavlje")


# ------------------------------------------------------------------ stranice

def stranica(zadaci: list[dict], indeks: int, velicina: int = ZADANA_VELICINA) -> dict:
    """Jedna stranica popisa — bez učitavanja svega odjednom.

    Vraća {"zadaci", "stranica", "stranica_ukupno", "od", "do", "ukupno"}.
    """
    svi = list(zadaci or [])
    velicina = int(velicina or ZADANA_VELICINA)
    if velicina not in VELICINE_STRANICE:
        velicina = ZADANA_VELICINA
    ukupno = len(svi)
    stranica_ukupno = max(1, (ukupno + velicina - 1) // velicina)
    index = max(0, min(stranica_ukupno - 1, int(indeks or 0)))
    od = index * velicina
    do = min(ukupno, od + velicina)
    return {
        "zadaci": svi[od:do],
        "stranica": index,
        "stranica_ukupno": stranica_ukupno,
        "od": od + 1 if ukupno else 0,
        "do": do,
        "ukupno": ukupno,
        "velicina": velicina,
    }


def tekst_stranice(info: dict) -> str:
    """„Zadaci 21–40 od 173"."""
    if not info or not info.get("ukupno"):
        return "Nema zadataka za ove filtre."
    return (f"Zadaci **{info['od']}–{info['do']}** od **{info['ukupno']}** "
            f"(stranica {info['stranica'] + 1}/{info['stranica_ukupno']})")


# ------------------------------------------------------------------ prikaz kartice

def oznake(zadatak: dict) -> list[str]:
    """Kratke oznake za karticu: težina, cjelina, bodovi, video…"""
    izlaz = []
    if model.tekst(zadatak.get("cjelina")):
        izlaz.append(model.tekst(zadatak["cjelina"]))
    if model.tekst(zadatak.get("potpoglavlje")):
        izlaz.append(model.tekst(zadatak["potpoglavlje"]))
    if model.tekst(zadatak.get("tezina")):
        izlaz.append("težina: " + model.tekst(zadatak["tezina"]))
    if model.broj(zadatak.get("bodovi")):
        izlaz.append(f"{model.broj(zadatak.get('bodovi')):g} bod.")
    if model.tekst(zadatak.get("tip")) == "visestruki_izbor":
        izlaz.append("višestruki izbor")
    if model.tekst(zadatak.get("slika")):
        izlaz.append("🖼️ slika")
    if model.tekst(zadatak.get("video_url")):
        izlaz.append("🎬 video")
    return izlaz


def naslov_kartice(zadatak: dict) -> str:
    """„Z-0123 · 3 bod. · 2 odgovora" — jednoredni sažetak iznad teksta."""
    dijelovi = [model.tekst(zadatak.get("id")) or "zadatak"]
    if model.broj(zadatak.get("bodovi")):
        dijelovi.append(f"{model.broj(zadatak.get('bodovi')):g} bod.")
    opcije = zadatak.get("opcije") or []
    if opcije:
        dijelovi.append(f"{len(opcije)} ponuđena odgovora")
    return " · ".join(dijelovi)


def kratki_tekst(zadatak: dict, najvise: int = 120) -> str:
    """Tekst zadatka bez LaTeX-a — za pretragu i obični popis."""
    tekst = model.tekst(zadatak.get("tekst"))
    for znak in ("$", "\\(", "\\)", "\\[", "\\]"):
        tekst = tekst.replace(znak, "")
    tekst = " ".join(tekst.split())
    return tekst[:najvise] + ("…" if len(tekst) > najvise else "")


# ------------------------------------------------------------------ provjere

def provjeri_naslov(naslov: str) -> str:
    """Naziv testa je obavezan (Cakijeva napomena: polje prazno, unos obavezan)."""
    if not model.tekst(naslov):
        return "Napiši naziv testa — bez naziva se ne može spremiti ni generirati PDF."
    if len(model.tekst(naslov)) < 3:
        return "Naziv testa je prekratak (najmanje 3 znaka)."
    return ""


def provjeri_odabir(odabrani: list[dict]) -> str:
    """Mora biti barem jedan zadatak i svaki mora imati konačan odgovor."""
    if not odabrani:
        return "Odaberi barem jedan zadatak."
    bez = [model.tekst(z.get("id")) for z in odabrani if not model.tekst(z.get("odgovor"))]
    if bez:
        return ("Ovi zadaci nemaju konačan odgovor u bazi (ne mogu se automatski ocijeniti): "
                + ", ".join(bez[:5]) + (" …" if len(bez) > 5 else ""))
    return ""


def sazetak(odabrani: list[dict]) -> dict:
    """Bodovi i broj zadataka za traku iznad gumba."""
    odabrani = list(odabrani or [])
    bodovi = sum(model.broj(z.get("bodovi"), 1) for z in odabrani)
    return {"zadataka": len(odabrani), "bodova": bodovi,
            "s_videom": sum(1 for z in odabrani if model.tekst(z.get("video_url")))}


# ------------------------------------------------------------------ prikaz: formule i tekst

# Znakovi koji u markdownu nešto znače — izvan formule ih treba escapirati.
SPECIJALNI = {
    "<": "&lt;", ">": "&gt;", "&": "&amp;",
}


def _escape_izvan_formule(dio: str) -> str:
    return "".join(SPECIJALNI.get(z, z) for z in dio)


def pripremi_za_prikaz(tekst) -> str:
    r"""Tekst zadatka spreman za `st.markdown` — formule rade, obični tekst je siguran.

    Preuzeto iz starog buildera (`escape_outside_math`), uz dodatak da \\(…\\) i \\[…\\]
    prvo prebace u `$…$` / `$$…$$` (tako je zapisano u bazi).
    """
    import re

    s = model.tekst(tekst)
    if not s:
        return ""
    s = s.replace("\\(", "$").replace("\\)", "$")
    s = s.replace("\\[", "$$").replace("\\]", "$$")
    dijelovi = re.split(r"(\$\$[^$]*\$\$|\$[^$]*\$)", s)
    izlaz = []
    for i, dio in enumerate(dijelovi):
        if i % 2 == 1:                                  # neparni dio je formula
            izlaz.append(dio)
        else:
            izlaz.append(_escape_izvan_formule(dio))
    return "".join(izlaz)
