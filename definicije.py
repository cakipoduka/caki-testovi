"""
CAKI testovi v2 — `definicije.py`
TEST KAO ZAPIS (ono što danas ne postoji).

Danas je „test" samo N redaka po učenicima s istom oznakom `serija` — zato se učenik ne može dodati
nakon objave i zato se ne zna što je točno bio test. Ovdje test postaje **jedan zapis** koji nosi
zadatke, pravila i način na koji se rezultat prikazuje.

Sve u ovom modulu su čiste funkcije (bez Streamlita i bez Googlea) — zato se mogu testirati.
"""
from __future__ import annotations

import random

import model
import tablice

# ------------------------------------------------------------------ riječnik

STANJA = ("nacrt", "objavljen", "zatvoren", "arhiviran")
VRSTE = ("vjezba", "ocjena")
VRSTA_NAZIV = {"vjezba": "Vježba", "ocjena": "Ocjena"}

STUPNJEVI = ("nikad", "pri_predaji", "uvijek")
STUPANJ_NAZIV = {
    "nikad": "Nikad",
    "pri_predaji": "Poslije",
    "uvijek": "Uvijek",
}

# 6 resursa koje učenik može vidjeti (Cakijeva odluka: Student View PO TESTU).
# `pri_predaji` za rješenja i video znači „nakon isteka roka" — do tada se ne smiju vidjeti jer bi
# učenik koji prvi preda podijelio odgovore ostalima (odluka 21.10.2026., zadržana).
RESURSI = {
    "bodovi": {"naziv": "Bodovanje po pitanju", "poslije_roka": False},
    "rjesenja": {"naziv": "Točna rješenja i objašnjenja", "poslije_roka": True},
    "video": {"naziv": "🎬 Video uz rješenje", "poslije_roka": True},
    "komentari": {"naziv": "Komentari profesora", "poslije_roka": False},
    "rezultat": {"naziv": "Ukupni rezultat, rang i prosjek", "poslije_roka": False},
    "pdf": {"naziv": "PDF izvoz rezultata", "poslije_roka": False},
}


def student_view_zadano() -> dict:
    """Zadano za novi test: bodove i rezultat vidi poslije predaje, rješenja i video nakon roka."""
    return {"bodovi": "pri_predaji", "rjesenja": "pri_predaji", "video": "pri_predaji",
            "komentari": "pri_predaji", "rezultat": "pri_predaji", "pdf": "uvijek"}


def _view_iz_jsona(v) -> dict:
    """Student View iz JSON-a, s dopunom zadanih vrijednosti (stariji zapisi)."""
    zadano = student_view_zadano()
    if isinstance(v, dict):
        ucitano = v
    else:
        tekst = model.tekst(v)
        ucitano = {}
        if tekst:
            try:
                import json
                objekt = json.loads(tekst)
                if isinstance(objekt, dict):
                    ucitano = objekt
            except Exception:                       # noqa: BLE001 — pokvaren JSON = zadano
                ucitano = {}
    izlaz = dict(zadano)
    for k in RESURSI:
        if model.tekst(ucitano.get(k)) in STUPNJEVI:
            izlaz[k] = model.tekst(ucitano.get(k))
    return izlaz


# ------------------------------------------------------------------ Student View

def smije_vidjeti(student_view, resurs: str, *, predano: bool = False,
                  rok_prosao: bool = False) -> bool:
    """Smije li učenik vidjeti `resurs` sada?

    - `nikad` → ne
    - `uvijek` → da
    - `pri_predaji` → za rješenja i video: **tek kad rok prođe**; za ostalo: kad preda
    """
    if resurs not in RESURSI:
        return False
    stupanj = _view_iz_jsona(student_view).get(resurs, "nikad")
    if stupanj == "nikad":
        return False
    if stupanj == "uvijek":
        return True
    if RESURSI[resurs]["poslije_roka"]:
        return bool(rok_prosao)
    return bool(predano)


def sto_vidi(student_view) -> list[dict]:
    """Za prikaz u administraciji: koji resurs, koja razina, što to znači."""
    izlaz = []
    for kljuc, opis in RESURSI.items():
        stupanj = _view_iz_jsona(student_view).get(kljuc, "nikad")
        izlaz.append({"kljuc": kljuc, "naziv": opis["naziv"], "stupanj": stupanj,
                      "znaci": ("ne vidi" if stupanj == "nikad"
                                else ("poslije roka" if (stupanj == "pri_predaji" and opis["poslije_roka"])
                                      else ("poslije predaje" if stupanj == "pri_predaji" else "uvijek")))})
    return izlaz


# ------------------------------------------------------------------ zadaci

def drugi_kljuc(zadatak: dict) -> str:
    return model.tekst((zadatak or {}).get("tip"))


def zadaci(definicija) -> list[dict]:
    return [z for z in model.kao_json((definicija or {}).get("zadaci_json")) if isinstance(z, dict)]


def bodovi_ukupno(zadaci_: list[dict]) -> float:
    return round(sum(model.broj((z or {}).get("bodovi"), 1) for z in zadaci_ or []), 2)


def _slovo(index: int) -> str:
    return chr(65 + index) if 0 <= index < 26 else ""


def _indeks_slova(slovo: str) -> int:
    s = model.tekst(slovo).upper()[:1]
    return ord(s) - 65 if "A" <= s <= "Z" else -1


def izmijesaj_odgovore(zadaci_: list[dict], seed) -> list[dict]:
    """Miješa SAMO ponuđene odgovore (redoslijed zadataka ostaje kakav je).

    Kod miješanja se **prepisuje točan odgovor u novo slovo** — inače bi ocjenjivanje bilo pogrešno
    (učenik odabere „C", a to je sada drugi tekst).
    """
    popis = [dict(z) for z in zadaci_ or []]
    lokalni = random.Random(f"{seed}|odgovori" if seed not in (None, "") else "caki")
    for z in popis:
        opcije = [model.tekst(o) for o in (z.get("opcije") or [])]
        if len(opcije) < 2:
            continue
        indeks_tocnog = _indeks_slova(model.tekst(z.get("odgovor")))
        if indeks_tocnog < 0 or indeks_tocnog >= len(opcije):
            continue                        # ključ nije slovo — ne diraj odgovore
        redoslijed = list(range(len(opcije)))
        lokalni.shuffle(redoslijed)
        z["opcije"] = [opcije[i] for i in redoslijed]
        z["odgovor"] = _slovo(redoslijed.index(indeks_tocnog))
    return popis


def izmijesaj(zadaci_: list[dict], seed, mijesaj_odgovore: bool = True) -> list[dict]:
    """A/B miješanje (Cakijeva odluka): ISTI sadržaj, drugi redoslijed zadataka i odgovora.

    Deterministički — isti `seed` uvijek daje isti test (važno za obranu od prigovora i za
    ponovni prikaz). Kod miješanja odgovora **prepisuje se točan odgovor** u novo slovo, inače bi
    ocijenjivanje bilo pogrešno.
    """
    popis = [dict(z) for z in zadaci_ or []]
    rnd = random.Random(str(seed) if seed not in (None, "") else "caki")
    rnd.shuffle(popis)
    if not mijesaj_odgovore:
        return popis
    return izmijesaj_odgovore(popis, seed)


def izbor_po_pravilima(banka: list[dict], pravila: list[dict], seed="") -> tuple[list[dict], list[str]]:
    """Slaganje testa po kvotama (npr. 4 iz algebre, 2 laka iz geometrije).

    `pravila` = [{"cjelina": "…", "tezina": "…", "broj": 4}] — prazno polje = ne filtrira.
    Vraća (odabrani, upozorenja). **Nikad ne vraća više nego što pravilo traži**, a ako nema
    dovoljno zadataka — kaže koliko fali (umjesto da tiho složi kraći test).
    """
    rnd = random.Random(str(seed) if seed not in (None, "") else "caki")
    odabrani: list[dict] = []
    upozorenja: list[str] = []
    iskoristeni: set[str] = set()

    for i, p in enumerate(pravila or [], start=1):
        cjelina = model.tekst((p or {}).get("cjelina"))
        tezina = model.tekst((p or {}).get("tezina"))
        tip = model.tekst((p or {}).get("tip"))
        trazi = model.cijeli((p or {}).get("broj"), 0)
        if trazi <= 0:
            continue
        kandidati = [
            z for z in banka or []
            if model.tekst(z.get("id")) not in iskoristeni
            and (not cjelina or model.tekst(z.get("cjelina")) == cjelina)
            and (not tezina or model.tekst(z.get("tezina")) == tezina)
            and (not tip or model.tekst(z.get("tip")) == tip)
        ]
        rnd.shuffle(kandidati)
        uzeto = kandidati[:trazi]
        for z in uzeto:
            iskoristeni.add(model.tekst(z.get("id")))
        odabrani += uzeto
        if len(uzeto) < trazi:
            opis = " · ".join(x for x in (cjelina, tezina, tip) if x) or f"pravilo {i}"
            upozorenja.append("„%s”: traženo %d, nađeno %d" % (opis, trazi, len(uzeto)))
    return odabrani, upozorenja


# ------------------------------------------------------------------ zapis testa

def nova_definicija(*, definicija_id: str, naziv: str, predmet: str, zadaci_: list[dict],
                    trajanje_min: int = 45, rok_od: str = "", rok_do: str = "",
                    vrsta: str = "ocjena", razina: str = "", autor: str = "",
                    ustanova_id: str = "caki", napomena: str = "",
                    student_view=None, varijanta_pravilo=None,
                    status: str = "nacrt") -> dict:
    """Sastavi zapis testa (dict spreman za `tablice.dodaj`)."""
    if status not in STANJA:
        raise ValueError(f"Nepoznato stanje: {status}")
    if vrsta not in VRSTE:
        raise ValueError(f"Nepoznata vrsta: {vrsta}")
    return {
        "definicija_id": model.tekst(definicija_id),
        "ustanova_id": model.tekst(ustanova_id) or "caki",
        "naziv": model.tekst(naziv),
        "predmet": model.tekst(predmet),
        "razina": model.tekst(razina),
        "vrsta": vrsta,
        "zadaci_json": model.u_json(zadaci_ or []),
        "broj_zadataka": len(zadaci_ or []),
        "bodovi_ukupno": bodovi_ukupno(zadaci_),
        "trajanje_min": model.cijeli(trajanje_min, 45),
        "rok_od": model.iso_datum(rok_od),
        "rok_do": model.iso_datum(rok_do),
        "status": status,
        "student_view_json": model.u_json(_view_iz_jsona(student_view)),
        "varijanta_pravilo": model.u_json(varijanta_pravilo or {"mijesaj_zadatke": True,
                                                                "mijesaj_odgovore": True}),
        "pdf_verzija": "",
        "autor": model.tekst(autor),
        "kreirano": model.sada_iso(),
        "napomena": model.tekst(napomena),
    }


def validiraj(d: dict) -> list[str]:
    """Što sprječava objavu. Vraća popis razloga (prazno = može se objaviti)."""
    greske = []
    if not model.tekst((d or {}).get("naziv")):
        greske.append("Test nema naziv.")
    zadaci_ = zadaci(d)
    if not zadaci_:
        greske.append("Test nema nijedan zadatak.")
    if model.cijeli((d or {}).get("trajanje_min"), 0) <= 0:
        greske.append("Vrijeme rješavanja mora biti veće od 0.")
    if bodovi_ukupno(zadaci_) <= 0:
        greske.append("Zadaci ne nose nijedan bod.")
    for i, z in enumerate(zadaci_, start=1):
        if not model.tekst((z or {}).get("id")):
            greske.append(f"Zadatak {i} nema ID.")
        if not model.tekst((z or {}).get("tekst")):
            greske.append(f"Zadatak {i} nema tekst.")
        if model.tekst((z or {}).get("tip")) == "visestruki_izbor" and len(z.get("opcije") or []) < 2:
            greske.append(f"Zadatak {i} je višestruki izbor, a nema barem dva odgovora.")
    od, do = model.datum((d or {}).get("rok_od")), model.datum((d or {}).get("rok_do"))
    if od and do and do < od:
        greske.append("Rok „do” je prije roka „od”.")
    return greske


def promijeni_status(sheet, definicija_id: str, novo: str, *, korisnik: str = "") -> bool:
    if novo not in STANJA:
        raise ValueError(f"Nepoznato stanje: {novo}")
    ok = tablice.azuriraj(sheet, tablice.TAB_DEFINICIJE, "definicija_id", definicija_id,
                          {"status": novo})
    if ok:
        tablice.zapisi_radnju(sheet, korisnik, f"status:{novo}", definicija_id)
    return ok


def ucitaj_sve(sheet) -> list[dict]:
    return tablice.ucitaj(sheet, tablice.TAB_DEFINICIJE)


def po_id(sheet, definicija_id: str) -> dict | None:
    for d in ucitaj_sve(sheet):
        if model.tekst(d.get("definicija_id")) == model.tekst(definicija_id):
            return d
    return None


def je_objavljen(d: dict | None) -> bool:
    return model.tekst((d or {}).get("status")) in ("objavljen", "zatvoren")


def nacrti(sheet) -> list[dict]:
    return [d for d in ucitaj_sve(sheet) if model.tekst(d.get("status")) == "nacrt"]
