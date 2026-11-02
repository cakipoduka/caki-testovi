"""
CAKI testovi v2 — `po_uceniku.py`
👤 KARTICA „PO UČENIKU" — po v1 rasporedu (`testovi_admin`, kartica „Po učeniku").

Sadržaj (redom kao u v1):
  1. popis testova učenika (test · datum · bodovi · %),
  2. **cjeline kroz sve testove — najslabija prva**,
  3. **🧠 Bloom po razinama** — samo za testove koji imaju Bloom (novi testovi),
  4. **Sažetak za roditelja** (tekst za WhatsApp/mail).

Cjeline se uzimaju iz **zadatka** (`cjelina`), pa rade i za stare (uvozne) testove.
Bloom se uzima iz **zadatka** kad postoji; ako ga nema — razina se preskače (ne izmišljamo).
"""
from __future__ import annotations

import model

BLOOM_REDOSLIJED = ("Pamćenje", "Razumijevanje", "Primjena", "Analiza", "Vrednovanje", "Sinteza")


def _je_tocno(r: dict) -> bool:
    return model.tekst(r.get("tocno")).lower() in ("da", "true", "točno", "tocno")


def prikupi(sheet_data: dict) -> dict:
    """`sheet_data` = {"dodjele", "pokusaji", "ocjene", "definicije"} → podaci za jednog učenika."""
    d = sheet_data or {}
    return d


def testovi_ucenika(dodjele: list[dict], pokusaji: list[dict], definicije_po_id: dict) -> list[dict]:
    """Svi testovi jednog učenika (iz dodjela/pokušaja), s bodovima i postotkom."""
    pokusaj_po_dodjeli = {model.tekst(p.get("dodjela_id")): p for p in pokusaji or []}
    izlaz = []
    for dd in dodjele or []:
        p = pokusaj_po_dodjeli.get(model.tekst(dd.get("dodjela_id"))) or {}
        d = (definicije_po_id or {}).get(model.tekst(dd.get("definicija_id"))) or {}
        bodovi = model.broj(p.get("bodovi"), 0)
        maks = model.broj(p.get("bodovi_max"), 0)
        izlaz.append({
            "test": model.tekst(d.get("naziv")) or model.tekst(dd.get("definicija_id")),
            "datum": model.tekst(p.get("predaja"))[:10] or "—",
            "bodovi": bodovi,
            "maks": maks,
            "postotak": int(round(100 * bodovi / maks)) if maks else 0,
            "status": model.tekst(p.get("status")) or "nije počeo",
        })
    return sorted(izlaz, key=lambda r: r["datum"])


def cjeline(zadaci: list[dict], ocjene: list[dict]) -> list[dict]:
    """Cjeline kroz sve testove, najslabija prva (udio točnih)."""
    po_id = {model.tekst(z.get("id")): z for z in zadaci or []}
    skup: dict[str, dict] = {}
    for r in ocjene or []:
        z = po_id.get(model.tekst(r.get("zadatak_id"))) or {}
        cj = model.tekst(z.get("cjelina")) or "— bez cjeline —"
        s = skup.setdefault(cj, {"cjelina": cj, "zadataka": 0, "tocno": 0, "netocno": 0,
                                 "odgovora": 0})
        s["zadataka"] += 1
        if _je_tocno(r):
            s["tocno"] += 1
        elif model.tekst(r.get("odgovor")):
            s["netocno"] += 1
        else:
            s["odgovora"] += 1

    izlaz = list(skup.values())
    for s in izlaz:
        uk = s["tocno"] + s["netocno"] + s["odgovora"]
        s["postotak"] = int(round(100 * s["tocno"] / uk)) if uk else 0
    izlaz.sort(key=lambda r: (r["postotak"], -r["zadataka"]))
    return izlaz


def bloom(zadaci: list[dict], ocjene: list[dict]) -> list[dict]:
    """Razine razmišljanja kroz testove — samo one koje zadaci stvarno imaju."""
    po_id = {model.tekst(z.get("id")): z for z in zadaci or []}
    skup: dict[str, dict] = {}
    for r in ocjene or []:
        z = po_id.get(model.tekst(r.get("zadatak_id"))) or {}
        razina = model.tekst(z.get("bloom"))
        if not razina:
            continue
        s = skup.setdefault(razina, {"razina": razina, "zadataka": 0, "tocno": 0})
        s["zadataka"] += 1
        if _je_tocno(r):
            s["tocno"] += 1
    izlaz = list(skup.values())
    for s in izlaz:
        s["postotak"] = int(round(100 * s["tocno"] / s["zadataka"])) if s["zadataka"] else 0
    izlaz.sort(key=lambda r: BLOOM_REDOSLIJED.index(r["razina"])
               if r["razina"] in BLOOM_REDOSLIJED else 99)
    return izlaz


def sazetak_za_roditelja(ucenik: str, testovi: list[dict], cjeline_: list[dict],
                         *, ime_brenda: str = "CAKI") -> str:
    """Kratki tekst za WhatsApp/mail — bez ocjena, samo ostvareni rezultat i preporuka."""
    redci = [f"{ucenik} — rezultati testova ({ime_brenda})"]
    if testovi:
        prosjek = int(round(sum(t["postotak"] for t in testovi) / len(testovi)))
        redci.append(f"Testova: {len(testovi)} · prosječno {prosjek} %")
        for t in testovi[-3:]:
            redci.append(f"• {t['test']}: {t['bodovi']:g}/{t['maks']:g} ({t['postotak']} %)")
    if cjeline_:
        najslabija = cjeline_[0]
        najjaca = cjeline_[-1]
        redci.append(f"Najjače: {najjaca['cjelina']} ({najjaca['postotak']} %)")
        redci.append(f"Za vježbanje: {najslabija['cjelina']} ({najslabija['postotak']} %)")
    redci.append("Rezultat pokazuje koliko je usvojeno — služi kao putokaz za dalje.")
    return "\n".join(redci)
