"""
CAKI testovi v2 — `brend.py`
🎨 OVO Caki UREĐUJE — podaci koji idu na svaki izvještaj (promocija firme).

Mijenjaš **samo ovu datoteku** (ili istoimeni ključ u Streamlit Secrets, koji ima prednost).
Ništa drugo u kodu ne treba dirati.

Što se mijenja ovdje:
  · `naziv`   — ime firme/kolektiva na zaglavlju
  · `slogan`  — jedna rečenica ispod imena
  · `web`, `email`, `telefon`, `adresa` — idu u podnožje **svake stranice** izvještaja
  · `boja`    — boja naglaska (hex), koristi se u tablicama i naslovima

Logo: stavi datoteku `caki-testovi/logo.png` (ili `logo.jpg`) — automatski se pojavi u zaglavlju.
Ako je nema, zaglavlje ide bez slike (ništa se ne ruši).

Font za PDF: stavi `caki-testovi/fontovi/DejaVuSans.ttf` (+ `DejaVuSans-Bold.ttf`) — PDF tada
koristi njega (najbolja pokrivenost hrvatskih slova). Ako ga nema, koristi se Vera iz reportlaba.
"""
from __future__ import annotations

import model

PODACI = {
    "naziv": "CAKI — Centar za poduku",
    "slogan": "Pripreme za maturu i razredne ispite",
    "web": "www.cakipoduka.com",
    "email": "info@cakipoduka.com",
    "telefon": "",
    "adresa": "",
    "boja": "#1f4e79",
}

# ključ u Secrets → polje u PODACI (ako Caki želi mijenjati bez diranja koda)
KLJUCEVI = {
    "BREND_NAZIV": "naziv",
    "BREND_SLOGAN": "slogan",
    "BREND_WEB": "web",
    "BREND_EMAIL": "email",
    "BREND_TELEFON": "telefon",
    "BREND_ADRESA": "adresa",
    "BREND_BOJA": "boja",
}


def ucitaj(secrets=None) -> dict:
    """Podaci o brendu: početne vrijednosti iz `PODACI`, prepisane onim što je u Secrets."""
    podaci = dict(PODACI)
    if secrets is not None:
        for kljuc, polje in KLJUCEVI.items():
            try:
                vrijednost = model.tekst(secrets.get(kljuc))
            except Exception:                          # noqa: BLE001 — nema Secrets
                vrijednost = ""
            if vrijednost:
                podaci[polje] = vrijednost
    return podaci


def kontakt_redak(podaci: dict) -> str:
    """Jedan redak za podnožje: web · e-mail · telefon."""
    dijelovi = []
    for polje in ("web", "email", "telefon"):
        vrijednost = model.tekst((podaci or {}).get(polje))
        if vrijednost:
            dijelovi.append(vrijednost)
    return "  ·  ".join(dijelovi)


def logo_putanja(pretraga=None):
    """Vrati `Path` do logotipa ako postoji (`logo.png`, `logo.jpg`, `logo.jpeg`)."""
    from pathlib import Path

    mapa = Path(pretraga) if pretraga else Path(__file__).resolve().parent
    for ime in ("logo.png", "logo.jpg", "logo.jpeg", "logo.PNG", "logo.JPG"):
        put = mapa / ime
        if put.exists():
            return put
    return None


def font_putanje(pretraga=None) -> tuple:
    """Vrati (obični, bold) putanje za DejaVuSans ako su u `fontovi/`; inače (None, None)."""
    from pathlib import Path

    mapa = (Path(pretraga) if pretraga else Path(__file__).resolve().parent) / "fontovi"
    obicni = mapa / "DejaVuSans.ttf"
    bold = mapa / "DejaVuSans-Bold.ttf"
    return (obicni if obicni.exists() else None, bold if bold.exists() else None)
