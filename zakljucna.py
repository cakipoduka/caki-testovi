"""
CAKI testovi v2 — `zakljucna.py`
🎓 ZAKLJUČNA OCJENA iz više testova (šifrarnik ocjena).

Zašto: profesor na kraju razdoblja ne gleda pojedinačni test, nego **prosjek učenika kroz testove**.
Ovo to izračuna, ali **ne odlučuje** — daje predlog i ostavlja profesor da ga promijeni.

Pravila (hrvatsko ocjenjivanje, Caki može mijenjati pragove u jednom retku):
  1 (nedovoljan) < 50 % · 2 (dovoljan) 50–64 % · 3 (dobar) 65–79 % · 4 (vrlo dobar) 80–89 % · 5 (odličan) 90 %+

VAŽNO: test koji učenik **nije pisao** ne ulazi u prosjek kao nula — inače bi izostanak s jednog testa
srušio ocjenu. Takav test se broji posebno („nije pisao: 2") i profesor odlučuje.
"""
from __future__ import annotations

import model

PRAGOVI = [(90, 5), (80, 4), (65, 3), (50, 2)]
NAZIVI = {5: "odličan (5)", 4: "vrlo dobar (4)", 3: "dobar (3)", 2: "dovoljan (2)", 1: "nedovoljan (1)"}


def postotak(bodovi, maks) -> int:
    b, m = model.broj(bodovi), model.broj(maks)
    return int(round(100 * b / m)) if m else 0


def predlozi_ocjenu(postotak: int, pragovi=None) -> int:
    """Brojka 1–5 iz prosjeka postotaka. Pragovi se mogu promijeniti bez diranja ostatka."""
    for granica, ocjena in (pragovi or PRAGOVI):
        if int(postotak or 0) >= granica:
            return ocjena
    return 1


def naziv_ocjene(ocjena: int) -> str:
    return NAZIVI.get(int(ocjena or 0), "—")


# ------------------------------------------------------------------ prikupljanje

def prikupi(dodjele: list[dict], pokusaji: list[dict], testovi: dict) -> list[dict]:
    """Za svakog učenika: rezultati po testu, prosjek, predlog ocjene i što nije pisao.

    `testovi` je preslikavanje `definicija_id` → definicija (za naziv i maksimum bodova).
    """
    po_uceniku: dict[str, dict] = {}
    po_dodjeli = {model.tekst(p.get("dodjela_id")): p for p in (pokusaji or [])}

    for d in (dodjele or []):
        ucenik = model.tekst(d.get("ucenik_id")).upper()
        if not ucenik:
            continue
        red = po_uceniku.setdefault(ucenik, {
            "ucenik_id": ucenik,
            "ime": model.tekst(d.get("ime_djeteta")),
            "grupa": model.tekst(d.get("grupa")),
            "testovi": [], "nije_pisao": [],
        })
        definicija = (testovi or {}).get(model.tekst(d.get("definicija_id"))) or {}
        naziv = model.tekst(definicija.get("naziv")) or model.tekst(d.get("definicija_id"))
        pokusaj = po_dodjeli.get(model.tekst(d.get("dodjela_id")))
        if pokusaj and model.tekst(pokusaj.get("status")) == "predano":
            p = postotak(pokusaj.get("bodovi"), pokusaj.get("bodovi_max"))
            red["testovi"].append({"test": naziv, "postotak": p,
                                   "bodovi": model.broj(pokusaj.get("bodovi")),
                                   "maks": model.broj(pokusaj.get("bodovi_max"))})
        elif not pokusaj:
            red["nije_pisao"].append(naziv)

    izlaz = []
    for red in po_uceniku.values():
        postoci = [t["postotak"] for t in red["testovi"]]
        prosjek = int(round(sum(postoci) / len(postoci))) if postoci else 0
        predlog = predlozi_ocjenu(prosjek) if postoci else 0
        izlaz.append({
            **red,
            "prosjek": prosjek,
            "predlog": predlog,
            "predlog_naziv": naziv_ocjene(predlog) if predlog else "—",
            "pisao": len(postoci),
            "nije_pisao_broj": len(red["nije_pisao"]),
        })
    izlaz.sort(key=lambda r: (-r["prosjek"], r["ucenik_id"]))
    return izlaz


def sazetak(redci: list[dict]) -> dict:
    """Koliko učenika po pojedinoj ocjeni — za brzi pregled na kraju."""
    brojevi = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 0: 0}
    for r in (redci or []):
        brojevi[int(r.get("predlog") or 0)] = brojevi.get(int(r.get("predlog") or 0), 0) + 1
    ukupno = sum(brojevi.values())
    prosjek = (sum(r["prosjek"] for r in (redci or [])) / len(redci)) if redci else 0
    return {"po_ocjeni": brojevi, "ukupno": ukupno, "prosjek_razreda": int(round(prosjek))}


def upozorenja(redci: list[dict]) -> list[str]:
    """Što profesor mora pogledati prije zaključivanja."""
    redci = list(redci or [])
    izlaz = []
    bez = [r for r in redci if not r.get("pisao")]
    if bez:
        izlaz.append("**" + str(len(bez)) + "** učenika nema ni jedan predan test — ne može se "
                     "predložiti ocjena.")
    nepotpuni = [r for r in redci if r.get("pisao") and r.get("nije_pisao_broj")]
    if nepotpuni:
        izlaz.append(f"**{len(nepotpuni)}** učenika nije pisalo sve testove — prosjek je iz "
                     "predanih, izostanci se ne računaju kao nula.")
    granicni = [r for r in redci if r.get("pisao") and r["prosjek"] in (49, 50, 64, 65, 79, 80, 89, 90)]
    if granicni:
        izlaz.append(f"**{len(granicni)}** učenika je na granici ocjene (49/50, 64/65, 79/80, 89/90) — "
                     "njih pogledaj posebno.")
    return izlaz


def tablica(redci: list[dict]) -> list[dict]:
    """Redci za prikaz u Streamlitu (onako kako profesor čita)."""
    return [{
        "Učenik": r.get("ime") or r["ucenik_id"],
        "Šifra": r["ucenik_id"],
        "Grupa": r.get("grupa") or "—",
        "Testova": f"{r['pisao']}/{r['pisao'] + r['nije_pisao_broj']}",
        "Prosjek %": r["prosjek"],
        "Predlog": r["predlog_naziv"],
        "Nije pisao": ", ".join(r["nije_pisao"][:3]) + (" …" if len(r["nije_pisao"]) > 3 else ""),
    } for r in (redci or [])]


# ------------------------------------------------------------------ razina rezultata (bez ocjene)

# Cakijeva napomena 26.10.2026.: „Ja kad držim poduku, ne ocjenjujem djecu nego im pomažem položiti
# ispite." Zato izvještaj za roditelje NE govori o školskoj ocjeni, nego o **ostvarenom rezultatu**.
RAZINE = [
    (90, "izvrstan rezultat"),
    (75, "vrlo dobar rezultat"),
    (60, "dobar rezultat"),
    (45, "osnovni rezultat — treba vježbati"),
    (0, "potrebno je sustavno vježbanje"),
]


def razina_rezultata(postotak: int) -> str:
    """Opisna razina rezultata (bez brojke ocjene) — za izvještaj roditelju."""
    for granica, naziv in RAZINE:
        if int(postotak or 0) >= granica:
            return naziv
    return RAZINE[-1][1]


def ostvareno(postotak: int) -> str:
    """Jedan redak za izvještaj: „78 % — vrlo dobar rezultat"."""
    return f"{int(postotak or 0)} % — {razina_rezultata(postotak)}"
