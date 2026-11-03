"""
CAKI testovi v2 — `distraktori.py`  (PLAN 15 — koji pogrešni odgovori se najviše biraju)

Za svaki zadatak s ponuđenim odgovorima (A–E) broji koliko je puta razred odabrao koji
**pogrešni** odgovor. To pokazuje je li ponuda „mamac" dobra: ako većina pogrešnih ide na
jedan odgovor, vjerojatno je zadatak nejasan ili je taj odgovor logična zamka.

Ulaz: `zadaci` (zamrznuti: `id`, `tekst`, `opcije`, `odgovor`) i `ocjene`
(`Ocjene_zadataka`: `zadatak_id`, `odgovor`, `tocno`).
"""
from __future__ import annotations

import model


def _je_tocno(red: dict) -> bool:
    return model.tekst(red.get("tocno")).lower() in ("da", "true", "točno", "tocno")


def _slovo(odgovor: str) -> str:
    """Prvo slovo odgovora (A, B, C…), veliko; prazno ako nema."""
    o = model.tekst(odgovor).strip().upper()
    return o[:1] if o else ""


def po_zadatku(zadaci, ocjene, *, top: int = 3) -> list[dict]:
    """Po zadatku: točan odgovor + najčešći pogrešni (do `top`), samo za zadatke s opcijama."""
    po_id: dict[str, list[dict]] = {}
    for r in ocjene or []:
        po_id.setdefault(model.tekst(r.get("zadatak_id")), []).append(r)

    izlaz = []
    for i, z in enumerate(zadaci or [], start=1):
        opcije = z.get("opcije") or []
        if not opcije:
            continue                                    # samo zadaci s ponuđenim odgovorima
        zid = model.tekst(z.get("id"))
        tocno_slovo = _slovo(z.get("odgovor"))
        redci = po_id.get(zid, [])
        greske: dict[str, int] = {}
        bez_odgovora = 0
        for r in redci:
            if _je_tocno(r):
                continue
            slovo = _slovo(r.get("odgovor"))
            if not slovo:
                bez_odgovora += 1
                continue
            if slovo == tocno_slovo:
                continue
            greske[slovo] = greske.get(slovo, 0) + 1

        poredano = sorted(greske.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
        pogresnih = sum(greske.values())
        izlaz.append({
            "redni": i,
            "zadatak_id": zid,
            "tekst": model.tekst(z.get("tekst"))[:70],
            "tocno": tocno_slovo,
            "pogresnih": pogresnih,
            "bez_odgovora": bez_odgovora,
            "najcesci": ", ".join(f"{s} ({n}×)" for s, n in poredano) or "—",
            "udio_jednog": (int(round(100 * poredano[0][1] / pogresnih))
                            if poredano and pogresnih else 0),
            "_poredano": poredano,
        })
    izlaz.sort(key=lambda r: (-r["pogresnih"], r["redni"]))
    return izlaz


def sazetak(redci: list[dict]) -> dict:
    """Koliko zadataka ima „jak mamac" (jedan pogrešni odgovor ≥ 50 % pogrešnih)."""
    if not redci:
        return {"zadataka": 0, "jak_mamac": 0, "najgori": None}
    jaki = [r for r in redci if r["pogresnih"] >= 3 and r["udio_jednog"] >= 50]
    return {
        "zadataka": len(redci),
        "jak_mamac": len(jaki),
        "najgori": redci[0] if redci else None,
    }
