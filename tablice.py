"""
CAKI testovi v2 — `tablice.py`
JEDINI sloj koji zna gdje podaci žive.

Zašto postoji: danas je cijeli sustav vezan na `gspread` — svaka stranica zna da je baza Google Sheet.
Kad dođe Supabase (planirano za zimske praznike), mijenja se **samo ovaj modul**, a sve ostalo ostaje.

Pravilo: **nijedan drugi modul ne uvozi gspread.** Ako nešto treba podatke, traži ih ovdje.
"""
from __future__ import annotations

import streamlit as st
import re
import threading

# ------------------------------------------------------------------ tablice i zaglavlja

TAB_DEFINICIJE = "Definicije_testova"
TAB_DODJELE = "Dodjele_ispita"          # v2: dodjele TESTOVA (CRM ima svoj `Dodjele`)
TAB_DODJELE_CRM = "Dodjele"             # CRM: dodjele učenika profesoru — NE dirati
TAB_POKUSAJI = "Pokusaji"
TAB_OCJENE = "Ocjene_zadataka"
TAB_STATISTIKA = "Statistika_zadataka"
TAB_IZMJENE_OCJENA = "Izmjene_ocjena"
TAB_ZALBE = "Zalbe"
TAB_DNEVNIK = "Dnevnik_radnji"
TAB_RADOVI = "Radovi"
TAB_POSJETE = "Posjete"

# ------------------------------------------------------------------ sigurnosni prekidač
# ŽIVA BAZA. Dok je `PISANJE` False, NIŠTA se ne upisuje (sve funkcije pisanja bacaju grešku).
# Aplikacija ga uključi tek kad Caki to izrijekom potvrdi (u Postavkama).
PISANJE = False


def postavi_pisanje(dozvoljeno: bool) -> bool:
    """Uključi/isključi upis u živu bazu. Vraća novo stanje."""
    global PISANJE
    PISANJE = bool(dozvoljeno)
    return PISANJE


def _provjeri_pisanje() -> None:
    if not PISANJE:
        raise PermissionError(
            "Upis u živu bazu je ISKLJUČEN. Uključi ga u ⚙️ Postavkama kad si siguran da želiš "
            "mijenjati pravi CRM Sheet.")


ZAGLAVLJA = {
    "Zalbe": ["zalba_id", "pokusaj_id", "zadatak_id", "ucenik_id", "podnesena",
              "razlog", "status", "odgovor", "tko_odgovorio", "odgovoreno", "rok_do"],
    "Izmjene_ocjena": ["izmjena_id", "pokusaj_id", "zadatak_id", "ocjena_prije",
                       "ocjena_poslije", "bodovi_prije", "bodovi_poslije", "izvor_prije",
                       "razlog", "povod", "tko", "kada"],
    TAB_DEFINICIJE: [
        "definicija_id", "ustanova_id", "naziv", "predmet", "razina", "vrsta",
        "zadaci_json", "broj_zadataka", "bodovi_ukupno", "trajanje_min",
        "rok_od", "rok_do", "status", "student_view_json", "varijanta_pravilo",
        "pdf_verzija", "autor", "kreirano", "napomena", "ai_pomoc",
    ],
    # v2: dodjele TESTOVA. CRM koristi `Dodjele` za nešto drugo — zato je ime različito.
    TAB_DODJELE: [
        "dodjela_id", "definicija_id", "ucenik_id", "ime_djeteta", "grupa",
        "rok_od", "rok_do", "varijanta_seed", "status", "dodijelio", "dodijeljeno",
    ],
    TAB_POKUSAJI: [
        "pokusaj_id", "dodjela_id", "definicija_id", "ucenik_id",
        "pocetak", "zadnja_aktivnost", "predaja", "trajanje_s",
        "odgovori_json", "bodovi", "bodovi_max", "status", "predano_po_roku",
        # 30.10.2026. (§12.11.4): ZAMRZNUTI zadaci koje je učenik stvarno vidio.
        # Prije se svaki put iznova čitalo iz TRENUTNE definicije → nije bilo dokaza što je vidio.
        "zadaci_json",
    ],
    TAB_OCJENE: [
        "pokusaj_id", "zadatak_id", "redni_broj", "odgovor", "tocno", "bodovi", "max",
        "izvor_ocjene", "vrijeme_s", "komentar",
    ],
    TAB_STATISTIKA: [
        "zadatak_id", "definicija_id", "n", "p_vrijednost", "diskriminativnost",
        "distraktori_json", "prosj_vrijeme_s", "izracunato",
    ],
    TAB_RADOVI: [
        "rad_id", "pokusaj_id", "ucenik_id", "naziv", "veza", "izvor",
        "velicina_bajtova", "prilozio", "prilozeno", "potvrdjeno", "napomena",
    ],
    TAB_POSJETE: [
        "posjeta_id", "ucenik_id", "kad", "radnja", "detalj", "naprava",
    ],
    TAB_DNEVNIK: ["kad", "korisnik", "radnja", "sto", "detalj"],
}


# ------------------------------------------------------------------ osnovno

def _kao_tekst(v) -> str:
    return "" if v is None else str(v).strip()


def ucitaj(sheet, tab: str) -> list[dict]:
    """Svi retci taba kao lista dictova. Nepostojeći tab = prazna lista (ne rušiti stranicu)."""
    try:
        ws = sheet.worksheet(tab)
    except Exception:                                   # noqa: BLE001 — tab još ne postoji
        return []
    try:
        return [dict(r) for r in ws.get_all_records()]
    except Exception:                                   # noqa: BLE001 — prazna tablica bez zaglavlja
        return []


def _normal_ime(tekst) -> str:
    """Normalizirano ime taba: bez razmaka na rubovima, mala slova, bez dijakritike."""
    s = _kao_tekst(tekst).strip().lower()
    for a, b in (("č", "c"), ("ć", "c"), ("ž", "z"), ("š", "s"), ("đ", "d")):
        s = s.replace(a, b)
    return " ".join(s.split())


def _naslovi_tabova(sheet) -> list[str]:
    """Svi naslovi tabova — prvo `worksheets()`, pa metapodaci (ako prvo padne)."""
    naslovi = []
    try:
        for ws in sheet.worksheets():
            naslov = getattr(ws, "title", None) or getattr(ws, "_properties", {}).get("title", "")
            if naslov:
                naslovi.append(_kao_tekst(naslov))
    except Exception:                                   # noqa: BLE001
        pass
    if not naslovi:
        try:
            meta = sheet.fetch_sheet_metadata()
            for list_ in (meta or {}).get("sheets", []):
                naslov = (list_.get("properties") or {}).get("title")
                if naslov:
                    naslovi.append(_kao_tekst(naslov))
        except Exception:                               # noqa: BLE001
            pass
    return naslovi


def _postojeci_tab(sheet, tab: str):
    """Nađi tab tolerantno: worksheets() → metapodaci → izravne varijante zapisa."""
    cilj = _normal_ime(tab)
    for naslov in _naslovi_tabova(sheet):
        if _normal_ime(naslov) == cilj:
            try:
                return sheet.worksheet(naslov)
            except Exception:                           # noqa: BLE001
                break
    # izravne varijante (Google je osjetljiv na točan zapis)
    for varijanta in (tab, tab.strip(), tab.lower(), tab.upper(), tab.capitalize()):
        try:
            ws = sheet.worksheet(varijanta)
            if ws is not None:
                return ws
        except Exception:                               # noqa: BLE001
            continue
    return None


def _sheet_iz_secrets():
    """Otvori CRM Sheet iznova iz Secrets (zaobilazi i predmemoriju objekta)."""
    try:
        import veza

        klijent = veza.klijent()
        for kljuc in ("CRM_SHEET_ID", "SHEET_ID"):
            try:
                sid = _kao_tekst(st.secrets.get(kljuc))
            except Exception:                           # noqa: BLE001
                sid = ""
            if sid:
                try:
                    return klijent.open_by_key(sid)
                except Exception:                       # noqa: BLE001
                    continue
    except Exception:                                   # noqa: BLE001
        pass
    return None


def _tab_po_indeksu(sheet, tab: str):
    """Nađi tab prolaskom po INDEKSU (0..60) i usporedbom naslova — najrobusnija varijanta."""
    cilj = _normal_ime(tab)
    for i in range(0, 60):
        try:
            ws = sheet.get_worksheet(i)
        except Exception:                               # noqa: BLE001
            break
        if ws is None:
            break
        try:
            if _normal_ime(getattr(ws, "title", "")) == cilj:
                return ws
        except Exception:                               # noqa: BLE001
            continue
    return None


def _tab_postoji(sheet, tab: str) -> bool:
    """Provjeri postojanje taba **izravnim čitanjem ćelije** (ne ovisi o popisu tabova)."""
    try:
        sheet.values_get(f"'{tab}'!A1")
        return True
    except Exception:                                   # noqa: BLE001
        return False


def _osvjezi_metapodatke(sheet) -> None:
    """Osvježi predmemoriju tabova na `Spreadsheet` objektu (gspread je drži u memoriji)."""
    try:
        sheet.fetch_sheet_metadata()
    except Exception:                                   # noqa: BLE001
        pass


def dijagnostika(sheet) -> dict:
    """Što aplikacija STVARNO vidi: naslov, ID, broj tabova i prvih 10 naslova.

    Služi za ⚙️ Postavke → Provjera baze: razlikuje „pogrešan Sheet" od „nema prava".
    """
    info = {"naslov": "", "id": "", "tabova": 0, "naslovi": [], "greska": ""}
    try:
        info["naslov"] = _kao_tekst(getattr(sheet, "title", ""))
        info["id"] = _kao_tekst(getattr(sheet, "id", ""))
    except Exception:                                   # noqa: BLE001
        pass
    naslovi = _naslovi_tabova(sheet)
    info["naslovi"] = naslovi[:10]
    info["tabova"] = len(naslovi)
    # 01.11.2026.: točni zapisi imena (nevidljivi znakovi / razmaci) — za rješavanje
    # „tab postoji ali se ne može otvoriti"
    info["naslovi_repr"] = [repr(n) for n in naslovi[:10]]
    info["ima_dodjele_ispita"] = any(
        _normal_ime(n) == _normal_ime("Dodjele_ispita") for n in naslovi)
    info["ima_dodjele"] = any(_normal_ime(n) == _normal_ime("Dodjele") for n in naslovi)
    if not naslovi:
        try:
            sheet.worksheets()
        except Exception as e:                          # noqa: BLE001
            info["greska"] = f"{type(e).__name__}: {e}"
    return info


def svjez_sheet(sheet):
    """Novi objekt istog Sheet-a (bez predmemorije) — pomoć kad popis tabova ostane prazan."""
    try:
        import veza

        klijent = veza.klijent()
        return klijent.open_by_key(getattr(sheet, "id", "") or "")
    except Exception:                                   # noqa: BLE001
        return None


def provjeri_zaglavlje(sheet, tab: str, ocekivano=None) -> tuple[bool, str]:
    """Vrati (odgovara, poruka). Štiti od pisanja u tab s drugim stupcima.

    Zašto: CRM tab `Dodjele` ima sasvim druge stupce (profesor, predmet, datum) — pisanje v2 redaka
    u njega pomiješalo je dvije vrste podataka (Caki, 01.11.2026.).
    """
    ocekivano = list(ocekivano or ZAGLAVLJA.get(tab) or [])
    try:
        ws = sheet.worksheet(tab)
        stvarno = [k for k in (ws.row_values(1) or []) if _kao_tekst(k)]
    except Exception:                                   # noqa: BLE001
        return True, "tab ne postoji — može se napraviti"
    if not stvarno:
        return True, "tab je prazan — zaglavlje će se upisati"
    if not ocekivano:
        return True, "nema očekivanog zaglavlja"
    if [s.lower() for s in stvarno] == [o.lower() for o in ocekivano]:
        return True, "zaglavlje odgovara"
    return False, (f"Tab `{tab}` ima DRUGE stupce ({', '.join(stvarno[:6])}…) — "
                   f"očekivano: {', '.join(ocekivano[:6])}…")


def osiguraj(sheet, tab: str):
    """Vrati worksheet; ako taba nema, napravi ga (samo uz dozvoljeno pisanje).

    Robustno na tri stvari koje su stvarno smetale (01.11.2026.):
      · gspread predmemorija tabova („nijedan tab nije vidljiv"), 
      · različit zapis imena (razmaci / velika slova / dijakritika),
      · `addSheet` koji padne jer tab **postoji** — tada se NE ruši, nego se dohvati.
    """
    _provjeri_pisanje()
    zaglavlje = ZAGLAVLJA.get(tab) or ["id"]

    # 0) PRISILNO osvježi metapodatke — gspread drži stari popis tabova u memoriji
    try:
        sheet.fetch_sheet_metadata()
    except Exception:                                   # noqa: BLE001
        pass

    # 1) izravno
    try:
        return sheet.worksheet(tab)
    except Exception:                                   # noqa: BLE001
        pass

    # 1b) ponovno, s dodatnim parametrima (gspread nekad traži `params`)
    try:
        sheet.fetch_sheet_metadata({"fields": "sheets.properties.title"})
        return sheet.worksheet(tab)
    except Exception:                                   # noqa: BLE001
        pass

    # 2) tolerantno po popisu
    postoji = _postojeci_tab(sheet, tab)
    if postoji is not None:
        return postoji

    # 3) tab postoji, ali ga popis ne vidi → osvježi metapodatke i probaj ponovno
    if _tab_postoji(sheet, tab):
        _osvjezi_metapodatke(sheet)
        try:
            return sheet.worksheet(tab)
        except Exception:                               # noqa: BLE001
            pass

    # 3b) tab postoji, ali ime se ne podudara — probaj po indeksu
    po_indeksu = _tab_po_indeksu(sheet, tab)
    if po_indeksu is not None:
        return po_indeksu

    # 4) napravi novi
    try:
        return sheet.add_worksheet(title=tab, rows=1000, cols=max(len(zaglavlje), 5))
    except Exception as e:                              # noqa: BLE001
        poruka = str(e)
        # 4a) Google kaže: tab već postoji → dohvati ga (nikad ne ruši objavu)
        if "already exists" in poruka.lower():
            _osvjezi_metapodatke(sheet)
            for varijanta in (tab, tab.strip(), tab.capitalize(), tab.lower(), tab.upper()):
                try:
                    return sheet.worksheet(varijanta)
                except Exception:                       # noqa: BLE001
                    continue
            if _tab_postoji(sheet, tab):
                _osvjezi_metapodatke(sheet)
                try:
                    return sheet.worksheet(tab)
                except Exception:                       # noqa: BLE001
                    pass
            svjez2 = _sheet_iz_secrets()
            if svjez2 is not None:
                try:
                    return svjez2.worksheet(tab)
                except Exception:                       # noqa: BLE001
                    pass
            po_indeksu = _tab_po_indeksu(sheet, tab)
            if po_indeksu is not None:
                return po_indeksu
            svjez = svjez_sheet(sheet)
            if svjez is not None:
                try:
                    return svjez.worksheet(tab)
                except Exception:                       # noqa: BLE001
                    pass
            raise RuntimeError(
                f"Tab `{tab}` postoji, ali ga aplikacija ne može otvoriti. "
                "Najčešće: servisni račun nema pravo **Editor** na tom Sheetu (ili `CRM_SHEET_ID` "
                "pokazuje na drugu datoteku). Dodijeli pristup i pokušaj ponovno."
            ) from e
        vidljivi = ", ".join(_naslovi_tabova(sheet)[:25]) or "(nijedan tab nije vidljiv)"
        raise RuntimeError(
            f"Tab `{tab}` nije moguće naći ni napraviti ({e}). "
            f"Tabovi koje aplikacija vidi: {vidljivi}. "
            "Provjeri isti Spreadsheet ID i pravo Editor za servisni račun."
        ) from e


def osiguraj_sve(sheet) -> list[str]:
    """Napravi sve tabove koje sustav traži. Vraća popis onih koji su nastali."""
    napravljeni = []
    for tab in ZAGLAVLJA:
        try:
            sheet.worksheet(tab)
        except Exception:                               # noqa: BLE001
            ws = osiguraj(sheet, tab)
            ws.update(values=[ZAGLAVLJA[tab]], range_name="A1")
            napravljeni.append(tab)
    return napravljeni


def dodaj(sheet, tab: str, redci: list[dict]) -> int:
    """Doda retke (jedan `append_rows` poziv — kvota). Vrijednosti po zaglavlju taba."""
    _provjeri_pisanje()
    if not redci:
        return 0
    ws = osiguraj(sheet, tab)
    zaglavlje = [_kao_tekst(h) for h in (ws.row_values(1) or [])] or ZAGLAVLJA[tab]
    ws.append_rows([[redci_r.get(h, "") for h in zaglavlje] for redci_r in redci],
                   value_input_option="RAW")
    return len(redci)


def _redak_po_kljucu(ws, kljuc: str, vrijednost: str) -> int | None:
    """Broj retka (1-based) gdje stupac `kljuc` ima `vrijednost`. None ako nema."""
    zaglavlje = [_kao_tekst(h) for h in (ws.row_values(1) or [])]
    if kljuc not in zaglavlje:
        return None
    i = zaglavlje.index(kljuc)
    for br, red in enumerate(ws.get_all_values()[1:], start=2):
        if i < len(red) and _kao_tekst(red[i]) == _kao_tekst(vrijednost):
            return br
    return None


def azuriraj(sheet, tab: str, kljuc: str, vrijednost: str, promjene: dict) -> bool:
    """Izmijeni jedan redak (traži se po `kljuc`). True = pronađen i upisan."""
    _provjeri_pisanje()
    ws = osiguraj(sheet, tab)
    redak = _redak_po_kljucu(ws, kljuc, vrijednost)
    if not redak:
        return False
    zaglavlje = [_kao_tekst(h) for h in (ws.row_values(1) or [])]
    for polje, novo in (promjene or {}).items():
        if polje not in zaglavlje:
            continue
        ws.update_cell(redak, zaglavlje.index(polje) + 1, novo)
    return True


def obrisi(sheet, tab: str, kljuc: str, vrijednost: str) -> bool:
    """Obriše redak po ključu. True = obrisan."""
    _provjeri_pisanje()
    ws = osiguraj(sheet, tab)
    redak = _redak_po_kljucu(ws, kljuc, vrijednost)
    if not redak:
        return False
    ws.delete_rows(redak)
    return True


# ------------------------------------------------------------------ oznake (ID-evi)

def _zadnji_broj(postojeci, prefiks: str) -> int:
    najveci = 0
    for x in postojeci or ():
        m = re.match(rf"^{re.escape(prefiks)}(\d+)$", _kao_tekst(x))
        if m:
            najveci = max(najveci, int(m.group(1)))
    return najveci


# --- zaštita od sudara ID-eva (MASTER §12.4 / §12.11.1) ---------------------------------
_REZERVIRANI: set[str] = set()
_REZERVIRANI_LOCK = threading.Lock()


def _ocisti_rezervacije() -> None:
    """Pomoćno za testove — ne koristi se u radu."""
    with _REZERVIRANI_LOCK:
        _REZERVIRANI.clear()


def ima_id(sheet, tab: str, polje: str, vrijednost: str) -> bool:
    """Postoji li taj ID već u tabu (čitanje iz Sheeta)."""
    return _kao_tekst(vrijednost) in set(svi_idovi(sheet, tab, polje))


def novi_id(postojeci, prefiks: str, sirina: int = 4, *, zaobidji=()) -> str:
    """Sljedeći slobodan ID, npr. prefiks `T26-` → `T26-0007`.

    **Zaštita od sudara (30.10.2026.):** ID se rezervira u procesu (Streamlit vrti više sesija u
    istom procesu) i preskače sve koji su već rezervirani ili navedeni u `zaobidji`.
    """
    zauzeti = {_kao_tekst(x) for x in (postojeci or ())} | set(zaobidji or ())
    with _REZERVIRANI_LOCK:
        zauzeti |= _REZERVIRANI
        broj = _zadnji_broj(zauzeti, prefiks) + 1
        kandidat = f"{prefiks}{broj:0{sirina}d}"
        while kandidat in zauzeti:                      # teoretski, ali neka bude sigurno
            broj += 1
            kandidat = f"{prefiks}{broj:0{sirina}d}"
        _REZERVIRANI.add(kandidat)
    return kandidat


def novi_id_za_tab(sheet, tab: str, polje: str, prefiks: str, sirina: int = 4) -> str:
    """Slobodan ID za tab: čita postojeće iz Sheeta, preskače rezervirane, vraća novi."""
    return novi_id(svi_idovi(sheet, tab, polje), prefiks, sirina)


def svi_idovi(sheet, tab: str, polje: str) -> list[str]:
    return [_kao_tekst(r.get(polje)) for r in ucitaj(sheet, tab) if _kao_tekst(r.get(polje))]


# ------------------------------------------------------------------ dnevnik

def zapisi_radnju(sheet, korisnik: str, radnja: str, sto: str, detalj: str = "") -> None:
    """Trag tko je što napravio — GDPR i obrana od prigovora („tko je to objavio?")."""
    from model import sada_iso

    try:
        dodaj(sheet, TAB_DNEVNIK, [{"kad": sada_iso(), "korisnik": korisnik,
                                    "radnja": radnja, "sto": sto, "detalj": detalj}])
    except Exception:                                   # noqa: BLE001 — dnevnik ne smije blokirati rad
        pass
