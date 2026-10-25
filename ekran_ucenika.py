"""
CAKI testovi v2 — `ekran_ucenika.py`
EKRAN RJEŠAVANJA: pitanje po pitanju, autosave, matematički unos, predaja s upozorenjem.

Dva načina rada:
  · **stvarno rješavanje** — učenik ima dodjelu; pokušaj se zapisuje (autosave, predaja)
  · **pregled za Cakija** (`dry=True`) — isti kod, ali **ništa se ne sprema**

Odvojeno od `app.py` namjerno: isti modul sutra koristi portal učenika.
"""
from __future__ import annotations

import streamlit as st

import model
import ocjenjivanje
import provedba
import rjesavanje
import unos_odgovora


def _k(*dijelovi) -> str:
    """Ključ sesije — kratak, bez razmaka, jedinstven po testu/dodjeli."""
    return "v2r_" + "_".join(str(d).replace(" ", "_")[:20] for d in dijelovi)


def _zadaci(definicija: dict, dodjela: dict) -> list[dict]:
    return provedba.zadaci_za_pokusaj(definicija, dodjela)


def _odgovori_kljuc(dodjela: dict) -> str:
    return _k("odg", dodjela.get("dodjela_id", "x"))


def prikazi(st, sheet, definicija: dict, dodjela: dict, *, dry: bool = False) -> None:
    """Cijeli ekran rješavanja za jednu dodjelu (ili pregled kad je `dry=True`)."""
    zadaci = _zadaci(definicija, dodjela)
    if not zadaci:
        st.error("Test nema ispravno spremljene zadatke — javi Cakiju.")
        return

    k_odg = _odgovori_kljuc(dodjela)
    k_pit = _k("pitanje", dodjela.get("dodjela_id", "x"))
    k_pok = _k("pokusaj", dodjela.get("dodjela_id", "x"))
    st.session_state.setdefault(k_odg, {})
    st.session_state.setdefault(k_pit, 0)

    # --- pokušaj: stvarni (u Sheetu) ili pregled (u sesiji)
    if dry:
        pokusaj = st.session_state.setdefault(k_pok, {
            "pokusaj_id": "PREGLED", "status": provedba.STATUS_U_TIJEKU,
            "pocetak": model.sada().strftime("%Y-%m-%d %H:%M:%S"),
            "odgovori_json": "{}", "dodjela_id": "PREGLED",
        })
    else:
        pokusaj = st.session_state.get(k_pok)
        if not pokusaj:
            pokusaj = provedba.zapocni(sheet, dodjela, definicija)
            st.session_state[k_pok] = pokusaj

    # --- traka: vrijeme i napredak
    istice = provedba.vrijeme_isteka(pokusaj, definicija)
    odgovori = st.session_state[k_odg]
    nap = rjesavanje.napredak(zadaci, odgovori)
    c1, c2, c3 = st.columns(3)
    c1.metric("Preostalo", model.preostalo_tekst(istice) if istice else "—")
    c2.metric("Bodova ukupno", f"{model.broj(definicija.get('bodovi_ukupno')):g}")
    c3.metric("Odgovoreno", f"{nap['odgovoreno']}/{nap['ukupno']}")
    st.progress(nap["postotak"] / 100)

    if istice and model.sada() > istice:
        st.warning("⏰ Vrijeme je isteklo — predaj test. Rezultat se označava kao predan po isteku.")

    # --- navigacija po pitanjima
    index = max(0, min(len(zadaci) - 1, int(st.session_state.get(k_pit, 0))))
    stanja = rjesavanje.stanje_pitanja(zadaci, odgovori)
    with st.container(border=True):
        st.caption("Pitanja: " + " · ".join(rjesavanje.oznaka_pitanja(i, stanja)
                                            for i in range(len(zadaci))))
        b1, b2, b3 = st.columns([1, 1, 4])
        if b1.button("← Prethodno", key=_k("preth", pokusaj["pokusaj_id"])):
            st.session_state[k_pit] = rjesavanje.sljedeci(index, len(zadaci), -1)
            st.rerun()
        if b2.button("Sljedeće →", key=_k("sljedece", pokusaj["pokusaj_id"])):
            st.session_state[k_pit] = rjesavanje.sljedeci(index, len(zadaci), 1)
            st.rerun()
        b3.caption(f"Pitanje **{index + 1}** od **{len(zadaci)}** · odgovor se sprema sam")

    # --- pitanje
    z = zadaci[index]
    trenutni = model.tekst(odgovori.get(str(index)))
    novi = trenutni
    with st.container(border=True):
        st.markdown(f"**Zadatak {index + 1}.** ({model.broj(z.get('bodovi'), 1):g} bod.)")
        st.markdown(rjesavanje.pripremi_latex(z.get("tekst")))
        if model.tekst(z.get("slika")):
            st.caption(f"🖼️ Uz zadatak ide slika: `{model.tekst(z.get('slika'))}`")

        opcije = [model.tekst(o) for o in (z.get("opcije") or []) if model.tekst(o)]
        if model.tekst(z.get("tip")) == "visestruki_izbor" and len(opcije) >= 2:
            slova = [""] + [chr(65 + i) for i in range(len(opcije))]
            odabrano = st.radio(
                "Odgovor", slova, index=slova.index(trenutni) if trenutni in slova else 0,
                key=_k("radio", pokusaj["pokusaj_id"], index),
                format_func=lambda s: ("— odaberi —" if not s
                                       else f"{s}) {rjesavanje.pripremi_latex(opcije[ord(s) - 65])}"),
            )
            novi = odabrano
        else:
            novi = unos_odgovora.unos_odgovora(
                "Odgovor", key=_k("unos", pokusaj["pokusaj_id"], index),
                vrijednost_latex=trenutni)

    if model.tekst(novi) != trenutni:
        st.session_state[k_odg][str(index)] = novi
        if not dry and model.tekst(pokusaj.get("status")) == provedba.STATUS_U_TIJEKU:
            try:
                provedba.spremi(sheet, pokusaj, {str(index): novi})
            except Exception:                          # noqa: BLE001 — autosave ne blokira
                st.caption("⚠️ Automatsko spremanje trenutno ne radi — odgovor je još na ekranu.")

    # --- predaja
    st.divider()
    sazetak = rjesavanje.sto_nedostaje(zadaci, st.session_state[k_odg])
    if sazetak["prazno"]:
        st.info(sazetak["poruka"])
    with st.expander("✅ Predaj test", expanded=bool(sazetak["prazno"])):
        for red in rjesavanje.sazetak_predaje(zadaci, st.session_state[k_odg]):
            st.caption(red)
        if st.button("✅ Predaj", type="primary", key=_k("predaj", pokusaj["pokusaj_id"])):
            try:
                if dry:
                    ocj = ocjenjivanje.ocjeni_zadatke(
                        zadaci, {int(k): v for k, v in st.session_state[k_odg].items()},
                        dopusti_ai=False)
                    st.success(f"🧪 Pregled: {rjesavanje.rezultat_tekst(ocj['bodovi'], ocj['maks'])} "
                               "— ništa nije spremljeno.")
                else:
                    rez = provedba.predaj(sheet, pokusaj, definicija,
                                          odgovori_=st.session_state[k_odg], dopusti_ai=False)
                    st.success(f"✅ Predano: {rjesavanje.rezultat_tekst(rez['bodovi'], rez['maks'])}")
                    if rez.get("ceka_profesora"):
                        st.warning(rjesavanje.poruka_o_cekanju(rez["ceka_profesora"]))
                    st.session_state.pop(k_pok, None)
            except Exception as e:                      # noqa: BLE001
                st.error(f"Predaja nije uspjela: {e}")


def prikazi_pregled_rjesenja(st, zadaci: list[dict], odgovori: dict, *,
                             pokazi_rjesenja: bool, pokazi_video: bool,
                             pokazi_bodove: bool) -> None:
    """Nakon testa: što je učenik odgovorio, točan odgovor i 🎬 video — po Student View-u."""
    for i, z in enumerate(zadaci or []):
        red = rjesavanje.pregled_zadatka(
            z, model.tekst((odgovori or {}).get(str(i))),
            pokazi_rjesenje=pokazi_rjesenja, pokazi_video=pokazi_video,
            pokazi_bodove=pokazi_bodove)
        oznaka = "🎬 video" if red["video"] else "pregled"
        with st.expander(f"Zadatak {i + 1} — {oznaka}"):
            st.markdown(rjesavanje.pripremi_latex(red["tekst"]))
            st.caption(f"Tvoj odgovor: **{red['moj_odgovor'] or '— (prazno)'}**")
            if red["pokazi_rjesenje"]:
                st.success(f"Točno: {red['tocan_odgovor']}")
            if red["video"]:
                st.markdown(f"🎬 **Video:** [{red['video']['naslov']}]({red['video']['url']})")
