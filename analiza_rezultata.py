"""
CAKI testovi v2 — `analiza_rezultata.py`
📊 STATISTIKA REZULTATA (Faza 1.1–1.3) — čiste funkcije, bez Streamlita.

1.1 `po_zadatku()` — uspjeh po zadatku (točno/netočno/prazno/%), najgori prvi
1.2 `po_cjelinama()` — uspjeh po cjelinama, najslabija prva
1.3 `zapoceli_nisu_predali()` — pokušaji u tijeku (tko je odustao)

Ulaz: `zadaci` (zamrznuti zadatak: id, tekst, bodovi, cjelina) + `ocjene`
(`Ocjene_zadataka`: pokusaj_id, zadatak_id, tocno, bodovi, max, odgovor).
"""
from __future__ import annotations

import model


def _je_tocno(red: dict) -> bool:
    return model.tekst(red.get("tocno")).lower() in ("da", "true", "točno", "tocno")


def po_zadatku(zadaci: list[dict], ocjene: list[dict]) -> list[dict]:
    """Po zadatku: koliko puta točno / netočno / bez odgovora, postotak uspjeha."""
    po_id: dict[str, list[dict]] = {}
    for r in ocjene or []:
        po_id.setdefault(model.tekst(r.get("zadatak_id")), []).append(r)

    izlaz = []
    for i, z in enumerate(zadaci or [], start=1):
        zid = model.tekst(z.get("id"))
        redci = po_id.get(zid, [])
        tocno = sum(1 for r in redci if _je_tocno(r))
        prazno = sum(1 for r in redci if not model.tekst(r.get("odgovor")))
        ukupno = len(redci)
        netocno = ukupno - tocno - prazno
        izlaz.append({
            "redni": i,
            "zadatak_id": zid,
            "tekst": model.tekst(z.get("tekst"))[:90],
            "cjelina": model.tekst(z.get("cjelina")),
            "bodovi": model.broj(z.get("bodovi"), 1),
            "tocno": tocno,
            "netocno": max(0, netocno),
            "prazno": prazno,
            "ukupno": ukupno,
            "postotak": int(round(100 * tocno / ukupno)) if ukupno else 0,
        })
    izlaz.sort(key=lambda r: (r["postotak"], -r["ukupno"]))
    return izlaz


def po_cjelinama(zadaci: list[dict], ocjene: list[dict]) -> list[dict]:
    """Po cjelini: udio točnih odgovora (najslabija prva)."""
    po_zad = {r["zadatak_id"]: r for r in po_zadatku(zadaci, ocjene)}
    cjeline: dict[str, dict] = {}
    for z in zadaci or []:
        zid = model.tekst(z.get("id"))
        cj = model.tekst(z.get("cjelina")) or "— bez cjeline —"
        stavka = cjeline.setdefault(cj, {"cjelina": cj, "zadataka": 0, "tocno": 0,
                                         "ukupno": 0})
        stavka["zadataka"] += 1
        red = po_zad.get(zid) or {}
        stavka["tocno"] += red.get("tocno", 0)
        stavka["ukupno"] += red.get("ukupno", 0)

    izlaz = []
    for stavka in cjeline.values():
        u = stavka["ukupno"]
        izlaz.append({**stavka, "postotak": int(round(100 * stavka["tocno"] / u)) if u else 0})
    izlaz.sort(key=lambda r: r["postotak"])
    return izlaz


def zapoceli_nisu_predali(pokusaji: list[dict], dodjele: list[dict]) -> list[dict]:
    """Pokušaji koji nisu predani (status nije `predan`)."""
    imena = {model.tekst(d.get("dodjela_id")): model.tekst(d.get("ime_djeteta"))
             or model.tekst(d.get("ucenik_id")) for d in (dodjele or [])}
    izlaz = []
    for p in pokusaji or []:
        if model.je_predan(p):   # 4.11.: prije samo „predan" → predani su bili na popisu
            continue
        izlaz.append({
            "ucenik": imena.get(model.tekst(p.get("dodjela_id")))
                      or model.tekst(p.get("ucenik_id")) or "—",
            "pocetak": model.tekst(p.get("pocetak")),
            "trajanje_s": model.broj(p.get("trajanje_s"), 0),
            "status": model.tekst(p.get("status")) or "u_tijeku",
        })
    return izlaz


def csv(redci: list[dict], kolone: list[str] | None = None) -> str:
    """CSV (točka-zarez) za Excel."""
    if not redci:
        return ""
    kolone = kolone or list(redci[0])
    linije = [";".join(kolone)]
    for r in redci:
        linije.append(";".join(str(r.get(k, "")).replace(";", ",") for k in kolone))
    return "\n".join(linije)
