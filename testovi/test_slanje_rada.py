"""
Testovi za slanje učenikova rada (Caki 23.11.2026.): „4 puta pokušao dodati sliku, nije prošlo,
a u izvještaju za roditelje piše ime datoteke i ‚čeka pregled'".

Uzrok 1: kad Drive odbije sliku, svejedno se zapisivao redak (ime datoteke, bez slike i bez
poveznice). Uzrok 2: poruka s razlogom brisala se odmah (`st.rerun()`), pa razlog nitko nije vidio.
Uzrok 3 (mogući): Drive koristi `GOOGLE_SERVICE_ACCOUNT_JSON_TESTOVI` ako postoji, a Sheet obični
ključ, pa to mogu biti dva različita računa. Poruka sada kaže kojim je računom pokušano.

Pokreni:  python -m pytest testovi/test_slanje_rada.py -q   (iz mape caki-testovi)
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import drive  # noqa: E402
import fake_gspread  # noqa: E402
import radovi  # noqa: E402
import tablice  # noqa: E402


@pytest.fixture
def sheet():
    s = fake_gspread.FakeSpreadsheet()
    s.dodaj(tablice.TAB_RADOVI, tablice.ZAGLAVLJA[tablice.TAB_RADOVI], [])
    return s


def _ucitaj_uspjeh(bajtovi, naziv, *, folder):
    return f"https://drive.google.com/file/{naziv}", ""


def _ucitaj_odbijeno(bajtovi, naziv, *, folder):
    return "", "Slanje u Drive nije uspjelo: mapa nije dostupna [404 notFound]"


def _radovi(s):
    return tablice.ucitaj(s, tablice.TAB_RADOVI)


# ------------------------------------------------------------------ posalji_ucenikov_rad

def test_drive_primio_sliku_zapis_s_poveznicom(sheet, upis_dozvoljen):
    rez = radovi.posalji_ucenikov_rad(sheet, pokusaj_id="P-1", ucenik_id="oh3229",
                                      bajtovi=b"jpg", naziv_datoteke="Dž 1.jpg", folder="F",
                                      ucitaj=_ucitaj_uspjeh)
    assert rez["ok"] and not rez["tehnicki"]
    [r] = _radovi(sheet)
    assert r["veza"].startswith("https://drive.google.com/file/")
    assert r["ucenik_id"] == "OH3229" and r["izvor"] == "sken"


def test_drive_odbio_bez_poveznice_nista_se_ne_zapisuje(sheet, upis_dozvoljen):
    """Točno Cakijev slučaj: prije je ovdje nastao redak „D..jpg — čeka pregled" bez slike."""
    rez = radovi.posalji_ucenikov_rad(sheet, pokusaj_id="P-1", ucenik_id="OH3229",
                                      bajtovi=b"jpg", naziv_datoteke="D.jpg", folder="F",
                                      ucitaj=_ucitaj_odbijeno)
    assert rez["ok"] is False
    assert "NIJE poslana" in rez["poruka"]
    assert "notFound" in rez["tehnicki"]
    assert _radovi(sheet) == []


def test_drive_odbio_ali_ima_poveznicu_zapis_poveznice(sheet, upis_dozvoljen):
    rez = radovi.posalji_ucenikov_rad(sheet, pokusaj_id="P-1", ucenik_id="OH3229",
                                      bajtovi=b"jpg", naziv_datoteke="D.jpg", folder="F",
                                      poveznica="https://photos.app/abc", ucitaj=_ucitaj_odbijeno)
    assert rez["ok"] and "notFound" in rez["tehnicki"]
    [r] = _radovi(sheet)
    assert r["veza"] == "https://photos.app/abc"
    assert "notFound" in r["napomena"]                 # Caki u Rezultatima vidi zašto


def test_samo_poveznica(sheet, upis_dozvoljen):
    pozvan = []
    rez = radovi.posalji_ucenikov_rad(sheet, pokusaj_id="P-1", ucenik_id="OH3229",
                                      poveznica="https://x", ucitaj=lambda *a, **k: pozvan.append(1))
    assert rez["ok"] and not pozvan                    # Drive se ni ne zove
    assert _radovi(sheet)[0]["veza"] == "https://x"


@pytest.mark.parametrize("kw,dio", [
    ({"pokusaj_id": ""}, "kad test počne"),
    ({"pokusaj_id": "P-1"}, "Odaberi fotografiju"),
])
def test_neispravan_unos_nista_ne_zapisuje(sheet, upis_dozvoljen, kw, dio):
    rez = radovi.posalji_ucenikov_rad(sheet, ucenik_id="OH3229", ucitaj=_ucitaj_uspjeh, **kw)
    assert rez["ok"] is False and dio in rez["poruka"]
    assert _radovi(sheet) == []


# ------------------------------------------------------------------ servisni račun

class _Secrets(dict):
    pass


class _St:
    def __init__(self, **secrets):
        self.secrets = _Secrets(secrets)


def _json(email):
    return json.dumps({"type": "service_account", "client_email": email, "private_key": "x"})


def test_vjerodajnice_prednost_ima_testovi_kljuc():
    st = _St(GOOGLE_SERVICE_ACCOUNT_JSON=_json("sheet@a.iam"),
             GOOGLE_SERVICE_ACCOUNT_JSON_TESTOVI=_json("drive@b.iam"))
    podaci, kljuc = drive.vjerodajnice(st)
    assert kljuc == "GOOGLE_SERVICE_ACCOUNT_JSON_TESTOVI"
    assert podaci["client_email"] == "drive@b.iam"


def test_racun_kaze_email_i_kljuc():
    st = _St(GOOGLE_SERVICE_ACCOUNT_JSON=_json("caki-streamlit-bot@x.iam.gserviceaccount.com"))
    r = drive.racun(st)
    assert r == {"email": "caki-streamlit-bot@x.iam.gserviceaccount.com",
                 "kljuc": "GOOGLE_SERVICE_ACCOUNT_JSON", "greska": ""}


def test_racun_bez_kljuca():
    r = drive.racun(_St())
    assert r["email"] == "" and "nema servisnog računa" in r["greska"]


# ------------------------------------------------------------------ dijagnostika mape

class _Get:
    def __init__(self, odgovor=None, greska=None):
        self.odgovor, self.greska = odgovor, greska

    def files(self):
        return self

    def get(self, **kw):
        assert kw["supportsAllDrives"] is True
        return self

    def execute(self):
        if self.greska:
            raise self.greska
        return self.odgovor


def test_provjeri_pristup_dijeljeni_disk_ok():
    rez = drive.provjeri_pristup("F", servis=_Get({"name": "02_Radovi_ucenika", "driveId": "0AL",
                                                   "capabilities": {"canAddChildren": True}}))
    assert rez["ok"] and "dijeljenom disku" in rez["poruka"]


def test_provjeri_pristup_bez_prava_dodavanja():
    rez = drive.provjeri_pristup("F", servis=_Get({"name": "M", "driveId": "0AL",
                                                   "capabilities": {"canAddChildren": False}}))
    assert not rez["ok"] and "Contributor" in rez["poruka"]


def test_provjeri_pristup_moj_disk():
    rez = drive.provjeri_pristup("F", servis=_Get({"name": "M",
                                                   "capabilities": {"canAddChildren": True}}))
    assert not rez["ok"] and "dijeljeni disk" in rez["poruka"]


class _HttpError(Exception):
    def __init__(self, status, sadrzaj):
        super().__init__("http")
        self.resp = type("R", (), {"status": status})()
        self.content = json.dumps(sadrzaj).encode()


def test_provjeri_pristup_mapa_nevidljiva():
    e = _HttpError(404, {"error": {"errors": [{"reason": "notFound"}], "message": "File not found"}})
    rez = drive.provjeri_pristup("F", servis=_Get(greska=e))
    assert not rez["ok"] and "notFound" in rez["poruka"]


def test_provjeri_pristup_bez_folder_id():
    assert "RADOVI_FOLDER_ID" in drive.provjeri_pristup("")["poruka"]


def test_drive_api_nije_ukljucen():
    e = _HttpError(403, {"error": {"errors": [{"reason": "accessNotConfigured"}],
                                   "status": "PERMISSION_DENIED",
                                   "details": [{"reason": "SERVICE_DISABLED"}]}})
    assert "Google Drive API nije uključen" in drive.opis_greske(e)


def test_nepoznata_greska_nosi_googleovu_poruku():
    e = _HttpError(400, {"error": {"errors": [{"reason": "badRequest"}],
                                   "message": "Invalid parents"}})
    assert "Invalid parents" in drive.opis_greske(e)
