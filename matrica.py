"""
CAKI testovi v2 — `matrica.py`
📋 MATRICA ODGOVORA (učenik × zadatak) — preuzeto iz v1 (`testovi_admin.matrica_ucenika`, L741),
uz Cakijev zahtjev 01.11.2026.: **zelena kvočica za točno, crveni križić za netočno, siva za prazno**
(v1 je davao samo znakove bez boje).

Koristi `Ocjene_zadataka` (pokusaj_id, zadatak_id, odgovor, tocno, bodovi, max).
"""
from __future__ import annotations

import model

ZNACKA_TOCNO = "✓"
ZNACKA_NETOCNO = "✗"
ZNACKA_PRAZNO = "—"


def _ocjene_po_pokusaju(ocjene: list[dict]) -> dict[str, dict[str, dict]]:
    izlaz: dict[str, dict[str, dict]] = {}
    for r in ocjene or []:
        pid = model.tekst(r.get("pokusaj_id"))
        zid = model.tekst(r.get("zadatak_id"))
        if pid and zid:
            izlaz.setdefault(pid, {})[zid] = r
    return izlaz


def redci(zadaci: list[dict], dodjele_: list[dict], pokusaji: list[dict],
          ocjene: list[dict]) -> list[dict]:
    """Red = učenik, stupac = zadatak. Vrijednosti: `✓` / `✗` / `—` (prazno)."""
    zadaci = zadaci or []
    po_pokusaju = _ocjene_po_pokusaju(ocjene)
    pokusaj_po_dodjeli = {model.tekst(p.get("dodjela_id")): p for p in (pokusaji or [])}

    izlaz = []
    for d in sorted(dodjele_ or [], key=lambda x: (model.tekst(x.get("ime_djeteta")),
                                                   model.tekst(x.get("ucenik_id")))):
        p = pokusaj_po_dodjeli.get(model.tekst(d.get("dodjela_id"))) or {}
        pid = model.tekst(p.get("pokusaj_id"))
        ocjene_p = po_pokusaju.get(pid, {})

        red = {
            "ucenik": (model.tekst(d.get("ime_djeteta"))
                       or model.tekst(d.get("ucenik_id")) or "—"),
            "sifra": model.tekst(d.get("ucenik_id")).upper(),
            "predao": bool(pid),
            "stanja": [],
        }
        for z in zadaci:
            zid = model.tekst(z.get("id"))
            o = ocjene_p.get(zid) or {}
            if model.tekst(o.get("tocno")).lower() in ("da", "true", "točno", "tocno"):
                red["stanja"].append("tocno")
            elif not model.tekst(o.get("odgovor")):
                red["stanja"].append("prazno")
            else:
                red["stanja"].append("netocno")

        maks = sum(model.broj(z.get("bodovi"), 1) for z in zadaci) or 0
        bodovi = sum(model.broj(o.get("bodovi"), 0) for o in ocjene_p.values())
        red["bodovi"] = bodovi
        red["maks"] = maks
        red["postotak"] = int(round(100 * bodovi / maks)) if maks else 0
        izlaz.append(red)
    return izlaz


def html(redci_: list[dict], zadaci: list[dict], *, imena_zadataka: bool = False) -> str:
    """HTML tablica s bojama: zelena ✓, crvena ✗, siva —."""
    if not redci_:
        return ""
    boje = {"tocno": ("#1a7f37", ZNACKA_TOCNO),
            "netocno": ("#c62828", ZNACKA_NETOCNO),
            "prazno": ("#9e9e9e", ZNACKA_PRAZNO)}
    zag = "".join(f"<th style='padding:3px 7px;border:1px solid #ccc;background:#f3ede4;'>"
                  f"{'Z' + str(i + 1)}</th>" for i in range(len(zadaci or [])))
    dijelovi = [
        "<table style='border-collapse:collapse;font-size:0.92em;'>",
        "<tr><th style='padding:3px 7px;border:1px solid #ccc;background:#f3ede4;'>Učenik</th>"
        "<th style='padding:3px 7px;border:1px solid #ccc;background:#f3ede4;'>Šifra</th>"
        + zag +
        "<th style='padding:3px 7px;border:1px solid #ccc;background:#f3ede4;'>Bodovi</th>"
        "<th style='padding:3px 7px;border:1px solid #ccc;background:#f3ede4;'>%</th></tr>",
    ]
    for r in redci_:
        celije = []
        for stanje in r.get("stanja") or []:
            boja, znak = boje.get(stanje, ("#9e9e9e", ZNACKA_PRAZNO))
            celije.append(f"<td style='padding:3px 7px;border:1px solid #ccc;text-align:center;"
                          f"color:{boja};font-weight:700;'>{znak}</td>")
        dijelovi.append(
            "<tr>"
            f"<td style='padding:3px 7px;border:1px solid #ccc;'>{r.get('ucenik')}</td>"
            f"<td style='padding:3px 7px;border:1px solid #ccc;'>{r.get('sifra')}</td>"
            + "".join(celije) +
            f"<td style='padding:3px 7px;border:1px solid #ccc;text-align:right;'>"
            f"{r.get('bodovi'):g}/{r.get('maks'):g}</td>"
            f"<td style='padding:3px 7px;border:1px solid #ccc;text-align:right;'>"
            f"{r.get('postotak')} %</td></tr>")
    dijelovi.append("</table>")
    return "".join(dijelovi)


def csv(redci_: list[dict]) -> str:
    """CSV (točka-zarez) za Excel — znakovi bez boje."""
    if not redci_:
        return ""
    zag = ["Ucenik", "Sifra"] + [f"Z{i + 1}" for i in range(len(redci_[0].get("stanja") or []))]
    zag += ["Bodovi", "Max", "Postotak"]
    linije = [";".join(zag)]
    for r in redci_:
        znakovi = [{"tocno": ZNACKA_TOCNO, "netocno": ZNACKA_NETOCNO}.get(s, "") for s in
                   (r.get("stanja") or [])]
        linije.append(";".join([str(r.get("ucenik")), str(r.get("sifra"))] + znakovi
                               + [str(r.get("bodovi")), str(r.get("maks")),
                                  str(r.get("postotak"))]))
    return "\n".join(linije)
