"""
CAKI testovi v2 — `provedba.py`
POKUŠAJ RJEŠAVANJA: početak → autosave → predaja.

Zašto pokušaj, a ne samo rezultat: bez pokušaja nema autosavea (Cakijev zahtjev: prekid ne smije
izgubiti odgovore), nema vremena po zadatku (za mjerenje) i nema ponovnog rješavanja.

Vrijeme se **uvijek** mjeri na poslužitelju (`pocetak` u tablici), nikad u pregledniku.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import definicije
import dodjele
import model
import ocjenjivanje
import tablice

STATUS_U_TIJEKU = "u_tijeku"
STATUS_PREDANO = "predano"
STATUS_PO_ISTEKU = "po_isteku"
STATUSI = (STATUS_U_TIJEKU, STATUS_PREDANO, STATUS_PO_ISTEKU)

GRACE_S = 60                    # tolerancija pri predaji odmah nakon roka


# ------------------------------------------------------------------ čitanje

def pokusaji_ucenika(sheet, dodjela_id: str) -> list[dict]:
    did = model.tekst(dodjela_id)
    return [p for p in tablice.ucitaj(sheet, tablice.TAB_POKUSAJI)
            if model.tekst(p.get("dodjela_id")) == did]


def pokusaj_po_id(sheet, pokusaj_id: str) -> dict | None:
    for p in tablice.ucitaj(sheet, tablice.TAB_POKUSAJI):
        if model.tekst(p.get("pokusaj_id")) == model.tekst(pokusaj_id):
            return p
    return None


def aktivni(sheet, dodjela_id: str) -> dict | None:
    """Pokušaj koji je u tijeku (za nastavak nakon F5/prekida)."""
    for p in pokusaji_ucenika(sheet, dodjela_id):
        if model.tekst(p.get("status")) == STATUS_U_TIJEKU:
            return p
    return None


def zadnji_predani(sheet, dodjela_id: str) -> dict | None:
    for p in pokusaji_ucenika(sheet, dodjela_id):
        if model.tekst(p.get("status")) in (STATUS_PREDANO, STATUS_PO_ISTEKU):
            return p
    return None


def predano(sheet, dodjela_id: str) -> bool:
    return zadnji_predani(sheet, dodjela_id) is not None


# ------------------------------------------------------------------ rok i vrijeme

def smije_poceti(dodjela: dict, definicija: dict, danas=None) -> tuple[bool, str]:
    """Smije li učenik otvoriti test sada. Vraća (smije, razlog ako ne smije)."""
    stanje = dodjele.stanje_roka(dodjela, definicija, danas)
    if stanje == "nije_poceo":
        r = dodjele.rok_dodjele(dodjela, definicija, danas)
        return False, f"Test se otvara {r['od_iso']}."
    if stanje == "zatvoren":
        r = dodjele.rok_dodjele(dodjela, definicija, danas)
        return False, f"Rok je prošao ({r['do_iso']})."
    return True, ""


def _kao_vrijeme(v) -> datetime | None:
    s = model.tekst(v)
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s[:19], fmt)
        except ValueError:
            continue
    return None


def vrijeme_isteka(pokusaj: dict, definicija: dict) -> datetime | None:
    pocetak = _kao_vrijeme((pokusaj or {}).get("pocetak"))
    if not pocetak:
        return None
    return pocetak + timedelta(minutes=model.cijeli((definicija or {}).get("trajanje_min"), 45))


def preostalo_s(pokusaj: dict, definicija: dict, sada=None) -> int:
    """Preostale sekunde (može biti negativno — tada je istekao)."""
    rok = vrijeme_isteka(pokusaj, definicija)
    if not rok:
        return 0
    return int((rok - (sada or model.sada())).total_seconds())


def je_istekao(pokusaj: dict, definicija: dict, sada=None) -> bool:
    return preostalo_s(pokusaj, definicija, sada) <= 0


# ------------------------------------------------------------------ početak

def zapocni(sheet, dodjela: dict, definicija: dict, *, sada=None) -> dict:
    """Otvori pokušaj (ili vrati postojeći u tijeku). **Ne dopušta** drugi pokušaj nakon predaje."""
    sada = sada or model.sada()
    did = model.tekst((dodjela or {}).get("dodjela_id"))
    if not did:
        raise ValueError("Dodjela nema ID.")
    if predano(sheet, did):
        raise ValueError("Test je već predan.")

    postoji = aktivni(sheet, did)
    if postoji:
        return postoji

    smije, razlog = smije_poceti(dodjela, definicija, sada.date())
    if not smije:
        raise ValueError(razlog)

    svi = tablice.svi_idovi(sheet, tablice.TAB_POKUSAJI, "pokusaj_id")
    pokusaj_id = tablice.novi_id(svi, "P26-")
    redak = {
        "pokusaj_id": pokusaj_id,
        "dodjela_id": did,
        "definicija_id": model.tekst((dodjela or {}).get("definicija_id")),
        "ucenik_id": model.tekst((dodjela or {}).get("ucenik_id")),
        "pocetak": sada.strftime("%Y-%m-%d %H:%M:%S"),
        "zadnja_aktivnost": sada.strftime("%Y-%m-%d %H:%M:%S"),
        "predaja": "",
        "trajanje_s": 0,
        "odgovori_json": model.u_json({}),
        "bodovi": 0,
        "bodovi_max": model.broj((definicija or {}).get("bodovi_ukupno")),
        "status": STATUS_U_TIJEKU,
        "predano_po_roku": "",
    }
    tablice.dodaj(sheet, tablice.TAB_POKUSAJI, [redak])
    tablice.azuriraj(sheet, tablice.TAB_DODJELE, "dodjela_id", did, {"status": "u_tijeku"})
    return redak


# ------------------------------------------------------------------ autosave

def odgovori(pokusaj: dict) -> dict:
    """Odgovori iz pokušaja kao {redni_broj(str): odgovor}.

    Sprema se kao JSON **objekt** (`{"0": "2"}`), a stariji zapisi mogli su biti lista — zato oba.
    """
    izlaz = model.kao_dict((pokusaj or {}).get("odgovori_json"))
    if izlaz:
        return {k: v for k, v in izlaz.items() if model.tekst(v)}
    lista = model.kao_json((pokusaj or {}).get("odgovori_json"))
    for i, v in enumerate(lista or []):
        if model.tekst(v):
            izlaz[str(i)] = v
    return izlaz


def _svjez(sheet, pokusaj: dict) -> dict:
    """Stanje pokušaja iz Sheeta — dict u sesiji može biti zastario (dva taba, dvostruki klik)."""
    pid = model.tekst((pokusaj or {}).get("pokusaj_id"))
    return pokusaj_po_id(sheet, pid) or (pokusaj or {})


def spremi(sheet, pokusaj: dict, novi_odgovori: dict, *, sada=None) -> bool:
    """Autosave: jedan upis po pozivu (Sheets kvota). Ne dira ništa ako je pokušaj predan."""
    if model.tekst(_svjez(sheet, pokusaj).get("status")) != STATUS_U_TIJEKU:
        return False
    sada = sada or model.sada()
    spojeni = odgovori(pokusaj)
    for k, v in (novi_odgovori or {}).items():
        kljuc = model.tekst(k)
        if kljuc:
            spojeni[kljuc] = v
    ok = tablice.azuriraj(sheet, tablice.TAB_POKUSAJI, "pokusaj_id",
                          model.tekst(pokusaj.get("pokusaj_id")),
                          {"odgovori_json": model.u_json(spojeni),
                           "zadnja_aktivnost": sada.strftime("%Y-%m-%d %H:%M:%S")})
    if ok:
        pokusaj["odgovori_json"] = model.u_json(spojeni)
    return ok


# ------------------------------------------------------------------ predaja

def zadaci_za_pokusaj(definicija: dict, dodjela: dict) -> list[dict]:
    """Zadaci u redoslijedu koji učenik vidje (A/B miješanje po seedu dodjele)."""
    sirovi = definicije.zadaci(definicija)
    try:
        pravilo = model.kao_json((definicija or {}).get("varijanta_pravilo"))
    except Exception:                                  # noqa: BLE001
        pravilo = []
    postavke = pravilo if isinstance(pravilo, dict) else {}
    mijesaj_z = postavke.get("mijesaj_zadatke", True)
    mijesaj_o = postavke.get("mijesaj_odgovore", True)
    if not mijesaj_z and not mijesaj_o:
        return sirovi
    seed = model.tekst((dodjela or {}).get("varijanta_seed")) or model.tekst((dodjela or {}).get("ucenik_id"))
    if not mijesaj_z:                                  # samo odgovori — redoslijed zadataka ostaje
        return definicije.izmijesaj_odgovore(sirovi, seed) if mijesaj_o else sirovi
    return definicije.izmijesaj(sirovi, seed, mijesaj_odgovore=mijesaj_o)


def predaj(sheet, pokusaj: dict, definicija: dict, *, odgovori_=None, sada=None, pozovi=None,
           dopusti_ai: bool = True) -> dict:
    """Ocijeni i zaključi pokušaj. Vraća {"bodovi", "maks", "status", "ceka_profesora", "detalji"}."""
    sada = sada or model.sada()
    if model.tekst(_svjez(sheet, pokusaj).get("status")) != STATUS_U_TIJEKU:
        raise ValueError("Ovaj pokušaj je već zaključen.")

    if odgovori_ is not None:
        spremi(sheet, pokusaj, odgovori_, sada=sada)

    dodjela = next((d for d in tablice.ucitaj(sheet, tablice.TAB_DODJELE)
                    if model.tekst(d.get("dodjela_id")) == model.tekst(pokusaj.get("dodjela_id"))), {})
    zadaci = zadaci_za_pokusaj(definicija, dodjela)
    odg = odgovori(pokusaj)
    ocjena = ocjenjivanje.ocjeni_zadatke(
        zadaci, {model.cijeli(k, -1): v for k, v in odg.items()}, pozovi=pozovi, dopusti_ai=dopusti_ai)

    pocetak = _kao_vrijeme(pokusaj.get("pocetak")) or sada
    po_roku = je_istekao(pokusaj, definicija, sada)
    status = STATUS_PO_ISTEKU if po_roku else STATUS_PREDANO

    tablice.azuriraj(sheet, tablice.TAB_POKUSAJI, "pokusaj_id", model.tekst(pokusaj.get("pokusaj_id")), {
        "predaja": sada.strftime("%Y-%m-%d %H:%M:%S"),
        "trajanje_s": max(0, int((sada - pocetak).total_seconds())),
        "bodovi": ocjena["bodovi"],
        "bodovi_max": ocjena["maks"],
        "status": status,
        "predano_po_roku": "Da" if po_roku else "Ne",
    })
    tablice.azuriraj(sheet, tablice.TAB_DODJELE, "dodjela_id", model.tekst(pokusaj.get("dodjela_id")),
                     {"status": "predano"})

    _upisi_ocjene(sheet, pokusaj, ocjena)
    return {"bodovi": ocjena["bodovi"], "maks": ocjena["maks"], "status": status,
            "ceka_profesora": ocjena["ceka_profesora"], "detalji": ocjena["detalji"],
            "postotak": ocjenjivanje.postotak(ocjena["bodovi"], ocjena["maks"])}


def _upisi_ocjene(sheet, pokusaj: dict, ocjena: dict) -> int:
    """Jedan redak po zadatku — osnova za mjerenje kvalitete zadatka (p, r, distraktori)."""
    redci = []
    for d in ocjena.get("detalji") or []:
        redci.append({
            "pokusaj_id": model.tekst(pokusaj.get("pokusaj_id")),
            "zadatak_id": model.tekst(d.get("zadatak_id")),
            "redni_broj": d.get("redni_broj"),
            "odgovor": model.tekst(d.get("odgovor")),
            "tocno": "Da" if d.get("tocno") else "Ne",
            "bodovi": d.get("bodovi"),
            "max": d.get("max"),
            "izvor_ocjene": model.tekst(d.get("izvor")),
            "vrijeme_s": "",
            "komentar": "",
        })
    return tablice.dodaj(sheet, tablice.TAB_OCJENE, redci)


def ocijeni_rucno(sheet, pokusaj_id: str, zadatak_id: str, *, tocno: bool, bodovi=None,
                  komentar: str = "", profesor: str = "") -> bool:
    """Profesor ispravlja ocjenu (obavezno kad je `izvor_ocjene` = „?")."""
    from tablice import TAB_OCJENE

    for r in tablice.ucitaj(sheet, TAB_OCJENE):
        if (model.tekst(r.get("pokusaj_id")) == model.tekst(pokusaj_id)
                and model.tekst(r.get("zadatak_id")) == model.tekst(zadatak_id)):
            iznos = bodovi if bodovi is not None else (r.get("max") if tocno else 0)
            ok = tablice.azuriraj(sheet, TAB_OCJENE, "pokusaj_id", pokusaj_id, {})  # placeholder
            # stvarni upis ide po kombinaciji pokušaj+zadatak → radimo izravno preko retka
            return _upisi_rucno(sheet, r, tocno, iznos, komentar, profesor)
    return False


def _upisi_rucno(sheet, redak: dict, tocno: bool, bodovi, komentar: str, profesor: str) -> bool:
    """Pomoćna: upiše ručnu ocjenu u točan redak `Ocjene_zadataka`."""
    ws = tablice.osiguraj(sheet, tablice.TAB_OCJENE)
    zaglavlje = [model.tekst(h) for h in (ws.row_values(1) or [])]
    if not zaglavlje:
        return False
    i_pok = zaglavlje.index("pokusaj_id") if "pokusaj_id" in zaglavlje else 0
    i_zad = zaglavlje.index("zadatak_id") if "zadatak_id" in zaglavlje else 1
    for br, red in enumerate(ws.get_all_values()[1:], start=2):
        if (i_pok < len(red) and model.tekst(red[i_pok]) == model.tekst(redak.get("pokusaj_id"))
                and i_zad < len(red) and model.tekst(red[i_zad]) == model.tekst(redak.get("zadatak_id"))):
            for polje, vrijednost in (("tocno", "Da" if tocno else "Ne"),
                                      ("bodovi", bodovi),
                                      ("izvor_ocjene", ocjenjivanje.IZVOR_PROFESOR),
                                      ("komentar", model.tekst(komentar))):
                if polje in zaglavlje:
                    ws.update_cell(br, zaglavlje.index(polje) + 1, vrijednost)
            tablice.zapisi_radnju(sheet, profesor, "rucna_ocjena",
                                 f"{redak.get('pokusaj_id')}/{redak.get('zadatak_id')}")
            return True
    return False
