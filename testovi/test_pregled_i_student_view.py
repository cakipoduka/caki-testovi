"""
Testovi za pregled riješenog testa (učenik) i za uređivanje Student Viewa po testu.

**Cakijev zahtjev 20.11.2026.:** „Nakon testa učenik bi trebao vidjeti ponovo zadatke s testa jer
neće upamtiti svaki zadatak; ako mu se prikažu samo rješenja i krivi odgovori nema potpunu sliku.
Slike + matematika renderirana s punim tekstom i ponuđenim odgovorima."

Prije je pregled davao samo „Tvoj odgovor: B" i „Točno: C" — bez teksta opcija i bez slike, pa
učenik nije znao što je B uopće bio. Ovdje se provjerava da pregled nosi i jedno i drugo, i da
ništa od toga ne procuri prije nego Student View dopusti rješenja.

Pokreni:  python -m pytest testovi/test_pregled_i_student_view.py -q   (iz mape caki-testovi)
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import definicije  # noqa: E402
import fake_gspread  # noqa: E402
import rjesavanje  # noqa: E402
import tablice  # noqa: E402

TEST_ID = "T26-0007"


def zadatak_izbor(**polja) -> dict:
    """Zamrznuti zadatak s višestrukim izborom, kakav ga `banka.zadatak_iz_retka()` radi."""
    z = {
        "id": "Z-101",
        "tekst": r"Odredi predznak diskriminante \(D = b^2 - 4ac\).",
        "tip": "visestruki_izbor",
        "opcije": ["D > 0 i a > 0", "D > 0 i a < 0", "D < 0 i a > 0", "D = 0 i a < 0"],
        "odgovor": "C",
        "bodovi": 2,
        "slika": "parabola_01.png",
    }
    z.update(polja)
    return z


# ================================================================== opcije_pregleda

def test_opcije_dobivaju_slova_redom():
    opcije = rjesavanje.opcije_pregleda(zadatak_izbor(), "", pokazi_rjesenje=True)
    assert [o["slovo"] for o in opcije] == ["A", "B", "C", "D"]
    assert opcije[2]["tekst"] == "D < 0 i a > 0"


def test_oznacen_je_i_moj_i_tocan_odgovor():
    opcije = rjesavanje.opcije_pregleda(zadatak_izbor(), "B", pokazi_rjesenje=True)
    moje = [o["slovo"] for o in opcije if o["moja"]]
    tocne = [o["slovo"] for o in opcije if o["tocna"]]
    assert moje == ["B"]
    assert tocne == ["C"]


def test_moj_odgovor_je_ujedno_tocan():
    opcije = rjesavanje.opcije_pregleda(zadatak_izbor(), "C", pokazi_rjesenje=True)
    pogodak = [o for o in opcije if o["moja"]]
    assert len(pogodak) == 1
    assert pogodak[0]["tocna"] is True


def test_bez_rjesenja_se_tocan_odgovor_ne_odaje():
    """Dok Student View ne dopusti rješenja, pregled ne smije reći koji je točan."""
    opcije = rjesavanje.opcije_pregleda(zadatak_izbor(), "B", pokazi_rjesenje=False)
    assert opcije, "opcije se i dalje prikazuju — učenik mora vidjeti što je bilo ponuđeno"
    assert all(o["tocna"] is False for o in opcije)
    assert [o["slovo"] for o in opcije if o["moja"]] == ["B"]


def test_kratki_odgovor_nema_opcija():
    z = zadatak_izbor(tip="kratki_odgovor", opcije=[])
    assert rjesavanje.opcije_pregleda(z, "3/a", pokazi_rjesenje=True) == []


def test_jedna_opcija_se_ne_broji_kao_izbor():
    z = zadatak_izbor(opcije=["samo jedna"])
    assert rjesavanje.opcije_pregleda(z, "A", pokazi_rjesenje=True) == []


def test_bez_odgovora_nijedna_opcija_nije_moja():
    opcije = rjesavanje.opcije_pregleda(zadatak_izbor(), "", pokazi_rjesenje=True)
    assert not any(o["moja"] for o in opcije)


def test_malo_slovo_odgovora_se_prihvaca():
    """Sprema se slovo; mala/velika slova ne smiju promijeniti ishod."""
    opcije = rjesavanje.opcije_pregleda(zadatak_izbor(), "b", pokazi_rjesenje=True)
    assert [o["slovo"] for o in opcije if o["moja"]] == ["B"]


# ================================================================== pregled_zadatka

def test_pregled_nosi_sliku_i_opcije():
    red = rjesavanje.pregled_zadatka(zadatak_izbor(), "B", pokazi_rjesenje=True,
                                     pokazi_video=False, pokazi_bodove=True)
    assert red["slika"] == "parabola_01.png"
    assert len(red["opcije"]) == 4
    assert red["tip"] == "visestruki_izbor"
    assert red["tekst"].startswith("Odredi predznak")


def test_pregled_daje_tekst_tocne_opcije():
    """„Točno: C" bez teksta ne znači ništa — zato i `tocan_tekst`."""
    red = rjesavanje.pregled_zadatka(zadatak_izbor(), "B", pokazi_rjesenje=True,
                                     pokazi_video=False, pokazi_bodove=True)
    assert red["tocan_odgovor"] == "C"
    assert red["tocan_tekst"] == "D < 0 i a > 0"


def test_pregled_bez_rjesenja_ne_daje_tekst_tocne():
    red = rjesavanje.pregled_zadatka(zadatak_izbor(), "B", pokazi_rjesenje=False,
                                     pokazi_video=False, pokazi_bodove=True)
    assert red["tocan_odgovor"] == ""
    assert red["tocan_tekst"] == ""
    assert red["opcije"], "ponuđeni odgovori ostaju vidljivi i bez rješenja"


def test_pregled_oznacava_prazan_odgovor():
    assert rjesavanje.pregled_zadatka(zadatak_izbor(), "", pokazi_rjesenje=True,
                                      pokazi_video=False, pokazi_bodove=True)["bez_odgovora"]
    assert not rjesavanje.pregled_zadatka(zadatak_izbor(), "B", pokazi_rjesenje=True,
                                          pokazi_video=False,
                                          pokazi_bodove=True)["bez_odgovora"]


def test_pregled_zadrzava_stara_polja():
    """Postojeći pozivatelji (app.py, stranica učenika) ne smiju se slomiti."""
    red = rjesavanje.pregled_zadatka(zadatak_izbor(), "B", pokazi_rjesenje=True,
                                     pokazi_video=True, pokazi_bodove=True,
                                     izvor_ocjene="?")
    for kljuc in ("tekst", "moj_odgovor", "tocan_odgovor", "pokazi_rjesenje", "video",
                  "pokazi_video", "pokazi_bodove", "izvor_ocjene", "ceka_profesora"):
        assert kljuc in red, kljuc
    assert red["ceka_profesora"] is True


# ================================================================== Student View: upis

@pytest.fixture
def baza():
    s = fake_gspread.FakeSpreadsheet()
    s.dodaj(tablice.TAB_DEFINICIJE, tablice.ZAGLAVLJA[tablice.TAB_DEFINICIJE], [
        {"definicija_id": TEST_ID, "naziv": "Kvadratna jednadžba", "status": "zatvoren",
         "zadaci_json": "[]", "student_view_json": ""},
    ])
    s.dodaj(tablice.TAB_DODJELE, tablice.ZAGLAVLJA[tablice.TAB_DODJELE], [
        {"dodjela_id": "D-1", "definicija_id": TEST_ID, "ucenik_id": "U1"}])
    s.dodaj(tablice.TAB_POKUSAJI, tablice.ZAGLAVLJA[tablice.TAB_POKUSAJI], [])
    s.dodaj(tablice.TAB_DNEVNIK, tablice.ZAGLAVLJA[tablice.TAB_DNEVNIK], [])
    return s


def _definicija(sheet) -> dict:
    return sheet.kao_objekti(tablice.TAB_DEFINICIJE)[0]


def test_postavi_student_view_sprema(baza, upis_dozvoljen):
    ok, poruka = definicije.postavi_student_view(
        baza, _definicija(baza), {"rjesenja": "nikad"}, korisnik="caki")
    assert ok is True, poruka
    spremljeno = json.loads(_definicija(baza)["student_view_json"])
    assert spremljeno["rjesenja"] == "nikad"


def test_djelomicna_izmjena_ne_brise_ostalo(baza, upis_dozvoljen):
    definicije.postavi_student_view(baza, _definicija(baza), {"rjesenja": "nikad"})
    definicije.postavi_student_view(baza, _definicija(baza), {"video": "uvijek"})
    spremljeno = json.loads(_definicija(baza)["student_view_json"])
    assert spremljeno["rjesenja"] == "nikad"
    assert spremljeno["video"] == "uvijek"
    for resurs in definicije.RESURSI:
        assert resurs in spremljeno


def test_sto_vidi_cita_ono_sto_je_zapisano(baza, upis_dozvoljen):
    definicije.postavi_student_view(baza, _definicija(baza), {"pdf": "nikad"})
    redci = definicije.sto_vidi(_definicija(baza)["student_view_json"])
    pdf = next(r for r in redci if r["kljuc"] == "pdf")
    assert pdf["stupanj"] == "nikad"


def test_nepoznat_resurs_se_odbija(baza, upis_dozvoljen):
    ok, razlog = definicije.postavi_student_view(baza, _definicija(baza), {"ocjene": "uvijek"})
    assert ok is False
    assert "Nepoznat resurs" in razlog
    assert _definicija(baza)["student_view_json"] == ""


def test_nepoznata_razina_se_odbija(baza, upis_dozvoljen):
    ok, razlog = definicije.postavi_student_view(baza, _definicija(baza),
                                                 {"rjesenja": "ponekad"})
    assert ok is False
    assert "Nepoznata razina" in razlog
    assert _definicija(baza)["student_view_json"] == ""


def test_arhiviran_test_se_ne_mijenja(baza, upis_dozvoljen, monkeypatch):
    d = dict(_definicija(baza), status="arhiviran")
    ok, razlog = definicije.postavi_student_view(baza, d, {"rjesenja": "uvijek"})
    assert ok is False
    assert "arhiv" in razlog.lower()


def test_pokusaji_ne_blokiraju(baza, upis_dozvoljen, monkeypatch):
    """Otvoriti rješenja nakon isteka roka normalan je posao, i kad su testovi već pisani."""
    monkeypatch.setattr(definicije, "pokusaji_testa",
                        lambda sheet, did: [{"pokusaj_id": "PK-1"}])
    ok, poruka = definicije.postavi_student_view(
        baza, _definicija(baza), {"rjesenja": "uvijek"}, korisnik="caki")
    assert ok is True, poruka
    assert json.loads(_definicija(baza)["student_view_json"])["rjesenja"] == "uvijek"


def test_bez_id_a(baza, upis_dozvoljen):
    ok, razlog = definicije.postavi_student_view(baza, {"naziv": "bez id"}, {"pdf": "nikad"})
    assert ok is False
    assert "ID" in razlog


def test_upis_ostavlja_trag(baza, upis_dozvoljen):
    definicije.postavi_student_view(baza, _definicija(baza), {"pdf": "nikad"}, korisnik="caki")
    dnevnik = baza.kao_objekti(tablice.TAB_DNEVNIK)
    assert len(dnevnik) == 1
    assert dnevnik[0]["radnja"] == "student_view"
    assert dnevnik[0]["sto"] == TEST_ID
    assert "pdf=nikad" in dnevnik[0]["detalj"]


def test_student_view_nije_u_meta_poljima():
    """`izmijeni()` ga i dalje ne smije upisivati bez provjere."""
    assert "student_view_json" not in definicije.META_POLJA


# ================================================================== statička provjera

@pytest.fixture(scope="module")
def app_izvor() -> str:
    return (REPO / "app.py").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def ekran_izvor() -> str:
    return (REPO / "ekran_ucenika.py").read_text(encoding="utf-8")


def test_app_sprema_student_view(app_izvor):
    assert "definicije.postavi_student_view(" in app_izvor


def test_pregled_crta_sliku_i_opcije(ekran_izvor):
    tijelo = ekran_izvor[ekran_izvor.find("def prikazi_pregled_rjesenja"):]
    assert "slike_zadataka.prikazi_sliku_html" in tijelo, "slika se ne crta u pregledu"
    assert 'red["opcije"]' in tijelo, "ponuđeni odgovori se ne crtaju u pregledu"
    assert "Ponuđeni odgovori" in tijelo


def test_pregled_ima_filtar_i_otvaranje(ekran_izvor):
    tijelo = ekran_izvor[ekran_izvor.find("def prikazi_pregled_rjesenja"):]
    assert "Netočni (" in tijelo
    assert "Otvori sve zadatke" in tijelo
