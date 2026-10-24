"""
CAKI testovi v2 — `upute.py`
UPUTE UNUTAR APLIKACIJE (Cakijev zahtjev: nikad zasebna stranica ni drugi prozor).

Svaka uputa: naslov · numerirani koraci · ⚠️ Pazi · ➡️ gdje dalje.
"""
from __future__ import annotations

UPUTE = {
    "testovi": {
        "naslov": "Kako sastaviti test (i zašto je zadano „nacrt”)",
        "koraci": [
            "Ovdje je popis svih testova. Novi test se pravi **ispod popisa**, iz postojeće baze "
            "zadataka (20.000+ zadataka se ne dira — samo se čita).",
            "Filtriraj po cjelini, težini, tipu ili traži u tekstu. Označi zadatke **redom kojim ide "
            "u test** — redoslijed odabira je redoslijed u testu.",
            "Upiši naziv, trajanje i rok. Klikni **💾 Spremi kao nacrt**.",
            "Nacrt **ne vidi nitko** dok ga ne objaviš u kartici 👥 Objavi — to je namjerno, da se "
            "slučajno ne pošalje cijelom programu.",
        ],
        "pazi": [
            "Zadatak bez konačnog odgovora ne može se automatski ocijeniti — sustav će ga odbiti "
            "pri provjeri.",
            "Ako mijenjaš zadatak u bazi poslije, **test se ne mijenja** — u testu je zamrznuta kopija.",
        ],
        "dalje": "Kad je nacrt spreman → kartica 👥 Objavi.",
    },
    "objavi": {
        "naslov": "Kome ide test (grupa, kanta ili pojedinac)",
        "koraci": [
            "Odaberi test i način: **👥 Grupa / kanta** (Upisi ili Matura) ili **🧑 Šifre učenika**.",
            "Odaberi grupe/kante — piše koliko učenika ima svaka. Klikni **📤 Objavi**.",
            "Ako je test bio nacrt, objava ga automatski prebaci u „objavljen”.",
            "Dopuna je uvijek moguća: vrati se i dodaj još učenika ili drugu grupu. **Duplikat se "
            "odbija** — tko već ima test, preskače se.",
        ],
        "pazi": [
            "Učenik dodan **nakon isteka roka** dobiva rok **od dana dodjele** — ne ostaje bez testa.",
            "Uklanjanje učenika nije dopušteno ako je već predao (rezultat je dokaz).",
        ],
        "dalje": "Rezultate gledaš u kartici 📊 Rezultati.",
    },
    "rezultati": {
        "naslov": "Kako čitati rezultate",
        "koraci": [
            "Odaberi test. Gore su tri brojke: **koliko je predalo**, **prosjek** i **raspon**.",
            "Tablica je poredana po postotku — **mjesto**, učenik, grupa, je li predao, bodovi.",
            "Ispod tablice piše **tko nije predao** — to je ono što se prije nije vidjelo.",
        ],
        "pazi": ["Rezultat je prazan dok učenik ne preda — „⏳” nije greška."],
        "dalje": "Mjerenje kvalitete zadatka (težina, diskriminativnost) dolazi u Fazi C.",
    },
    "postavke": {
        "naslov": "Što učenik vidi (Student View)",
        "koraci": [
            "Po svakom testu posebno odlučuješ što učenik vidi: bodove, rješenja, video, komentare, "
            "ukupni rezultat i PDF.",
            "Tri su stanja: **nikad**, **poslije** i **uvijek**.",
            "Za rješenja i video „poslije” znači **nakon isteka roka** — tako učenik koji prvi preda "
            "ne može podijeliti odgovore ostalima.",
        ],
        "pazi": ["Promjena vrijedi za buduće preglede; već predani rezultati se ne brišu."],
        "dalje": "Uređivanje tih razina dolazi uz ekran rješavanja (Faza B).",
    },
}


def prikazi(st, kljuc: str) -> None:
    """Sklopivi blok s uputom. Nepoznat ključ = ništa (ne ruši stranicu)."""
    u = UPUTE.get(str(kljuc or ""))
    if not u:
        return
    with st.expander(f"ℹ️ {u['naslov']}", expanded=False):
        for i, korak in enumerate(u.get("koraci", []), start=1):
            st.markdown(f"**{i}.** {korak}")
        if u.get("pazi"):
            st.markdown("**⚠️ Pazi:**")
            for p in u["pazi"]:
                st.markdown(f"- {p}")
        if u.get("dalje"):
            st.caption(f"➡️ {u['dalje']}")
