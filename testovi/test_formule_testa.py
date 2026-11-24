"""
📐 Formule uz test — preneseno iz v1 (Caki 24.11.2026.).

Pokreni:  python -m pytest testovi/test_formule_testa.py -q   (iz mape caki-testovi)
"""
from __future__ import annotations

import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
for _p in (REPO, REPO / "testovi"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import definicije  # noqa: E402
import fake_gspread  # noqa: E402
import formule_testa as F  # noqa: E402
import tablice  # noqa: E402

BAZA = [
    {"formula_id": "F1", "naslov": "Kvadratna jednadžba", "cjelina": "Algebra",
     "paket": "Matura — službene", "tekst_latex": r"x_{1,2}=\frac{-b\pm\sqrt{b^2-4ac}}{2a}",
     "aktivno": "Da"},
    {"formula_id": "F2", "naslov": "Volumen kocke", "cjelina": "Geometrija",
     "paket": "Matura — službene", "tekst_latex": "V=a^3", "aktivno": ""},
    {"formula_id": "F3", "naslov": "Sinusov poučak", "cjelina": "Trigonometrija",
     "paket": "Dodatne", "tekst_latex": r"\frac{a}{\sin\alpha}=2R", "aktivno": "Da"},
    {"formula_id": "F4", "naslov": "Stara", "paket": "Dodatne", "tekst_latex": "x", "aktivno": "Ne"},
]


def test_aktivne_i_paketi():
    assert [f["formula_id"] for f in F.aktivne(BAZA)] == ["F1", "F2", "F3"]
    assert F.paketi(BAZA) == ["Dodatne", "Matura — službene"]


def test_izbor_paket_plus_pojedinacna_bez_duplikata():
    izbor = F.izbor_za_test(BAZA, ["Matura — službene"], ["F1", "F3"])
    assert [f["formula_id"] for f in izbor] == ["F1", "F2", "F3"]
    assert set(izbor[0]) == {"formula_id", "naslov", "cjelina", "paket", "tekst_latex",
                             "datoteka", "opis"}


def test_izbor_sve_ne_uzima_neaktivne():
    assert [f["formula_id"] for f in F.izbor_za_test(BAZA, sve=True)] == ["F1", "F2", "F3"]


def test_json_kruzno_i_trenutni_izbor():
    d = {"formule_json": F.u_json(F.izbor_za_test(BAZA, ["Dodatne"], ["F2"]))}
    assert [f["formula_id"] for f in F.iz_definicije(d)] == ["F2", "F3"]
    assert F.trenutni_izbor(d) == (["Dodatne", "Matura — službene"], ["F2", "F3"])
    assert F.iz_definicije({}) == [] and F.iz_definicije({"formule_json": "pokvareno"}) == []
    assert F.u_json([]) == ""


def test_tekst_formule():
    assert F.tekst_formule({"tekst_latex": "V=a^3"}) == "$$V=a^3$$"
    assert F.tekst_formule({"tekst_latex": "$V=a^3$"}) == "$V=a^3$"


def test_ucitaj_iz_baze():
    s = fake_gspread.FakeSpreadsheet()
    s.dodaj("Formule", list(BAZA[0].keys()), BAZA[:1])
    assert F.ucitaj_iz_baze(s)[0]["formula_id"] == "F1"
    assert F.ucitaj_iz_baze(fake_gspread.FakeSpreadsheet()) == []
    assert F.ucitaj_iz_baze(None) == []


def test_spremanje_u_test_dopise_stupac_koji_tab_nema(upis_dozvoljen):
    """Postojeći tab `Definicije_testova` nema `formule_json` — vrijednost se ne smije izgubiti."""
    staro = [c for c in tablice.ZAGLAVLJA["Definicije_testova"] if c != "formule_json"]
    s = fake_gspread.FakeSpreadsheet()
    s.dodaj("Definicije_testova", staro, [{
        "definicija_id": "T1", "naziv": "Matura A", "status": "objavljen", "zadaci_json": "[]",
        "rok_od": "2026-11-01", "rok_do": "2026-12-31"}])
    s.dodaj("Pokusaji", tablice.ZAGLAVLJA["Pokusaji"], [])
    s.dodaj("Dnevnik_radnji", tablice.ZAGLAVLJA["Dnevnik_radnji"], [])
    d = definicije.po_id(s, "T1")
    ok, razlog = definicije.izmijeni(
        s, d, {"formule_json": F.u_json(F.izbor_za_test(BAZA, ["Dodatne"]))}, korisnik="caki")
    assert ok, razlog
    d2 = definicije.po_id(s, "T1")
    assert [f["formula_id"] for f in F.iz_definicije(d2)] == ["F3"]
    assert d2["naziv"] == "Matura A"                    # ostali podaci netaknuti


APP = '''
import json, sys
sys.path.insert(0, {repo!r}); sys.path.insert(0, {testovi!r})
import streamlit as st
import ekran_ucenika
zadaci = [{{"id": "Z1", "tekst": "Koliko je $2+2$?", "odgovor": "4", "bodovi": 1,
           "tip": "kratki_odgovor"}}]
definicija = {{"definicija_id": "T1", "naziv": "Matura A", "zadaci_json": json.dumps(zadaci),
              "trajanje_min": 60, "formule_json": st.session_state["_formule"]}}
ekran_ucenika.prikazi(st, None, definicija, {{"dodjela_id": "D1", "ucenik_id": "OH3229"}},
                      dry=True)
'''


def _app(tmp_path, formule_json):
    from streamlit.testing.v1 import AppTest

    f = tmp_path / "rjesavanje.py"
    f.write_text(APP.format(repo=str(REPO), testovi=str(REPO / "testovi")), encoding="utf-8")
    at = AppTest.from_file(str(f), default_timeout=60)
    at.session_state["_formule"] = formule_json
    return at.run()


def test_ucenik_vidi_formule_tijekom_testa(tmp_path):
    at = _app(tmp_path, F.u_json(F.izbor_za_test(BAZA, ["Matura — službene"])))
    assert not at.exception, [str(e.value) for e in at.exception]
    tekst = " | ".join(m.value for m in at.markdown)
    assert "**Kvadratna jednadžba** · *Algebra*" in tekst and "$$V=a^3$$" in tekst


def test_bez_formula_nema_gumba(tmp_path):
    at = _app(tmp_path, "")
    assert not at.exception, [str(e.value) for e in at.exception]
    assert "Kvadratna" not in " | ".join(m.value for m in at.markdown)
