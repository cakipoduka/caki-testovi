"""
CAKI testovi v2 — `pages/1_Ucenik.py`
PRAVA STRANICA UČENIKA: prijava šifrom → popis testova → rješavanje → pregled rezultata.

Ovo je ono što učenik vidi. Admin kartice (Testovi, Objavi, Rezultati, Postavke) su u glavnoj
aplikaciji i ovdje se ne učitavaju.

PRIJAVA
    Šifra učenika (npr. `AA1111`) — ista šifra koju učenik ima u CRM-u i portalu.
    Lozinka nije potrebna jer učenik vidi **samo svoje** dodjele.

STANJA
    · rok nije počeo / prošao → poruka, nema rješavanja
    · `u_tijeku`  → „▶ Nastavi" (autosave čuva odgovore)
    · `predano`   → rezultat + pregled rješenja **po Student View-u**
"""
from __future__ import annotations

import streamlit as st

import definicije
import dodjele
import ekran_ucenika
import drive
import model
import posjete
import provedba
import radovi
from veza import sheet_crm

st.set_page_config(page_title="CAKI — Testovi", page_icon="📝", layout="centered")


@st.cache_resource(show_spinner=False)
def _sheet():
    return sheet_crm()


def _prijava() -> str:
    if st.session_state.get("v2u_sifra"):
        return st.session_state["v2u_sifra"]
    st.title("📝 CAKI — Testovi")
    st.caption("Prijavi se svojom šifrom (dobio si je u školi).")
    with st.form("v2u_prijava"):
        sifra = st.text_input("Šifra učenika", placeholder="npr. AA1111").strip().upper()
        if st.form_submit_button("Prijavi se", type="primary") and sifra:
            st.session_state["v2u_sifra"] = sifra
            st.rerun()
    return ""


def _pokusaj_za(sheet, dodjela: dict):
    """Aktivni pokušaj ili zadnji predani za tu dodjelu."""
    did = model.tekst(dodjela.get("dodjela_id"))
    return provedba.aktivni(sheet, did) or provedba.zadnji_predani(sheet, did)


def _pregled_rjesenja(sheet, dodjela: dict, definicija: dict, pokusaj: dict) -> None:
    """Prikaži ono što Student View dopušta — ništa više."""
    view = definicija.get("student_view_json")
    rok_prosao = dodjele.stanje_roka(dodjela, definicija) == "zatvoren"
    smije_rjesenja = definicije.smije_vidjeti(view, "rjesenja", predano=True, rok_prosao=rok_prosao)
    smije_video = definicije.smije_vidjeti(view, "video", predano=True, rok_prosao=rok_prosao)
    smije_bodove = definicije.smije_vidjeti(view, "bodovi", predano=True, rok_prosao=rok_prosao)

    if not smije_rjesenja:
        st.caption("Rješenja će biti dostupna "
                   + ("nakon isteka roka." if rok_prosao is False else "kasnije."))
        return
    ekran_ucenika.prikazi_pregled_rjesenja(
        st, definicije.zadaci(definicija), provedba.odgovori(pokusaj),
        pokazi_rjesenja=True, pokazi_video=smije_video, pokazi_bodove=smije_bodove)


def _kartica(dodjela: dict, definicija: dict, pokusaj) -> None:
    naziv = model.tekst(definicija.get("naziv")) or model.tekst(definicija.get("definicija_id"))
    trajanje = model.cijeli(definicija.get("trajanje_min"), 45)
    bodovi = model.broj(definicija.get("bodovi_ukupno"))
    stanje = dodjele.stanje_roka(dodjela, definicija)
    rok = dodjele.rok_dodjele(dodjela, definicija)
    kljuc = model.tekst(dodjela.get("dodjela_id"))

    with st.container(border=True):
        st.markdown(f"### {naziv}")
        st.caption(f"{model.cijeli(definicija.get('broj_zadataka'), 0)} zadataka · "
                   f"{bodovi:g} bodova · {trajanje} min")
        st.caption(f"Rok: **{model.datum_hr(rok['od']) or '—'}** – "
                   f"**{model.datum_hr(rok['do']) or '—'}**")

        # 📷 učenik sam prilaže fotografiju/sken papirnog rada (doma, mobitelom)
        with st.expander("📷 Priloži svoj rad (fotografija ili sken)"):
            _pid = ""
            _svi = provedba.pokusaji_ucenika(st.session_state["_v2u_sheet"], kljuc) \
                if hasattr(provedba, "pokusaji_ucenika") else []
            if _svi:
                _pid = model.tekst(_svi[-1].get("pokusaj_id"))
            if not _pid:
                st.caption("Rad možeš priložiti kad test počne. Fotografiraj papir i pošalji ovdje.")
            else:
                _postojeci = radovi.za_pokusaj(st.session_state["_v2u_sheet"], _pid)
                if _postojeci:
                    st.caption("Već priloženo: " + radovi.stanje(_postojeci))
                _datoteka = st.file_uploader("Odaberi fotografiju ili PDF", type=["png", "jpg", "jpeg", "pdf"],
                                             key=f"v2u_rad_{kljuc}")
                _link = st.text_input("…ili zalijepi poveznicu (npr. s mobitela)",
                                      key=f"v2u_rad_link_{kljuc}")
                if st.button("📤 Pošalji rad", key=f"v2u_rad_salji_{kljuc}"):
                    try:
                        _veza = ""
                        if _datoteka is not None:
                            _bajtovi = _datoteka.getvalue()
                            _folder = drive.folder_id(st.secrets)
                            _veza, _greska = drive.ucitaj(_bajtovi, radovi.sef_datoteke(_datoteka.name),
                                                          folder=_folder)
                            if _greska:
                                st.warning(_greska + " Pošalji kao poveznicu ispod.")
                        radovi.dodaj_ucenikov_rad(
                            st.session_state["_v2u_sheet"], pokusaj_id=_pid, ucenik_id=sifra,
                            veza=_veza or model.tekst(_link),
                            sadrzaj=(_datoteka.getvalue() if (_datoteka and not _veza) else None),
                            naziv=(_datoteka.name if _datoteka else "Poveznica"))
                        posjete.zabiljezi(st.session_state["_v2u_sheet"], ucenik_id=sifra,
                                          radnja="rad", detalj=kljuc)
                        st.success("Rad je poslan profesoru. ✅")
                        st.rerun()
                    except Exception as e:              # noqa: BLE001
                        st.error(f"Rad nije poslan: {e}")

        if pokusaj and model.tekst(pokusaj.get("status")) == provedba.STATUS_PREDANO:
            bod = model.broj(pokusaj.get("bodovi"))
            maks = model.broj(pokusaj.get("bodovi_max"))
            postotak = int(round(100 * bod / maks)) if maks else 0
            st.success(f"✅ Predano — **{bod:g} / {maks:g}** bodova ({postotak} %)")
            with st.expander("Pogledaj rješenja"):
                _pregled_rjesenja(st.session_state["_v2u_sheet"], dodjela, definicija, pokusaj)
        elif stanje != "otvoren":
            st.warning("Rok još nije otvoren ili je prošao — javi se profesoru.")
        else:
            tekst = "▶ Nastavi" if pokusaj else "▶ Počni"
            if st.button(tekst, type="primary", key=f"v2u_{kljuc}"):
                st.session_state["v2u_aktivni"] = kljuc
                st.rerun()


def main() -> None:
    sifra = _prijava()
    if not sifra:
        return
    try:
        sheet = _sheet()
    except Exception as e:                              # noqa: BLE001
        st.error(f"Aplikacija se ne može spojiti na podatke: {e}")
        return
    st.session_state["_v2u_sheet"] = sheet

    # 👀 zabilježi posjetu — JEDNOM po sesiji (štiti Google kvotu od 60 upisa/min)
    try:
        naprava = posjete.naprava_iz_upita(
            st.context.headers.get("User-Agent", "") if hasattr(st, "context") else "")
        posjete.biljeska_jednom(st, sheet, ucenik_id=sifra, radnja="posjeta", naprava=naprava)
    except Exception:                                   # noqa: BLE001 — praćenje ne blokira
        pass

    lijevo, desno = st.columns([3, 1])
    lijevo.markdown(f"### 📝 Moji testovi · **{sifra}**")
    if desno.button("Odjava", key="v2u_odjava"):
        for k in ("v2u_sifra", "v2u_aktivni"):
            st.session_state.pop(k, None)
        st.rerun()

    try:
        moje = dodjele.za_ucenika(sheet, sifra)
    except Exception as e:                              # noqa: BLE001
        st.error(f"Popis testova se ne može pročitati: {e}")
        return

    # --- rješavanje odabranog testa
    aktivni = st.session_state.get("v2u_aktivni")
    if aktivni:
        odabrana = next((d for d in moje if model.tekst(d.get("dodjela_id")) == aktivni), None)
        definicija = definicije.po_id(sheet, model.tekst((odabrana or {}).get("definicija_id")))
        if odabrana and definicija:
            if st.button("← Natrag na popis", key="v2u_natrag"):
                st.session_state.pop("v2u_aktivni", None)
                st.rerun()
            try:
                posjete.biljeska_jednom(st, sheet, ucenik_id=sifra, radnja="test",
                                        detalj=model.tekst(definicija.get("definicija_id")))
            except Exception:                           # noqa: BLE001
                pass
            ekran_ucenika.prikazi(st, sheet, definicija, odabrana, dry=False)
            return
        st.session_state.pop("v2u_aktivni", None)

    if not moje:
        st.info("Nemaš dodijeljenih testova. Ako misliš da je greška, javi profesoru.")
        return

    for dodjela in moje:
        definicija = definicije.po_id(sheet, model.tekst(dodjela.get("definicija_id")))
        if definicija:
            _kartica(dodjela, definicija, _pokusaj_za(sheet, dodjela))


main()
