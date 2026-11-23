"""
Testovi za Cakijeve prijave od 23.11.2026.:

1. „Ispit sam zatvorio, a učenik nema pristup rješenjima." Uzrok: rok za rješenja gledao je samo
   datum. Učenik dodan na dan testa dobiva rok = dan dodjele, pa mu je rok ostao otvoren i nakon
   zatvaranja. Sada `dodjele.stanje_roka()` poštuje status `zatvoren`/`arhiviran`, a
   `definicije.zatvori_odmah()` postavlja i status.
2. „OBAVEZNO omogućiti brisanje učenika s ispita ako je slučajno dodan." → `dodjele.ukloni_ucenika()`.

Pokreni:  python -m pytest testovi/test_zatvoren_i_uklanjanje.py -q   (iz mape caki-testovi)
"""
from __future__ import annotations

import pathlib
import sys
from datetime import date, timedelta

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import definicije  # noqa: E402
import dodjele  # noqa: E402
import fake_gspread  # noqa: E402
import tablice  # noqa: E402

DANAS = date(2026, 11, 23)
TEST = "T26-0100"


def _sheet(**tabovi) -> fake_gspread.FakeSpreadsheet:
    s = fake_gspread.FakeSpreadsheet()
    for naziv, retci in tabovi.items():
        s.dodaj(naziv, tablice.ZAGLAVLJA[naziv], retci)
    return s


# ------------------------------------------------------------------ 1. zatvoren test

def _def(status="objavljen", rok_od="2026-11-01", rok_do="2026-11-10"):
    return {"definicija_id": TEST, "status": status, "rok_od": rok_od, "rok_do": rok_do}


def test_ucenik_dodan_danas_ima_otvoren_rok_dok_test_nije_zatvoren():
    # pravilo „dodan poslije roka → rok je dan dodjele" i dalje vrijedi
    dodjela = {"dodijeljeno": "2026-11-23T10:00:00"}
    assert dodjele.stanje_roka(dodjela, _def(), danas=DANAS) == "otvoren"


@pytest.mark.parametrize("status", ["zatvoren", "arhiviran"])
def test_zatvoren_test_je_zatvoren_bez_obzira_na_datum(status):
    dodjela = {"dodijeljeno": "2026-11-23T10:00:00"}          # točno Cakijev slučaj
    assert dodjele.stanje_roka(dodjela, _def(status=status), danas=DANAS) == "zatvoren"


def test_zatvoren_test_s_rokom_u_buducnosti_je_zatvoren():
    d = _def(status="zatvoren", rok_od="2026-11-20", rok_do="2026-12-31")
    assert dodjele.stanje_roka({}, d, danas=DANAS) == "zatvoren"


def test_objavljen_test_i_dalje_ovisi_o_datumu():
    d = _def(rok_od="2026-11-20", rok_do="2026-12-31")
    dodjela = {"dodijeljeno": "2026-11-15T09:00:00"}
    assert dodjele.stanje_roka(dodjela, d, danas=DANAS) == "otvoren"
    assert dodjele.stanje_roka(dodjela, d, danas=date(2026, 11, 19)) == "nije_poceo"
    assert dodjele.stanje_roka(dodjela, d, danas=date(2027, 1, 1)) == "zatvoren"


def test_rjesenja_pri_predaji_vidljiva_kad_je_test_zatvoren():
    view = {"rjesenja": "pri_predaji"}
    dodjela = {"dodijeljeno": "2026-11-23T10:00:00"}
    otvoren = dodjele.stanje_roka(dodjela, _def(), danas=DANAS) == "zatvoren"
    zatvoren = dodjele.stanje_roka(dodjela, _def(status="zatvoren"), danas=DANAS) == "zatvoren"
    assert definicije.smije_vidjeti(view, "rjesenja", predano=True, rok_prosao=otvoren) is False
    assert definicije.smije_vidjeti(view, "rjesenja", predano=True, rok_prosao=zatvoren) is True


def test_zatvori_odmah_postavlja_status_i_rok(upis_dozvoljen):
    s = _sheet(Definicije_testova=[{**_def(rok_do="2026-12-31"), "naziv": "Matura A",
                                    "zadaci_json": "[]"}])
    ok, poruka = definicije.zatvori_odmah(s, TEST, korisnik="caki")
    assert ok, poruka
    d = definicije.po_id(s, TEST)
    assert d["status"] == "zatvoren"
    assert d["rok_do"] == (date.today() - timedelta(days=1)).isoformat()
    # i učenik dodan danas sada vidi test kao zatvoren
    assert dodjele.stanje_roka({"dodijeljeno": date.today().isoformat()}, d) == "zatvoren"


def test_zatvori_odmah_ne_vraca_arhivirani_u_zatvoren(upis_dozvoljen):
    s = _sheet(Definicije_testova=[{**_def(status="arhiviran"), "naziv": "Stari",
                                    "zadaci_json": "[]"}])
    definicije.zatvori_odmah(s, TEST)
    assert definicije.po_id(s, TEST)["status"] == "arhiviran"


# ------------------------------------------------------------------ 2. uklanjanje učenika

@pytest.fixture
def baza():
    return _sheet(
        Definicije_testova=[{**_def(), "naziv": "Matura A", "zadaci_json": "[]"}],
        Dodjele_ispita=[
            {"dodjela_id": "D-1", "definicija_id": TEST, "ucenik_id": "OH3229"},   # predao
            {"dodjela_id": "D-2", "definicija_id": TEST, "ucenik_id": "AA1111"},   # slučajno dodan
            {"dodjela_id": "D-3", "definicija_id": "T26-0200", "ucenik_id": "OH3229"},
        ],
        Pokusaji=[
            {"pokusaj_id": "P-1", "dodjela_id": "D-1", "definicija_id": TEST,
             "ucenik_id": "OH3229", "status": "predano"},
            {"pokusaj_id": "P-9", "dodjela_id": "D-3", "definicija_id": "T26-0200",
             "ucenik_id": "OH3229", "status": "predano"},
        ],
        Ocjene_zadataka=[
            {"pokusaj_id": "P-1", "zadatak_id": "Z1"},
            {"pokusaj_id": "P-1", "zadatak_id": "Z2"},
            {"pokusaj_id": "P-9", "zadatak_id": "Z1"},
        ],
        Zalbe=[{"zalba_id": "Ž-1", "pokusaj_id": "P-1", "zadatak_id": "Z1"}],
        Radovi=[{"rad_id": "R-1", "pokusaj_id": "P-1", "naziv": "D.jpg"},
                {"rad_id": "R-2", "pokusaj_id": "P-9", "naziv": "drugi.jpg"}],
        Izmjene_ocjena=[],
        Dnevnik_radnji=[],
    )


def _idovi(s, tab, kljuc):
    return sorted(r.get(kljuc) for r in tablice.ucitaj(s, tab))


def test_ukloni_ucenika_bez_pokusaja(baza, upis_dozvoljen):
    rez = dodjele.ukloni_ucenika(baza, "D-2", korisnik="caki")
    assert rez["uklonjeno"], rez
    assert _idovi(baza, tablice.TAB_DODJELE, "dodjela_id") == ["D-1", "D-3"]


def test_ukloni_ucenika_s_rezultatom_bez_potvrde_odbija(baza, upis_dozvoljen):
    rez = dodjele.ukloni_ucenika(baza, "D-1")
    assert not rez["uklonjeno"] and "rezultat" in rez["razlog"]
    assert "D-1" in _idovi(baza, tablice.TAB_DODJELE, "dodjela_id")
    assert len(tablice.ucitaj(baza, tablice.TAB_OCJENE)) == 3


def test_ukloni_ucenika_s_rezultatom_brise_samo_njegovo(baza, upis_dozvoljen):
    rez = dodjele.ukloni_ucenika(baza, "D-1", s_rezultatom=True, korisnik="caki")
    assert rez["uklonjeno"], rez
    assert rez["brojevi"] == {"ocjene": 2, "izmjene": 0, "zalbe": 1, "radovi": 1, "pokusaji": 1}
    # isti učenik na DRUGOM testu ostaje netaknut
    assert _idovi(baza, tablice.TAB_DODJELE, "dodjela_id") == ["D-2", "D-3"]
    assert _idovi(baza, tablice.TAB_POKUSAJI, "pokusaj_id") == ["P-9"]
    assert _idovi(baza, tablice.TAB_OCJENE, "pokusaj_id") == ["P-9"]
    assert _idovi(baza, tablice.TAB_RADOVI, "rad_id") == ["R-2"]
    assert _idovi(baza, tablice.TAB_ZALBE, "zalba_id") == []
    # trag u dnevniku
    dnevnik = tablice.ucitaj(baza, tablice.TAB_DNEVNIK)
    assert dnevnik and dnevnik[-1]["radnja"] == "uklonjen_ucenik"
    assert "OH3229" in dnevnik[-1]["sto"]


def test_ukloni_nepostojecu_dodjelu(baza, upis_dozvoljen):
    rez = dodjele.ukloni_ucenika(baza, "D-404")
    assert not rez["uklonjeno"] and "ne postoji" in rez["razlog"]


def test_opseg_uklanjanja_samo_broji(baza):
    op = dodjele.opseg_uklanjanja(baza, "D-1")
    assert op == {"dodjela_id": "D-1", "pokusaji": 1, "predano": 1, "ocjene": 2, "izmjene": 0,
                  "zalbe": 1, "radovi": 1, "ima_rezultat": True}
    assert len(tablice.ucitaj(baza, tablice.TAB_OCJENE)) == 3          # ništa nije obrisano
    assert dodjele.opseg_uklanjanja(baza, "D-2")["ima_rezultat"] is False


def test_ukloni_bez_ukljucenog_upisa_ne_brise(baza):
    tablice.postavi_pisanje(False)
    with pytest.raises(PermissionError):
        dodjele.ukloni_ucenika(baza, "D-2")
    assert "D-2" in _idovi(baza, tablice.TAB_DODJELE, "dodjela_id")
