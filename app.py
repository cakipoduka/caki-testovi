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

import banka
import definicije
import dodjele
import grupe
import model
import tablice
import upute
from veza import sheet_baze, sheet_crm

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
_sto_secret = model.tekst(st.secrets.get("V2_UPIS")).lower() in ("da", "1", "true")
if "v2_upis" not in st.session_state:
    st.session_state["v2_upis"] = _sto_secret
tablice.postavi_pisanje(bool(st.session_state.get("v2_upis")))


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


# ------------------------------------------------------------------ zaglavlje

st.title("🧪 Testovi — nova generacija")
st.caption("Paralelni razvoj: stara aplikacija i dalje radi. Ovdje se gradi sustav po MASTER dokumentu.")

with st.sidebar:
    st.markdown("### 🧪 CAKI Testovi v2")
    if st.button("🔄 Osvježi podatke"):
        _osvjezi()
    st.caption("Faza A: testovi, objave, rezultati. Rješavanje dolazi sljedeće.")

    st.divider()
    st.markdown("#### 🔐 Živa baza")
    if st.session_state.get("v2_upis"):
        st.success("Upis je UKLJUČEN — mijenja pravi CRM Sheet.")
    else:
        st.info("Upis je ISKLJUČEN — sve se samo čita. Ništa se ne može pokvariti.")
    st.toggle("Uključi upis u živu bazu", key="v2_upis",
              help="Kad je isključeno, nijedan podatak se ne upisuje (samo čitanje). "
                   "Uključi tek kad želiš spremiti test ili objaviti učenicima.")
    tablice.postavi_pisanje(bool(st.session_state.get("v2_upis")))
    st.divider()
    with st.expander("🔧 Pripremi tabove (samo prvi put)"):
        st.warning("Ovo stvara **nove** tabove u CRM Sheetu. Postojeće tabove i bazu zadataka "
                   "**ne dira**. Ako tabovi već postoje, ništa se ne mijenja.")
        st.caption("Tabovi koji nastaju: " + ", ".join(tablice.ZAGLAVLJA) + ".")
        _potvrda = st.checkbox("Razumijem da se radi o ŽIVOM CRM Sheetu", key="v2_potvrdi_tabovi")
        if st.button("Napravi tabove", disabled=not (_potvrda and st.session_state.get("v2_upis"))):
            try:
                napravljeni = tablice.osiguraj_sve(_sheet())
                st.success(f"Napravljeno: {', '.join(napravljeni) or 'već postoji — ništa nije mijenjano'}")
                _osvjezi()
            except Exception as e:                      # noqa: BLE001
                st.error(f"Nije uspjelo: {e}")
        if not st.session_state.get("v2_upis"):
            st.caption("Uključi upis u bočnoj traci da bi gumb radio.")

tab_testovi, tab_objavi, tab_rezultati, tab_postavke = st.tabs(
    ["🧪 Testovi", "👥 Objavi", "📊 Rezultati", "⚙️ Postavke"])


# ------------------------------------------------------------------ 🧪 Testovi

with tab_testovi:
    upute.prikazi(st, "testovi")

    testovi = _testovi()
    if not testovi:
        st.info("Još nema testova. Slijedi korake niže — prvi test se pravi iz baze zadataka.")
    else:
        st.dataframe([{
            "ID": model.tekst(t.get("definicija_id")),
            "Naziv": model.tekst(t.get("naziv")),
            "Status": model.tekst(t.get("status")),
            "Zadataka": t.get("broj_zadataka"),
            "Bodova": t.get("bodovi_ukupno"),
            "Rok": f"{model.datum_hr(t.get('rok_od'))} – {model.datum_hr(t.get('rok_do'))}",
            "Vrsta": definicije.VRSTA_NAZIV.get(model.tekst(t.get("vrsta")), ""),
        } for t in testovi], hide_index=True, width="stretch")

    st.divider()
    st.subheader("➕ Novi test iz baze")

    zadaci_svi = _zadaci()
    if not zadaci_svi:
        st.warning("Baza je prazna ili se ne može pročitati — provjeri `SHEET_ID` i dijeljenje Sheeta.")
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    f_tekst = c1.text_input("Traži u tekstu / ID-u", key="v2_f_tekst")
    f_cjelina = c2.selectbox("Cjelina", [""] + banka.vrijednosti(zadaci_svi, "cjelina"), key="v2_f_cj")
    f_tezina = c3.selectbox("Težina", [""] + banka.vrijednosti(zadaci_svi, "tezina"), key="v2_f_tez")
    f_tip = c4.selectbox("Tip", ["", "kratki_odgovor", "visestruki_izbor"], key="v2_f_tip")

    pronadeni = banka.filtriraj(zadaci_svi, tekst=f_tekst, cjelina=f_cjelina,
                                tezina=f_tezina, tip=f_tip)
    st.caption(f"U bazi **{len(zadaci_svi)}** zadataka · filtar pronašao **{len(pronadeni)}** "
               f"· s videom: **{sum(1 for z in pronadeni if model.tekst(z.get('video_url')))}**")

    prikaz = pronadeni[:200]
    opcije = {model.tekst(z.get("id")): z for z in prikaz}
    odabrani_id = st.multiselect(
        "Odaberi zadatke (redoslijed = redoslijed u testu)", list(opcije),
        format_func=lambda i: f"{i} · {model.tekst(opcije[i].get('tekst'))[:70]}",
        key="v2_odabrani")
    if len(pronadeni) > len(prikaz):
        st.caption(f"Prikazano prvih {len(prikaz)} — preciziraj filtar da dođeš do ostalih.")

    odabrani = [opcije[i] for i in odabrani_id]
    if odabrani:
        st.caption(f"Odabrano **{len(odabrani)}** zadataka · **{definicije.bodovi_ukupno(odabrani):g}** bodova")

    with st.form("v2_novi_test"):
        g1, g2, g3 = st.columns(3)
        naziv = g1.text_input("Naziv testa", placeholder="npr. Matura — linearna funkcija")
        predmet = g2.text_input("Predmet", value="matematika")
        vrsta = g3.selectbox("Vrsta", definicije.VRSTE,
                             format_func=lambda v: definicije.VRSTA_NAZIV.get(v, v))
        h1, h2, h3 = st.columns(3)
        trajanje = h1.number_input("Trajanje (min)", 5, 240, 45, 5)
        rok_od = h2.date_input("Rok od")
        rok_do = h3.date_input("Rok do")
        napomena = st.text_area("Napomena za sebe", height=70)
        posalji = st.form_submit_button("💾 Spremi kao nacrt", type="primary",
                                        disabled=not odabrani)

    if posalji:
        try:
            novi_id = tablice.novi_id([model.tekst(t.get("definicija_id")) for t in _testovi()], "T26-")
            d = definicije.nova_definicija(
                definicija_id=novi_id, naziv=naziv, predmet=predmet, zadaci_=odabrani,
                trajanje_min=int(trajanje), rok_od=model.iso_datum(rok_od),
                rok_do=model.iso_datum(rok_do), vrsta=vrsta, autor="caki",
                napomena=napomena, status="nacrt")
            greske = definicije.validiraj(d)
            if greske:
                for g in greske:
                    st.error(g)
            else:
                tablice.dodaj(_sheet(), tablice.TAB_DEFINICIJE, [d])
                tablice.zapisi_radnju(_sheet(), "caki", "novi_test", novi_id, naziv)
                st.success(f"Spremljeno kao **nacrt** `{novi_id}` — nitko ga još ne vidi. "
                           f"Objavi ga u kartici 👥 Objavi.")
                _osvjezi()
        except Exception as e:                          # noqa: BLE001
            st.error(f"Nije uspjelo: {e}")


# ------------------------------------------------------------------ 👥 Objavi

with tab_objavi:
    upute.prikazi(st, "objavi")
    testovi = _testovi()
    if not testovi:
        st.info("Prvo napravi test u kartici 🧪 Testovi.")
        st.stop()

    opcije_t = {model.tekst(t.get("definicija_id")): t for t in testovi}
    odabir_t = st.selectbox("Test", list(opcije_t),
                            format_func=lambda i: f"{opcije_t[i].get('naziv')} · "
                                                  f"{model.tekst(opcije_t[i].get('status'))}",
                            key="v2_obj_test")
    d = opcije_t[odabir_t]

    u_roku = dodjele.rok_dodjele({}, d)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Zadataka", d.get("broj_zadataka"))
    k2.metric("Bodova", d.get("bodovi_ukupno"))
    k3.metric("Rok", f"{model.datum_hr(u_roku['od'])} – {model.datum_hr(u_roku['do'])}")
    k4.metric("Dodijeljeno", len([x for x in _dodjele()
                                  if model.tekst(x.get("definicija_id")) == odabir_t]))

    st.markdown("**Kome ide**")
    nacin = st.radio("Način", ["grupa", "rucno"], horizontal=True,
                     format_func=lambda k: "👥 Grupa / kanta" if k == "grupa" else "🧑 Šifre učenika",
                     key="v2_obj_nacin")

    ucenici = []
    grupa_naziv = ""
    if nacin == "grupa":
        grupe = _grupe()
        if not grupe:
            st.caption("Nema grupa ni kanti (Upisi / Raspored Mature) — upiši šifre ručno.")
        else:
            opcije_g = {g["kod"]: g for g in grupe}
            odabrane = st.multiselect(
                "Grupa / kanta", list(opcije_g),
                format_func=lambda k: f"{opcije_g[k]['naziv']} ({len(opcije_g[k]['ucenici'])} uč.)",
                key="v2_obj_grupe")
            for k in odabrane:
                ucenici += list(opcije_g[k]["ucenici"])
            grupa_naziv = ", ".join(opcije_g[k]["naziv"] for k in odabrane)
    else:
        sifre = st.text_input("Šifre učenika (zarez)", key="v2_obj_sifre",
                              placeholder="AA1111, BB2222")
        ucenici = [{"ucenik_id": s.strip().upper()} for s in model.tekst(sifre).split(",") if s.strip()]

    if st.button("📤 Objavi", type="primary", disabled=not ucenici, key="v2_obj_gumb"):
        try:
            rez = dodjele.dodaj(_sheet(), d, ucenici, grupa=grupa_naziv, dodijelio="caki")
            if model.tekst(d.get("status")) == "nacrt":
                definicije.promijeni_status(_sheet(), odabir_t, "objavljen", korisnik="caki")
            st.success(f"Dodano **{rez['dodano']}** učenika."
                       + (f" Preskočeno (već imaju): {len(rez['preskoceno'])}."
                          if rez["preskoceno"] else ""))
            _osvjezi()
        except Exception as e:                          # noqa: BLE001
            st.error(f"Nije uspjelo: {e}")

    moje = [x for x in _dodjele() if model.tekst(x.get("definicija_id")) == odabir_t]
    if moje:
        st.markdown(f"**Kome je poslan ({len(moje)})**")
        st.dataframe([{
            "Učenik": model.tekst(x.get("ime_djeteta")) or model.tekst(x.get("ucenik_id")),
            "Šifra": model.tekst(x.get("ucenik_id")),
            "Grupa": model.tekst(x.get("grupa")) or "—",
            "Status": model.tekst(x.get("status")),
            "Rok": (lambda r: f"{model.datum_hr(r['od'])} – {model.datum_hr(r['do'])}"
                    + (" (od dodjele)" if r["produzen"] else ""))(
                        dodjele.rok_dodjele(x, d)),
        } for x in moje], hide_index=True, width="stretch")


# ------------------------------------------------------------------ 📊 Rezultati

with tab_rezultati:
    upute.prikazi(st, "rezultati")
    testovi = _testovi()
    if not testovi:
        st.info("Još nema testova.")
        st.stop()

    opcije_r = {model.tekst(t.get("definicija_id")): t for t in testovi}
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
        st.dataframe([{k: r[k] for k in ("Mj.", "Učenik", "Grupa", "Predao", "Bodovi", "%")}
                      for r in redci], hide_index=True, width="stretch")
        nisu = [r["Učenik"] for r in redci if r["Predao"] != "✅"]
        if nisu:
            st.warning("**Nije predalo:** " + ", ".join(nisu[:20]) + (" …" if len(nisu) > 20 else ""))


# ------------------------------------------------------------------ ⚙️ Postavke

with tab_postavke:
    upute.prikazi(st, "postavke")
    testovi = _testovi()
    if testovi:
        opcije_s = {model.tekst(t.get("definicija_id")): t for t in testovi}
        odabir_s = st.selectbox("Test", list(opcije_s),
                                format_func=lambda i: model.tekst(opcije_s[i].get("naziv")),
                                key="v2_post_test")
        d = opcije_s[odabir_s]
        st.markdown("**Što učenik vidi (po ovom testu)**")
        for red in definicije.sto_vidi(d.get("student_view_json")):
            st.caption(f"· {red['naziv']} — **{red['znaci']}**")
        st.caption("Mijenjanje tih razina dolazi u sljedećem koraku (Faza B), kad i ekran rješavanja.")
    else:
        st.info("Nema testova — postavke se vežu na test.")

    st.divider()
    with st.expander("🔑 Tajne koje aplikacija vidi (samo imena, nikad vrijednosti)"):
        try:
            imena = sorted(st.secrets.keys())
        except Exception:                               # noqa: BLE001
            imena = []
        if not imena:
            st.caption("Secrets nije dostupan.")
        for ime in imena:
            vrijednost = _tajna(ime)
            if ime.startswith("GOOGLE_SERVICE_ACCOUNT") or "PASSWORD" in ime.upper():
                stanje = "✅ postavljeno" if vrijednost else "❌ prazno"
            else:
                stanje = f"`{vrijednost[:8]}…`" if vrijednost else "❌ prazno"
            st.caption(f"· `{ime}` — {stanje}")
        st.caption("Nikad ne prikazujemo sadržaj ključa ni lozinke — samo prva slova ID-eva.")

    st.markdown("**Baza zadataka**")
    zadaci_svi = _zadaci()
    if zadaci_svi:
        b = banka.brojevi(zadaci_svi)
        st.caption(f"Ukupno **{b['ukupno']}** · s videom **{b['sa_videom']}** · "
                   f"cjelina: **{len(b['po_cjelini'])}** · težina: **{len(b['po_tezini'])}**")
    try:
        info_v = banka.stupci_videa(_baza())
    except Exception as e:                              # noqa: BLE001
        info_v = {"postoji": False, "stupac": "video_url", "stupac_naslov": ""}
        st.caption(f"Baza se ne može provjeriti: {e}")
    if info_v["postoji"]:
        st.success(f"🎬 Stupac `{info_v['stupac']}` postoji u bazi — video rješenja se čitaju odatle. "
                   "Sustav **ne dodaje** stupce u bazu.")
    else:
        st.warning(f"U bazi nema stupca `{info_v['stupac']}`. Ako ga želiš koristiti, dodaj ga ručno "
                   "u tab `Zadaci` — sustav to **ne radi sam** na živoj bazi.")
