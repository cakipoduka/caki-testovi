"""
CAKI testovi v2 — `podsjetnik.py`
📨 KOGA PODSJETITI — tko nije otvorio test, tko je otvorio a nije predao.

Zašto: Caki pošalje test i informaciju, ali ne zna je li došla do učenika. Sada se to vidi i može se
**poslati poruka** (WhatsApp, e-mail, roditelju) — bez slanja iz aplikacije, jer to Caki radi svojim
kanalom. Aplikacija pripremi **popis i tekst**.

Kategorije (od najhitnije):
  · `nije_otvorio`   — učenik nije ni otvorio portal od objave
  · `otvorio_nije_poceo` — bio je, ali test nije počeo
  · `poceo_nije_predao`  — počeo je i stao (autosave čuva, ali rok ide)
  · `predao`         — ne treba podsjetnik
"""
from __future__ import annotations

import model

KATEGORIJE = {
    "nije_otvorio": "nije ni otvorio portal",
    "otvorio_nije_poceo": "otvorio portal, nije počeo test",
    "poceo_nije_predao": "počeo test, nije predao",
    "predao": "predao",
}


def kategorija(pokusaj, je_otvorio: bool) -> str:
    """U kojoj je skupini učenik za ovaj test."""
    if pokusaj and model.tekst(pokusaj.get("status")) == "predano":
        return "predao"
    if pokusaj:
        return "poceo_nije_predao"
    return "otvorio_nije_poceo" if je_otvorio else "nije_otvorio"


def popis(dodjele: list[dict], pokusaji: list[dict], posjete_sazetak: dict | None = None,
          *, samo_aktivne: bool = True) -> list[dict]:
    """Za svaku dodjelu: učenik, kategorija i treba li podsjetnik."""
    po_dodjeli = {model.tekst(p.get("dodjela_id")): p for p in (pokusaji or [])}
    sazetak = posjete_sazetak or {}
    izlaz = []
    for d in (dodjele or []):
        ucenik = model.tekst(d.get("ucenik_id")).upper()
        if not ucenik:
            continue
        pokusaj = po_dodjeli.get(model.tekst(d.get("dodjela_id")))
        otvorio = bool((sazetak.get(ucenik) or {}).get("posjeta", 0))
        kat = kategorija(pokusaj, otvorio)
        izlaz.append({
            "ucenik_id": ucenik,
            "ime": model.tekst(d.get("ime_djeteta")) or ucenik,
            "grupa": model.tekst(d.get("grupa")),
            "dodjela_id": model.tekst(d.get("dodjela_id")),
            "kategorija": kat,
            "opis": KATEGORIJE.get(kat, ""),
            "treba": kat != "predao",
            "posjeta": int((sazetak.get(ucenik) or {}).get("posjeta", 0)),
            "zadnji": model.tekst((sazetak.get(ucenik) or {}).get("zadnji")),
        })
    redoslijed = {"nije_otvorio": 0, "otvorio_nije_poceo": 1,
                  "poceo_nije_predao": 2, "predao": 3}
    izlaz.sort(key=lambda r: (redoslijed.get(r["kategorija"], 4), r["ime"]))
    return [r for r in izlaz if r["treba"]] if samo_aktivne else izlaz


def brojevi(redci: list[dict]) -> dict:
    """Koliko u kojoj skupini (za brzi pregled iznad popisa)."""
    izlaz = {k: 0 for k in KATEGORIJE}
    for r in (redci or []):
        izlaz[r["kategorija"]] = izlaz.get(r["kategorija"], 0) + 1
    izlaz["ukupno"] = len(redci or [])
    return izlaz


def tekst_poruke(ime: str, naziv_testa: str, rok: str = "", kategorija_kljuc: str = "") -> str:
    """Kratka poruka koju Caki može poslati (WhatsApp/e-mail). Prilagođena situaciji."""
    ime = model.tekst(ime) or "učenik"
    naziv_testa = model.tekst(naziv_testa) or "test"
    rok_dio = f" Rok je {rok}." if model.tekst(rok) else ""
    if kategorija_kljuc == "poceo_nije_predao":
        return (f"Bok {ime}, počeo si {naziv_testa}, ali nije predan.{rok_dio} "
                "Odgovori su spremljeni — otvori portal i predaj kad završiš.")
    if kategorija_kljuc == "otvorio_nije_poceo":
        return (f"Bok {ime}, vidio sam da si otvorio portal, ali {naziv_testa} nije počeo.{rok_dio} "
                "Otvaranje testa ne pokreće vrijeme — slobodno počni kad si spreman.")
    return (f"Bok {ime}, {naziv_testa} te još čeka i nije otvoren.{rok_dio} "
            "Prijavi se u portal sa svojom šifrom.")


def sve_poruke(redci: list[dict], naziv_testa: str, rok: str = "") -> str:
    """Sve poruke u jednom tekstu (za kopiranje u WhatsApp grupu ili e-mail)."""
    dijelovi = [f"Podsjetnik — {model.tekst(naziv_testa)}"
                + (f" (rok {rok})" if model.tekst(rok) else ""), ""]
    for r in (redci or []):
        dijelovi.append(f"• {r['ime']} ({r['ucenik_id']}) — {r['opis']}")
        dijelovi.append("  " + tekst_poruke(r["ime"], naziv_testa, rok, r["kategorija"]))
        dijelovi.append("")
    return "\n".join(dijelovi).strip()
