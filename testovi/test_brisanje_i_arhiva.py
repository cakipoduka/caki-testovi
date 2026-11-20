"""
Testovi za brisanje testa (s rezultatima i bez njih) i za radnje nad više testova iz arhive.

Pokriva Cakijev zahtjev od 20.11.2026. — „OBRIŠI TESTOVE iz arhive i baze, opcija obriši i
rezultate DA/NE" — i tri defekta nađena pri provjeri postojećeg koda:

  1. `Statistika_zadataka` se nije brisala (uvjet je tražio stupac `statistika_id`, kojeg taj
     tab nema), pa su redci ostajali kao siročići.
  2. `Pokusaji` su se brisali po `definicija_id`, koji smije biti prazan — zato `pokusaji_testa()`
     i traži preko `dodjela_id`. Takav pokušaj brisanje bi promašilo.
  3. `Dnevnik_radnji` je dobivao prazan redak, jer se pisalo ključevima `radnja_id`/`kada`/`tko`/
     `detalji`, a tab ima `kad`/`korisnik`/`radnja`/`sto`/`detalj`.

I jedan strukturni test: nijedno sučelje ne smije stajati unutar `except` bloka — točno to je
držalo oba gumba za brisanje nedostupnima.

Pokreni:  python -m pytest testovi/test_brisanje_i_arhiva.py -q   (iz mape caki-testovi)
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
import fake_gspread  # noqa: E402
import tablice  # noqa: E402

GLAVNI = "T26-0007"          # test s pokušajima (ima dokaz)
PRAZNI = "T26-0008"          # test bez pokušaja (smije se obrisati i uz „rezultati: NE")


def _sheet(**tabovi) -> fake_gspread.FakeSpreadsheet:
    """Lažni Sheet s pravim zaglavljima iz `tablice.ZAGLAVLJA`."""
    s = fake_gspread.FakeSpreadsheet()
    for naziv, retci in tabovi.items():
        s.dodaj(naziv, tablice.ZAGLAVLJA[naziv], retci)
    return s


@pytest.fixture
def baza() -> fake_gspread.FakeSpreadsheet:
    """Dva testa: jedan s rezultatima, jedan bez. Oba imaju statistiku — da se vidi da se
    briše samo svoja."""
    return _sheet(
        Definicije_testova=[
            {"definicija_id": GLAVNI, "naziv": "Kvadratna jednadžba", "predmet": "matematika",
             "status": "zatvoren", "broj_zadataka": 3, "bodovi_ukupno": 6, "zadaci_json": "[]"},
            {"definicija_id": PRAZNI, "naziv": "Derivacije — nacrt", "predmet": "matematika",
             "status": "nacrt", "broj_zadataka": 2, "bodovi_ukupno": 4, "zadaci_json": "[]"},
        ],
        Dodjele_ispita=[
            {"dodjela_id": "D-1", "definicija_id": GLAVNI, "ucenik_id": "U1"},
            {"dodjela_id": "D-2", "definicija_id": GLAVNI, "ucenik_id": "U2"},
            {"dodjela_id": "D-9", "definicija_id": PRAZNI, "ucenik_id": "U3"},
        ],
        Pokusaji=[
            # definicija_id NAMJERNO prazan — tako ga upisuje dio puta kroz dodjelu (defekt 2)
            {"pokusaj_id": "PK-1", "dodjela_id": "D-1", "definicija_id": "",
             "ucenik_id": "U1", "status": "predano"},
            {"pokusaj_id": "PK-2", "dodjela_id": "D-2", "definicija_id": GLAVNI,
             "ucenik_id": "U2", "status": "predano"},
        ],
        Ocjene_zadataka=[
            {"pokusaj_id": "PK-1", "zadatak_id": "Z1", "redni_broj": 1, "bodovi": 2},
            {"pokusaj_id": "PK-1", "zadatak_id": "Z2", "redni_broj": 2, "bodovi": 0},
            {"pokusaj_id": "PK-1", "zadatak_id": "Z3", "redni_broj": 3, "bodovi": 2},
            {"pokusaj_id": "PK-2", "zadatak_id": "Z1", "redni_broj": 1, "bodovi": 2},
            {"pokusaj_id": "PK-2", "zadatak_id": "Z2", "redni_broj": 2, "bodovi": 2},
        ],
        Izmjene_ocjena=[{"izmjena_id": "IZ-1", "pokusaj_id": "PK-1", "zadatak_id": "Z2",
                         "tko": "caki"}],
        Zalbe=[{"zalba_id": "ZA-1", "pokusaj_id": "PK-1", "zadatak_id": "Z2",
                "ucenik_id": "U1", "status": "nova"}],
        Statistika_zadataka=[
            {"zadatak_id": "Z1", "definicija_id": GLAVNI, "n": 2, "p_vrijednost": "1"},
            {"zadatak_id": "Z2", "definicija_id": GLAVNI, "n": 2, "p_vrijednost": "0.5"},
            {"zadatak_id": "Z1", "definicija_id": PRAZNI, "n": 0, "p_vrijednost": ""},
        ],
        Dnevnik_radnji=[],
    )


def _redci(sheet, tab: str) -> list[dict]:
    return sheet.kao_objekti(tab)


# ================================================================== tablice.obrisi_gdje

def test_obrisi_gdje_brise_sve_poklapajuce(baza, upis_dozvoljen):
    n = tablice.obrisi_gdje(baza, tablice.TAB_OCJENE, {"pokusaj_id": "PK-1"})
    assert n == 3
    ostalo = _redci(baza, tablice.TAB_OCJENE)
    assert [r["pokusaj_id"] for r in ostalo] == ["PK-2", "PK-2"]


def test_obrisi_gdje_dva_uvjeta_brise_tocno_jedan(baza, upis_dozvoljen):
    """`Ocjene_zadataka` nema jedinstven stupac — ključ je pokusaj_id + zadatak_id."""
    n = tablice.obrisi_gdje(baza, tablice.TAB_OCJENE,
                            {"pokusaj_id": "PK-1", "zadatak_id": "Z2"})
    assert n == 1
    ostalo = [(r["pokusaj_id"], r["zadatak_id"]) for r in _redci(baza, tablice.TAB_OCJENE)]
    assert ("PK-1", "Z2") not in ostalo
    assert ("PK-1", "Z1") in ostalo and ("PK-2", "Z2") in ostalo


def test_obrisi_gdje_nepoznat_stupac_ne_brise_nista(baza, upis_dozvoljen):
    """Radije ništa nego pogrešan redak — upravo ovo je defekt 1 ostavio neobrisanim."""
    prije = len(_redci(baza, tablice.TAB_STATISTIKA))
    n = tablice.obrisi_gdje(baza, tablice.TAB_STATISTIKA, {"statistika_id": "nema me"})
    assert n == 0
    assert len(_redci(baza, tablice.TAB_STATISTIKA)) == prije


def test_obrisi_gdje_susjedne_retke_brise_u_jednom_pozivu(baza, upis_dozvoljen):
    """Kvota 429: tri susjedna retka moraju otići jednim `delete_rows`, ne s tri poziva."""
    ws = baza.worksheet(tablice.TAB_OCJENE)
    ws.pozivi = 0
    tablice.obrisi_gdje(baza, tablice.TAB_OCJENE, {"pokusaj_id": "PK-1"})
    assert ws.pozivi == 1, f"očekivan 1 poziv brisanja, bilo ih je {ws.pozivi}"


def test_obrisi_gdje_bez_dozvole_pisanja_baca(baza):
    """ARHITEKTURA §1 pravilo 2: upis je zadano isključen."""
    with pytest.raises(PermissionError):
        tablice.obrisi_gdje(baza, tablice.TAB_OCJENE, {"pokusaj_id": "PK-1"})


# ================================================================== opseg_brisanja

def test_opseg_nepostojeceg_testa(baza):
    opseg = definicije.opseg_brisanja(baza, "T26-9999")
    assert opseg["postoji"] is False
    assert opseg["smije_bez_rezultata"] is False


def test_opseg_bez_id_a(baza):
    assert "Nedostaje" in definicije.opseg_brisanja(baza, "")["razlog"]


def test_opseg_testa_bez_pokusaja(baza):
    opseg = definicije.opseg_brisanja(baza, PRAZNI)
    assert opseg["postoji"] is True
    assert opseg["pokusaji"] == 0
    assert opseg["dodjele"] == 1
    assert opseg["ima_pokusaje"] is False
    assert opseg["smije_bez_rezultata"] is True
    assert opseg["razlog"] == ""


def test_opseg_testa_s_pokusajima(baza):
    opseg = definicije.opseg_brisanja(baza, GLAVNI)
    assert opseg["naziv"] == "Kvadratna jednadžba"
    assert opseg["pokusaji"] == 2
    assert opseg["dodjele"] == 2
    assert opseg["ocjene"] == 5
    assert opseg["izmjene"] == 1
    assert opseg["zalbe"] == 1
    assert opseg["statistika"] == 2          # samo svoja, ne i redak testa PRAZNI
    assert opseg["rezultata_ukupno"] == 2 + 5 + 1 + 1 + 2
    assert opseg["smije_bez_rezultata"] is False
    assert "pokušaja" in opseg["razlog"]


def test_opseg_nista_ne_mijenja(baza):
    """Read-only: dijalog se otvara i prije nego korisnik odluči."""
    prije = {t: len(_redci(baza, t)) for t in
             (tablice.TAB_DEFINICIJE, tablice.TAB_POKUSAJI, tablice.TAB_OCJENE)}
    definicije.opseg_brisanja(baza, GLAVNI)
    assert {t: len(_redci(baza, t)) for t in prije} == prije


# ================================================================== obrisi() — bez sile

def test_obrisi_bez_pokusaja_brise_test_i_dodjele(baza, upis_dozvoljen):
    ok, razlog = definicije.obrisi(baza, PRAZNI, korisnik="caki")
    assert ok is True, razlog
    assert [r["definicija_id"] for r in _redci(baza, tablice.TAB_DEFINICIJE)] == [GLAVNI]
    assert "D-9" not in [r["dodjela_id"] for r in _redci(baza, tablice.TAB_DODJELE)]


def test_obrisi_bez_pokusaja_ostavlja_trag(baza, upis_dozvoljen):
    definicije.obrisi(baza, PRAZNI, korisnik="caki")
    dnevnik = _redci(baza, tablice.TAB_DNEVNIK)
    assert len(dnevnik) == 1
    zapis = dnevnik[0]
    assert zapis["radnja"] == "obrisan_test"
    assert zapis["sto"] == PRAZNI
    assert zapis["korisnik"] == "caki"
    assert zapis["kad"] and zapis["detalj"]


def test_obrisi_s_pokusajima_bez_sile_odbija(baza, upis_dozvoljen):
    ok, razlog = definicije.obrisi(baza, GLAVNI, korisnik="caki")
    assert ok is False
    assert "pokušaja" in razlog
    # ništa se nije dotaklo
    assert len(_redci(baza, tablice.TAB_DEFINICIJE)) == 2
    assert len(_redci(baza, tablice.TAB_POKUSAJI)) == 2
    assert len(_redci(baza, tablice.TAB_OCJENE)) == 5


# ================================================================== obrisi() — sa silom

def test_obrisi_sa_silom_brise_cijelu_kaskadu(baza, upis_dozvoljen):
    ok, razlog = definicije.obrisi(baza, GLAVNI, korisnik="caki", sila=True)
    assert ok is True, razlog
    assert [r["definicija_id"] for r in _redci(baza, tablice.TAB_DEFINICIJE)] == [PRAZNI]
    assert _redci(baza, tablice.TAB_POKUSAJI) == []
    assert _redci(baza, tablice.TAB_OCJENE) == []
    assert _redci(baza, tablice.TAB_IZMJENE_OCJENA) == []
    assert _redci(baza, tablice.TAB_ZALBE) == []
    for broj in ("pokušaji **2**", "ocjene **5**", "dodjele **2**"):
        assert broj in razlog


def test_obrisi_sa_silom_brise_i_statistiku(baza, upis_dozvoljen):
    """DEFEKT 1: prije se statistika nikad nije brisala (tražio se stupac `statistika_id`)."""
    definicije.obrisi(baza, GLAVNI, korisnik="caki", sila=True)
    ostalo = _redci(baza, tablice.TAB_STATISTIKA)
    assert [r["definicija_id"] for r in ostalo] == [PRAZNI]


def test_obrisi_sa_silom_brise_pokusaj_bez_definicija_id(baza, upis_dozvoljen):
    """DEFEKT 2: PK-1 ima prazan `definicija_id` — brisanje po njemu bi ga promašilo."""
    assert any(r["pokusaj_id"] == "PK-1" and not r["definicija_id"]
               for r in _redci(baza, tablice.TAB_POKUSAJI)), "priprema testa nije ispravna"
    definicije.obrisi(baza, GLAVNI, korisnik="caki", sila=True)
    assert "PK-1" not in [r["pokusaj_id"] for r in _redci(baza, tablice.TAB_POKUSAJI)]


def test_obrisi_sa_silom_ostavlja_popunjen_trag(baza, upis_dozvoljen):
    """DEFEKT 3: dnevnik je dobivao redak s pogrešnim imenima stupaca, pa prazan."""
    definicije.obrisi(baza, GLAVNI, korisnik="caki", sila=True)
    dnevnik = _redci(baza, tablice.TAB_DNEVNIK)
    assert len(dnevnik) == 1
    zapis = dnevnik[0]
    assert zapis["radnja"] == "obrisan_test_s_rezultatima"
    assert zapis["sto"] == GLAVNI
    assert zapis["korisnik"] == "caki"
    assert zapis["kad"], "stupac `kad` je prazan — dnevnik ne bi imao vrijeme radnje"
    assert "pokušaji 2" in zapis["detalj"]
    assert "statistika 2" in zapis["detalj"]


def test_obrisi_ne_dira_drugi_test(baza, upis_dozvoljen):
    definicije.obrisi(baza, GLAVNI, korisnik="caki", sila=True)
    assert [r["dodjela_id"] for r in _redci(baza, tablice.TAB_DODJELE)] == ["D-9"]


# ================================================================== više odjednom

def test_obrisi_vise_mjesana_hrpa(baza, upis_dozvoljen):
    """Jedan odbijeni test ne smije zaustaviti ostale."""
    rez = definicije.obrisi_vise(baza, [PRAZNI, GLAVNI], korisnik="caki")
    assert rez["obrisani"] == [PRAZNI]
    assert [o for o, _ in rez["odbijeni"]] == [GLAVNI]
    assert "pokušaja" in rez["odbijeni"][0][1]
    assert PRAZNI in rez["poruka"] and GLAVNI in rez["poruka"]
    assert [r["definicija_id"] for r in _redci(baza, tablice.TAB_DEFINICIJE)] == [GLAVNI]


def test_obrisi_vise_sa_silom_brise_oba(baza, upis_dozvoljen):
    rez = definicije.obrisi_vise(baza, [PRAZNI, GLAVNI], sila=True, korisnik="caki")
    assert sorted(rez["obrisani"]) == sorted([PRAZNI, GLAVNI])
    assert rez["odbijeni"] == []
    assert _redci(baza, tablice.TAB_DEFINICIJE) == []


def test_obrisi_vise_bez_odabira(baza, upis_dozvoljen):
    rez = definicije.obrisi_vise(baza, [], korisnik="caki")
    assert rez["obrisani"] == [] and rez["odbijeni"] == []
    assert "Nije odabran" in rez["poruka"]


def test_vrati_vise_iz_arhive(upis_dozvoljen):
    sheet = _sheet(
        Definicije_testova=[
            {"definicija_id": "T25-0112", "naziv": "Matura 2025 B", "status": "arhiviran",
             "zadaci_json": "[]"},
            {"definicija_id": "T25-0098", "naziv": "Nizovi", "status": "arhiviran",
             "zadaci_json": "[]"},
            {"definicija_id": "T26-0001", "naziv": "Aktivni", "status": "zatvoren",
             "zadaci_json": "[]"},
        ],
        Dodjele_ispita=[], Pokusaji=[], Dnevnik_radnji=[],
    )
    rez = definicije.vrati_vise_iz_arhive(sheet, ["T25-0112", "T25-0098", "T26-0001"],
                                          korisnik="caki")
    assert sorted(rez["vraceni"]) == ["T25-0098", "T25-0112"]
    assert [o for o, _ in rez["odbijeni"]] == ["T26-0001"]
    assert "nije u arhivi" in rez["odbijeni"][0][1]
    stanja = {r["definicija_id"]: r["status"] for r in _redci(sheet, tablice.TAB_DEFINICIJE)}
    assert stanja["T25-0112"] == "zatvoren" and stanja["T25-0098"] == "zatvoren"


# ================================================================== app.py (statička provjera)

@pytest.fixture(scope="module")
def app_izvor() -> str:
    return (REPO / "app.py").read_text(encoding="utf-8")


INTERAKTIVNI = {
    "button", "download_button", "form_submit_button", "checkbox", "toggle", "radio",
    "selectbox", "multiselect", "text_input", "text_area", "number_input", "date_input",
    "time_input", "file_uploader", "slider", "select_slider", "data_editor", "color_picker",
}
NAJVISE_REDAKA_OBJASNJENJA = 8


def _je_posuda(cvor) -> bool:
    """Je li `with` otvara expander, popover ili obrazac (dakle sučelje, ne resurs)?"""
    for stavka in getattr(cvor, "items", []):
        poziv = stavka.context_expr
        if (isinstance(poziv, ast.Call) and isinstance(poziv.func, ast.Attribute)
                and poziv.func.attr in ("expander", "popover", "form")):
            return True
    return False


def _ima_interaktivno(cvor) -> bool:
    for unutra in ast.walk(cvor):
        if (isinstance(unutra, ast.Call) and isinstance(unutra.func, ast.Attribute)
                and unutra.func.attr in INTERAKTIVNI):
            return True
    return False


def _zakopano_sucelje(izvor: str) -> list[tuple[int, str]]:
    """Sučelje unutar `except` bloka koje NIJE samo objašnjenje greške.

    Objašnjenje je dopušteno i korisno (UX pravilo 7: „ako funkcija padne, napiši što
    provjeriti"). Zakopana funkcionalnost nije. Razlika koju mjerimo:

      · ima interaktivni element (gumb, polje, odabir) → to je funkcionalnost, ne objašnjenje,
      · dulje je od osam redaka → isto.

    Primjer dopuštenog: `except` oko objave prikaže „Što provjeriti" s dva `st.caption`.
    Primjer nedopuštenog: cijela „Matrica razreda" (38 redaka) nađena 20.11. unutar `except`
    bloka Provjere odgovora — vidjela se samo kad bi Provjera pala.
    """
    nalazi = []
    for cvor in ast.walk(ast.parse(izvor)):
        if not isinstance(cvor, ast.ExceptHandler):
            continue
        for dijete in cvor.body:
            if not isinstance(dijete, ast.With) or not _je_posuda(dijete):
                continue
            duzina = (dijete.end_lineno or dijete.lineno) - dijete.lineno + 1
            if _ima_interaktivno(dijete):
                nalazi.append((dijete.lineno, "ima interaktivni element"))
            elif duzina > NAJVISE_REDAKA_OBJASNJENJA:
                nalazi.append((dijete.lineno, f"{duzina} redaka — predugo za objašnjenje"))
    return sorted(nalazi)


def test_app_se_parsira(app_izvor):
    ast.parse(app_izvor)


def test_nijedna_funkcionalnost_nije_zakopana_u_except_bloku(app_izvor):
    """Upravo je ovo držalo oba gumba za brisanje nedostupnima (app.py 916 i 991).

    Sučelje unutar `except` prikaže se samo kad nešto drugo padne — dakle nikad u normalnom
    radu. Prvo pokretanje ovog testa 20.11. našlo je i treći slučaj: „🧮 Matrica razreda"
    unutar `except` bloka Provjere odgovora.
    """
    nalazi = _zakopano_sucelje(app_izvor)
    opis = "; ".join(f"red {red}: {zasto}" for red, zasto in nalazi)
    assert nalazi == [], f"funkcionalnost zakopana u except bloku — {opis}"


def test_matrica_razreda_se_vidi_u_normalnom_radu(app_izvor):
    """Imenovana provjera za treći nađeni slučaj, da se dedent ne vrati slučajno."""
    for cvor in ast.walk(ast.parse(app_izvor)):
        if not isinstance(cvor, ast.ExceptHandler):
            continue
        for dijete in cvor.body:
            if not isinstance(dijete, ast.With) or not _je_posuda(dijete):
                continue
            naljepnica = ""
            for stavka in dijete.items:
                for arg in getattr(stavka.context_expr, "args", []):
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        naljepnica += arg.value
            assert "Matrica razreda" not in naljepnica, (
                f"Matrica razreda je opet unutar except bloka (red {dijete.lineno})")


def test_objasnjenje_greske_u_exceptu_je_dopusteno(app_izvor):
    """Kontrola samog pravila: „Što provjeriti" nakon neuspjele objave SMIJE ostati u except.

    Da ovaj test padne, značilo bi da je provjera iznad previše stroga i da će tjerati
    uklanjanje korisnih objašnjenja.
    """
    assert 'st.expander("Što provjeriti")' in app_izvor
    assert all("Što provjeriti" not in str(red) for red, _ in _zakopano_sucelje(app_izvor))


def test_brisanje_je_u_kartici_testovi(app_izvor):
    """Dijalog brisanja mora stajati prije kartice 🧱 Složi test — tamo `_odabir_l` postoji."""
    brisanje = app_izvor.find('st.expander("🗑️ Obriši test")')
    slozi = app_izvor.find('if _akt == "🧱 Složi test":')
    odabir = app_izvor.find("_odabir_l = st.selectbox")
    assert brisanje != -1, "dijalog brisanja nije nađen"
    assert 0 < odabir < brisanje < slozi


def test_app_zove_nove_funkcije(app_izvor):
    for poziv in ("definicije.opseg_brisanja(", "definicije.obrisi_vise(",
                  "definicije.vrati_vise_iz_arhive("):
        assert poziv in app_izvor, poziv


def test_app_nema_starih_kljuceva_brisanja(app_izvor):
    """Dva stara expandera moraju biti uklonjena, ne samo premještena."""
    for ostatak in ("v2_bris_sve_", "_potvrda_bris", "Obriši test (trajno)"):
        assert ostatak not in app_izvor, ostatak
