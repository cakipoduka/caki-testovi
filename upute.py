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
    "ocjene": {
        "naslov": "Kako se računa predlog zaključne ocjene",
        "koraci": [
            "Sustav uzima **sve predane testove** učenika i računa prosjek postotaka.",
            "Iz prosjeka predlaže ocjenu: **<50 % = 1**, 50–64 % = 2, 65–79 % = 3, 80–89 % = 4, 90 %+ = 5.",
            "Test koji učenik **nije pisao** ne ulazi u prosjek kao nula — bilježi se odvojeno.",
            "Tablica pokazuje i **koliko testova** je pisao (npr. 1/2) i koje nije.",
        ],
        "pazi": [
            "Predlog je **izračun, ne odluka** — profesor ocjenu mijenja po svom nahođenju.",
            "Učenici na granici (49/50, 64/65, 79/80, 89/90) posebno se izdvajaju.",
        ],
        "dalje": "CSV izvoz je za šifrarnik ili e-dnevnik.",
    },
    "kvaliteta": {
        "naslov": "Kako čitati mjerenje zadataka",
        "koraci": [
            "**p (težina)** = udio učenika koji je zadatak riješio točno. Ispod 0,30 je pretežak, "
            "iznad 0,90 prelagan (ne razlikuje nikoga).",
            "**r (diskriminacija)** = razlikuje li zadatak dobre od slabijih. Ispod 0,20 ne razlikuje; "
            "**negativan** znači da bolji učenici griješe — tada je najčešće krivo označen točan odgovor.",
            "**Distraktori** — ponuđeni odgovor koji nitko ne odabere je „mrtav”; zamijeni ga vjerojatnijim.",
            "**Cronbach α** = pouzdanost cijelog testa; ≥ 0,70 je prihvatljivo za razredni test.",
        ],
        "pazi": [
            "Manje od 10 predanih radova daje nestabilne brojke — tada se ne mijenjaju zadaci.",
            "Ako piše da pokušaji čekaju provjeru, brojke su privremene.",
        ],
        "dalje": "Odluku o izmjeni zadatka donosi profesor, ne brojka.",
    },
    "ucenik": {
        "naslov": "Kako izgleda rješavanje (i pregled)",
        "koraci": [
            "Odaberi test i način: **👁️ Pregled** (ništa se ne sprema) ili **🧑 Stvarni učenik** "
            "(učenik ima dodjelu).",
            "Pitanja se prikazuju **jedno po jedno**; ispod je popis svih pitanja s oznakom je li "
            "odgovoreno (✓) ili prazno (·).",
            "Kratki odgovor upisuje se u **matematičko polje** (MathLive); ako polje ne radi, ostaje "
            "običan tekst.",
            "Odgovor se **sprema sam** — prekid veze ne briše rad.",
            "Predaja pokazuje **koliko je prazno** i traži potvrdu.",
        ],
        "pazi": [
            "U pregledu je autosave isključen — ništa se ne zapisuje u Sheet.",
            "🎬 video i točna rješenja vide se **tek kad Student View to dopušta** (rješenja nakon roka).",
        ],
        "dalje": "Rezultati su u kartici 📊 Rezultati.",
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
