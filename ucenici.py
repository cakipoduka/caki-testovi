"""
CAKI testovi v2 — `ucenici.py`
🔎 PRETRAGA UČENIKA U CRM-u + dodjela testa po učeniku (Cakijeva želja 28.10.2026.).

Zašto: do sada se test dodjeljivao upisom **šifre** (TEST01). Caki želi **pretražiti CRM bazu učenika**
(ime, email, grupa) i dodijeliti test točno odabranom učeniku — bez ručnog traženja šifre.

Ovo je čisto slaganje povrh postojećeg: `dodjele.dodaj` (idempotentno) + `tablice.ucitaj`.
Ne dira shemu; čita CRM tab `Ucenici` (i `Učenici`, ako je tako zapisan).
"""
from __future__ import annotations

import model

# Nazivi taba u CRM-u kroz vrijeme (čita se prvi koji postoji)
TABOVI_UCENIKA = ("Ucenici", "Učenici", "Studenti")

# Stupci po kojima se traži (imena kroz vrijeme)
POLJA_IMENA = ("ime", "ime_prezime", "ucenik", "naziv")
POLJA_EMAILA = ("email", "e_mail", "mail")
POLJA_GRUPE = ("grupa", "grupe", "razred", "skupina")
POLJA_ID = ("ucenik_id", "id", "sifra_ucenika", "šifra")


def _prvo(redak: dict, polja) -> str:
    for ime in polja:
        vrijednost = model.tekst(redak.get(ime))
        if vrijednost:
            return vrijednost
    return ""


def _normal(tekst) -> str:
    """Mala slova bez dijakritika — da „Marić" nađe i „maric"."""
    s = model.tekst(tekst).lower()
    for a, b in (("č", "c"), ("ć", "c"), ("ž", "z"), ("š", "s"), ("đ", "d")):
        s = s.replace(a, b)
    return " ".join(s.split())


def tab_ucenika(sheet) -> str:
    """Koji tab s učenicima postoji u CRM Sheetu (prazno = nema)."""
    try:
        imena = {model.tekst(w.title) for w in sheet.worksheets()}
    except Exception:                                  # noqa: BLE001
        return ""
    for kandidat in TABOVI_UCENIKA:
        if kandidat in imena:
            return kandidat
    return ""


def ucitaj_ucenike(sheet) -> list[dict]:
    """Svi učenici iz CRM-a kao [{ucenik_id, ime, email, grupa, sirovo}]."""
    import tablice

    tab = tab_ucenika(sheet)
    if not tab:
        return []
    izlaz = []
    for redak in tablice.ucitaj(sheet, tab) or []:
        ime = _prvo(redak, POLJA_IMENA)
        if not ime:
            continue
        izlaz.append({
            "ucenik_id": _prvo(redak, POLJA_ID),
            "ime": ime,
            "ime_djeteta": ime,
            "email": _prvo(redak, POLJA_EMAILA),
            "grupa": _prvo(redak, POLJA_GRUPE),
            "sirovo": redak,
        })
    return izlaz


def pretrazi(ucenici: list[dict], upit: str) -> list[dict]:
    """Tolerantna pretraga: svaka riječ upita mora se naći u imenu, emailu ili grupi."""
    rijeci = [_normal(r) for r in model.tekst(upit).split() if model.tekst(r)]
    if not rijeci:
        return list(ucenici or [])
    izlaz = []
    for u in ucenici or []:
        polje = _normal(" ".join([model.tekst(u.get("ime")), model.tekst(u.get("email")),
                                  model.tekst(u.get("grupa"))]))
        if all(r in polje for r in rijeci):
            izlaz.append(u)
    return izlaz


def dodijeli_test(sheet, definicija: dict, ucenici_odabrani: list[dict],
                  korisnik: str = "") -> tuple[int, list]:
    """Dodijeli test odabranim učenicima (preko `dodjele.dodaj`). Vraća (broj novih, greške)."""
    import dodjele

    if not (definicija or {}).get("definicija_id"):
        return 0, ["Nedostaje definicija testa."]
    if not ucenici_odabrani:
        return 0, ["Nije odabran nijedan učenik."]

    # `dodjele.dodaj` traži šifre učenika; ako je nema, koristimo ime kao šifru (jedinstveno u praksi)
    sifre = []
    for u in ucenici_odabrani:
        sifra = model.tekst(u.get("ucenik_id")) or model.tekst(u.get("email")) or model.tekst(u.get("ime"))
        if sifra:
            sifre.append(sifra)

    try:
        rezultat = dodjele.dodaj(sheet, definicija, sifre, dodijelio=korisnik)
    except TypeError:
        rezultat = dodjele.dodaj(sheet, definicija, sifre)
    except Exception as e:                             # noqa: BLE001
        return 0, [f"{type(e).__name__}: {e}"]

    # `dodjele.dodaj` vraća dict: {"dodano": int, "preskoceno": [...], "dodjele": [...]}
    if isinstance(rezultat, dict):
        return int(rezultat.get("dodano") or 0), []
    if isinstance(rezultat, (list, tuple, set)):
        return len(rezultat), []
    return int(rezultat or 0), []
