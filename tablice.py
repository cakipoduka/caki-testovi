"""
CAKI testovi v2 — `tablice.py`
JEDINI sloj koji zna gdje podaci žive.

Zašto postoji: danas je cijeli sustav vezan na `gspread` — svaka stranica zna da je baza Google Sheet.
Kad dođe Supabase (planirano za zimske praznike), mijenja se **samo ovaj modul**, a sve ostalo ostaje.

Pravilo: **nijedan drugi modul ne uvozi gspread.** Ako nešto treba podatke, traži ih ovdje.
"""
from __future__ import annotations

import re

# ------------------------------------------------------------------ tablice i zaglavlja

TAB_DEFINICIJE = "Definicije_testova"
TAB_DODJELE = "Dodjele"
TAB_POKUSAJI = "Pokusaji"
TAB_OCJENE = "Ocjene_zadataka"
TAB_STATISTIKA = "Statistika_zadataka"
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
    TAB_DEFINICIJE: [
        "definicija_id", "ustanova_id", "naziv", "predmet", "razina", "vrsta",
        "zadaci_json", "broj_zadataka", "bodovi_ukupno", "trajanje_min",
        "rok_od", "rok_do", "status", "student_view_json", "varijanta_pravilo",
        "pdf_verzija", "autor", "kreirano", "napomena",
    ],
    TAB_DODJELE: [
        "dodjela_id", "definicija_id", "ucenik_id", "ime_djeteta", "grupa",
        "rok_od", "rok_do", "varijanta_seed", "status", "dodijelio", "dodijeljeno",
    ],
    TAB_POKUSAJI: [
        "pokusaj_id", "dodjela_id", "definicija_id", "ucenik_id",
        "pocetak", "zadnja_aktivnost", "predaja", "trajanje_s",
        "odgovori_json", "bodovi", "bodovi_max", "status", "predano_po_roku",
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


def osiguraj(sheet, tab: str):
    """Vrati worksheet; ako taba nema, napravi ga sa zadanim zaglavljem (samo uz dozvoljeno pisanje)."""
    _provjeri_pisanje()
    zaglavlje = ZAGLAVLJA.get(tab) or ["id"]
    try:
        return sheet.worksheet(tab)
    except Exception:                                   # noqa: BLE001
        return sheet.add_worksheet(title=tab, rows=1000, cols=max(len(zaglavlje), 5))


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


def novi_id(postojeci, prefiks: str, sirina: int = 4) -> str:
    """Sljedeći slobodan ID, npr. prefiks `T26-` → `T26-0007`."""
    return f"{prefiks}{_zadnji_broj(postojeci, prefiks) + 1:0{sirina}d}"


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
