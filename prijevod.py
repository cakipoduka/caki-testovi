"""
CAKI testovi v2 — `prijevod.py`
🌐 PRIJEVOD ODABRANIH ZADATAKA (bez diranja baze) — online test i PDF na engleskom.

Cakijeva odluka 28.10.2026.: učenik radi na engleskom; prevode se **samo odabrani zadaci**, prijevod
**NE ide u bazu** (`Zadaci` se ne mijenja). Prijevod se drži **uz definiciju testa**, može se
**pregledati i ispraviti prije objave**, a učenik ga vidi samo ako je test objavljen s jezikom `en`.

Ključna pravila (zaštita od „AI izmisli"):
  · **LaTeX se ne dira** — formule ostaju identične (provjera: isti broj `$`, `\\frac`, `\\sqrt`…),
  · **brojevi ostaju isti** — ako se promijeni broj, prijevod se označi kao sumnjiv,
  · ako prijevoda nema → prikazuje se original (nikad prazno).
"""
from __future__ import annotations

import model
import ocjenjivanje

PRAVILA = (
    "Ti si prevoditelj matematičkih zadataka sa hrvatskog na engleski.\n"
    "STROGA PRAVILA:\n"
    "1. NE mijenjaj LaTeX: sve između $...$ i naredbe poput \\frac, \\sqrt, \\left, \\right ostaju "
    "identične.\n"
    "2. NE mijenjaj brojeve, mjerne jedinice ni ponuđene odgovore (samo riječi).\n"
    "3. Prevedi prirodnim engleskim koji koriste udžbenici matematike.\n"
    "4. Vrati ISKLJUČIVO JSON: {\"tekst_en\": \"...\", \"opcije_en\": [\"...\"]}\n"
)

ZAMJENE = {"tekst": "tekst_en", "opcije": "opcije_en"}


# ------------------------------------------------------------------ priprema

def stavke_za_prijevod(zadaci: list[dict]) -> list[dict]:
    """Što treba prevesti: id, tekst i opcije (samo ono što postoji)."""
    izlaz = []
    for z in (zadaci or []):
        zid = model.tekst(z.get("id"))
        if not zid:
            continue
        izlaz.append({
            "id": zid,
            "tekst": model.tekst(z.get("tekst")),
            "opcije": [model.tekst(o) for o in (z.get("opcije") or []) if model.tekst(o)],
        })
    return izlaz


def sastavi_upit(zadatak: dict) -> list[dict]:
    """Poruke za AI: pravila + tekst i opcije."""
    sadrzaj = (
        f"TEKST:\n{model.tekst(zadatak.get('tekst'))}\n\n"
        f"OPCIJE:\n" + "\n".join(f"{chr(65 + i)}) {o}" for i, o in
                                 enumerate(zadatak.get("opcije") or []))
    )
    return [{"role": "system", "content": PRAVILA}, {"role": "user", "content": sadrzaj}]


# ------------------------------------------------------------------ provjera kvalitete

def _latex_dijelovi(tekst) -> list[str]:
    """Sve LaTeX naredbe i formule — moraju preživjeti prijevod."""
    import re

    s = model.tekst(tekst)
    return (re.findall(r"\$[^$]*\$", s)
            + re.findall(r"\\[a-zA-Z]+", s))


def _brojevi(tekst) -> list[str]:
    import re

    return re.findall(r"\d+[.,]?\d*", model.tekst(tekst))


def provjeri(original: dict, prijevod: dict) -> list[str]:
    """Vrati popis problema (prazno = prijevod izgleda ispravno)."""
    problemi = []
    if not model.tekst((prijevod or {}).get("tekst_en")):
        problemi.append("Nema engleskog teksta.")
        return problemi

    a, b = _latex_dijelovi(original.get("tekst")), _latex_dijelovi(prijevod.get("tekst_en"))
    if a != b:
        problemi.append(f"LaTeX se promijenio: {len(a)} → {len(b)} dijelova.")

    brojevi_a = _brojevi(original.get("tekst"))
    brojevi_b = _brojevi(prijevod.get("tekst_en"))
    if sorted(brojevi_a) != sorted(brojevi_b):
        problemi.append(f"Brojevi se razlikuju: {brojevi_a} → {brojevi_b}")

    opcije = original.get("opcije") or []
    opcije_en = (prijevod or {}).get("opcije_en") or []
    if opcije and len(opcije) != len(opcije_en):
        problemi.append(f"Broj opcija: {len(opcije)} → {len(opcije_en)}")
    return problemi


# ------------------------------------------------------------------ primjena

def primijeni(zadatak: dict, prijeslov: dict) -> dict:
    """Vrati kopiju zadatka s engleskim tekstom (ako postoji prijevod)."""
    z = dict(zadatak or {})
    p = prijeslov or {}
    if model.tekst(p.get("tekst_en")):
        z["tekst"] = model.tekst(p["tekst_en"])
        z["tekst_izvorni"] = model.tekst(zadatak.get("tekst"))
    opcije_en = [model.tekst(o) for o in (p.get("opcije_en") or []) if model.tekst(o)]
    if opcije_en and len(opcije_en) >= 2:
        z["opcije"] = opcije_en
    return z


def primijeni_na_sve(zadaci: list[dict], prijevodi: dict) -> list[dict]:
    """Svaki zadatak zamijeni engleskim tekstom gdje prijevod postoji (inače ostaje hrvatski)."""
    prijevodi = prijevodi or {}
    return [primijeni(z, prijevodi.get(model.tekst(z.get("id")))) for z in (zadaci or [])]


def jezik_definicije(definicija: dict) -> str:
    """`hr` (zadano) ili `en` — odluka profesora pri objavi."""
    return "en" if model.tekst((definicija or {}).get("jezik")).lower() == "en" else "hr"


# ------------------------------------------------------------------ AI poziv

def prevedi(zadaci: list[dict], *, kljuc: str, tajna: str, pozovi=None) -> tuple[dict, list]:
    """Prevedi zadatke. Vraća (prijevodi, greske). `pozovi(poruke, kljuc, tajna)` je injektabilan."""
    import json

    prijevodi, greske = {}, []
    for stavka in stavke_za_prijevod(zadaci):
        try:
            if pozovi is None:
                import ai_pomoc

                odgovor, greska = ai_pomoc.pitaj(sastavi_upit(stavka), kljuc=kljuc, tajna=tajna)
            else:
                odgovor, greska = pozovi(sastavi_upit(stavka), kljuc, tajna)
        except Exception as e:                          # noqa: BLE001
            odgovor, greska = "", f"{type(e).__name__}: {e}"
        if greska or not odgovor:
            greske.append(f"{stavka['id']}: {greska or 'prazan odgovor'}")
            continue
        try:
            podaci = json.loads(odgovor[odgovor.index("{"):odgovor.rindex("}") + 1])
        except Exception:                               # noqa: BLE001
            greske.append(f"{stavka['id']}: odgovor nije JSON")
            continue
        problemi = provjeri(stavka, podaci)
        if problemi:
            greske.append(f"{stavka['id']}: " + "; ".join(problemi))
        prijevodi[stavka["id"]] = podaci
    return prijevodi, greske
