"""
CAKI testovi v2 — `statistika.py`
📈 STATISTIKA ZADATAKA — **APPEND** upis (Cakijeva odluka 30.10.2026., MASTER §12.11.3).

Zašto append, a ne overwrite: svaki snapshot nosi **vremensku oznaku** (`izracunato`), pa se može
raditi IRT analiza i vidjeti kako se zadatak ponaša kroz generacije. Prepisivanje bi tu povijest
nepovratno izgubilo.

Shema (`tablice.ZAGLAVLJA[TAB_STATISTIKA]`):
    zadatak_id · definicija_id · n · p_vrijednost · diskriminativnost ·
    distraktori_json · prosj_vrijeme_s · izracunato

Ovdje je **upis uz predaju** (jedan redak po zadatku po predaji) — polja koja se mogu izračunati
odmah (n, p, prosječno vrijeme, distraktori) i **izracunato** kao vrijeme zapisa. Diskriminativnost
traži više pokušaja istog testa, pa je ostaje prazna do agregacije (`analitika.diskriminativnost`).
"""
from __future__ import annotations

import json

import analitika
import model
import tablice


def _svi(sheet) -> list[dict]:
    try:
        return tablice.ucitaj(sheet, tablice.TAB_STATISTIKA) or []
    except Exception:                                   # noqa: BLE001
        return []


def _distraktori_json(zadatak: dict, odgovori: list[str]) -> str:
    """Koliko je puta koji ponuđeni odgovor odabran (samo višestruki izbor)."""
    opcije = [model.tekst(o) for o in (zadatak.get("opcije") or []) if model.tekst(o)]
    if not opcije:
        return ""
    brojac = {chr(65 + i): 0 for i in range(len(opcije))}
    for odgovor in odgovori:
        slovo = model.tekst(odgovor).upper()[:1]
        if slovo in brojac:
            brojac[slovo] += 1
    ukupno = sum(brojac.values()) or 1
    return json.dumps({k: round(v / ukupno, 3) for k, v in brojac.items()}, ensure_ascii=False)


def zapisi_predaju(sheet, *, pokusaj_id: str, definicija_id: str,
                   zadaci: list[dict], odgovori: dict, ocjene: list[dict]) -> int:
    """Upiši JEDAN redak po zadatku (append) nakon predaje. Vraća broj zapisanih redaka.

    `ocjene` = retci iz `Ocjene_zadataka` (pokusaj_id, zadatak_id, bodovi, max, vrijeme_s…).
    """
    if not zadaci:
        return 0
    trenutak = model.sada_iso()
    ocjena_po_zadatku = {model.tekst(r.get("zadatak_id")): r for r in (ocjene or [])}

    izlaz = []
    for index, z in enumerate(zadaci):
        zid = model.tekst(z.get("id"))
        if not zid:
            continue
        red = ocjena_po_zadatku.get(zid) or {}
        max_bod = model.broj(red.get("max"), model.broj(z.get("bodovi"), 1)) or 1
        bodovi = model.broj(red.get("bodovi"), 0)

        # p-vrijednost za JEDAN pokušaj je 0 ili 1 (poslije se agregira kroz više pokušaja)
        p = round(min(1.0, max(0.0, bodovi / max_bod)), 4) if max_bod else 0.0
        odgovor = model.tekst((odgovori or {}).get(str(index)) or (odgovori or {}).get(str(index + 1)))

        izlaz.append({
            "zadatak_id": zid,
            "definicija_id": model.tekst(definicija_id),
            "n": 1,
            "p_vrijednost": p,
            "diskriminativnost": "",                    # traži više pokušaja
            "distraktori_json": _distraktori_json(z, [odgovor]),
            "prosj_vrijeme_s": model.broj(red.get("vrijeme_s"), "") if red.get("vrijeme_s") else "",
            "izracunato": trenutak,
        })

    if not izlaz:
        return 0
    tablice.dodaj(sheet, tablice.TAB_STATISTIKA, izlaz)
    return len(izlaz)


def agregat(sheet, zadatak_id: str) -> dict:
    """Zbroj svih snapshotova jednog zadatka (n, prosječni p, raspon vremena)."""
    zid = model.tekst(zadatak_id)
    redci = [r for r in _svi(sheet) if model.tekst(r.get("zadatak_id")) == zid]
    if not redci:
        return {}
    n = sum(model.broj(r.get("n"), 0) for r in redci) or 0
    p_parts = [(model.broj(r.get("p_vrijednost"), 0), model.broj(r.get("n"), 1) or 1)
               for r in redci if model.tekst(r.get("p_vrijednost")) != ""]
    p = sum(v * w for v, w in p_parts) / sum(w for _, w in p_parts) if p_parts else 0.0
    return {"zadatak_id": zid, "n": n, "p_vrijednost": round(p, 4), "snapshotova": len(redci)}


def zadnji_snapshot(sheet, zadatak_id: str) -> dict:
    """Najnoviji zapis za zadatak (append-only: zadnji po `izracunato`)."""
    zid = model.tekst(zadatak_id)
    redci = sorted([r for r in _svi(sheet) if model.tekst(r.get("zadatak_id")) == zid],
                   key=lambda r: model.tekst(r.get("izracunato")))
    return redci[-1] if redci else {}


def diskriminativnost_iz_pokusaja(pokusaji: list[dict]) -> float:
    """Pomoćno: point-biserial preko `analitika` (kad se skupi više pokušaja istog testa)."""
    try:
        return round(float(analitika.diskriminativnost(pokusaji)), 4)
    except Exception:                                   # noqa: BLE001
        return 0.0
