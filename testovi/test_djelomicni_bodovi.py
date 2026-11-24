"""
✏️ Ispravak ocjene s djelomičnim bodovima — kao v1 „Provjera i ispravak ocjena" (Caki 24.11.2026.).

Pokreni:  python -m pytest testovi/test_djelomicni_bodovi.py -q   (iz mape caki-testovi)
"""
from __future__ import annotations

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
for _p in (REPO, REPO / "testovi"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import model  # noqa: E402
import provedba  # noqa: E402
import tablice  # noqa: E402
import test_zalbe_odgovor as tz  # noqa: E402


def _o(s, zad):
    return tz._ocjena(s, zad)


def test_djelomicno_upise_bodove_i_preracuna(upis_dozvoljen):
    s = tz._sheet()
    ok, poruka = provedba.ocijeni_odlukom(s, "P1", "Z11", "djelomicno", bodovi="0,5", maks=1,
                                          komentar="Postupak dobar, zaokruživanje ne.")
    assert ok, poruka
    r = _o(s, "Z11")
    assert model.broj(r["bodovi"]) == 0.5 and r["tocno"] == "Ne" and r["izvor_ocjene"] == "profesor"
    assert r["komentar"] == "Postupak dobar, zaokruživanje ne."
    assert model.broj(tablice.ucitaj(s, "Pokusaji")[0]["bodovi"]) == 0.5
    [izm] = tablice.ucitaj(s, "Izmjene_ocjena")
    assert model.broj(izm["bodovi_poslije"]) == 0.5


def test_tocno_i_netocno(upis_dozvoljen):
    s = tz._sheet()
    assert provedba.ocijeni_odlukom(s, "P1", "Z8", "tocno", maks=1)[0]
    assert model.broj(_o(s, "Z8")["bodovi"]) == 1
    assert provedba.ocijeni_odlukom(s, "P1", "Z8", "netocno", maks=1)[0]
    assert model.broj(_o(s, "Z8")["bodovi"]) == 0


def test_djelomicno_izvan_granica_odbija(upis_dozvoljen):
    s = tz._sheet()
    for b in ("0", "1", "1,5", "abc"):
        ok, _ = provedba.ocijeni_odlukom(s, "P1", "Z11", "djelomicno", bodovi=b, maks=1)
        assert not ok, b
    assert tablice.ucitaj(s, "Izmjene_ocjena") == []
    assert not provedba.ocijeni_odlukom(s, "P1", "Z11", "", maks=1)[0]


def _app(tmp_path, s, uloga):
    return tz._app(tmp_path, s, uloga)


def test_profesor_daje_djelomicno_kroz_sucelje(tmp_path, upis_dozvoljen):
    s = tz._sheet()
    at = _app(tmp_path, s, "profesor")
    assert not at.exception, [str(e.value) for e in at.exception]
    odl = at.radio(key="t_1_odl_Z11")
    odl.set_value("djelomicno")
    at.number_input(key="t_1_bod_Z11").set_value(0.5)
    at.text_input(key="t_1_kom_Z11").input("Pola boda za postupak.")
    [b for b in at.button if b.label == "💾 Spremi ocjenu"][1].click()
    at.run()
    assert not at.exception, [str(e.value) for e in at.exception]
    assert model.broj(_o(s, "Z11")["bodovi"]) == 0.5
    labels = [e.label for e in at.expander]
    assert "Zadatak 2 — 🟡 djelomično · 0.5/1 boda" in labels


def test_samo_komentar_bez_promjene_odluke(tmp_path, upis_dozvoljen):
    s = tz._sheet()
    provedba.ocijeni_odlukom(s, "P1", "Z11", "djelomicno", bodovi=0.5, maks=1)
    at = _app(tmp_path, s, "profesor")
    at.text_input(key="t_1_kom_Z11").input("Novi komentar.")
    [b for b in at.button if b.label == "💾 Spremi ocjenu"][1].click()
    at.run()
    r = _o(s, "Z11")
    assert model.broj(r["bodovi"]) == 0.5 and r["komentar"] == "Novi komentar."


def test_ucenik_vidi_djelomicno_ali_nema_obrasca(tmp_path, upis_dozvoljen):
    s = tz._sheet()
    provedba.ocijeni_odlukom(s, "P1", "Z11", "djelomicno", bodovi=0.5, maks=1,
                             komentar="Pola boda za postupak.")
    at = _app(tmp_path, s, "ucenik")
    assert not at.exception, [str(e.value) for e in at.exception]
    assert "Zadatak 2 — 🟡 djelomično · 0.5/1 boda" in [e.label for e in at.expander]
    assert not [b for b in at.button if b.label == "💾 Spremi ocjenu"]
    assert any("Pola boda za postupak." in i.value for i in at.info)
