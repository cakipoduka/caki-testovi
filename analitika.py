"""
CAKI testovi v2 — `analitika.py`
MJERENJE KVALITETE ZADATKA — čega u starom sustavu uopće nije bilo.

Što računa (i zašto):
  · **p-vrijednost** (težina) — udio učenika koji je zadatak riješio točno.
        p < 0,30 → pretežak · p > 0,90 → prelagan (ne razlikuje nikoga)
  · **diskriminativnost** (r) — razlikuje li zadatak dobre od slabijih učenika.
        r < 0,20 → zadatak ne razlikuje (provjeriti tekst ili ponuđene odgovore)
  · **distraktori** — koliko je puta koji ponuđeni odgovor odabran.
        distraktor koji nitko ne odabere = „mrtav" (ne radi svoj posao)
  · **Cronbach α** — pouzdanost cijelog testa (0–1; ≥ 0,70 je prihvatljivo za razredni test)

Sve je čisto (bez Streamlita i bez Sheeta) — ulaz su zapisi iz `Ocjene_zadataka` i `Pokusaji`,
zato se lako testira.

VAŽNO: ovo su **pokazatelji, ne presude**. Mali razred (n < 10) daje nestabilne brojke i to se
u izvještaju mora reći, inače profesor počne „popravljati" ispravne zadatke.
"""
from __future__ import annotations

import math

import model

PRAG_PRELAKO = 0.90          # p iznad ovoga: zadatak ne razlikuje
PRAG_PREVISE_TESKO = 0.30    # p ispod ovoga: pretežak za ovu skupinu
PRAG_DISKRIMINACIJE = 0.20   # r ispod ovoga: ne razlikuje dobre od slabijih
PRAG_ALFA = 0.70             # pouzdanost ispod: test miješa više različitih stvari
NAJMANJE_ZA_STATISTIKU = 10  # ispod ovoga brojke su orijentacijske


# ------------------------------------------------------------------ osnovno

def _tocno(red: dict) -> bool:
    vrijednost = red.get("tocno")
    if isinstance(vrijednost, bool):
        return vrijednost
    return model.tekst(vrijednost).lower() in ("true", "1", "da", "tocno", "točno")


def _prosjek(brojevi) -> float:
    n = len(brojevi)
    return sum(brojevi) / n if n else 0.0


def _sd(brojevi) -> float:
    n = len(brojevi)
    if n < 2:
        return 0.0
    sredina = _prosjek(brojevi)
    return math.sqrt(sum((x - sredina) ** 2 for x in brojevi) / n)


# ------------------------------------------------------------------ po zadatku

def p_vrijednost(svi: list[dict]) -> float:
    """Udio točnih odgovora (0–1)."""
    if not svi:
        return 0.0
    return sum(1 for r in svi if _tocno(r)) / len(svi)


def diskriminativnost(svi: list[dict], ukupno_po_pokusaju: dict) -> float:
    """Point-biserial: korelacija točnosti zadatka s ukupnim rezultatom pokušaja.

    Računa se u čistom Pythonu (bez numpyja) da modul radi svugdje. Vraća −1 … 1;
    negativna vrijednost znači da bolji učenici češće griješe (znak loše formulacije).
    """
    parovi = []
    for r in svi or []:
        pid = model.tekst(r.get("pokusaj_id"))
        if pid not in ukupno_po_pokusaju:
            continue
        parovi.append((1.0 if _tocno(r) else 0.0, float(ukupno_po_pokusaju[pid])))
    if len(parovi) < 3:
        return 0.0
    p = _prosjek([x for x, _ in parovi])
    q = 1.0 - p
    if p in (0.0, 1.0):
        return 0.0                                   # nema varijance → nema korelacije
    sredina_uk = _prosjek([y for _, y in parovi])
    sd_uk = _sd([y for _, y in parovi])
    if sd_uk == 0:
        return 0.0
    tocni = [y for x, y in parovi if x == 1.0]
    netocni = [y for x, y in parovi if x == 0.0]
    if not tocni or not netocni:
        return 0.0
    razlika = _prosjek(tocni) - _prosjek(netocni)
    return round(razlika / sd_uk * math.sqrt(p * q), 3)


def distraktori(opcije: list[str], svi: list[dict], tocan: str) -> list[dict]:
    """Koliko je puta koji ponuđeni odgovor odabran (i je li „mrtav")."""
    broj = {model.tekst(o): 0 for o in (opcije or []) if model.tekst(o)}
    for r in svi or []:
        odabrano = model.tekst(r.get("odgovor"))
        if odabrano in broj:
            broj[odabrano] += 1
    ukupno = sum(broj.values())
    izlaz = []
    for tekst, koliko in broj.items():
        izlaz.append({
            "opcija": tekst,
            "odabrano": koliko,
            "udio": round(koliko / ukupno, 3) if ukupno else 0.0,
            "tocan": model.tekst(tekst) == model.tekst(tocan),
            "mrtav": koliko == 0 and model.tekst(tekst) != model.tekst(tocan),
        })
    return izlaz


def oznaka_tezine(p: float) -> str:
    if p > PRAG_PRELAKO:
        return "prelagan"
    if p < PRAG_PREVISE_TESKO:
        return "pretežak"
    return "primjeren"


def oznaka_diskriminacije(r: float) -> str:
    if r < 0:
        return "obrnut (bolji griješe)"
    if r < PRAG_DISKRIMINACIJE:
        return "ne razlikuje"
    return "razlikuje"


def preporuka(p: float, r: float, mrtvi: int) -> str:
    """Kratka, izvediva preporuka — ne „statistika radi statistike"."""
    if r < 0:
        return "Provjeri je li točan odgovor dobro označen — bolji učenici griješe."
    if p > PRAG_PRELAKO and r < PRAG_DISKRIMINACIJE:
        return "Prelagan i ne razlikuje — koristi ga kao uvodni, ne za ocjenu."
    if p < PRAG_PREVISE_TESKO and r < PRAG_DISKRIMINACIJE:
        return "Pretežak za ovu skupinu — provjeri je li potrebno predznanje."
    if mrtvi:
        return f"{mrtvi} ponuđeni odgovor nitko nije odabrao — zamijeni ga vjerojatnijim."
    if r < PRAG_DISKRIMINACIJE:
        return "Ne razlikuje dobre od slabijih — provjeri formulaciju."
    return "Zadatak radi svoj posao."


# ------------------------------------------------------------------ cijeli test

def cronbach_alfa(matrice: list[list[float]]) -> float:
    """Pouzdanost testa. `matrice` = jedan redak po pokušaju, jedan stupac po zadatku (0/1 ili bodovi)."""
    redci = [r for r in (matrice or []) if r]
    if len(redci) < 2:
        return 0.0
    k = len(redci[0])
    if k < 2:
        return 0.0
    stupci = [[float(red[i]) for red in redci] for i in range(k)]
    zbroj_varijanci = sum(_sd(s) ** 2 for s in stupci)
    ukupno = [sum(red) for red in redci]
    var_ukupno = _sd(ukupno) ** 2
    if var_ukupno == 0:
        return 0.0
    alfa = (k / (k - 1)) * (1 - zbroj_varijanci / var_ukupno)
    return round(max(-1.0, min(1.0, alfa)), 3)


def oznaka_pouzdanosti(alfa: float) -> str:
    if alfa >= 0.80:
        return "visoka"
    if alfa >= PRAG_ALFA:
        return "prihvatljiva"
    if alfa > 0:
        return "niska — test miješa više različitih stvari"
    return "ne može se izračunati (premalo podataka)"


def statistika_zadatka(zadatak: dict, ocjene: list[dict], ukupno_po_pokusaju: dict) -> dict:
    """Sve brojke za jedan zadatak + preporuka."""
    svi = [r for r in (ocjene or [])
           if model.tekst(r.get("zadatak_id")) == model.tekst((zadatak or {}).get("id"))]
    p = p_vrijednost(svi)
    r = diskriminativnost(svi, ukupno_po_pokusaju)
    dist = distraktori((zadatak or {}).get("opcije") or [], svi, (zadatak or {}).get("odgovor"))
    mrtvi = sum(1 for d in dist if d["mrtav"])
    return {
        "zadatak_id": model.tekst((zadatak or {}).get("id")),
        "tekst": model.tekst((zadatak or {}).get("tekst"))[:120],
        "odgovora": len(svi),
        "p": round(p, 3),
        "tezina": oznaka_tezine(p),
        "r": r,
        "diskriminacija": oznaka_diskriminacije(r),
        "distraktori": dist,
        "mrtvih_distraktora": mrtvi,
        "preporuka": preporuka(p, r, mrtvi),
    }


def izracunaj(zadaci: list[dict], ocjene: list[dict], pokusaji: list[dict]) -> dict:
    """Cijeli izvještaj za jedan test.

    `pokusaji` trebaju imati `pokusaj_id` i `bodovi` (ukupno po pokušaju).
    """
    ukupno_po_pokusaju = {model.tekst(p.get("pokusaj_id")): model.broj(p.get("bodovi"))
                          for p in (pokusaji or []) if model.tekst(p.get("pokusaj_id"))}
    po_zadatku = [statistika_zadatka(z, ocjene, ukupno_po_pokusaju) for z in (zadaci or [])]

    # matrica za alfau: pokušaj × zadatak (1 = točno, 0 = netočno)
    ids_zad = [model.tekst(z.get("id")) for z in (zadaci or [])]
    ids_pok = list(ukupno_po_pokusaju)
    matrica = []
    for pid in ids_pok:
        red = []
        for zid in ids_zad:
            pogodak = next((r for r in (ocjene or [])
                            if model.tekst(r.get("pokusaj_id")) == pid
                            and model.tekst(r.get("zadatak_id")) == zid), None)
            red.append(1.0 if (pogodak and _tocno(pogodak)) else 0.0)
        matrica.append(red)

    alfa = cronbach_alfa(matrica)
    n = len(ukupno_po_pokusaju)
    bodovi = list(ukupno_po_pokusaju.values())
    return {
        "zadataka": len(zadaci or []),
        "ucenika": n,
        "alfa": alfa,
        "pouzdanost": oznaka_pouzdanosti(alfa),
        "prosjek_bodova": round(_prosjek(bodovi), 2) if bodovi else 0.0,
        "medijan_bodova": round(_medijan(bodovi), 2) if bodovi else 0.0,
        "raspon_bodova": (round(min(bodovi), 2), round(max(bodovi), 2)) if bodovi else (0, 0),
        "po_zadatku": po_zadatku,
        "po_cjelinama": po_cjelinama(zadaci, ocjene),
        "pouzdano": n >= NAJMANJE_ZA_STATISTIKU,
        "napomena": ("" if (n >= NAJMANJE_ZA_STATISTIKU or n == 0) else
                     f"Manje od {NAJMANJE_ZA_STATISTIKU} predanih — brojke su orijentacijske, "
                     "ne donosi zaključke o zadatku."),
    }


def _medijan(brojevi):
    uredeni = sorted(brojevi or [])
    n = len(uredeni)
    if not n:
        return 0.0
    sredina = n // 2
    return uredeni[sredina] if n % 2 else (uredeni[sredina - 1] + uredeni[sredina]) / 2


def sazetak(izvjestaj: dict, najvise: int = 5) -> list[str]:
    """Najvažnije rečenice za brzi pregled (Caki ne čita tablice)."""
    if not izvjestaj or not izvjestaj.get("po_zadatku"):
        return []
    redci = []
    if izvjestaj.get("napomena"):
        redci.append("⚠️ " + izvjestaj["napomena"])
    slabi = [z for z in izvjestaj.get("po_zadatku", [])
             if z["diskriminacija"] in ("ne razlikuje", "obrnut (bolji griješe)")]
    teski = [z for z in izvjestaj.get("po_zadatku", []) if z["tezina"] == "pretežak"]
    if slabi:
        redci.append(f"{len(slabi)} zadataka ne razlikuje dobre od slabijih.")
    if teski:
        redci.append(f"{len(teski)} zadataka je preteško za ovu skupinu.")
    mrtvi = sum(z["mrtvih_distraktora"] for z in izvjestaj.get("po_zadatku", []))
    if mrtvi:
        redci.append(f"{mrtvi} ponuđenih odgovora nitko nije odabrao.")
    alfa = izvjestaj.get("alfa", 0)
    if alfa and alfa < PRAG_ALFA:
        redci.append(f"Pouzdanost testa je niska (α = {alfa}) — test miješa previše različitih stvari.")
    slaba = najslabija_cjelina(izvjestaj)
    if slaba:
        redci.append(slaba)
    if not redci:
        redci.append("Nema upozorenja — zadaci rade svoj posao.")
    return redci[:najvise]


# ------------------------------------------------------------------ po cjelinama

def po_cjelinama(zadaci: list[dict], ocjene: list[dict]) -> list[dict]:
    """Koja cjelina najviše pada — zbroj bodova po cjelini, najslabija prva.

    Učeniku to govori „vježbaj ovo", profesoru „ovo nije sjelo na satu". Zadatak ulazi u cjelinu
    prema polju `cjelina` (prazno → „(bez cjeline)").
    """
    ocjene_po_zadatku = {}
    for r in (ocjene or []):
        ocjene_po_zadatku.setdefault(model.tekst(r.get("zadatak_id")), []).append(r)

    skupine: dict[str, dict] = {}
    for z in (zadaci or []):
        cjelina = model.tekst(z.get("cjelina")) or "(bez cjeline)"
        red = skupine.setdefault(cjelina, {"cjelina": cjelina, "zadataka": 0,
                                           "odgovora": 0, "tocnih": 0, "bodovi": 0.0,
                                           "bodovi_max": 0.0})
        red["zadataka"] += 1
        red["bodovi_max"] += model.broj(z.get("bodovi"), 1)
        for r in ocjene_po_zadatku.get(model.tekst(z.get("id")), []):
            red["odgovora"] += 1
            red["bodovi"] += model.broj(r.get("bodovi"))
            if _tocno(r):
                red["tocnih"] += 1

    izlaz = []
    for red in skupine.values():
        p = (red["tocnih"] / red["odgovora"]) if red["odgovora"] else 0.0
        izlaz.append({**red, "p": round(p, 3), "udio_bodova": round(
            (red["bodovi"] / red["bodovi_max"]) if red["bodovi_max"] else 0.0, 3)})
    izlaz.sort(key=lambda r: (r["p"], -r["zadataka"]))
    return izlaz


def najslabija_cjelina(izvjestaj: dict) -> str:
    """Jedna rečenica za sažetak: koja cjelina najviše pada."""
    cjeline = (izvjestaj or {}).get("po_cjelinama") or []
    slabe = [c for c in cjeline if c["odgovora"] and c["p"] < 0.5]
    if not slabe:
        return ""
    prva = slabe[0]
    return (f"Najslabija cjelina: **{prva['cjelina']}** "
            f"({int(round(prva['p'] * 100))} % točnih na {prva['zadataka']} zadataka).")
