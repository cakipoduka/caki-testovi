"""
CAKI testovi v2 — `repriza.py`  („isti test ponovno, za one koji ga nisu pisali")

Caki (5.11.2026.): „Možeš li pročitati koji su zadaci u Inicijalno testiranje - MATURA A razina
bili i da isti takav test formiramo u v2 i objavimo učenicima koji ga do sada nisu riješili."

Kako radi (bez prepisivanja i bez ručnog kopiranja):
  · uvezeni test (`T26-0007`) je **arhiviran** i ima zamrznute zadatke u `zadaci_json`,
  · `kloniraj_kao_novi()` napravi NOVU definiciju s ISTIM zadacima (status `nacrt`),
  · `nisu_predali()` vrati učenike koji za taj test nemaju predan pokušaj,
  · `objavi_odabranima()` napravi dodjele za upravo te učenike.

Ništa se ne prepisuje u v1; arhivirani test ostaje kakav jest.
"""
from __future__ import annotations

import json

import model
import tablice


def zadaci_iz_definicije(definicija: dict) -> list[dict]:
    """Zadaci iz `zadaci_json` (lista dictova); prazno ako nema."""
    try:
        zadaci = json.loads(model.tekst((definicija or {}).get("zadaci_json")) or "[]")
    except Exception:                                   # noqa: BLE001
        return []
    return [z for z in zadaci if isinstance(z, dict)]


def kloniraj_kao_novi(sheet, definicija_id: str, *, naziv: str = "",
                      status: str = "nacrt", autor: str = "caki") -> dict:
    """Nova definicija s ISTIM zadacima. Vraća {"definicija_id", "broj_zadataka", "greska"}."""
    izlaz = {"definicija_id": "", "broj_zadataka": 0, "greska": ""}
    did = model.tekst(definicija_id)
    if not did:
        izlaz["greska"] = "Nedostaje definicija_id."
        return izlaz

    stara = None
    for d in tablice.ucitaj(sheet, tablice.TAB_DEFINICIJE):
        if model.tekst(d.get("definicija_id")) == did:
            stara = d
            break
    if not stara:
        izlaz["greska"] = f"Test `{did}` ne postoji."
        return izlaz

    zadaci = zadaci_iz_definicije(stara)
    if not zadaci:
        izlaz["greska"] = "Test nema zapisane zadatke (`zadaci_json` je prazan)."
        return izlaz

    import definicije                                  # izbjegavamo krug pri importu

    novi_id = tablice.novi_id([model.tekst(x.get("definicija_id"))
                               for x in tablice.ucitaj(sheet, tablice.TAB_DEFINICIJE)],
                              "T26-")
    naziv_novi = model.tekst(naziv) or (model.tekst(stara.get("naziv")) + " — ponovno")
    zapis = definicije.nova_definicija(
        definicija_id=novi_id,
        naziv=naziv_novi,
        predmet=model.tekst(stara.get("predmet")) or "Matematika",
        zadaci_=zadaci,
        trajanje_min=model.broj(stara.get("trajanje_min"), 45) or 45,
        vrsta=model.tekst(stara.get("vrsta")) or "ocjena",
        status=model.tekst(status) or "nacrt",
        rok_od=model.tekst(stara.get("rok_od")),
        rok_do=model.tekst(stara.get("rok_do")),
        autor=autor,
        napomena=f"kopija testa {did}",
        ai_pomoc=model.tekst(stara.get("ai_pomoc")) or "ne",
    )
    tablice.dodaj(sheet, tablice.TAB_DEFINICIJE, [zapis])
    izlaz["definicija_id"] = novi_id
    izlaz["broj_zadataka"] = len(zadaci)
    return izlaz


def nisu_predali(sheet, definicija_id: str) -> list[dict]:
    """Učenici koji za TAJ test nemaju predan pokušaj (a imaju dodjelu ili su u bazi).

    Vraća [{ucenik_id, ime_djeteta}].
    """
    did = model.tekst(definicija_id)
    dodjele = [d for d in tablice.ucitaj(sheet, tablice.TAB_DODJELE)
               if model.tekst(d.get("definicija_id")) == did]
    pokusaji = {model.tekst(p.get("dodjela_id")): p
                for p in tablice.ucitaj(sheet, tablice.TAB_POKUSAJI)
                if model.tekst(p.get("definicija_id")) == did}

    izlaz = []
    for d in dodjele:
        p = pokusaji.get(model.tekst(d.get("dodjela_id")))
        if p and model.tekst(p.get("status")).lower() == "predan":
            continue
        izlaz.append({"ucenik_id": model.tekst(d.get("ucenik_id")).upper(),
                      "ime_djeteta": model.tekst(d.get("ime_djeteta"))})
    izlaz.sort(key=lambda r: r["ime_djeteta"] or r["ucenik_id"])
    return izlaz


def objavi_odabranima(sheet, nova_definicija_id: str, ucenici_ids, *,
                      rok_od: str = "", rok_do: str = "", dodijelio: str = "caki") -> dict:
    """Napravi dodjele za zadane šifre (bez duplikata). Vraća {"napravljeno", "preskoceno"}."""
    did = model.tekst(nova_definicija_id)
    if not did:
        return {"napravljeno": 0, "preskoceno": 0}

    postojece = {model.tekst(d.get("ucenik_id")).upper()
                 for d in tablice.ucitaj(sheet, tablice.TAB_DODJELE)
                 if model.tekst(d.get("definicija_id")) == did}
    idovi = tablice.svi_idovi(sheet, tablice.TAB_DODJELE, "dodjela_id")

    novi, preskoceno = [], 0
    for uid in ucenici_ids or []:
        u = model.tekst(uid).upper()
        if not u or u in postojece:
            preskoceno += 1
            continue
        novi.append({
            "dodjela_id": tablice.novi_id(idovi, "D26-"),
            "definicija_id": did,
            "ucenik_id": u,
            "ime_djeteta": "",
            "grupa": "",
            "rok_od": rok_od,
            "rok_do": rok_do,
            "varijanta_seed": u,
            "status": "dodijeljeno",
            "dodijelio": dodijelio,
            "dodijeljeno": model.sada_iso(),
        })
        idovi.append(novi[-1]["dodjela_id"])
        postojece.add(u)

    if novi:
        tablice.dodaj(sheet, tablice.TAB_DODJELE, novi)
    return {"napravljeno": len(novi), "preskoceno": preskoceno}
