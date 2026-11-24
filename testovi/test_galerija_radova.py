"""
🖼️ Ocjenjivanje uz radove (Caki 24.11.2026.): lijevo zadaci, desno priložene slike/PDF.

Pokreni:  python -m pytest testovi/test_galerija_radova.py -q   (iz mape caki-testovi)
"""
from __future__ import annotations

import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
for _p in (REPO, REPO / "testovi"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import galerija_radova as g  # noqa: E402

FID = "1OWV10nWCsQns1HyGQNsLqIe9uyTQyGMT"


@pytest.mark.parametrize("veza", [
    f"https://drive.google.com/file/d/{FID}/view?usp=drivesdk",
    f"https://drive.google.com/open?id={FID}",
    f"https://drive.google.com/uc?export=download&id={FID}",
])
def test_drive_poveznice_daju_pregled(veza):
    assert g.drive_id(veza) == FID
    assert g.nacin_prikaza(veza) == ("drive", f"https://drive.google.com/file/d/{FID}/preview")


def test_izravna_slika_i_ostale_poveznice():
    assert g.nacin_prikaza("https://x.hr/a/sken.JPG")[0] == "slika"
    assert g.nacin_prikaza("https://photos.app.goo.gl/abc")[0] == "poveznica"
    assert g.nacin_prikaza("") == ("", "")


def test_oznaka():
    assert g.oznaka({"naziv": "C.jpg"}, 1) == "1. C.jpg ⏳"
    assert g.oznaka({"naziv": "C.jpg", "potvrdjeno": "2026-11-24"}, 2) == "2. C.jpg ✅"


APP = '''
import json, sys
sys.path.insert(0, {repo!r}); sys.path.insert(0, {testovi!r})
import streamlit as st
import ekran_ucenika, galerija_radova, provedba, tablice
s = st.session_state["_sheet"]
p = tablice.ucitaj(s, "Pokusaji")[0]
radovi = st.session_state["_radovi"]
lijevo, desno = st.columns([1.1, 1])
with lijevo:
    with st.container(height=880):
        ekran_ucenika.prikazi_pregled_rjesenja(
            st, json.loads(p["zadaci_json"]), provedba.odgovori(p), pokazi_rjesenja=True,
            pokazi_video=False, pokazi_bodove=True, sheet=s, pokusaj=p, ucenik_id="OH3229",
            kljuc="t", uloga="profesor")
with desno:
    galerija_radova.prikazi(st, radovi, kljuc="g",
                            potvrdi=lambda rid: st.session_state.update(_potvrdjen=rid))
'''


def _app(tmp_path, radovi, zalbe_retci=()):
    from streamlit.testing.v1 import AppTest
    import test_zalbe_odgovor as tz

    f = tmp_path / "split.py"
    f.write_text(APP.format(repo=str(REPO), testovi=str(REPO / "testovi")), encoding="utf-8")
    at = AppTest.from_file(str(f), default_timeout=60)
    at.session_state["_sheet"] = tz._sheet(list(zalbe_retci))
    at.session_state["_radovi"] = radovi
    return at.run()


RADOVI = [{"rad_id": "R1", "naziv": "C.jpg", "veza": f"https://drive.google.com/file/d/{FID}/view"},
          {"rad_id": "R2", "naziv": "D.pdf", "veza": "https://drive.google.com/file/d/2abcdefghijkl/view"},
          {"rad_id": "R3", "naziv": "D..jpg", "veza": ""}]


def test_raspored_lijevo_desno_radi(tmp_path, upis_dozvoljen):
    at = _app(tmp_path, RADOVI)
    assert not at.exception, [str(e.value) for e in at.exception]
    assert [e.label for e in at.expander if e.label.startswith("Zadatak")]       # lijevo zadaci
    assert any("bez datoteke" in c.value for c in at.caption)                   # R3 nije sakriven
    at.button(key="g_gal_next").click().run()
    assert at.session_state["g_gal_i"] == 1
    at.button(key="g_gal_ok_R2").click().run()
    assert at.session_state["_potvrdjen"] == "R2"


def test_bez_radova_poruka(tmp_path, upis_dozvoljen):
    at = _app(tmp_path, [])
    assert not at.exception
    assert any("nije priložio rad" in i.value for i in at.info)


def test_ispravak_zalbe_unutar_rasporeda(tmp_path, upis_dozvoljen):
    """Ispravak žalbe ima stupce (Spremi/Odustani) — unutar lijevog stupca to je dopušteno."""
    import test_zalbe_odgovor as tz
    at = _app(tmp_path, RADOVI, [{**tz.ZALBA, "status": "odbijena", "odgovor": "Ne."}])
    [b for b in at.button if b.label == "✏️ Ispravi odgovor ili odluku"][0].click()
    at.run()
    assert not at.exception, [str(e.value) for e in at.exception]
    assert [b for b in at.button if b.label == "Spremi ispravak"]
