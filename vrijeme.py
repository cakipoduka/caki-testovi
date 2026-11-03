"""
CAKI testovi v2 — `vrijeme.py`  (PLAN 16 — vremenska analiza)

Dva pogleda:
  · **po učeniku** — koliko je trajao pokušaj (`trajanje_s`) i je li udario u rok,
  · **po zadatku** — koliko je prosječno trebalo za zadatak (`Ocjene_zadataka.vrijeme_s`),
    ali samo ako je to polje popunjeno (novi testovi); za uvezene testove ga nema.

Ne izmišlja podatke: ako `vrijeme_s` nema, to se kaže.
"""
from __future__ import annotations

import model


def po_uceniku(pokusaji, dodjele) -> list[dict]:
    """Trajanje po učeniku (minute), sortirano od najduljeg."""
    imena = {model.tekst(d.get("dodjela_id")):
             (model.tekst(d.get("ime_djeteta")) or model.tekst(d.get("ucenik_id")))
             for d in dodjele or []}
    izlaz = []
    for p in pokusaji or []:
        sek = model.broj(p.get("trajanje_s"), 0)
        if not sek:
            continue
        izlaz.append({
            "ucenik": imena.get(model.tekst(p.get("dodjela_id")))
                      or model.tekst(p.get("ucenik_id")) or "—",
            "minute": int(round(sek / 60)),
            "status": model.tekst(p.get("status")) or "—",
        })
    izlaz.sort(key=lambda r: -r["minute"])
    return izlaz


def po_zadatku(zadaci, ocjene) -> list[dict]:
    """Prosječno vrijeme po zadatku; prazno ako `vrijeme_s` nije popunjeno."""
    po_id: dict[str, list[float]] = {}
    for r in ocjene or []:
        v = model.broj(r.get("vrijeme_s"), 0)
        if not v:
            continue
        po_id.setdefault(model.tekst(r.get("zadatak_id")), []).append(float(v))

    izlaz = []
    for i, z in enumerate(zadaci or [], start=1):
        zid = model.tekst(z.get("id"))
        vremena = po_id.get(zid) or []
        if not vremena:
            continue
        izlaz.append({
            "redni": i,
            "zadatak_id": zid,
            "tekst": model.tekst(z.get("tekst"))[:70],
            "prosjek_s": int(round(sum(vremena) / len(vremena))),
            "najdulje_s": int(round(max(vremena))),
            "mjerenja": len(vremena),
        })
    izlaz.sort(key=lambda r: -r["prosjek_s"])
    return izlaz


def sazetak(pokusaji, dodjele, zadaci, ocjene) -> dict:
    """Brojevi za karticu + zastavica ima li vremena po zadatku."""
    ucenici = po_uceniku(pokusaji, dodjele)
    zad = po_zadatku(zadaci, ocjene)
    minute = [r["minute"] for r in ucenici]
    return {
        "ucenika": len(ucenici),
        "prosjek_min": int(round(sum(minute) / len(minute))) if minute else 0,
        "najdulje_min": max(minute) if minute else 0,
        "najkrace_min": min(minute) if minute else 0,
        "ima_vrijeme_zadatka": bool(zad),
        "najsporiji_zadatak": zad[0] if zad else None,
    }
