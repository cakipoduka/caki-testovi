"""
Žalba — odgovor profesora (Caki 24.11.2026.):

„Nakon žalbe prof. mora vidjeti žalbu u caki-testovi i moći odgovoriti na nju. Samo jednom, bez
dugačke rasprave; nakon odgovora traži se odluka o bodovima — priznaju se ili ne — i zaključuje
se konačno stanje bodova na tom zadatku." + „Obrazac ‚Žalba na ocjenu' ne treba profesoru."

Pokreni:  python -m pytest testovi/test_zalbe_odgovor.py -q   (iz mape caki-testovi)
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
for _p in (REPO, REPO / "testovi"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import fake_gspread  # noqa: E402
import tablice  # noqa: E402
import zalbe  # noqa: E402

ZADACI = [{"id": "Z8", "tekst": "Brid kocke?", "odgovor": "A", "bodovi": 1,
           "tip": "visestruki_izbor", "opcije": ["24.65 cm", "25 cm", "25.33 cm", "26 cm"]},
          {"id": "Z11", "tekst": "Vrijednost izraza?", "odgovor": "8.8605", "bodovi": 1,
           "tip": "kratki_odgovor"}]


def _sheet(zalbe_retci=()):
    s = fake_gspread.FakeSpreadsheet()
    s.dodaj("Pokusaji", tablice.ZAGLAVLJA["Pokusaji"], [{
        "pokusaj_id": "P1", "dodjela_id": "D1", "definicija_id": "T1", "ucenik_id": "OH3229",
        "predaja": "2026-11-23T10:00:00", "status": "predano", "bodovi": 0, "bodovi_max": 2,
        "odgovori_json": json.dumps({"0": "D", "1": "8.86"}), "zadaci_json": json.dumps(ZADACI)}])
    s.dodaj("Ocjene_zadataka", tablice.ZAGLAVLJA["Ocjene_zadataka"], [
        {"pokusaj_id": "P1", "zadatak_id": "Z8", "redni_broj": 0, "odgovor": "D", "tocno": "ne",
         "bodovi": 0, "max": 1, "izvor_ocjene": "string"},
        {"pokusaj_id": "P1", "zadatak_id": "Z11", "redni_broj": 1, "odgovor": "8.86",
         "tocno": "ne", "bodovi": 0, "max": 1, "izvor_ocjene": "string"}])
    s.dodaj("Zalbe", tablice.ZAGLAVLJA["Zalbe"], list(zalbe_retci))
    s.dodaj("Izmjene_ocjena", tablice.ZAGLAVLJA["Izmjene_ocjena"], [])
    s.dodaj("Dnevnik_radnji", tablice.ZAGLAVLJA["Dnevnik_radnji"], [])
    return s


ZALBA = {"zalba_id": "Z26-0001", "pokusaj_id": "P1", "zadatak_id": "Z11", "ucenik_id": "OH3229",
         "podnesena": "2026-11-24T00:30:00", "razlog": "Zaokružio sam na dvije decimale.",
         "status": "podnesena", "rok_do": "2026-11-28"}


def _zalba(s, zid="Z26-0001"):
    return next(z for z in tablice.ucitaj(s, "Zalbe") if z["zalba_id"] == zid)


def _ocjena(s, zad):
    return next(r for r in tablice.ucitaj(s, "Ocjene_zadataka") if r["zadatak_id"] == zad)


# ------------------------------------------------------------------ pravila

def test_priznaj_daje_pune_bodove_zakljucuje_i_ostavlja_trag(upis_dozvoljen):
    s = _sheet([ZALBA])
    ok, poruka = zalbe.zakljuci(s, "Z26-0001", priznaj=True, odgovor="U redu, priznajem.")
    assert ok, poruka
    z = _zalba(s)
    assert z["status"] == "prihvacena" and z["odgovor"] == "U redu, priznajem."
    assert model_broj(_ocjena(s, "Z11")["bodovi"]) == 1
    [izm] = tablice.ucitaj(s, "Izmjene_ocjena")
    assert izm["povod"] == "zalba" and izm["zadatak_id"] == "Z11"
    p = tablice.ucitaj(s, "Pokusaji")[0]
    assert model_broj(p["bodovi"]) == 1                   # zbroj pokušaja preračunat


def test_ne_priznaj_ostavlja_bodove(upis_dozvoljen):
    s = _sheet([ZALBA])
    ok, _ = zalbe.zakljuci(s, "Z26-0001", priznaj=False, odgovor="Traži se četiri decimale.")
    assert ok
    assert _zalba(s)["status"] == "odbijena"
    assert model_broj(_ocjena(s, "Z11")["bodovi"]) == 0
    assert tablice.ucitaj(s, "Izmjene_ocjena") == []


def test_odgovor_je_obavezan(upis_dozvoljen):
    s = _sheet([ZALBA])
    ok, poruka = zalbe.zakljuci(s, "Z26-0001", priznaj=True, odgovor="  ")
    assert not ok and "odgovor" in poruka
    assert _zalba(s)["status"] == "podnesena"


def test_samo_jednom_bez_rasprave(upis_dozvoljen):
    s = _sheet([ZALBA])
    zalbe.zakljuci(s, "Z26-0001", priznaj=False, odgovor="Ne.")
    ok, poruka = zalbe.zakljuci(s, "Z26-0001", priznaj=True, odgovor="Ipak da.")
    assert not ok and "već zaključena" in poruka
    assert _zalba(s)["status"] == "odbijena"


def test_ucenik_ne_moze_ponovo_nakon_odgovora(upis_dozvoljen):
    s = _sheet([{**ZALBA, "status": "odbijena", "odgovor": "Ne."}])
    p = tablice.ucitaj(s, "Pokusaji")[0]
    smije, zasto = zalbe.moze_podnijeti(s, p, "Z11", sada="2026-11-24")
    assert not smije and "riješena" in zasto
    with pytest.raises(ValueError):
        zalbe.podnesi(s, pokusaj=p, zadatak_id="Z11", razlog="opet", sada="2026-11-24")


def test_prazna_zalba_se_ne_salje(upis_dozvoljen):
    s = _sheet()
    p = tablice.ucitaj(s, "Pokusaji")[0]
    with pytest.raises(ValueError, match="Napiši"):
        zalbe.podnesi(s, pokusaj=p, zadatak_id="Z8", razlog="", sada="2026-11-24")


def test_opis_odluke():
    assert zalbe.opis_odluke({"status": "prihvacena"}) == "bodovi priznati"
    assert zalbe.opis_odluke({"status": "odbijena"}) == "bodovi nisu priznati"
    assert zalbe.opis_odluke({"status": "podnesena"}) == "čeka odgovor"


def model_broj(v):
    import model
    return model.broj(v, 0)


# ------------------------------------------------------------------ pravi Streamlit (AppTest)

APP = '''
import json, sys
sys.path.insert(0, {repo!r}); sys.path.insert(0, {testovi!r})
import streamlit as st
import ekran_ucenika, provedba, tablice
s = st.session_state["_sheet"]
p = tablice.ucitaj(s, "Pokusaji")[0]
ekran_ucenika.prikazi_pregled_rjesenja(
    st, json.loads(p["zadaci_json"]), provedba.odgovori(p), pokazi_rjesenja=True,
    pokazi_video=False, pokazi_bodove=True, sheet=s, pokusaj=p, ucenik_id="OH3229",
    kljuc="t", uloga=st.session_state["_uloga"])
'''


def _app(tmp_path, sheet, uloga):
    from streamlit.testing.v1 import AppTest

    f = tmp_path / "pregled.py"
    f.write_text(APP.format(repo=str(REPO), testovi=str(REPO / "testovi")), encoding="utf-8")
    at = AppTest.from_file(str(f), default_timeout=60)
    at.session_state["_sheet"] = sheet
    at.session_state["_uloga"] = uloga
    return at.run()


def _sve(at):
    return " | ".join([x.value for x in at.caption] + [x.value for x in at.markdown]
                      + [x.value for x in at.warning] + [x.value for x in at.info]
                      + [x.value for x in at.success])


def test_profesor_bez_zalbe_nema_obrasca(tmp_path, upis_dozvoljen):
    at = _app(tmp_path, _sheet(), "profesor")
    assert not at.exception, [str(e.value) for e in at.exception]
    assert not [t for t in at.text_area if "Žalba" in t.label]   # druga slika: obrazac maknut
    assert not at.radio or all("Odluka" not in r.label for r in at.radio)


def test_profesor_vidi_zalbu_odgovara_i_zakljucuje(tmp_path, upis_dozvoljen):
    s = _sheet([ZALBA])
    at = _app(tmp_path, s, "profesor")
    assert not at.exception, [str(e.value) for e in at.exception]
    assert "Zaokružio sam na dvije decimale." in _sve(at)
    [odg] = [t for t in at.text_area if "Odgovor učeniku" in t.label]
    [odl] = [r for r in at.radio if r.label == "Odluka o bodovima"]
    odg.input("Točno je na četiri decimale, ali priznajem.")
    odl.set_value(odl.options[0])                     # ✅ Priznajem bodove (1 b.)
    [b for b in at.button if b.label == "Odgovori i zaključi žalbu"][0].click()
    at.run()
    assert not at.exception, [str(e.value) for e in at.exception]
    assert _zalba(s)["status"] == "prihvacena"
    assert model_broj(_ocjena(s, "Z11")["bodovi"]) == 1
    tekst = _sve(at)
    assert "bodovi priznati" in tekst
    assert not [t for t in at.text_area if "Odgovor učeniku" in t.label]
    # 24.11.: ne zaključava se konačno — postoji gumb za ispravak
    assert [b for b in at.button if b.label == "✏️ Ispravi odgovor ili odluku"]


def test_profesor_bez_odluke_ne_zakljucuje(tmp_path, upis_dozvoljen):
    s = _sheet([ZALBA])
    at = _app(tmp_path, s, "profesor")
    [t for t in at.text_area if "Odgovor učeniku" in t.label][0].input("Ne znam još.")
    [b for b in at.button if b.label == "Odgovori i zaključi žalbu"][0].click()
    at.run()
    assert any("Odaberi odluku" in e.value for e in at.error)
    assert _zalba(s)["status"] == "podnesena"


def test_ucenik_vidi_odgovor_i_odluku(tmp_path, upis_dozvoljen):
    s = _sheet([{**ZALBA, "status": "odbijena", "odgovor": "Traži se četiri decimale."}])
    at = _app(tmp_path, s, "ucenik")
    assert not at.exception, [str(e.value) for e in at.exception]
    tekst = _sve(at)
    assert "Traži se četiri decimale." in tekst and "bodovi nisu priznati" in tekst
    # na Z11 nema novog obrasca; na Z8 (bez žalbe) obrazac postoji
    assert len([t for t in at.text_area if "Žalba" in t.label]) == 1


# ------------------------------------------------------------------ 24.11.: ispravak profesora

def test_ispravak_priznato_u_nepriznato_vraca_bodove(upis_dozvoljen):
    s = _sheet([ZALBA])
    zalbe.zakljuci(s, "Z26-0001", priznaj=True, odgovor="Priznajem.")
    assert model_broj(_ocjena(s, "Z11")["bodovi"]) == 1
    ok, poruka = zalbe.ispravi(s, "Z26-0001", priznaj=False, odgovor="Ipak ne — 4 decimale.")
    assert ok, poruka
    assert _zalba(s)["status"] == "odbijena" and _zalba(s)["odgovor"] == "Ipak ne — 4 decimale."
    assert model_broj(_ocjena(s, "Z11")["bodovi"]) == 0
    assert model_broj(tablice.ucitaj(s, "Pokusaji")[0]["bodovi"]) == 0
    povodi = [r["povod"] for r in tablice.ucitaj(s, "Izmjene_ocjena")]
    assert povodi == ["zalba", "zalba_ispravak"]


def test_ispravak_nepriznato_u_priznato_daje_bodove(upis_dozvoljen):
    s = _sheet([ZALBA])
    zalbe.zakljuci(s, "Z26-0001", priznaj=False, odgovor="Ne.")
    ok, _ = zalbe.ispravi(s, "Z26-0001", priznaj=True, odgovor="Pogledao sam ponovo — da.")
    assert ok and _zalba(s)["status"] == "prihvacena"
    assert model_broj(_ocjena(s, "Z11")["bodovi"]) == 1


def test_ispravak_samo_teksta_ne_dira_bodove(upis_dozvoljen):
    s = _sheet([ZALBA])
    zalbe.zakljuci(s, "Z26-0001", priznaj=False, odgovor="Ne.")
    ok, poruka = zalbe.ispravi(s, "Z26-0001", priznaj=False, odgovor="Ne, traži se 4 decimale.")
    assert ok and "odluka ista" in poruka
    assert tablice.ucitaj(s, "Izmjene_ocjena") == []
    assert _zalba(s)["odgovor"] == "Ne, traži se 4 decimale."


def test_ispravak_zahtijeva_odgovor(upis_dozvoljen):
    s = _sheet([{**ZALBA, "status": "odbijena", "odgovor": "Ne."}])
    ok, poruka = zalbe.ispravi(s, "Z26-0001", priznaj=True, odgovor="")
    assert not ok and _zalba(s)["status"] == "odbijena"


def test_ispravak_kroz_sucelje(tmp_path, upis_dozvoljen):
    s = _sheet([{**ZALBA, "status": "odbijena", "odgovor": "Ne."}])
    at = _app(tmp_path, s, "profesor")
    [b for b in at.button if b.label == "✏️ Ispravi odgovor ili odluku"][0].click()
    at.run()
    [t for t in at.text_area if "Ispravljeni odgovor" in t.label][0].input("Ipak priznajem.")
    odl = [r for r in at.radio if r.label == "Odluka o bodovima"][0]
    odl.set_value(odl.options[0])
    [b for b in at.button if b.label == "Spremi ispravak"][0].click()
    at.run()
    assert not at.exception, [str(e.value) for e in at.exception]
    assert _zalba(s)["status"] == "prihvacena"
    assert model_broj(_ocjena(s, "Z11")["bodovi"]) == 1
