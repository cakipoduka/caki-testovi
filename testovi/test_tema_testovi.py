"""
Testovi za `tema_testovi.py` i za novi raspored kartice 🧪 Testovi (popis lijevo, detalj desno).

Raspored je složen po mockupu „CAKI Testovi v2" (Cakijeva odluka 20.11.2026.). Ovdje se provjerava
ono što se može provjeriti bez pokrenutog Streamlita: čiste funkcije koje grade HTML, i statička
svojstva `app.py`.

Pokreni:  python -m pytest testovi/test_tema_testovi.py -q   (iz mape caki-testovi)
"""
from __future__ import annotations

import ast
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import definicije  # noqa: E402
import tema_testovi as tt  # noqa: E402


# ================================================================== status → natpis

def test_svako_stanje_ima_natpis():
    """Ako se doda novo stanje u `definicije.STANJA`, mora dobiti i natpis za čovjeka."""
    for stanje in definicije.STANJA:
        assert stanje in tt.STATUS_CHIP, f"stanje `{stanje}` nema natpis u STATUS_CHIP"


def test_natpisi_nisu_sirovi_podaci():
    """UX pravilo 5: korisnik vidi „Zatvoren", nikad `zatvoren`."""
    for stanje, (natpis, _) in tt.STATUS_CHIP.items():
        assert natpis != stanje
        assert natpis[:1].isupper()


@pytest.mark.parametrize("stanje,ocekivano", [
    ("nacrt", ("Nacrt", "")),
    ("objavljen", ("Objavljen", "g")),
    ("zatvoren", ("Zatvoren", "b")),
    ("arhiviran", ("Arhiviran", "o")),
])
def test_status_natpis(stanje, ocekivano):
    assert tt.status_natpis(stanje) == ocekivano


def test_status_natpis_podnosi_smece():
    assert tt.status_natpis("  ZATVOREN ") == ("Zatvoren", "b")
    assert tt.status_natpis("") == ("—", "")
    assert tt.status_natpis(None) == ("—", "")
    assert tt.status_natpis("nepoznato") == ("nepoznato", "")


# ================================================================== HTML pomoćnici

def test_stavka_escapira_naziv():
    """Naziv testa upisuje čovjek; `<` u njemu ne smije razbiti popis."""
    izlaz = tt.stavka(naziv="Kut <90° i ampersand &", oznaka="T26-0007",
                      status_html='<span class="kc-chip">Zatvoren</span>',
                      meta="24 zadatka")
    assert "&lt;90°" in izlaz and "&amp;" in izlaz
    assert "<90°" not in izlaz
    assert '<span class="kc-chip">Zatvoren</span>' in izlaz   # čip prolazi kao HTML


def test_stavka_bez_dodatka_ne_crta_prazan_redak():
    assert 'class="st ' not in tt.stavka("N", "T-1", "", "meta")
    assert 'class="st g"' in tt.stavka("N", "T-1", "", "meta", dodatak="12 predano",
                                       dodatak_boja="g")


def test_naslov_escapira_i_propusta_cipove():
    izlaz = tt.naslov("Test <b>x</b>", "T26-0007", '<span class="kc-chip">Nacrt</span>')
    assert "&lt;b&gt;" in izlaz
    assert '<span class="kc-chip">Nacrt</span>' in izlaz
    assert "T26-0007" in izlaz


def test_naslov_prazan_naziv():
    assert "—" in tt.naslov("", "T-1", "")


def test_brojevi():
    izlaz = tt.brojevi((24, "zadataka"), (48, "bodova"), (12, "pokušaja"))
    assert izlaz.count("<div><b>") == 3
    assert "<b>24</b><span>zadataka</span>" in izlaz


def test_brojevi_bez_parova():
    assert tt.brojevi() == '<div class="tt-brojevi"></div>'


@pytest.mark.parametrize("vrsta", ["b", "o", "c"])
def test_poruka_vrste(vrsta):
    assert f'tt-poruka {vrsta}' in tt.poruka(vrsta, "tekst")


def test_poruka_nepoznata_vrsta_pada_na_plavu():
    assert "tt-poruka b" in tt.poruka("ljubicasta", "tekst")


def test_poruka_propusta_html_pozivatelja():
    """Poruke redovito sadrže <b> i nazive stupaca; escapiranje je na pozivatelju."""
    assert "<b>Zadaci</b>" in tt.poruka("b", "<b>Zadaci</b> su zaključani")


def test_prazno_escapira():
    izlaz = tt.prazno("Nema <ničega>", "Idi u 🧱 Složi test")
    assert "&lt;ničega&gt;" in izlaz
    assert "Složi test" in izlaz


def test_primijeni_ubacuje_css(monkeypatch):
    ubaceno = []
    monkeypatch.setattr(tt.st, "markdown",
                        lambda s, **kw: ubaceno.append((s, kw)))
    tt.primijeni()
    assert len(ubaceno) == 1
    sadrzaj, kw = ubaceno[0]
    assert kw.get("unsafe_allow_html") is True
    assert "tt-stavka" in sadrzaj and "tt-brojevi" in sadrzaj


def test_css_ne_dira_zajednicku_temu():
    """`caki_tema.py` je ista datoteka u četiri repoa — ovaj dodatak ne smije mijenjati njezine
    varijable, samo dodavati svoje (`--tt-*`)."""
    for varijabla in ("--kc-blue:", "--kc-ink:", "--kc-bg:"):
        assert varijabla not in tt.CSS, f"{varijabla} se redefinira u tema_testovi"
    assert "--tt-crvena:" in tt.CSS


# ================================================================== app.py (statička provjera)

@pytest.fixture(scope="module")
def app_izvor() -> str:
    return (REPO / "app.py").read_text(encoding="utf-8")


def test_app_se_parsira(app_izvor):
    ast.parse(app_izvor)


def test_app_koristi_dodatnu_temu(app_izvor):
    assert "import tema_testovi" in app_izvor
    assert "tema_testovi.primijeni()" in app_izvor
    # dodatak ide POSLIJE zajedničke teme, inače ga ona pregazi
    assert app_izvor.find("tema.primijeni()") < app_izvor.find("tema_testovi.primijeni()")


def test_popis_i_detalj_su_dva_stupca(app_izvor):
    assert "_lijevo, _desno = st.columns([2, 3]" in app_izvor


def test_popis_crta_kartice_s_odabirom(app_izvor):
    """Odabrana kartica dobiva drugi ključ, da je CSS može istaknuti."""
    assert "tt_{'odabran' if _odabran_x else 'stavka'}_" in app_izvor
    assert 'st.session_state.__setitem__' in app_izvor


def test_stari_selectbox_je_uklonjen(app_izvor):
    """Odabir je sada u popisu; stari `selectbox` ne smije ostati kao drugi put do istog."""
    assert 'key="v2_l_test"' not in app_izvor
    assert "Odaberi test za radnje" not in app_izvor


def test_prazno_stanje_govori_sto_napraviti(app_izvor):
    assert "tema_testovi.prazno(" in app_izvor
    assert "Još nema nijednog testa" in app_izvor


def test_statusi_idu_kroz_natpise(app_izvor):
    """Nigdje u kartici ne smije pisati sirovi status iz baze."""
    assert "tema_testovi.status_natpis(" in app_izvor
