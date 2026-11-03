"""
CAKI testovi v2 — `skola.py`  (VANJSKE GRUPE / ŠKOLA)

Specifikacija Caki + Claude (5.11.2026.). Ovo je **prvi dio**: grupe, članovi, šifre, zatvaranje.

PRAVILA (skraćeno iz specifikacije):
  · podaci vanjskih grupa NE idu u CRM Sheet nego u poseban Sheet (`SKOLA_SHEET_ID`),
  · u CRM tabove (`Dodjele_ispita`, `Pokusaji`, `Ocjene_zadataka`) ide **samo šifra** `SK-<godina>-<broj>`,
  · imena i mailovi stoje isključivo u `Skolski_profili` (na školskom Sheetu),
  · vanjski učenik NIKAD ne smije u CRM tab „Ucenici" (test to provjerava),
  · čitanje isključivo `tablice.ucitaj`, pisanje `tablice.dodaj/azuriraj/obrisi`,
  · zaglavlje novog taba se upisuje odmah (inače prvi redak postane zaglavlje).

Tabovi (školski Sheet):
  Skolske_grupe        grupa_id · naziv · vrsta · vlasnik · skolska_godina ·
                       naslov_za_ucenike · aktivan
  Skolske_grupe_clanovi grupa_id · ucenik_id · od · do
  Skolski_profili      ucenik_id · ime_prezime · skolski_mail · grupa_id
"""
from __future__ import annotations

import model
import tablice

TAB_GRUPE = "Skolske_grupe"
TAB_CLANOVI = "Skolske_grupe_clanovi"
TAB_PROFILI = "Skolski_profili"

ZAGLAVLJA = {
    TAB_GRUPE: ["grupa_id", "naziv", "vrsta", "vlasnik", "skolska_godina",
                "naslov_za_ucenike", "aktivan"],
    TAB_CLANOVI: ["grupa_id", "ucenik_id", "od", "do"],
    TAB_PROFILI: ["ucenik_id", "ime_prezime", "skolski_mail", "grupa_id"],
}

VRSTA_SKOLA = "skola"


def osiguraj(sheet) -> list[str]:
    """Napravi tabove i **upiši zaglavlja** (specifikacija E). Vraća popis novih tabova."""
    napravljeni = []
    for tab, kolone in ZAGLAVLJA.items():
        try:
            postoji = bool(tablice.ucitaj(sheet, tab))
        except Exception:                               # noqa: BLE001
            postoji = False
        if postoji:
            continue
        try:
            ws = tablice.osiguraj(sheet, tab)
            if ws is not None:
                ws.update(values=[kolone], range_name="A1")
                try:
                    tablice._zaboravi(sheet, tab)  # da čitanje vidi novo zaglavlje
                except Exception:                   # noqa: BLE001
                    pass
                napravljeni.append(tab)
        except Exception:                               # noqa: BLE001
            continue
    return napravljeni


def grupe(sheet, *, vlasnik: str = "", samo_aktivne: bool = True) -> list[dict]:
    """Popis grupa; filtar po vlasniku („moje grupe")."""
    v = model.tekst(vlasnik).strip().lower()
    izlaz = []
    for g in tablice.ucitaj(sheet, TAB_GRUPE):
        if samo_aktivne and model.tekst(g.get("aktivan")).lower() in ("ne", "false", "0"):
            continue
        if v and model.tekst(g.get("vlasnik")).strip().lower() != v:
            continue
        izlaz.append(g)
    return izlaz


def nova_grupa(sheet, naziv: str, *, vlasnik: str = "Caki", skolska_godina: str = "",
               naslov_za_ucenike: str = "") -> dict:
    """Napravi grupu (vrsta je uvijek `skola`). Vraća redak koji je upisan."""
    osiguraj(sheet)
    postojeci = [model.tekst(g.get("grupa_id")) for g in tablice.ucitaj(sheet, TAB_GRUPE)]
    grupa_id = tablice.novi_id(postojeci, "SG-")
    redak = {
        "grupa_id": grupa_id,
        "naziv": model.tekst(naziv),
        "vrsta": VRSTA_SKOLA,
        "vlasnik": model.tekst(vlasnik) or "Caki",
        "skolska_godina": model.tekst(skolska_godina),
        "naslov_za_ucenike": model.tekst(naslov_za_ucenike),
        "aktivan": "Da",
    }
    tablice.dodaj(sheet, TAB_GRUPE, [redak])
    return redak


def _crm_sifre(sheet_crm) -> set[str]:
    """Šifre iz CRM taba `Ucenici` — da se šifre grupa ne poklope s postojećim učenicima."""
    izlaz: set[str] = set()
    for naslov in ("Učenici", "Ucenici"):
        try:
            for r in tablice.ucitaj(sheet_crm, naslov):
                s = model.tekst(r.get("ucenik_id")).upper()
                if s:
                    izlaz.add(s)
        except Exception:                               # noqa: BLE001
            continue
    return izlaz


def _postojece_sifre(sheet) -> set[str]:
    izlaz = set()
    for r in tablice.ucitaj(sheet, TAB_PROFILI):
        s = model.tekst(r.get("ucenik_id")).upper()
        if s:
            izlaz.add(s)
    return izlaz


def nova_sifra(godina: str, zauzete: set[str]) -> str:
    """Sljedeća slobodna `SK-<godina>-<broj>` (001, 002, …)."""
    g = model.tekst(godina) or "2026"
    najveci = 0
    prefiks = f"SK-{g}-"
    for s in zauzete:
        if s.startswith(prefiks):
            try:
                najveci = max(najveci, int(s[len(prefiks):]))
            except ValueError:
                continue
    return f"{prefiks}{najveci + 1:03d}"


def dodaj_ucenike(sheet, grupa_id: str, imena: str, *, godina: str = "",
                  sheet_crm=None) -> dict:
    """Zalijepljena imena (jedan po retku, `Ime Prezime` ili `Ime Prezime; mail`) → profili + članovi.

    Vraća {"dodano": n, "sifre": [ ... ], "preskoceno": n}.
    """
    gid = model.tekst(grupa_id)
    if not gid:
        return {"dodano": 0, "sifre": [], "preskoceno": 0}
    osiguraj(sheet)

    zauzete = _postojece_sifre(sheet)
    if sheet_crm is not None:
        zauzete |= _crm_sifre(sheet_crm)

    profili, clanovi, sifre = [], [], []
    preskoceno = 0
    for linija in model.tekst(imena).split("\n"):
        linija = linija.strip()
        if not linija:
            continue
        dijelovi = [d.strip() for d in linija.replace("\t", ";").split(";")]
        ime = dijelovi[0]
        mail = dijelovi[1] if len(dijelovi) > 1 else ""
        if not ime:
            preskoceno += 1
            continue
        sifra = nova_sifra(godina, zauzete)
        if sifra in zauzete:                            # sigurnosna petlja
            preskoceno += 1
            continue
        zauzete.add(sifra)
        profili.append({"ucenik_id": sifra, "ime_prezime": ime,
                        "skolski_mail": mail, "grupa_id": gid})
        clanovi.append({"grupa_id": gid, "ucenik_id": sifra, "od": model.sada_iso()[:10],
                        "do": ""})
        sifre.append({"ucenik_id": sifra, "ime_prezime": ime})

    if profili:
        tablice.dodaj(sheet, TAB_PROFILI, profili)
        tablice.dodaj(sheet, TAB_CLANOVI, clanovi)
    return {"dodano": len(profili), "sifre": sifre, "preskoceno": preskoceno}


def clanovi(sheet, grupa_id: str) -> list[dict]:
    """Članovi grupe s imenom (spoj s `Skolski_profili`)."""
    gid = model.tekst(grupa_id)
    imena = {model.tekst(p.get("ucenik_id")).upper(): model.tekst(p.get("ime_prezime"))
             for p in tablice.ucitaj(sheet, TAB_PROFILI)}
    izlaz = []
    for c in tablice.ucitaj(sheet, TAB_CLANOVI):
        if model.tekst(c.get("grupa_id")) != gid:
            continue
        sifra = model.tekst(c.get("ucenik_id")).upper()
        izlaz.append({"ucenik_id": sifra, "ime_prezime": imena.get(sifra, ""),
                      "od": model.tekst(c.get("od")), "do": model.tekst(c.get("do"))})
    return izlaz


def csv_popis(sheet, grupa_id: str) -> str:
    """CSV popis šifri za podjelu učenicima (ime; šifra)."""
    redci = clanovi(sheet, grupa_id)
    linije = ["ime_prezime;sifra"]
    for r in redci:
        linije.append(f"{r['ime_prezime']};{r['ucenik_id']}")
    return "\n".join(linije)


def zatvori_grupu(sheet, grupa_id: str, *, obrisi_podatke: bool = True) -> dict:
    """Kraj godine: grupu deaktiviraj, a imena/mailove OBRIŠI (šifre i rezultati ostaju)."""
    gid = model.tekst(grupa_id)
    izlaz = {"deaktivirano": 0, "obrisano_profila": 0}
    for g in tablice.ucitaj(sheet, TAB_GRUPE):
        if model.tekst(g.get("grupa_id")) != gid:
            continue
        try:
            if tablice.azuriraj(sheet, TAB_GRUPE, "grupa_id", gid, {"aktivan": "Ne"}):
                izlaz["deaktivirano"] += 1
        except Exception:                               # noqa: BLE001
            pass
        break

    if not obrisi_podatke:
        return izlaz
    for p in tablice.ucitaj(sheet, TAB_PROFILI):
        if model.tekst(p.get("grupa_id")) != gid:
            continue
        try:
            if tablice.azuriraj(sheet, TAB_PROFILI, "ucenik_id",
                                model.tekst(p.get("ucenik_id")),
                                {"ime_prezime": "", "skolski_mail": ""}):
                izlaz["obrisano_profila"] += 1
        except Exception:                               # noqa: BLE001
            pass
    return izlaz
