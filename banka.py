"""
CAKI testovi v2 — `banka.py`
ČITANJE POSTOJEĆE BAZE ZADATAKA (20.000+ zadataka) — **samo čitanje**, baza se ne dira.

Baza ostaje tamo gdje je (`Zadaci` u `caki-baza-zadataka`), a novi sustav iz nje uzima zadatke i
**zamrzava ih u test**. Time izmjena u bazi nikad ne mijenja test koji je već objavljen.

Novo u v2 (Cakijev zahtjev 24.10.): **🎬 video uz rješenje** (`video_url`, `video_naslov`) — prikazuje
se učeniku **nakon testa**, nikad tijekom rješavanja.
"""
from __future__ import annotations

import model
import tablice

TAB_ZADACI = "Zadaci"
STUPAC_VIDEO = "video_url"
STUPAC_VIDEO_NASLOV = "video_naslov"


# ------------------------------------------------------------------ video (samo čitanje!)

def stupci_videa(sheet) -> dict:
    """Postoji li `video_url` u bazi? **Ne dodaje ništa** — živa baza se ne mijenja.

    Cakijeva napomena 25.10.2026.: video rješenja su **već planirana u bazi** (stupac `video_url`
    postoji u shemi), samo još nisu snimljena. Zato novi sustav taj stupac samo čita.
    """
    try:
        ws = sheet.worksheet(TAB_ZADACI)
    except Exception:                                   # noqa: BLE001
        return {"postoji": False, "stupac": STUPAC_VIDEO, "stupac_naslov": ""}
    zaglavlje = [model.tekst(h) for h in (ws.row_values(1) or [])]
    return {
        "postoji": STUPAC_VIDEO in zaglavlje,
        "stupac": STUPAC_VIDEO,
        "stupac_naslov": STUPAC_VIDEO_NASLOV if STUPAC_VIDEO_NASLOV in zaglavlje else "",
        "stupaca": len(zaglavlje),
    }


# ------------------------------------------------------------------ čitanje

def ucitaj(sheet) -> list[dict]:
    """Svi zadaci iz baze (retci taba `Zadaci`)."""
    return tablice.ucitaj(sheet, TAB_ZADACI)


def _opcije(retak: dict) -> list[str]:
    """Ponuđeni odgovori: JSON lista, tekst s prijelomima ili „A) …; B) …"."""
    sirovo = retak.get("ponudjeni_odgovori")
    if isinstance(sirovo, list):
        return [model.tekst(o) for o in sirovo if model.tekst(o)]
    tekst = model.tekst(sirovo)
    if not tekst:
        return []
    kao_json = model.kao_json(tekst)
    if kao_json:
        return [model.tekst(o) for o in kao_json if model.tekst(o)]
    dijelovi = [d.strip() for d in tekst.replace(";", "\n").split("\n") if d.strip()]
    ocisceno = []
    for d in dijelovi:
        d = model.tekst(d)
        if len(d) > 1 and d[0].upper() in "ABCDEFGHIJ" and d[1] in ")]:-":
            d = d[2:].strip()
        ocisceno.append(d)
    return [d for d in ocisceno if d]


def zadatak_iz_retka(retak: dict) -> dict | None:
    """Bazin redak → zamrznuti zadatak za test. None ako zadatak nije upotrebljiv."""
    r = retak or {}
    zid = model.tekst(r.get("id"))
    tekst = model.tekst(r.get("tekst_zadatka_latex")) or model.tekst(r.get("tekst"))
    if not zid or not tekst:
        return None
    odgovor = model.tekst(r.get("konacan_odgovor"))
    opcije = _opcije(r)
    visestruki = (model.tekst(r.get("tip_zadatka")) == "visestruki_izbor" and len(opcije) >= 2)
    return {
        "id": zid,
        "tekst": tekst,
        "tip": "visestruki_izbor" if visestruki else "kratki_odgovor",
        "opcije": opcije if visestruki else [],
        "odgovor": odgovor,
        "bodovi": model.broj(r.get("bodovi"), 1) or 1,
        "slika": model.tekst(r.get("slika_putanja")) or model.tekst(r.get("slika")),
        "video_url": model.tekst(r.get(STUPAC_VIDEO)),
        "video_naslov": model.tekst(r.get(STUPAC_VIDEO_NASLOV)),
        "cjelina": model.tekst(r.get("cjelina")),
        "potpoglavlje": model.tekst(r.get("potpoglavlje")),
        "tezina": model.tekst(r.get("tezina")),
        "bloom": model.tekst(r.get("bloom")),
        "izvor": model.tekst(r.get("izvor_naziv")),
        "razred": model.tekst(r.get("razred")),
    }


def svi_zadaci(sheet) -> list[dict]:
    """Svi upotrebljivi zadaci, normalizirani (preskače skupine i prazne)."""
    izlaz = []
    for r in ucitaj(sheet):
        if model.tekst(r.get("uloga")).lower() == "skupina":
            continue
        z = zadatak_iz_retka(r)
        if z:
            izlaz.append(z)
    return izlaz


def po_id(zadaci: list[dict]) -> dict[str, dict]:
    return {model.tekst(z.get("id")): z for z in zadaci or [] if model.tekst(z.get("id"))}


# ------------------------------------------------------------------ pretraga

def filtriraj(zadaci: list[dict], *, tekst: str = "", cjelina: str = "", potpoglavlje: str = "",
              tezina: str = "", tip: str = "", bloom: str = "", ima_video=None,
              ima_sliku=None) -> list[dict]:
    """Filtriranje baze za slaganje testa. Prazan filtar ne ograničava."""
    t = model.tekst(tekst).lower()
    izlaz = []
    for z in zadaci or []:
        if t and t not in (model.tekst(z.get("tekst")) + " " + model.tekst(z.get("id"))).lower():
            continue
        if cjelina and model.tekst(z.get("cjelina")) != cjelina:
            continue
        if potpoglavlje and model.tekst(z.get("potpoglavlje")) != potpoglavlje:
            continue
        if tezina and model.tekst(z.get("tezina")) != tezina:
            continue
        if tip and model.tekst(z.get("tip")) != tip:
            continue
        if bloom and model.tekst(z.get("bloom")) != bloom:
            continue
        if ima_video is True and not model.tekst(z.get("video_url")):
            continue
        if ima_video is False and model.tekst(z.get("video_url")):
            continue
        if ima_sliku is True and not model.tekst(z.get("slika")):
            continue
        izlaz.append(z)
    return izlaz


def vrijednosti(zadaci: list[dict], polje: str) -> list[str]:
    """Jedinstvene vrijednosti polja (za padajuće izbornike), sortirane."""
    return sorted({model.tekst((z or {}).get(polje)) for z in zadaci or [] if model.tekst((z or {}).get(polje))})


def brojevi(zadaci: list[dict]) -> dict:
    """Sazetak baze po cjelinama/težinama — za „ima li dovoljno zadataka" prije slaganja."""
    po_cjelini, po_tezini = {}, {}
    for z in zadaci or []:
        cj = model.tekst(z.get("cjelina")) or "— bez cjeline —"
        te = model.tekst(z.get("tezina")) or "— bez težine —"
        po_cjelini[cj] = po_cjelini.get(cj, 0) + 1
        po_tezini[te] = po_tezini.get(te, 0) + 1
    return {"ukupno": len(zadaci or []), "po_cjelini": po_cjelini, "po_tezini": po_tezini,
            "sa_videom": sum(1 for z in zadaci or [] if model.tekst(z.get("video_url")))}


# ------------------------------------------------------------------ video

def video_za(zadatak: dict) -> dict | None:
    """🎬 Video uz zadatak (za prikaz NAKON testa). None ako ga nema."""
    url = model.tekst((zadatak or {}).get("video_url"))
    if not url:
        return None
    return {"url": url, "naslov": model.tekst((zadatak or {}).get("video_naslov")) or "Objašnjenje zadatka"}


def postavi_video(sheet, zadatak_id: str, url: str, naslov: str = "") -> tuple[bool, str]:
    """Upiše video u **postojeći** stupac `video_url`. Nikad ne dodaje stupac u živu bazu.

    Vraća (uspjelo, poruka). Ako stupca nema — Caki ga treba dodati ručno u Sheetu.
    """
    info = stupci_videa(sheet)
    if not info["postoji"]:
        return False, (f"U bazi nema stupca `{STUPAC_VIDEO}`. Dodaj ga ručno u tab `Zadaci` "
                       "(novi zadnji stupac) — sustav ga ne dodaje sam u živu bazu.")
    ws = sheet.worksheet(TAB_ZADACI)
    zaglavlje = [model.tekst(h) for h in (ws.row_values(1) or [])]
    if "id" not in zaglavlje:
        return False, "Baza nema stupac `id`."
    i_id = zaglavlje.index("id")
    for br, red in enumerate(ws.get_all_values()[1:], start=2):
        if i_id < len(red) and model.tekst(red[i_id]) == model.tekst(zadatak_id):
            ws.update_cell(br, zaglavlje.index(STUPAC_VIDEO) + 1, model.tekst(url))
            if naslov and info["stupac_naslov"]:
                ws.update_cell(br, zaglavlje.index(STUPAC_VIDEO_NASLOV) + 1, model.tekst(naslov))
            return True, "Snimljeno."
    return False, "Zadatak nije nađen u bazi."
    i_id = zaglavlje.index("id")
    for br, red in enumerate(ws.get_all_values()[1:], start=2):
        if i_id < len(red) and model.tekst(red[i_id]) == model.tekst(zadatak_id):
            ws.update_cell(br, zaglavlje.index(STUPAC_VIDEO) + 1, model.tekst(url))
            if STUPAC_VIDEO_NASLOV in zaglavlje:
                ws.update_cell(br, zaglavlje.index(STUPAC_VIDEO_NASLOV) + 1, model.tekst(naslov))
            return True
    return False
