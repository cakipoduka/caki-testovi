"""
CAKI testovi v2 — `app.py`
Nova aplikacija za sustav testiranja (paralelni razvoj, ne dira stare repoе).

Što radi u ovoj verziji (Faza A):
  · 🧪 Testovi — popis testova, slaganje novog testa iz postojeće baze (20.000+ zadataka)
  · 👥 Objavi — kome ide: grupa/kanta/pojedinac; dopuna nakon objave; rok po učeniku
  · 📊 Rezultati — po testu: rang, prosjek, ko nije predao, po grupama
  · ⚙️ Postavke — Student View po testu, video uz rješenje, priprema tabova

Ručno rješavanje (učenik) dolazi u Fazi B — tada se ovdje dodaje i pregled “kako vidi učenik”.

SECRETS: GOOGLE_SERVICE_ACCOUNT_JSON, SHEET_ID (baza zadataka), CRM_SHEET_ID, APP_PASSWORD
"""
import streamlit as st

# Kategorije vrednovanja (UZV/RP/MK) — iste kao u v1 (`KATEGORIJE_INFO` u Test Builderu)
_KATEGORIJE_INFO = [
    ("UZV", "Usvojenost znanja i vještina"),
    ("RP", "Rješavanje problema"),
    ("MK", "Matematička komunikacija"),
]

import analitika
import provedba
import posjete
import podsjetnik
import banka
import builder
import definicije
import dodjele
import ekran_ucenika
import grupe
import izvjestaj
import model
import slike_zadataka
import tablice
import ucenici
import samoprovjera
import tex_test
import upute
import zakljucna
from veza import sheet_baze, sheet_crm
import predlosci
import pdf_izvjestaj
import radovi

st.set_page_config(page_title="CAKI — Testovi v2", page_icon="🧪", layout="wide")


# ------------------------------------------------------------------ prijava

def _lozinka() -> str:
    return str(st.secrets.get("APP_PASSWORD", "") or "")


def prijava() -> bool:
    ocekivana = _lozinka()
    if not ocekivana:
        st.title("🧪 CAKI — Testovi v2")
        st.error("U Secrets ove aplikacije dodaj `APP_PASSWORD` (i `GOOGLE_SERVICE_ACCOUNT_JSON`, "
                 "`SHEET_ID`, `CRM_SHEET_ID`).")
        return False

    def _na_unos():
        st.session_state["v2_autoriziran"] = (
            st.session_state.get("v2_lozinka") == ocekivana)

    if st.session_state.get("v2_autoriziran"):
        return True
    st.title("🧪 CAKI — Testovi v2")
    st.caption("Nova generacija sustava testiranja. Stara aplikacija radi dalje — ovo je paralelni razvoj.")
    st.text_input("Lozinka", type="password", key="v2_lozinka", on_change=_na_unos)
    if st.session_state.get("v2_autoriziran") is False:
        st.error("Pogrešna lozinka.")
    return False


if not prijava():
    st.stop()

# ------------------------------------------------------------------ sigurnosna kočnica
# ŽIVA BAZA. Upis je zadano ISKLJUČEN — uključuje se u bočnoj traci (ili `V2_UPIS = "da"` u Secrets).
# 28.10.2026.: Caki radi na ŽIVOJ bazi — upis je uvijek uključen (prekidač uklonjen).
# Sigurnosni sloj u `tablice` ostaje: ako se kodom postavi `postavi_pisanje(False)`, upis se blokira.
tablice.postavi_pisanje(True)


# ------------------------------------------------------------------ provjera tajni
OBAVEZNE_TAJNE = {
    "CRM_SHEET_ID": ("ID Sheeta „CAKI CRM — Prijave i baza”",
                     "u URL-u Sheeta: docs.google.com/spreadsheets/d/**ID**/edit"),
    "SHEET_ID": ("ID baze zadataka (caki-baza-zadataka)",
                 "u URL-u Sheeta: docs.google.com/spreadsheets/d/**ID**/edit"),
}


def _tajna(kljuc: str, zadano: str = "") -> str:
    try:
        return str(st.secrets.get(kljuc) or zadano).strip()
    except Exception:                                   # noqa: BLE001 — nema secrets.toml
        return zadano


def _nedostajuce() -> list[tuple[str, str, str]]:
    izlaz = []
    for kljuc, (opis, gdje) in OBAVEZNE_TAJNE.items():
        if not _tajna(kljuc):
            izlaz.append((kljuc, opis, gdje))
    if not any(_tajna(k) for k in ("GOOGLE_SERVICE_ACCOUNT_JSON_TESTOVI",
                                   "GOOGLE_SERVICE_ACCOUNT_JSON")):
        izlaz.append(("GOOGLE_SERVICE_ACCOUNT_JSON(_TESTOVI)",
                      "JSON servisnog računa", "Streamlit → Settings → Secrets"))
    return izlaz


_nedostaje = _nedostajuce()
if _nedostaje:
    st.error("**Aplikacija još nema sve tajne u Streamlit Secrets.** Dodaj ovo pa Reboot:")
    for kljuc, opis, gdje in _nedostaje:
        st.markdown(f"- `{kljuc}` — {opis}\n  — *{gdje}*")
    st.info("**Najlakše:** otvori aplikaciju koja već radi (npr. `caki-baza-zadataka`) → "
            "⋮ → Settings → Secrets → kopiraj odatle `SHEET_ID` i `CRM_SHEET_ID` (iste su vrijednosti).")
    with st.expander("Kako izgleda Secrets kad je ispravno"):
        st.code('APP_PASSWORD = "lozinka"\n'
                'CRM_SHEET_ID = "1AbC…"\n'
                'SHEET_ID = "1XyZ…"\n'
                'GOOGLE_SERVICE_ACCOUNT_JSON_TESTOVI = \'\'\'{ … }\'\'\'', language="toml")
    st.stop()


# ------------------------------------------------------------------ podaci

@st.cache_resource(show_spinner=False)
def _sheet():
    return sheet_crm()


@st.cache_resource(show_spinner=False)
def _baza():
    return sheet_baze()


def _prikazi_tekst_s_tabelama(tekst, kljuc: str = "") -> None:
    """Prikaži tekst zadatka; pipe tablice idu kao PRAVA tablica (Caki 29.10.2026.).

    Ako tablice nema — prikaz je isti kao prije (`builder.pripremi_za_prikaz`).
    """
    import tabele

    try:
        if not tabele.ima_tabelu(tekst):
            st.markdown(builder.pripremi_za_prikaz(tekst)[:900])
            return
        for dio in tabele.podijeli(tekst):
            if dio["tip"] == "tabela":
                st.markdown(tabele.html_tabela(dio["sadrzaj"]), unsafe_allow_html=True)
            else:
                _cisto = model.tekst(dio["sadrzaj"]).strip()
                if _cisto:
                    st.markdown(builder.pripremi_za_prikaz(_cisto)[:900])
    except Exception:                                  # noqa: BLE001
        st.markdown(builder.pripremi_za_prikaz(tekst)[:900])


@st.cache_data(ttl=300, show_spinner="Čitam bazu zadataka…")
def _zadaci():
    try:
        return banka.svi_zadaci(_baza())
    except Exception as e:                              # noqa: BLE001 — Caki mora vidjeti grešku
        st.error(f"Baza zadataka se ne može pročitati: {e}")
        return []


@st.cache_data(ttl=60, show_spinner=False)
def _testovi():
    try:
        return definicije.ucitaj_sve(_sheet())
    except Exception as e:                              # noqa: BLE001
        st.error(f"Testovi se ne mogu pročitati: {e}")
        return []


@st.cache_data(ttl=60, show_spinner=False)
def _dodjele():
    try:
        return tablice.ucitaj(_sheet(), tablice.TAB_DODJELE)
    except Exception:                                   # noqa: BLE001
        return []


@st.cache_data(ttl=120, show_spinner=False)
def _ocjene():
    try:
        return tablice.ucitaj(_sheet(), tablice.TAB_OCJENE)
    except Exception:                                   # noqa: BLE001
        return []


@st.cache_data(ttl=120, show_spinner=False)
def _pokusaji():
    try:
        return tablice.ucitaj(_sheet(), tablice.TAB_POKUSAJI)
    except Exception:                                   # noqa: BLE001
        return []


@st.cache_data(ttl=120, show_spinner=False)
def _grupe():
    """Grupe Upisa + kante Mature. Greška ne ruši objavu — samo nema izbora po grupi."""
    try:
        return grupe.sve_grupe(_sheet())
    except Exception as e:                              # noqa: BLE001
        st.warning(f"Grupe se ne mogu pročitati ({e}). Upiši šifre ručno.")
        return []


def _osvjezi():
    st.cache_data.clear()
    st.rerun()




def _je_kopija(naslov: str) -> str:
    """Vrati upozorenje ako naslov Sheeta izgleda kao kopija/backup, inače prazno."""
    n = model.tekst(naslov).lower()
    if not n:
        return ""
    for znak in ("copy of", "kopija", "backup", "backup_", "prije cijepanja", "kopija od"):
        if znak in n:
            return (f"⚠️ Baza kojoj je aplikacija spojena zove se **„{naslov}”** — to izgleda kao "
                    "**kopija/backup**, a ne živa baza. Provjeri `SHEET_ID` u Secrets.")
    return ""


@st.cache_data(ttl=60, show_spinner=False)
def _info_baze() -> list[str]:
    """Kratka dijagnostika: koji Sheet, postoji li tab `Zadaci`, koliko redaka, koja zaglavlja."""
    from banka import TAB_ZADACI

    redci = []
    try:
        sheet = _baza()
        redci.append(f"· Sheet: **{getattr(sheet, 'title', '(nepoznat)')}**")
        redci.append(f"· ID Sheeta: `{str(getattr(sheet, 'id', ''))[:12]}…`")
    except Exception as e:                              # noqa: BLE001
        return [f"· Sheet se ne može otvoriti: {e}"]

    naslovi = []
    try:
        naslovi = [w.title for w in sheet.worksheets()]
        redci.append(f"· Tabovi ({len(naslovi)}): " + ", ".join(naslovi[:12]) + ("…" if len(naslovi) > 12 else ""))
    except Exception as e:                              # noqa: BLE001
        redci.append(f"· Tabove nije moguće popisati: {e}")

    if TAB_ZADACI not in naslovi:
        redci.append(f"· ⚠️ **Nema taba `{TAB_ZADACI}`** — `SHEET_ID` vjerojatno pokazuje na pogrešan Sheet.")
        return redci

    try:
        ws = sheet.worksheet(TAB_ZADACI)
        svi = ws.get_all_values()
        redci.append(f"· Tab `{TAB_ZADACI}`: **{max(0, len(svi) - 1)}** redaka, "
                     f"{len(svi[0]) if svi else 0} stupaca")
        if svi:
            zagl = [str(h) for h in svi[0]]
            redci.append("· Zaglavlje: " + ", ".join(zagl[:10]) + ("…" if len(zagl) > 10 else ""))
            redci.append("· Video stupac: " + ("`video_url` ✅" if "video_url" in zagl else "**nema**"))
    except Exception as e:                              # noqa: BLE001
        redci.append(f"· Tab `{TAB_ZADACI}` se ne može pročitati: {e}")
    return redci


# ------------------------------------------------------------------ zaglavlje

st.title("🧪 Testovi — nova generacija")
st.caption("Paralelni razvoj: stara aplikacija i dalje radi. Ovdje se gradi sustav po MASTER dokumentu.")

with st.sidebar:
    st.markdown("### 🧪 CAKI Testovi v2")
    if st.button("🔄 Osvježi podatke"):
        _osvjezi()
    st.caption("Faza A: testovi, objave, rezultati. Rješavanje dolazi sljedeće.")

    st.divider()

tab_testovi, tab_pdf, tab_objavi, tab_rezultati, tab_kvaliteta, tab_ocjene, tab_ucenik, tab_postavke = st.tabs(
    ["🧪 Testovi", "🧱 Složi test", "👥 Objavi", "📊 Rezultati", "📈 Kvaliteta", "🎓 Ocjene",
     "🧑‍🎓 Kao učenik", "⚙️ Postavke"])


# ------------------------------------------------------------------ 🧪 Testovi

with tab_testovi:
    upute.prikazi(st, "testovi")
    st.caption("Popis testova i radnje. **Novi test slažeš u 🧱 Složi test.**")

    _testovi_lista = _testovi()
    if not _testovi_lista:
        st.info("Još nema testova → **🧱 Složi test** (odaberi zadatke → Spremi kao online test).")
    else:
        st.dataframe([{
            "ID": model.tekst(x.get("definicija_id")),
            "Naziv": model.tekst(x.get("naziv")),
            "Status": model.tekst(x.get("status")),
            "Zadataka": model.broj(x.get("broj_zadataka")),
            "Bodova": model.broj(x.get("bodovi_ukupno")),
            "Rok": f"{model.datum_hr(x.get('rok_od')) or '—'} – {model.datum_hr(x.get('rok_do')) or '—'}",
            "Vrsta": definicije.VRSTA_NAZIV.get(model.tekst(x.get("vrsta")), ""),
        } for x in _testovi_lista], hide_index=True, width="stretch")

        st.divider()
        st.divider()
        _opcije_l = {model.tekst(x.get("definicija_id")): x for x in _testovi_lista}
        _odabir_l = st.selectbox("Odaberi test za radnje", list(_opcije_l),
                                 format_func=lambda i: f"{model.tekst(_opcije_l[i].get('naziv'))} · "
                                                       f"{model.tekst(_opcije_l[i].get('status'))}",
                                 key="v2_l_test")
        _d_l = _opcije_l[_odabir_l]
        # 🗑 BRISANJE TESTA (Caki 31.10.2026.) — uz potvrdu, čuva dokaze
        with st.expander("🗑 Obriši test"):
            st.caption("Brisanje je trajno. Test s **ijednim pokušajem** ne može se obrisati — "
                       "tada ga **arhiviraj** (podaci ostaju kao dokaz).")
            _potvrda = st.checkbox("Potvrđujem da želim trajno obrisati ovaj test",
                                   key="v2_brisi_potvrda")
            if st.button("🗑 Obriši test", type="secondary", key="v2_brisi_test",
                         disabled=not _potvrda):
                _ok, _razlog = definicije.obrisi(_sheet(), _odabir_l, korisnik="caki")
                if _ok:
                    st.success(_razlog)
                    _osvjezi()
                else:
                    st.error(_razlog)
                    if "pokušaja" in _razlog:
                        st.caption("Savjet: ostavi test u statusu `arhiviran` — skriva se iz "
                                   "popisa, a rezultati i dokazi ostaju.")

        _smije_l, _razlog_l = definicije.smije_urediti(_sheet(), _d_l)
        _status_l = model.tekst(_d_l.get("status"))

        c1, c2, c3 = st.columns(3)
        # --- pauza / puštanje
        if _status_l == "objavljen":
            if c1.button("⏸️ Učini nedostupnim učenicima", key="v2_l_pauza",
                         help="Test prelazi u „zatvoren” — učenici ga ne mogu otvoriti ni predati."):
                try:
                    definicije.promijeni_status(_sheet(), _odabir_l, "zatvoren", korisnik="caki")
                    st.success("Test je nedostupan učenicima. Sada ga možeš urediti.")
                    _osvjezi()
                except Exception as e:                  # noqa: BLE001
                    st.error(f"Nije uspjelo: {e}")
        elif _status_l == "zatvoren":
            if c1.button("▶️ Ponovno pusti učenicima", key="v2_l_pusti",
                         help="Vraća test u „objavljen” — učenici ga opet vide."):
                try:
                    definicije.promijeni_status(_sheet(), _odabir_l, "objavljen", korisnik="caki")
                    st.success("Test je ponovno dostupan učenicima.")
                    _osvjezi()
                except Exception as e:                  # noqa: BLE001
                    st.error(f"Nije uspjelo: {e}")
        else:
            c1.caption(f"Status: **{_status_l}**")

        c2.caption("✏️ " + ("mijenjanje dopušteno — " + _razlog_l if _smije_l else _razlog_l))
        if c3.button("📊 Vidi rezultate", key="v2_l_rez"):
            st.session_state["v2_rez_test"] = _odabir_l
            st.caption("Rezultati su u kartici 📊 Rezultati (test je tamo već odabran).")

        # --- uređivanje
        if _smije_l:
            with st.expander("✏️ Uredi test (naziv, trajanje, rokovi, napomena)"):
                with st.form(f"v2_uredi_{_odabir_l}"):
                    u1, u2 = st.columns(2)
                    _n_naziv = u1.text_input("Naziv", value=model.tekst(_d_l.get("naziv")))
                    _n_nap = u2.text_input("Napomena", value=model.tekst(_d_l.get("napomena")))
                    u3, u4, u5 = st.columns(3)
                    _n_traj = u3.number_input("Trajanje (min)", 5, 240,
                                              model.cijeli(_d_l.get("trajanje_min"), 45), 5)
                    _n_od = u4.date_input("Rok od",
                                          value=model.datum(_d_l.get("rok_od")) or model.sada().date())
                    _n_do = u5.date_input("Rok do",
                                          value=model.datum(_d_l.get("rok_do")) or model.sada().date())
                    if st.form_submit_button("💾 Spremi izmjene", type="primary"):
                        try:
                            if _n_do < _n_od:
                                st.error("Rok „do” ne može biti prije roka „od”.")
                            else:
                                definicije.izmijeni(_sheet(), _d_l, {
                                    "naziv": _n_naziv, "napomena": _n_nap,
                                    "trajanje_min": int(_n_traj),
                                    "rok_od": model.iso_datum(_n_od),
                                    "rok_do": model.iso_datum(_n_do),
                                }, korisnik="caki")
                                st.success("Izmjene spremljene.")
                                _osvjezi()
                        except Exception as e:          # noqa: BLE001
                            st.error(f"Nije spremljeno: {e}")


with tab_pdf:
    upute.prikazi(st, "pdf")
    st.caption("**Jedno mjesto za slaganje testa:** odaberi zadatke iz baze → ispiši **PDF** ili "
               "spremi kao **online test** (isti odabir, dva izlaza).")

    _zadaci_pdf = _zadaci()
    if not _zadaci_pdf:
        st.warning("Baza se ne može pročitati ili je prazna → ⚙️ Postavke → 🩺 Provjera baze.")
    else:
        try:
            # --- filtri (VIŠESTRUKI izbor)
            f1, f2, f3 = st.columns(3)
            _cjeline = f1.multiselect("Cjelina", builder.vrijednosti(_zadaci_pdf, "cjelina"),
                                      key="v2p_cjeline")
            _potp = f2.multiselect("Potpoglavlje", builder.potpoglavlja_za(_zadaci_pdf, _cjeline),
                                   key="v2p_potp")
            _tezine = f3.multiselect("Težina", builder.vrijednosti(_zadaci_pdf, "tezina"),
                                     key="v2p_tezine")

            f4, f5, f6 = st.columns(3)
            _izvori = f4.multiselect("Biblioteka izvora", builder.vrijednosti(_zadaci_pdf, "izvor"),
                                     key="v2p_izvori")
            _tipovi = f5.multiselect("Tip zadatka", builder.vrijednosti(_zadaci_pdf, "tip"),
                                     key="v2p_tipovi")
            _trazi = f6.text_input("Traži u tekstu / ID-u", key="v2p_trazi")

            _nadeni = builder.filtriraj(_zadaci_pdf, tekst=_trazi, cjelina=_cjeline,
                                        potpoglavlje=_potp, tezina=_tezine, tip=_tipovi,
                                        izvor=_izvori)

            # --- stranice 20/30/40 (ne učitavamo sve odjednom)
            s1, s2 = st.columns([2, 1])
            _velicina = s1.radio("Zadataka po stranici", builder.VELICINE_STRANICE, horizontal=True,
                                 index=0, key="v2p_velicina")
            _info = builder.stranica(_nadeni, int(st.session_state.get("v2p_stranica", 0)), _velicina)
            if s2.button("↻ Prva stranica", key="v2p_prva"):
                st.session_state["v2p_stranica"] = 0
                _info = builder.stranica(_nadeni, 0, _velicina)
            st.caption(builder.tekst_stranice(_info))

            # --- prikaz slika u popisu (kao u starom builderu)
            _prikazi_slike = st.toggle("🖼️ Prikaži slike zadataka u popisu", value=True,
                                       key="v2p_prikazi_slike",
                                       help="Isključi ako je popis spor ili ako slike nisu potrebne.")
            _odabrani = st.session_state.setdefault("v2p_odabrani", {})

            _lijevo, _desno = st.columns([3, 2])

            with _lijevo:
                _p1, _p2 = st.columns(2)
                if _p1.button("◀ Prethodna stranica", key="v2p_prev_gore",
                              disabled=_info["stranica"] == 0):
                    st.session_state["v2p_stranica"] = max(0, _info["stranica"] - 1)
                    st.rerun()
                if _p2.button("Sljedeća ▶", key="v2p_next_gore",
                              disabled=_info["stranica"] + 1 >= _info["stranica_ukupno"]):
                    st.session_state["v2p_stranica"] = _info["stranica"] + 1
                    st.rerun()
                st.caption(builder.tekst_stranice(_info))
                _g1, _g2 = st.columns([1, 1])
                if _g1.button(f"➕ Dodaj sve prikazane ({len(_info['zadaci'])})", key="v2p_dodaj_sve"):
                    for _zz in _info["zadaci"]:
                        _zid_s = model.tekst(_zz.get("id"))
                        if _zid_s and _zid_s not in _odabrani:
                            _odabrani[_zid_s] = _zz
                    st.rerun()
                if _g2.button("🧹 Očisti odabir", key="v2p_ocisti_gore"):
                    st.session_state["v2p_odabrani"] = {}
                    st.rerun()

                for _z in _info["zadaci"]:
                    _zid = model.tekst(_z.get("id"))
                    _je_dodan = _zid in _odabrani
                    with st.container(border=True):
                        c1, c2 = st.columns([4, 1])
                        c1.markdown(f"**{builder.naslov_kartice(_z)}**")
                        if _je_dodan:
                            c2.success("✓ već dodano")
                        else:
                            if c2.button("➕ Dodaj", key=f"v2p_add_{_zid}"):
                                _odabrani[_zid] = _z
                                st.rerun()
                        _prikazi_tekst_s_tabelama(_z.get("tekst"), kljuc="popis")
                        _opcije_md = banka.opcije_markdown(_z)
                        if _opcije_md:
                            st.markdown(_opcije_md, unsafe_allow_html=True)
                        st.caption(" · ".join(builder.oznake(_z)))
                        if _prikazi_slike and model.tekst(_z.get("slika")):
                            try:
                                _ok_slika = slike_zadataka.prikazi_sliku_html(st, _z.get("slika"))
                                if not _ok_slika:
                                    st.caption("🖼️ slika nije prikazana → vidi „🩺 Zašto se slike ne vide”")
                            except Exception as _e_slika:   # noqa: BLE001
                                st.caption(f"🖼️ slika se ne može prikazati ({type(_e_slika).__name__})")

            with _desno:
                st.markdown(f"### 📋 Odabrano ({len(_odabrani)})")
                if not _odabrani:
                    st.caption("Nema odabranih zadataka. Dodaj ih gumbom lijevo.")
                else:
                    _ukupno_bod = sum(model.broj(z.get("bodovi"), 1) for z in _odabrani.values())
                    st.caption(f"Ukupno **{_ukupno_bod:g}** bodova.")
                    _redoslijed = list(_odabrani)
                    for _poz, _zid_d in enumerate(_redoslijed):
                        _zd = _odabrani[_zid_d]
                        with st.container(border=True):
                            d1, d2, d3, d4 = st.columns([4, 1, 1, 1])
                            d1.markdown(f"**{model.tekst(_zd.get('id'))}** · "
                                        f"{model.broj(_zd.get('bodovi'), 1):g} bod.")
                            if d2.button("↑", key=f"v2p_gore_{_zid_d}", help="pomakni gore",
                                         disabled=_poz == 0):
                                _novi = _redoslijed[:]
                                _novi[_poz - 1], _novi[_poz] = _novi[_poz], _novi[_poz - 1]
                                st.session_state["v2p_odabrani"] = {k: _odabrani[k] for k in _novi}
                                st.rerun()
                            if d3.button("↓", key=f"v2p_dolje_{_zid_d}", help="pomakni dolje",
                                         disabled=_poz == len(_redoslijed) - 1):
                                _novi = _redoslijed[:]
                                _novi[_poz + 1], _novi[_poz] = _novi[_poz], _novi[_poz + 1]
                                st.session_state["v2p_odabrani"] = {k: _odabrani[k] for k in _novi}
                                st.rerun()
                            if d4.button("✕", key=f"v2p_del_{_zid_d}", help="ukloni"):
                                _odabrani.pop(_zid_d, None)
                                st.rerun()
                            d1.markdown(builder.pripremi_za_prikaz(_zd.get("tekst"))[:220].replace("|", "\u2502"), unsafe_allow_html=True)
                            with st.expander("⚙️ Detalji zadatka"):
                                _bloom = st.selectbox(
                                    "🧠 Bloom razina (za analizu napretka)",
                                    ["— nije oznaceno (preskace se u analizi) —",
                                     "Pamcenje", "Razumijevanje", "Primjena",
                                     "Analiza", "Vrednovanje", "Sinteza"],
                                    index=0, key=f"v2p_bloom_{_zid_d}")
                                if _bloom.startswith("—"):
                                    _zd.pop("bloom", None)
                                else:
                                    _zd["bloom"] = _bloom
                                _prikazi = st.checkbox(
                                    "Prikazi ponudene odgovore (A/B/C/D) za ovaj zadatak",
                                    value=_zd.get("prikazi_opcije", True) is not False,
                                    key=f"v2p_opc_{_zid_d}")
                                _zd["prikazi_opcije"] = bool(_prikazi)
                                _bod = st.text_input("Bodovi", value=str(model.broj(
                                    _zd.get("bodovi"), 1)).replace(".", ","),
                                    key=f"v2p_bod_{_zid_d}")
                                try:
                                    _zd["bodovi"] = max(1, int(float(_bod.replace(",", "."))))
                                except ValueError:
                                    st.caption("Bodovi moraju biti broj.")

                                # KATEGORIJE VREDNOVANJA (UZV/RP/MK) — kao u Claudeovoj verziji
                                st.caption("Kategorije vrednovanja (može više odjednom, bodovi po "
                                           "kategoriji):")
                                _kat = dict(_zd.get("kategorije") or {})
                                _kk1, _kk2, _kk3 = st.columns(3)
                                for _kol, (_kod, _naziv) in zip((_kk1, _kk2, _kk3),
                                                                _KATEGORIJE_INFO):
                                    with _kol:
                                        _cekirano = st.checkbox(
                                            _kod, value=_kod in _kat, key=f"v2p_kat_{_zid_d}_{_kod}",
                                            help=_naziv)
                                        _bod_k = st.text_input(
                                            "bod.", value=str(_kat.get(_kod, "")),
                                            key=f"v2p_katbod_{_zid_d}_{_kod}",
                                            label_visibility="collapsed",
                                            disabled=not _cekirano)
                                        if _cekirano:
                                            _kat[_kod] = model.tekst(_bod_k).replace(".", ",")
                                        else:
                                            _kat.pop(_kod, None)
                                if _kat:
                                    _zd["kategorije"] = _kat
                                    _zbroj_k = tex_test.zbroj_kategorija(_zd)
                                    if abs(_zbroj_k - model.broj(_zd.get("bodovi"), 1)) > 1e-9:
                                        st.error(f"Zbroj po kategorijama: **{_zbroj_k:g} / "
                                                 f"{model.broj(_zd.get('bodovi'), 1):g} bod.** — "
                                                 "PDF se ne generira dok se ne uskladi.")
                                    else:
                                        st.success(f"Zbroj po kategorijama: {_zbroj_k:g} / "
                                                   f"{model.broj(_zd.get('bodovi'), 1):g} bod.")
                                else:
                                    _zd.pop("kategorije", None)

                                _opcije_panel = banka.opcije_markdown(_zd)
                                if _opcije_panel:
                                    st.markdown(_opcije_panel, unsafe_allow_html=True)

                _mamac_on = st.checkbox(
                    "➕ Dodaj „nista od navedenog” svim zadacima visestrukog izbora",
                    key="v2p_mamac",
                    help="Dodaje se samo u PDF-u, ne mijenja bazu (kao u starom builderu).")

                with st.expander("🩺 Zašto se slike ne vide"):
                    try:
                        _folderi = slike_zadataka.folder_kandidati(st)
                        _racuni = slike_zadataka.sa_kandidati(st)
                        st.caption(f"· Foldera u Secrets: **{len(_folderi)}**"
                                   + (" (`SLIKE_FOLDER_ID`: " + _folderi[0][:12] + "…)"
                                      if _folderi else " — dodaj `SLIKE_FOLDER_ID`"))
                        st.caption(f"· Servisnih računa: **{len(_racuni)}**")
                        if not _folderi:
                            st.warning("Bez `SLIKE_FOLDER_ID` slike se ne mogu dohvatiti.")
                        elif not _racuni:
                            st.warning("Nema servisnog računa u Secrets.")
                        else:
                            st.caption("Ako folder postoji, provjeri da je **podijeljen s tim "
                                       "računom** (barem „Viewer”).")
                            _naziv = next((model.tekst(z.get("slika")) for z in _info["zadaci"]
                                           if model.tekst(z.get("slika"))), "")
                            if _naziv:
                                _bytes = slike_zadataka.slika_bytes(_naziv, _folderi[0],
                                                                    slike_zadataka.token(_racuni[0]))
                                st.caption(f"· Probna slika `{_naziv}`: "
                                           + ("**dohvaćena** ✅" if _bytes else "**nije dohvaćena** ❌"))
                    except Exception as _e_d:            # noqa: BLE001
                        st.caption(f"Dijagnostika nije dostupna: {_e_d}")

            st.divider()
            _lista = list(_odabrani.values())
            _saz = builder.sazetak(_lista)
            st.markdown(f"**Odabrano: {_saz['zadataka']} zadataka · {_saz['bodova']:g} bodova**")
            if _lista and st.button("🧹 Očisti odabir", key="v2p_ocisti"):
                st.session_state["v2p_odabrani"] = {}
                st.rerun()

            # --- 📁 PREDLOŠCI i 💾 NACRT (preuzeto iz v1: `TestBuilder_predlosci` / `_draft`)
            with st.expander("📁 Predlošci i nacrt (nastavi gdje si stao)"):
                try:
                    _pl = predlosci.predlosci(_sheet())
                    _nac = predlosci.nacrt(_sheet())

                    if _nac and _nac.get("zadaci"):
                        st.caption(f"💾 Nacrt od **{model.tekst(_nac.get('draft_id'))}** — "
                                   f"{len(_nac.get('zadaci') or [])} zadataka"
                                   + (f", naslov: {model.tekst(_nac.get('naslov_dokumenta'))}"
                                      if model.tekst(_nac.get("naslov_dokumenta")) else ""))
                        if st.button("▶ Nastavi iz nacrta", key="v2p_nacrt_ucitaj"):
                            st.session_state["v2p_odabrani"] = {
                                model.tekst(z.get("id")): z for z in _nac["zadaci"]
                                if model.tekst(z.get("id"))}
                            st.rerun()

                    if _pl:
                        _opcije_pl = {model.tekst(r.get("predlozak_id")): r for r in _pl}
                        _odabir_pl = st.selectbox(
                            "Spremljeni predlošci", list(_opcije_pl),
                            format_func=lambda k: f"{model.tekst(_opcije_pl[k].get('naziv'))} · "
                                                  f"{model.broj(_opcije_pl[k].get('broj_zadataka'))} zad.",
                            key="v2p_pl_odabir")
                        c_a, c_b = st.columns(2)
                        if c_a.button("⬇ Učitaj predložak", key="v2p_pl_ucitaj"):
                            _u = predlosci.ucitaj_predlozak(_sheet(), _odabir_pl)
                            if _u.get("zadaci"):
                                st.session_state["v2p_odabrani"] = {
                                    model.tekst(z.get("id")): z for z in _u["zadaci"]
                                    if model.tekst(z.get("id"))}
                                st.rerun()
                        if c_b.button("🗑 Obriši predložak", key="v2p_pl_obrisi"):
                            predlosci.obrisi_predlozak(_sheet(), _odabir_pl)
                            st.rerun()
                    else:
                        st.caption("Još nema spremljenih predložaka.")

                    with st.form("v2p_pl_spremi"):
                        _naziv_pl = st.text_input("Naziv predloška",
                                                  placeholder="npr. Matura — linearna funkcija")
                        if st.form_submit_button("💾 Spremi odabir kao predložak",
                                                 disabled=not _lista):
                            try:
                                _red = predlosci.spremi_predlozak(
                                    _sheet(), naziv=_naziv_pl, zadaci=_lista,
                                    naslov_dokumenta=model.tekst(st.session_state.get("v2p_naslov")),
                                    tip_dokumenta=model.tekst(st.session_state.get("v2p_tipd")))
                                st.success(f"Predložak spremljen: **{_red['naziv']}**")
                            except Exception as _e_pl:      # noqa: BLE001
                                st.error(f"Predložak nije spremljen: {_e_pl}")

                    if _lista:
                        if st.button("💾 Spremi nacrt (nastavak rada)", key="v2p_nacrt_spremi"):
                            _ok = predlosci.spremi_nacrt(
                                _sheet(), zadaci=_lista,
                                naslov_dokumenta=model.tekst(st.session_state.get("v2p_naslov")),
                                tip_dokumenta=model.tekst(st.session_state.get("v2p_tipd")))
                            st.success("Nacrt spremljen." if _ok else
                                       "Nacrt nije spremljen (upis u bazu isključen?).")
                except Exception as _e_pl2:                 # noqa: BLE001
                    st.caption(f"Predlošci trenutno nisu dostupni: {_e_pl2}")

            # --- metapodaci i PDF
            m1, m2, m3 = st.columns(3)
            _naslov = m1.text_input("Naslov testa (obavezno)", key="v2p_naslov",
                                    placeholder="npr. Kvadratna jednadžba — 1. provjera")
            _datum = m2.text_input("Datum", value=model.sada().strftime("%d.%m.%Y."), key="v2p_datum")
            _tipd = m3.selectbox("Tip dokumenta", tex_test.TIP_DOKUMENTA, key="v2p_tipd")
            _rjesenja = st.checkbox("Uključi rješenja na kraju dokumenta", key="v2p_rjesenja")

            _greska_naslov = builder.provjeri_naslov(_naslov)
            if _greska_naslov:
                st.caption("✏️ " + _greska_naslov)

            _problemi = tex_test.provjeri_kategorije(_lista) if _lista else []
            if _problemi:
                for _pr in _problemi:
                    st.warning(_pr)
                st.caption("🚫 **PDF je blokiran** dok se zbroj po kategorijama ne uskladi s bodovima "
                           "(isto pravilo kao u starom builderu).")

            _izlaz = st.radio("Što sa odabranim zadacima?",
                              ["📄 Ispis (PDF)", "🌐 Online test (objavi učenicima)"],
                              horizontal=True, key="v2p_izlaz")

            if _izlaz.startswith("🌐"):
                o1, o2, o3 = st.columns(3)
                _predmet = o1.text_input("Predmet", value="matematika", key="v2p_predmet")
                _trajanje = o2.number_input("Trajanje (min)", 5, 240, 45, 5, key="v2p_trajanje")
                _vrsta = o3.selectbox("Vrsta", definicije.VRSTE, key="v2p_vrsta",
                                      format_func=lambda v: definicije.VRSTA_NAZIV.get(v, v))
                _ai_dostupan = st.toggle(
                    "💡 AI pomoć dostupna učenicima tijekom rješavanja", value=False,
                    key="v2p_ai",
                    help="Ako je isključeno, učenik ne vidi blok pomoći. Ako je uključeno, bot "
                         "pomaže **bez davanja konačnog rješenja** (najviše 3 pitanja po zadatku).")
                _d1, _d2 = st.columns(2)
                _rok_od = _d1.date_input("Rok od (test nije dostupan prije)", key="v2p_rok_od")
                _rok_do = _d2.date_input("Rok do (test nije dostupan poslije)", key="v2p_rok_do")
                if _rok_do < _rok_od:
                    st.error("Rok „do” ne može biti prije roka „od”.")
                else:
                    st.caption(f"Učenik može pisati **{model.datum_hr(_rok_od)}** – "
                               f"**{model.datum_hr(_rok_do)}**; izvan toga test nije dostupan.")
                if st.button("💾 Spremi kao online test (nacrt)", type="primary",
                             disabled=(bool(_greska_naslov) or not _lista or _rok_do < _rok_od),
                             key="v2p_spremi"):
                    try:
                        _novi_id = tablice.novi_id(
                            [model.tekst(x.get("definicija_id")) for x in _testovi()], "T26-")
                        _d = definicije.nova_definicija(
                            definicija_id=_novi_id, naziv=_naslov, predmet=_predmet,
                            zadaci_=_lista, trajanje_min=int(_trajanje), vrsta=_vrsta,
                            autor="caki", status="nacrt",
                            ai_pomoc="da" if _ai_dostupan else "ne",
                            rok_od=model.iso_datum(_rok_od), rok_do=model.iso_datum(_rok_do))
                        _greske = definicije.validiraj(_d)
                        if _greske:
                            for _g in _greske:
                                st.error(_g)
                        else:
                            tablice.dodaj(_sheet(), tablice.TAB_DEFINICIJE, [_d])
                            tablice.zapisi_radnju(_sheet(), "caki", "novi_test", _novi_id, _naslov)
                            st.success(f"Spremljeno kao nacrt `{_novi_id}` — objavi u 👥 Objavi.")
                            st.session_state["v2p_odabrani"] = {}
                            _osvjezi()
                    except Exception as _e_u:            # noqa: BLE001
                        st.error(f"Nije spremljeno: {_e_u}")
            else:
                if st.button("📄 Generiraj PDF testa", type="primary",
                             disabled=bool(_greska_naslov) or not _lista or bool(_problemi),
                             key="v2p_generiraj"):
                    try:
                        _slike_za_pdf = {}
                        try:
                            _folderi = slike_zadataka.folder_kandidati(st)
                            _racuni = slike_zadataka.sa_kandidati(st)
                            if _folderi and _racuni:
                                _slike_za_pdf = tex_test.dohvati_slike(
                                    _lista, folder=_folderi[0], sa_info_dict=_racuni[0])
                                if _slike_za_pdf:
                                    st.caption(f"🖼️ U PDF ide **{len(_slike_za_pdf)}** slika "
                                               "(ostale se preskaču da PDF ne padne).")
                        except Exception:                   # noqa: BLE001
                            _slike_za_pdf = {}
                        _pdf = tex_test.generiraj(naziv=_naslov, zadaci=_lista, datum=_datum,
                                                  tip=_tipd, ukljuci_rjesenja=_rjesenja,
                                                  slike=_slike_za_pdf,
                                                  dodaj_mamac=bool(st.session_state.get('v2p_mamac')),
                                                  mamac_tekst='Nista od navedenog')
                        st.success(f"PDF generiran ({len(_pdf) // 1024} KB).")
                        st.download_button("⬇️ Preuzmi PDF", data=_pdf,
                                           file_name=tex_test.ime_datoteke(_naslov),
                                           mime="application/pdf", key="v2p_preuzmi")
                    except Exception as _e:                 # noqa: BLE001
                        st.error(f"PDF nije generiran: {_e}")
        except Exception as _e:                             # noqa: BLE001
            st.error(f"Kartica PDF-a trenutno ne radi: {_e}")


with tab_objavi:
    upute.prikazi(st, "objavi")
    _testovi_obj = _testovi()
    if not _testovi_obj:
        st.info("Ova kartica se puni kad postoji barem jedan test. Napravi ga u 🧪 Testovi.")
    else:
        _opcije_t = {model.tekst(x.get("definicija_id")): x for x in _testovi_obj}
        _odabir_t = st.selectbox("Test", list(_opcije_t),
                                 format_func=lambda i: f"{_opcije_t[i].get('naziv')} · "
                                                       f"{model.tekst(_opcije_t[i].get('status'))}",
                                 key="v2_obj_test")
        _d = _opcije_t[_odabir_t]

        _u_roku = dodjele.rok_dodjele({}, _d)
        _k1, _k2, _k3, _k4 = st.columns(4)
        _k1.metric("Zadataka", _d.get("broj_zadataka"))
        _k2.metric("Bodova", _d.get("bodovi_ukupno"))
        _k3.metric("Rok", f"{model.datum_hr(_u_roku['od'])} – {model.datum_hr(_u_roku['do'])}")
        _k4.metric("Dodijeljeno", len([x for x in _dodjele()
                                       if model.tekst(x.get("definicija_id")) == _odabir_t]))

        st.divider()
        # ============================================================ KOME OBJAVLJUJEM (jedini blok)
        # Obrazac preuzet iz `caki-baza-zadataka/testovi_online.py` (Caki 28.10.2026.)
        _PUBLIKE = {
            "nacrt": "🔒 Nacrt — spremi, ne vidi ga nitko",
            "grupa": "👥 Grupa / kanta (Matura ili Upisi)",
            "ucenici": "🧑 Pojedini učenici",
            "svi": "🌍 Svi učenici programa",
        }
        st.markdown("**Kome objavljujem**")
        _publika = st.radio("Kome objavljujem", list(_PUBLIKE),
                            format_func=lambda k: _PUBLIKE[k], index=0,
                            key="v2_obj_publika", label_visibility="collapsed")

        _cilj: list[dict] = []
        _program = ""

        if _publika == "grupa":
            _sve_g = []
            try:
                _sve_g = _grupe()
            except Exception:                          # noqa: BLE001
                _sve_g = []
            _opcije_g = {model.tekst(g.get("kod") or g.get("grupa_id")): g
                         for g in _sve_g if g.get("ucenici")}
            if not _opcije_g:
                st.warning("Nema grupa ni kanti s učenicima — provjeri raspored Mature ili grupe Upisa.")
            else:
                _odabrane_g = st.multiselect(
                    "Grupa / kanta", list(_opcije_g),
                    format_func=lambda k: f"{model.tekst(_opcije_g[k].get('naziv')) or k} "
                                          f"({len(_opcije_g[k]['ucenici'])} uč.)",
                    key="v2_obj_grupe")
                for _k in _odabrane_g:
                    _cilj += [{"ucenik_id": model.tekst(u.get("ucenik_id")).upper(),
                               "ime_djeteta": model.tekst(u.get("ime_djeteta"))}
                              for u in (_opcije_g[_k].get("ucenici") or [])
                              if model.tekst(u.get("ucenik_id"))]

        elif _publika == "ucenici":
            _svi_u: dict[str, str] = {}
            # 1) CRM baza učenika (pretraga po imenu)
            try:
                for _u in ucenici.svi_ucenici(_sheet(), sheet_crm()):
                    _uid = model.tekst(_u.get("ucenik_id")).upper()
                    if not _uid:
                        continue
                    _izv = ", ".join(_u.get("izvori") or [])[:40]
                    _svi_u[_uid] = (model.tekst(_u.get("ime")) or "—") + (
                        f" · {_izv}" if _izv else "")
            except Exception:                          # noqa: BLE001
                pass
            # 2) ako CRM nema tab učenika — grupe
            if not _svi_u:
                try:
                    for _g in _grupe():
                        for _u in (_g.get("ucenici") or []):
                            _uid = model.tekst(_u.get("ucenik_id")).upper()
                            if _uid:
                                _svi_u.setdefault(_uid, model.tekst(_u.get("ime_djeteta")))
                except Exception:                      # noqa: BLE001
                    pass

            if _svi_u:
                st.caption(f"Pretraga po **{len(_svi_u)}** učenika — piši dio imena ili šifru.")
                _odabrani_u = st.multiselect(
                    "Učenici", sorted(_svi_u),
                    format_func=lambda k: f"{_svi_u.get(k) or '—'} ({k})",
                    key="v2_obj_ucenici")
                _cilj += [{"ucenik_id": k, "ime_djeteta": _svi_u.get(k, "")} for k in _odabrani_u]
            else:
                st.caption("Nema popisa učenika u CRM-u — upiši šifre ručno ispod.")

            _rucno = st.text_input("Ili šifre ručno (odvoji zarezom)", key="v2_obj_sifre",
                                   placeholder="AA1111, BB2222")
            for _s in [x.strip().upper() for x in model.tekst(_rucno).split(",") if x.strip()]:
                _cilj.append({"ucenik_id": _s, "ime_djeteta": ""})

        elif _publika == "svi":
            _program = st.selectbox("Program", ["matura", "instrukcije", "upisi"],
                                    key="v2_obj_program")
            st.warning("Ovo objavljuje **svim učenicima odabranog programa** — koristi kad test "
                       "stvarno ide svima.", icon="⚠️")

        else:
            st.caption("🔒 Nacrt se sprema u Sheet, ali ga **ne vidi nijedan učenik**. Poslije ga "
                       "objavljuješ u 🧪 Testovi.")

        # ---- sažetak prije objave (UX: vidiš što ćeš napraviti)
        if _publika == "svi":
            _moze = True
            st.caption(f"Objava ide **svim učenicima programa `{_program}`**.")
        else:
            _jedinstveni = {u["ucenik_id"] for u in _cilj if u.get("ucenik_id")}
            _moze = bool(_jedinstveni)
            if _moze:
                _imena = ", ".join(sorted({u.get("ime_djeteta") or u["ucenik_id"]
                                           for u in _cilj})[:6])
                st.caption(f"Test će dobiti **{len(_jedinstveni)}** učenika: {_imena}"
                           + (" …" if len(_jedinstveni) > 6 else ""))

        if st.button("📤 Objavi", type="primary", key="v2_obj_gumb", disabled=not _moze):
            try:
                if _publika == "svi":
                    _cilj = []
                    for _g in _grupe():
                        if model.tekst(_g.get("program")).lower() != _program:
                            continue
                        _cilj += [{"ucenik_id": model.tekst(u.get("ucenik_id")).upper(),
                                   "ime_djeteta": model.tekst(u.get("ime_djeteta"))}
                                  for u in (_g.get("ucenici") or [])
                                  if model.tekst(u.get("ucenik_id"))]
                _rez = dodjele.dodaj(_sheet(), _d, _cilj, dodijelio="caki")
                if model.tekst(_d.get("status")) == "nacrt":
                    definicije.promijeni_status(_sheet(), _odabir_t, "objavljen", korisnik="caki")
                st.success(f"Dodano **{_rez.get('dodano', 0)}** učenika."
                           + (f" Preskočeno (već imaju): {len(_rez.get('preskoceno') or [])}."
                              if _rez.get("preskoceno") else ""))
                _osvjezi()
            except Exception as _e_obj:                 # noqa: BLE001
                st.error(f"Objava nije uspjela — **{type(_e_obj).__name__}**: {_e_obj}")
                with st.expander("Što provjeriti"):
                    st.caption("· postoji li tab `Dodjele` (⚙️ Postavke → Pripremi tabove)")
                    st.caption("· ima li test definiciju i barem jedan zadatak")

with tab_rezultati:
    upute.prikazi(st, "rezultati")
    testovi = _testovi()
    if not testovi:
        st.info("Ova kartica se puni kad postoji barem jedan test.")
    else:
        opcije_r = {model.tekst(x.get("definicija_id")): x for x in testovi}
        odabir_r = st.selectbox("Test", list(opcije_r),
                                format_func=lambda i: model.tekst(opcije_r[i].get("naziv")),
                                key="v2_rez_test")
        d = opcije_r[odabir_r]
        dod = [x for x in _dodjele() if model.tekst(x.get("definicija_id")) == odabir_r]
        pok = [p for p in _pokusaji() if model.tekst(p.get("definicija_id")) == odabir_r]

        po_dodjeli = {model.tekst(p.get("dodjela_id")): p for p in pok}
        redci = []
        for x in dod:
            p = po_dodjeli.get(model.tekst(x.get("dodjela_id")))
            bodovi = model.broj((p or {}).get("bodovi"))
            maks = model.broj((p or {}).get("bodovi_max"))
            redci.append({
                "Učenik": model.tekst(x.get("ime_djeteta")) or model.tekst(x.get("ucenik_id")),
                "Grupa": model.tekst(x.get("grupa")) or "—",
                "Predao": "✅" if p else "⏳",
                "Bodovi": f"{bodovi:g} / {maks:g}" if p else "—",
                "%": int(round(100 * bodovi / maks)) if maks else "",
            })
        redci.sort(key=lambda r: (-(r["%"] if isinstance(r["%"], int) else -1), r["Učenik"]))
        for i, r in enumerate(redci, start=1):
            r["Mj."] = i if isinstance(r["%"], int) else ""

        if not redci:
            st.info("Ovaj test još nije nikome poslan (kartica 👥 Objavi).")
        else:
            predali = [r["%"] for r in redci if isinstance(r["%"], int)]
            m1, m2, m3 = st.columns(3)
            m1.metric("Predalo", f"{len(predali)} / {len(redci)}")
            m2.metric("Prosjek", f"{int(round(sum(predali) / len(predali)))} %" if predali else "—")
            m3.metric("Raspon", f"{min(predali)}–{max(predali)} %" if predali else "—")
            st.dataframe(
                [{**{k: r[k] for k in ("Mj.", "Učenik", "Grupa", "Predao", "Bodovi")},
                  "% (trakica)": r["%"], "% (broj)": r["%"]}
                 for r in redci], hide_index=True, width="stretch",
                column_config={
                    # trakica + broj (Caki želi oboje)
                    "% (trakica)": st.column_config.ProgressColumn(
                        "Postotak", min_value=0, max_value=100, format="%d %%"),
                    "% (broj)": st.column_config.NumberColumn("%", format="%d %%"),
                })
            nisu = [r["Učenik"] for r in redci if r["Predao"] != "✅"]
            if nisu:
                st.warning("**Nije predalo:** " + ", ".join(nisu[:20])
                           + (" …" if len(nisu) > 20 else ""))

            # --- 👀 prati li učenik portal
            with st.expander("👀 Praćenje pristupa (koliko puta je učenik otvorio portal)"):
                try:
                    _pracenje = posjete.sazetak(_sheet())
                except Exception as e:              # noqa: BLE001
                    _pracenje = {}
                    st.caption(f"Praćenje nije dostupno: {e}")
                if not _pracenje:
                    st.caption("Još nema zabilježenih posjeta. Bilježi se od prvog ulaska učenika "
                               "u portal (jednom po sesiji, da se ne troši Google kvota).")
                else:
                    st.dataframe([{
                        "Šifra": r["ucenik_id"],
                        "Posjeta": r["posjeta"],
                        "Testova otvoreno": r["testova"],
                        "Radova": r["radova"],
                        "Zadnji put": model.tekst(r["zadnji"])[:16],
                    } for r in sorted(_pracenje.values(), key=lambda x: x["zadnji"], reverse=True)],
                        hide_index=True, width="stretch")

            # --- 📨 koga podsjetiti
            with st.expander("📨 Koga podsjetiti (i što mu napisati)"):
                try:
                    _prac = posjete.sazetak(_sheet())
                except Exception:                   # noqa: BLE001
                    _prac = {}
                _redci_p = podsjetnik.popis(dod, pok, _prac)
                _b = podsjetnik.brojevi(podsjetnik.popis(dod, pok, _prac, samo_aktivne=False))
                st.caption(f"Nije otvorio portal: **{_b['nije_otvorio']}** · "
                           f"otvorio a nije počeo: **{_b['otvorio_nije_poceo']}** · "
                           f"počeo a nije predao: **{_b['poceo_nije_predao']}** · "
                           f"predao: **{_b['predao']}**")
                if not _redci_p:
                    st.success("Svi su predali — nema koga podsjetiti.")
                else:
                    st.dataframe([{
                        "Učenik": r["ime"],
                        "Šifra": r["ucenik_id"],
                        "Grupa": r["grupa"] or "—",
                        "Stanje": r["opis"],
                        "Posjeta": r["posjeta"],
                    } for r in _redci_p], hide_index=True, width="stretch")
                    st.text_area(
                        "Tekst za kopiranje (WhatsApp / e-mail)",
                        value=podsjetnik.sve_poruke(_redci_p, model.tekst(d.get("naziv"))),
                        height=220, key="v2_podsjetnik_tekst")
                    st.caption("Aplikacija **ne šalje** poruke — kopiraj tekst i pošalji svojim "
                               "kanalom (WhatsApp grupa, e-mail, roditelj).")

            # --- izvoz za Excel (profesor zna raditi s tablicom)
            import csv
            import io

            _buf = io.StringIO()
            _pisac = csv.writer(_buf, delimiter=";")
            _pisac.writerow(["Mjesto", "Ucenik", "Sifra", "Grupa", "Predao", "Bodovi", "Maks", "Postotak"])
            for r in redci:
                _pisac.writerow([r["Mj."], r["Učenik"], "", r["Grupa"], r["Predao"],
                                 r["Bodovi"], "", r["%"]])
            st.download_button(
                "⬇️ Preuzmi rezultate (CSV za Excel)",
                data=_buf.getvalue().encode("utf-8-sig"),
                file_name=f"rezultati_{odabir_r}.csv",
                mime="text/csv",
                key="v2_rez_csv",
            )

            # --- pregled rješenja po učeniku (profesor vidi i 🎬 video)
            st.divider()
            st.markdown("**Pregled rješenja po učeniku**")
            zadaci_r = definicije.zadaci(d)
            for x in dod:
                p = po_dodjeli.get(model.tekst(x.get("dodjela_id")))
                if not p:
                    continue
                ime = model.tekst(x.get("ime_djeteta")) or model.tekst(x.get("ucenik_id"))
                bodovi = model.broj(p.get("bodovi"))
                maks = model.broj(p.get("bodovi_max"))
                with st.expander(f"{ime} — {bodovi:g}/{maks:g} bodova"):
                    # 📷 papirnati dio: priloženi skenovi i poveznice
                    _pid = model.tekst(p.get("pokusaj_id"))
                    try:
                        _radovi = radovi.za_pokusaj(_sheet(), _pid)
                    except Exception:               # noqa: BLE001
                        _radovi = []
                    st.caption("📷 Papirnati dio: " + radovi.stanje(_radovi))
                    for _r in _radovi:
                        if model.tekst(_r.get("veza")):
                            st.markdown(f"· [{model.tekst(_r.get('naziv'))}]({model.tekst(_r.get('veza'))}) "
                                        + ("✅ pregledano" if model.tekst(_r.get("potvrdjeno"))
                                           else "⏳ čeka pregled"))
                            if not model.tekst(_r.get("potvrdjeno")):
                                if st.button("✅ Potvrdi pregled", key=f"v2_rad_{_r.get('rad_id')}"):
                                    try:
                                        radovi.potvrdi(_sheet(), _r.get("rad_id"))
                                        st.success("Pregled potvrđen.")
                                        _osvjezi()
                                    except Exception as e:   # noqa: BLE001
                                        st.error(f"Nije uspjelo: {e}")
                    with st.form(f"v2_rad_form_{_pid}"):
                        _veza = st.text_input("Poveznica na sken (Drive, mobitel…)",
                                              key=f"v2_rad_veza_{_pid}")
                        _naziv = st.text_input("Naziv", value="Skenirani rad",
                                              key=f"v2_rad_naziv_{_pid}")
                        if st.form_submit_button("📎 Priloži rad") and model.tekst(_veza):
                            try:
                                radovi.dodaj_vezu(_sheet(), pokusaj_id=_pid,
                                                  ucenik_id=model.tekst(x.get("ucenik_id")),
                                                  veza=_veza, naziv=_naziv)
                                st.success("Rad priložen.")
                                _osvjezi()
                            except Exception as e:       # noqa: BLE001
                                st.error(f"Nije uspjelo: {e}")

                    # 📄 izvještaj za roditelje (HTML → ispiši kao PDF; hrvatski znakovi rade)
                    try:
                        _rez = [{
                            "naziv": model.tekst(d.get("naziv")),
                            "bodovi": model.broj(p.get("bodovi")),
                            "maks": model.broj(p.get("bodovi_max")),
                            "datum": model.datum_hr(model.tekst(p.get("predano"))),
                        }]
                        pdf_izvjestaj.prikazi_preuzimanje(
                            st,
                            ucenik={"ucenik_id": model.tekst(x.get("ucenik_id")), "ime": ime,
                                    "grupa": model.tekst(x.get("grupa"))},
                            testovi=_rez, radovi=_radovi,
                            kljuc=_pid + "_" + model.tekst(x.get("ucenik_id")),
                        )
                        izvjestaj.prikazi_preuzimanje(
                            st,
                            ucenik={"ucenik_id": model.tekst(x.get("ucenik_id")), "ime": ime,
                                    "grupa": model.tekst(x.get("grupa"))},
                            testovi=_rez, radovi=_radovi,
                            kljuc=_pid + "_" + model.tekst(x.get("ucenik_id")),
                        )
                    except Exception as e:           # noqa: BLE001
                        st.caption(f"Izvještaj se ne može pripremiti: {e}")

                    odg = provedba.odgovori(p)
                    ekran_ucenika.prikazi_pregled_rjesenja(
                        st, zadaci_r, odg,
                        pokazi_rjesenja=True, pokazi_video=True, pokazi_bodove=True)


with tab_kvaliteta:
    upute.prikazi(st, "kvaliteta")
    testovi_k = _testovi()
    if not testovi_k:
        st.info("Mjerenje počinje kad postoji test i barem nekoliko predanih radova.")
    else:
        opcije_k = {model.tekst(x.get("definicija_id")): x for x in testovi_k}
        odabir_k = st.selectbox("Test", list(opcije_k),
                                format_func=lambda i: model.tekst(opcije_k[i].get("naziv")),
                                key="v2_kval_test")
        d_k = opcije_k[odabir_k]
        pok_k = [p for p in _pokusaji() if model.tekst(p.get("definicija_id")) == odabir_k]
        ids_k = {model.tekst(p.get("pokusaj_id")) for p in pok_k}
        ocjene_k = [o for o in _ocjene() if model.tekst(o.get("pokusaj_id")) in ids_k]

        if not pok_k:
            st.info("Još nitko nije predao ovaj test — mjerenje nema smisla bez odgovora.")
        else:
            izv = analitika.izracunaj(definicije.zadaci(d_k), ocjene_k, pok_k)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Predanih", izv["ucenika"])
            m2.metric("Prosjek bodova", f"{izv['prosjek_bodova']:g}")
            m3.metric("Pouzdanost α", f"{izv['alfa']:g}")
            m4.metric("Zadataka", izv["zadataka"])
            st.caption(f"Pouzdanost: **{izv['pouzdanost']}** · medijan **{izv['medijan_bodova']:g}** · "
                       f"raspon **{izv['raspon_bodova'][0]:g}–{izv['raspon_bodova'][1]:g}**")

            for red in analitika.sazetak(izv):
                (st.warning if red.startswith("⚠️") else st.info)(red)

            ceka = sum(1 for p in pok_k if model.cijeli(p.get("ceka_provjeru"), 0) > 0)
            if ceka:
                st.warning(f"{ceka} pokušaja čeka ručnu provjeru — brojke su privremene.")

            st.dataframe([{
                "Zadatak": z["zadatak_id"],
                "Tekst": z["tekst"][:60],
                "Odgovora": z["odgovora"],
                "p (težina)": z["p"],
                "Ocjena težine": z["tezina"],
                "r (diskriminacija)": z["r"],
                "Razlikuje?": z["diskriminacija"],
                "Preporuka": z["preporuka"],
            } for z in izv["po_zadatku"]], hide_index=True, width="stretch",
                column_config={
                    "p (težina)": st.column_config.ProgressColumn(
                        "p (težina)", min_value=0.0, max_value=1.0, format="%.2f"),
                })

            st.markdown("**Po cjelinama (što najviše pada)**")
            st.dataframe([{
                "Cjelina": c["cjelina"],
                "Zadataka": c["zadataka"],
                "Odgovora": c["odgovora"],
                "Točnih": c["tocnih"],
                "p": c["p"],
                "Udio bodova": c["udio_bodova"],
            } for c in izv.get("po_cjelinama", [])], hide_index=True, width="stretch")

            st.markdown("**Distraktori (koji su odgovori birani)**")
            for z in izv["po_zadatku"]:
                if not z["distraktori"]:
                    continue
                with st.expander(f"{z['zadatak_id']} — p={z['p']}, r={z['r']}"):
                    for dist in z["distraktori"]:
                        oznaka = "✅ točan" if dist["tocan"] else ("⚫ mrtav" if dist["mrtav"] else "")
                        st.progress(min(1.0, float(dist["udio"])),
                                    text=f"{dist['opcija'][:40]} — {dist['odabrano']}× {oznaka}")


with tab_ocjene:
    upute.prikazi(st, "ocjene")
    testovi_z = _testovi()
    if not testovi_z:
        st.info("Ocjene se računaju kad postoje testovi i dodjele.")
    else:
        testovi_po_id = {model.tekst(x.get("definicija_id")): x for x in testovi_z}
        redci = zakljucna.prikupi(_dodjele(), _pokusaji(), testovi_po_id)

        if not redci:
            st.info("Nema dodjela — prvo objavi test u 👥 Objavi.")
        else:
            sazetak = zakljucna.sazetak(redci)
            m1, m2, m3 = st.columns(3)
            m1.metric("Učenika", sazetak["ukupno"])
            m2.metric("Prosjek razreda", f"{sazetak['prosjek_razredda'] if False else sazetak['prosjek_razreda']} %")
            m3.metric("Odličnih (5)", sazetak["po_ocjeni"].get(5, 0))

            for u in zakljucna.upozorenja(redci):
                st.warning(u)

            st.dataframe(
                [{**red, "Prosjek (trakica)": red["Prosjek %"]}
                 for red in zakljucna.tablica(redci)], hide_index=True, width="stretch",
                column_config={
                    "Prosjek (trakica)": st.column_config.ProgressColumn(
                        "Prosjek", min_value=0, max_value=100, format="%d %%"),
                    "Prosjek %": st.column_config.NumberColumn("Prosjek %", format="%d %%"),
                })

            st.caption("Predlog ocjene je **izračun**, ne odluka. Profesor ga mijenja po svom "
                       "nahođenju — pragovi su 50/65/80/90 %.")

            import csv
            import io

            _buf = io.StringIO()
            _p = csv.writer(_buf, delimiter=";")
            _p.writerow(["Ucenik", "Sifra", "Grupa", "Testova", "Prosjek %", "Predlog"])
            for r in redci:
                _p.writerow([r.get("ime") or r["ucenik_id"], r["ucenik_id"], r.get("grupa", ""),
                             f"{r['pisao']}/{r['pisao'] + r['nije_pisao_broj']}",
                             r["prosjek"], r["predlog_naziv"]])
            st.download_button("⬇️ Preuzmi ocjene (CSV)", data=_buf.getvalue().encode("utf-8-sig"),
                               file_name="zakljucne_ocjene.csv", mime="text/csv", key="v2_ocj_csv")


with tab_ucenik:
    upute.prikazi(st, "ucenik")
    testovi_u = _testovi()
    if not testovi_u:
        st.info("**Još nema ni jednog testa** — zato je ova kartica prazna. Rješavanje se veže na test.")
        st.markdown("**Što napraviti:** 🧪 Testovi → označi zadatke → *Spremi kao nacrt* → vrati se ovamo. "
                    "Ili odmah isprobaj ekran ispod, **bez spremanja**:")
        with st.expander("⚡ Brzi pregled — 3 zadatka iz baze, ništa se ne sprema"):
            zadaci_bp = _zadaci()
            if not zadaci_bp:
                st.caption("Baza se ne može pročitati — vidi ⚙️ Postavke → 🩺 Provjera baze.")
            else:
                opcije_bp = {model.tekst(z.get("id")): z for z in zadaci_bp[:300] if model.tekst(z.get("id"))}
                odabir_bp = st.multiselect(
                    "Zadaci za probu (prvih 300 u bazi)", list(opcije_bp),
                    default=list(opcije_bp)[:3],
                    format_func=lambda i: f"{i} · {model.tekst(opcije_bp[i].get('tekst'))[:60]}",
                    key="v2_bp_zadaci")
                if odabir_bp and st.button("▶ Otvori pregled", type="primary", key="v2_bp_otvori"):
                    try:
                        d_bp = definicije.nova_definicija(
                            definicija_id="PREGLED", naziv="Brzi pregled", predmet="matematika",
                            zadaci_=[opcije_bp[i] for i in odabir_bp], trajanje_min=45,
                            status="objavljen")
                        dodjela_bp = {
                            "dodjela_id": "PREGLED-BP", "definicija_id": "PREGLED",
                            "ucenik_id": "PREGLED", "ime_djeteta": "Pregled",
                            "varijanta_seed": "PREGLED:BP", "status": "dodijeljeno",
                        }
                        st.session_state["v2_bp_aktivno"] = True
                        ekran_ucenika.prikazi(st, None, d_bp, dodjela_bp, dry=True)
                    except Exception as e:              # noqa: BLE001
                        st.error(f"Pregled se ne može otvoriti: {e}")
    else:
        opcije_u = {model.tekst(x.get("definicija_id")): x for x in testovi_u}
        odabir_u = st.selectbox("Test", list(opcije_u),
                                format_func=lambda i: f"{model.tekst(opcije_u[i].get('naziv'))} · "
                                                      f"{model.tekst(opcije_u[i].get('status'))}",
                                key="v2_uc_test")
        d_u = opcije_u[odabir_u]

        nacin_u = st.radio("Način", ["pregled", "ucenik"], horizontal=True,
                           format_func=lambda k: ("👁️ Pregled — ništa se ne sprema" if k == "pregled"
                                                  else "🧑 Stvarni učenik (ima dodjelu)"),
                           key="v2_uc_nacin")

        if nacin_u == "pregled":
            st.caption("Ovo je **točno ono što učenik vidi**: pitanje po pitanju, matematički unos, "
                       "autosave (ovdje isključen), predaja s upozorenjem. Ništa se ne zapisuje.")
            _dodjela_pregled = {
                "dodjela_id": "PREGLED-" + odabir_u,
                "definicija_id": odabir_u,
                "ucenik_id": "PREGLED",
                "ime_djeteta": "Pregled",
                "varijanta_seed": "PREGLED:" + odabir_u,
                "status": "dodijeljeno",
            }
            try:
                ekran_ucenika.prikazi(st, _sheet(), d_u, _dodjela_pregled, dry=True)
            except Exception as e:                      # noqa: BLE001
                st.error(f"Pregled se ne može otvoriti: {e}")
        else:
            sifra_u = st.text_input("Šifra učenika", key="v2_uc_sifra",
                                    placeholder="AA1111").strip().upper()
            if not sifra_u:
                st.caption("Upiši šifru učenika koji ima ovaj test (kartica 👥 Objavi).")
            else:
                dodjela_u = dodjele.jedna(_sheet(), odabir_u, sifra_u)
                if not dodjela_u:
                    st.warning(f"Učenik `{sifra_u}` nema ovaj test. Dodaj ga u 👥 Objavi.")
                else:
                    stanje_u = dodjele.stanje_roka(dodjela_u, d_u)
                    st.caption(f"Rok: **{model.datum_hr(dodjela_u.get('rok_od')) or '—'}** – "
                               f"**{model.datum_hr(dodjela_u.get('rok_do')) or '—'}** · stanje: **{stanje_u}**")
                    if provedba.predano(_sheet(), dodjela_u.get("dodjela_id")):
                        st.success("Učenik je već predao — vidi 📊 Rezultati.")
                    elif stanje_u != "otvoren":
                        st.warning("Rok još nije otvoren ili je prošao — rješavanje nije moguće.")
                    else:
                        try:
                            ekran_ucenika.prikazi(st, _sheet(), d_u, dodjela_u, dry=False)
                        except Exception as e:          # noqa: BLE001
                            st.error(f"Rješavanje se ne može otvoriti: {e}")


with tab_postavke:
    upute.prikazi(st, "postavke")

    st.subheader("🧪 Samoprovjera (prijašnja rješenja)")
    with st.expander("Pokaži samoprovjeru", expanded=False):
        try:
            samoprovjera.prikazi(st)
        except Exception as _e_sp:                 # noqa: BLE001
            st.caption(f"Samoprovjera nije dostupna: {_e_sp}")

    st.subheader("🩺 Provjera sustava")
    try:
        _u = _je_kopija(getattr(_baza(), "title", ""))
        if _u:
            st.error(_u)
    except Exception:                                   # noqa: BLE001
        pass
    c1, c2, c3 = st.columns(3)
    c1.metric("Upis u bazu", "UKLJUČEN" if tablice.PISANJE else "isključen")
    testovi_svi = _testovi()
    c2.metric("Testova", len(testovi_svi))
    c3.metric("Dodjela", len(_dodjele()))

    # --- baza zadataka
    with st.expander("🩺 Provjera baze", expanded=not _zadaci()):
        try:
            _info = _info_baze()
            for red in _info:
                st.caption(red)
        except Exception as e:                          # noqa: BLE001
            st.error(f"Baza se ne može provjeriti: {e}")
        try:
            _shema = banka.provjeri_shemu(_baza())
            if not _shema["postoji"]:
                st.error("Tab `Zadaci` nije nađen — provjeri `SHEET_ID`.")
            elif _shema["nedostaju"]:
                st.error("**Baza je promijenila shemu — nedostaju stupci koje sustav čita:** "
                         + ", ".join(f"`{s}`" for s in _shema["nedostaju"])
                         + ".\n\nAko su preimenovani, javi mi točan naziv — popravak je u "
                           "`banka.zadatak_iz_retka()` (jedna funkcija).")
            else:
                st.success(f"Svi stupci koje sustav čita postoje ({_shema['stupaca']} stupaca u bazi).")
            if _shema.get("neobavezni_nedostaju"):
                st.caption("Neobavezni stupci kojih nema (sustav radi i bez njih): "
                           + ", ".join(f"`{s}`" for s in _shema["neobavezni_nedostaju"]))
        except Exception as e:                          # noqa: BLE001
            st.caption(f"Shema se ne može provjeriti: {e}")

        if st.button("↻ Ponovno provjeri bazu", key="v2_provjeri_bazu"):
            st.cache_data.clear()
            st.rerun()

    # --- tajne
    with st.expander("🔑 Tajne koje aplikacija vidi (imena, ne vrijednosti)"):
        try:
            imena = sorted(st.secrets.keys())
        except Exception:                               # noqa: BLE001
            imena = []
        if not imena:
            st.caption("Secrets nije dostupan.")
        for ime in imena:
            vrijednost = _tajna(ime)
            if ime.startswith("GOOGLE_SERVICE_ACCOUNT") or "PASSWORD" in ime.upper() or "KEY" in ime.upper():
                stanje = "✅ postavljeno" if vrijednost else "❌ prazno"
            else:
                stanje = f"`{vrijednost[:10]}…`" if vrijednost else "❌ prazno"
            st.caption(f"· `{ime}` — {stanje}")

    # --- video
    try:
        info_v = banka.stupci_videa(_baza())
    except Exception as e:                              # noqa: BLE001
        info_v = {"postoji": False, "stupac": "video_url", "stupac_naslov": ""}
        st.caption(f"Video se ne može provjeriti: {e}")
    if info_v.get("postoji"):
        st.success(f"🎬 Stupac `{info_v['stupac']}` postoji u bazi — video se čita odatle "
                   "(sustav **ne dodaje** stupce).")
    else:
        st.warning(f"U bazi nema stupca `{info_v.get('stupac', 'video_url')}`.")

    # --- tabovi
    st.divider()
    with st.expander("🔧 Pripremi tabove (samo prvi put)"):
        st.warning("Ovo stvara **nove** tabove u CRM Sheetu. Postojeće tabove i bazu zadataka "
                   "**ne dira**. Ako tabovi već postoje, ništa se ne mijenja.")
        st.caption("Tabovi koji nastaju: " + ", ".join(tablice.ZAGLAVLJA) + ".")
        _potvrda = st.checkbox("Razumijem da se radi o ŽIVOM CRM Sheetu", key="v2_potvrdi_tabovi")
        if st.button("Napravi tabove", disabled=not (_potvrda and tablice.PISANJE)):
            try:
                napravljeni = tablice.osiguraj_sve(_sheet())
                st.success(f"Napravljeno: {', '.join(napravljeni) or 'već postoji — ništa nije mijenjano'}")
                _osvjezi()
            except Exception as e:                      # noqa: BLE001
                st.error(f"Nije uspjelo: {e}")
        if not tablice.PISANJE:
            st.caption("Uključi upis u bočnoj traci da bi gumb radio.")

    # --- Student View (samo ako ima testova)
    if testovi_svi:
        st.divider()
        opcije_s = {model.tekst(x.get("definicija_id")): x for x in testovi_svi}
        odabir_s = st.selectbox("Što učenik vidi — za test", list(opcije_s),
                                format_func=lambda i: model.tekst(opcije_s[i].get("naziv")),
                                key="v2_post_test")
        for red in definicije.sto_vidi(opcije_s[odabir_s].get("student_view_json")):
            st.caption(f"· {red['naziv']} — **{red['znaci']}**")
        st.caption("Mijenjanje tih razina dolazi uz ekran rješavanja (Faza B).")
