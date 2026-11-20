"""
Zdravlje koda: nijedna datoteka ne smije koristiti naziv koji nigdje nije postavljen.

**Zašto ovaj test postoji.** `app.py` je jedna duga skripta koju Streamlit izvodi od vrha prema
dnu; Python ne provjerava nazive dok redak stvarno ne dođe na red. Zato krivo napisano ime
varijable živi mjesecima i pukne tek kad netko otvori baš taj blok. Dosad su tako nađena tri
slučaja:

  · `_status_l` — bio korišten, nigdje postavljen (gumb Deaktiviraj/Aktiviraj), 20.11.2026.
  · `_odabir_r` — ispravno se zove `odabir_r`; dva gumba „⬇ CSV" u kartici 📊 Rezultati rušila
    su svoj blok pri svakom crtanju, 20.11.2026.
  · `_odabir_l` u karticama gdje nije postavljen — v. `test_brisanje_i_arhiva.py`.

Provjera traje djelić sekunde i hvata cijelu tu vrstu greške odjednom.

Treba `pyflakes` (u `requirements-dev.txt`). Ako nije instaliran, test se preskače, da
nepotpuno okruženje ne ruši ostatak paketa.

Pokreni:  python -m pytest testovi/test_zdravlje_koda.py -q   (iz mape caki-testovi)
"""
from __future__ import annotations

import io
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# Datoteke koje nisu naše (font, tex predlošci) ili se ne izvode kao modul.
PRESKOCI = {"__init__.py"}


def _moduli() -> list[pathlib.Path]:
    """Sve .py datoteke repoa: korijen, `pages/` i `testovi/`."""
    nadjene = sorted(REPO.glob("*.py")) + sorted(REPO.glob("pages/*.py")) \
        + sorted((REPO / "testovi").glob("*.py"))
    return [p for p in nadjene if p.name not in PRESKOCI]


def _nedefinirani(putanja: pathlib.Path) -> list[str]:
    """Poruke pyflakesa o nazivima koji se koriste, a nigdje ne postavljaju."""
    from pyflakes import api, reporter

    izlaz, greske = io.StringIO(), io.StringIO()
    api.check(putanja.read_text(encoding="utf-8"), str(putanja),
              reporter.Reporter(izlaz, greske))
    return [red for red in izlaz.getvalue().splitlines() if "undefined name" in red]


def test_pronadjeni_su_moduli():
    """Osigurava da test nešto stvarno provjerava — prazan popis bi uvijek prolazio."""
    imena = {p.name for p in _moduli()}
    assert "app.py" in imena
    assert "definicije.py" in imena
    assert len(imena) > 20


# Već poznato, čeka popravak — da test čuva od NOVIH slučajeva umjesto da stalno crveni.
# Kad se neki popravi, briše se odavde; test tada traži da popis bude točan.
POZNATO = {
    # `sve_stavke_dolari_neuparene()` nigdje ne postoji. Zove se iz provjere neuparenih znakova
    # `$` u LaTeXu, i to samo za zadatke sa `stavke` (skupine a, b, c). Za popravak treba
    # NAPISATI tu funkciju, pa nije dirano uz isporuku 20.11. — v. UPDATE_20-11_kartica_testovi.
    "tex_test.py": {"sve_stavke_dolari_neuparene"},
}


def _ime_naziva(poruka: str) -> str:
    """Iz `datoteka.py:186:43: undefined name 'x'` izvuci `x`."""
    return poruka.rsplit("'", 2)[-2] if "'" in poruka else poruka


def test_nema_novih_nedefiniranih_naziva():
    pytest.importorskip("pyflakes", reason="instaliraj: pip install -r requirements-dev.txt")
    novi = []
    for putanja in _moduli():
        dopusteno = POZNATO.get(putanja.name, set())
        for red in _nedefinirani(putanja):
            if _ime_naziva(red) not in dopusteno:
                novi.append(red)
    assert not novi, ("nazivi koji se koriste, a nigdje se ne postavljaju:\n"
                      + "\n".join(novi))


def test_poznati_slucajevi_jos_postoje():
    """Kad se poznati slučaj popravi, mora nestati i s popisa — inače popis laže."""
    pytest.importorskip("pyflakes", reason="instaliraj: pip install -r requirements-dev.txt")
    po_datoteci = {p.name: {_ime_naziva(r) for r in _nedefinirani(p)} for p in _moduli()}
    for datoteka, nazivi in POZNATO.items():
        rijeseni = nazivi - po_datoteci.get(datoteka, set())
        assert not rijeseni, (f"`{datoteka}`: {', '.join(sorted(rijeseni))} je popravljen — "
                              "obriši ga iz POZNATO u ovom testu")
