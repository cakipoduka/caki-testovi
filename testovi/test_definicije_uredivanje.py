"""
Testovi za odblokiranje uređivanja testa i za arhivu (biblioteka predložaka).

Pokriva ono što je Caki 20.11.2026. prijavio kao blokadu:
  · test bez ijednog pokušaja mora se moći mijenjati i NAKON što rok počne,
  · test S pokušajima mora dopustiti okvirne podatke (naziv, rok, trajanje, AI), a ne zadatke,
  · arhiva mora biti povratna (`vrati_iz_arhive`), inače su uvezeni v1 testovi zaključani zauvijek,
  · u `app.py`: `_status_l` mora biti postavljen prije upotrebe (prije je bio NameError).

Pokreni (iz mape `caki-testovi`):  python -m pytest testovi -q
"""
from __future__ import annotations

import ast
import pathlib
import sys

import pytest

# Testovi su unutar repoa (dogovor 20.11.2026.), pa je korijen repoa jedna razina iznad.
# Put u `sys.path` postavlja `conftest.py` u ovoj mapi; ovdje ga drzimo za citanje `app.py`.
REPO = pathlib.Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import definicije  # noqa: E402
import tablice     # noqa: E402

DANAS = "2026-11-20"
POKUSAJ_PREDAN = {"pokusaj_id": "PK-0001", "dodjela_id": "D-1", "status": "predan",
                  "predaja": "2026-10-30T10:00:00"}


def napravi(**polja) -> dict:
    """Definicija testa s razumnim zadanim vrijednostima."""
    d = {"definicija_id": "T26-0001", "naziv": "Kvadratna jednadžba", "predmet": "matematika",
         "status": "objavljen", "rok_od": "2026-10-29", "rok_do": "2026-12-01",
         "trajanje_min": 45, "ai_pomoc": "ne", "zadaci_json": "[]"}
    d.update(polja)
    return d


@pytest.fixture
def bez_pokusaja(monkeypatch):
    monkeypatch.setattr(definicije, "pokusaji_testa", lambda sheet, did: [])


@pytest.fixture
def s_pokusajem(monkeypatch):
    monkeypatch.setattr(definicije, "pokusaji_testa", lambda sheet, did: [POKUSAJ_PREDAN])


@pytest.fixture
def upisi(monkeypatch):
    """Hvata pozive `tablice.azuriraj` umjesto da piše u Sheet."""
    zapisano = []
    monkeypatch.setattr(tablice, "azuriraj",
                        lambda sheet, tab, kljuc, vrijednost, polja: zapisano.append(
                            (tab, vrijednost, dict(polja))) or True)
    monkeypatch.setattr(tablice, "zapisi_radnju",
                        lambda *a, **k: None)
    return zapisano


# ------------------------------------------------------------------ smije_urediti (ZADACI)

def test_rok_pocinje_a_nitko_nije_otvorio_smije(bez_pokusaja):
    """OVO je bila Cakijeva blokada: „Rok je počeo 29.10.2026."""
    smije, razlog = definicije.smije_urediti(None, napravi(), danas=DANAS)
    assert smije is True
    assert "⚠️" in razlog and "nitko nije otvorio" in razlog


def test_pokusaj_zaklju_cava_zadatke(s_pokusajem):
    smije, razlog = definicije.smije_urediti(None, napravi(), danas=DANAS)
    assert smije is False
    assert "pokušaja" in razlog


def test_arhiviran_se_ne_mijenja(bez_pokusaja):
    smije, razlog = definicije.smije_urediti(None, napravi(status="arhiviran"), danas=DANAS)
    assert smije is False
    assert "arhiviran" in razlog.lower()


def test_nacrt_i_zatvoren_bez_pokusaja_smiju(bez_pokusaja):
    for status in ("nacrt", "zatvoren"):
        smije, _ = definicije.smije_urediti(None, napravi(status=status), danas=DANAS)
        assert smije is True, status


def test_rok_jos_nije_pocneo_smije(bez_pokusaja):
    smije, razlog = definicije.smije_urediti(
        None, napravi(rok_od="2026-12-05", rok_do="2026-12-10"), danas=DANAS)
    assert smije is True
    assert "nije počeo" in razlog


# ------------------------------------------------------------------ smije_urediti_metapodatke

def test_meta_s_pokusajima_smije_uz_upozorenje(s_pokusajem):
    smije, razlog = definicije.smije_urediti_metapodatke(None, napravi())
    assert smije is True
    assert "⚠️" in razlog and "ne zadaci" in razlog


def test_meta_arhiviran_ne_smije(s_pokusajem):
    smije, razlog = definicije.smije_urediti_metapodatke(None, napravi(status="arhiviran"))
    assert smije is False
    assert "arhiv" in razlog.lower()


def test_meta_polja_ne_sadrze_zadatke():
    assert "zadaci_json" not in definicije.META_POLJA
    for polje in ("naziv", "trajanje_min", "rok_od", "rok_do", "ai_pomoc", "status"):
        assert polje in definicije.META_POLJA


# ------------------------------------------------------------------ izmijeni()

def test_izmijeni_prolazi_i_kad_test_ima_pokusaje(s_pokusajem, upisi):
    ok, razlog = definicije.izmijeni(None, napravi(), {"rok_do": "2026-12-20"}, korisnik="caki")
    assert ok is True, razlog
    assert upisi and upisi[0][2] == {"rok_do": "2026-12-20"}


def test_izmijeni_ne_prolazi_za_arhivirani(s_pokusajem, upisi):
    ok, razlog = definicije.izmijeni(None, napravi(status="arhiviran"), {"naziv": "Novo"})
    assert ok is False
    assert not upisi
    assert "arhiv" in razlog.lower()


def test_izmijeni_odbacuje_zadatke(s_pokusajem, upisi):
    ok, razlog = definicije.izmijeni(None, napravi(), {"zadaci_json": "[{}]"})
    assert ok is False
    assert not upisi
    assert "dopuštenih polja" in razlog


def test_izmijeni_prazan_naziv_ne(s_pokusajem, upisi):
    ok, _ = definicije.izmijeni(None, napravi(), {"naziv": "   "})
    assert ok is False
    assert not upisi


# ------------------------------------------------------------------ arhiva

@pytest.fixture
def arhiva(monkeypatch):
    """Jedan test u Sheetu; `promijeni_status` mijenja status u mjestu."""
    stanje = {"d": napravi(status="zatvoren")}
    monkeypatch.setattr(definicije, "po_id", lambda sheet, did: stanje["d"])

    def _status(sheet, did, novo, *, korisnik=""):
        stanje["d"] = dict(stanje["d"], status=novo)
        return True

    monkeypatch.setattr(definicije, "promijeni_status", _status)
    return stanje


def test_arhiviraj_postavlja_status(arhiva):
    ok, razlog = definicije.arhiviraj(None, "T26-0001", korisnik="caki")
    assert ok is True
    assert arhiva["d"]["status"] == "arhiviran"
    assert "predložak" in razlog


def test_arhiviraj_dvaput_ne(arhiva):
    definicije.arhiviraj(None, "T26-0001")
    ok, razlog = definicije.arhiviraj(None, "T26-0001")
    assert ok is False
    assert "već" in razlog


def test_vrati_iz_arhive_daje_zatvoren(arhiva):
    definicije.arhiviraj(None, "T26-0001")
    ok, razlog = definicije.vrati_iz_arhive(None, "T26-0001", korisnik="caki")
    assert ok is True
    assert arhiva["d"]["status"] == "zatvoren"
    assert "Objavi" in razlog


def test_vrati_iz_arhive_pa_se_smije_urediti(arhiva, monkeypatch):
    """Cijeli put: uvezeni v1 test (arhiviran) → iz arhive → uređivanje otvoreno."""
    monkeypatch.setattr(definicije, "pokusaji_testa", lambda sheet, did: [])
    definicije.arhiviraj(None, "T26-0001")
    assert definicije.smije_urediti(None, arhiva["d"], danas=DANAS)[0] is False
    definicije.vrati_iz_arhive(None, "T26-0001")
    assert definicije.smije_urediti(None, arhiva["d"], danas=DANAS)[0] is True


def test_vrati_samo_iz_arhive(arhiva):
    ok, razlog = definicije.vrati_iz_arhive(None, "T26-0001")
    assert ok is False
    assert "nije u arhivi" in razlog


def test_vrati_ne_objavljuje(arhiva):
    definicije.arhiviraj(None, "T26-0001")
    ok, razlog = definicije.vrati_iz_arhive(None, "T26-0001", novi_status="objavljen")
    assert ok is False
    assert arhiva["d"]["status"] == "arhiviran"


def test_arhiviran_je_u_stanjima():
    assert "arhiviran" in definicije.STANJA


# ------------------------------------------------------------------ app.py (statička provjera)

@pytest.fixture(scope="module")
def app_izvor() -> str:
    return (REPO / "app.py").read_text(encoding="utf-8")


def test_app_se_parsira(app_izvor):
    ast.parse(app_izvor)


def test_status_l_postavljen_prije_upotrebe(app_izvor):
    """Prije 20.11.2026. `_status_l` je bio samo korišten → NameError na gumbu Deaktiviraj."""
    postavljanje = app_izvor.find("_status_l = model.tekst")
    prva_upotreba = app_izvor.find('_status_l == "objavljen"')
    assert postavljanje != -1, "_status_l se nigdje ne postavlja"
    assert 0 < postavljanje < prva_upotreba


def test_app_zove_arhivu_i_uredivanje_sadrzaja(app_izvor):
    for poziv in ("definicije.arhiviraj(", "definicije.vrati_iz_arhive(",
                  "definicije.smije_urediti_metapodatke(", "_u_slozi_test("):
        assert poziv in app_izvor, poziv


def test_app_ima_filtar_arhive(app_izvor):
    assert 'key="v2_l_arhiva"' in app_izvor


def test_u_slozi_test_puni_slagalicu(app_izvor):
    """Gumb za uređivanje sadržaja mora pisati u isti ključ koji slagalica čita."""
    tijelo = app_izvor[app_izvor.find("def _u_slozi_test"):]
    tijelo = tijelo[:tijelo.find("def _je_kopija")]
    assert 'st.session_state["v2p_odabrani"]' in tijelo
    assert 'tema.idi_na("tv", "🧱 Složi test")' in tijelo
