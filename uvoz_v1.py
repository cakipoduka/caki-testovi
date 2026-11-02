"""
CAKI testovi v2 — `uvoz_v1.py`
UVOZ REZULTATA IZ v1 (Cakijev zahtjev 31.10.2026.): „simulacija državne mature" — **svi učenici
koji imaju rezultat** prelaze u v2 kao pročitani (arhivski) test s rezultatom.

Zašto je to sigurno: v1 je sve zamrznuo u CRM Sheet — `Testovi_zakazani` (zadaci koje je učenik
stvarno dobio) i `Rezultati_testova` (bodovi, odgovori, detalji po zadatku). Uvoz NE čita bazu
zadataka, pa učenik u v2 vidi **iste** zadatke koje je rješavao, a ne današnju verziju iz baze.

Što nastaje (jedan test → jedan skup redaka):
  1 × `Definicije_testova` — status **„arhiviran"** (nitko ga ne može ponovno zadati ni mijenjati),
  1 × `Dodjele` po učeniku — status „predano",
  1 × `Pokusaji` po učeniku — status „predano", bodovi/predaja/odgovori iz v1 + snimka zadataka,
  1 × `Ocjene_zadataka` po zadatku — iz v1 `detalji_json` (tko je što točno riješio).

Idempotentno: test se prepoznaje po `v1_test: <naziv>` u `napomena` definicije, a učenik po
postojećem pokušaju — drugi uvoz preskače i ne pravi duplikate.
"""
from __future__ import annotations

import definicije
import model
import tablice

V1_TEST_TAB = "Testovi_zakazani"
V1_REZ_TAB = "Rezultati_testova"

OZNAKA_UVOZA = "v1_test:"          # marker u `napomena` definicije (idempotentnost)
AUTOR_UVOZA = "uvoz v1"
GRUPA_UVOZA = "v1 (uvezeno)"


# ================================================================ čitanje v1

def _v1_tablica(sheet, tab: str) -> list[dict]:
    """Retci v1 taba; nepostojeći tab = prazno (uvoz ne smije puknuti zbog toga)."""
    try:
        return [dict(r) for r in sheet.worksheet(tab).get_all_records()]
    except Exception:                                   # noqa: BLE001 — taba nema / prazan
        return []


def _kljuc_naziva(tekst) -> str:
    """Naziv za usporedbu: mala slova, bez dijakritike i viška razmaka."""
    s = model.tekst(tekst).lower()
    for a, b in (("č", "c"), ("ć", "c"), ("ž", "z"), ("š", "s"), ("đ", "d")):
        s = s.replace(a, b)
    return " ".join(s.split())


def pronadji_testove(sheet, upit: str = "simulacij") -> list[dict]:
    """v1 testovi iz `Testovi_zakazani` čiji naziv sadrži `upit`.

    v1 je za grupu upisivao **jedan redak po učeniku**, pa se retci grupiraju po nazivu:
    vraća [{"naziv", "test_idovi", "zadaci_json", "predmet", "trajanje_min", "rok_od", "rok_do",
            "redaka"}].
    """
    trazi = _kljuc_naziva(upit)
    grupe: dict[str, dict] = {}
    for r in _v1_tablica(sheet, V1_TEST_TAB):
        naziv = model.tekst(r.get("naziv"))
        if not naziv:
            continue
        if trazi and trazi not in _kljuc_naziva(naziv):
            continue
        k = _kljuc_naziva(naziv)
        g = grupe.setdefault(k, {"naziv": naziv, "test_idovi": [], "zadaci_json": "",
                                 "predmet": "", "trajanje_min": 45, "rok_od": "", "rok_do": "",
                                 "redaka": 0})
        tid = model.tekst(r.get("test_id"))
        if tid and tid not in g["test_idovi"]:
            g["test_idovi"].append(tid)
        g["redaka"] += 1
        if not g["zadaci_json"]:
            g["zadaci_json"] = model.tekst(r.get("zadaci_json"))
        if not g["predmet"]:
            g["predmet"] = model.tekst(r.get("predmet"))
        g["trajanje_min"] = model.cijeli(r.get("trajanje_min"), g["trajanje_min"]) or 45
        g["rok_od"] = g["rok_od"] or model.iso_datum(r.get("otvara_od"))
        g["rok_do"] = g["rok_do"] or model.iso_datum(r.get("zatvara_od"))
    izlaz = list(grupe.values())
    for g in izlaz:
        g["broj_rezultata"] = len(_rezultati_za(sheet, g["test_idovi"]))
    izlaz.sort(key=lambda g: (-g["broj_rezultata"], g["naziv"]))
    return izlaz


def _rezultati_za(sheet, test_idovi) -> list[dict]:
    ids = {model.tekst(t) for t in (test_idovi or []) if model.tekst(t)}
    return [r for r in _v1_tablica(sheet, V1_REZ_TAB)
            if model.tekst(r.get("test_id")) in ids and model.tekst(r.get("ucenik_id"))]


def _v1_zadaci_json_za_test(sheet, test_id: str) -> str:
    """`zadaci_json` iz v1 retka TOG testa (u v1 svaki učenik ima svoj redak)."""
    trazeni = model.tekst(test_id)
    for r in _v1_tablica(sheet, V1_TEST_TAB):
        if model.tekst(r.get("test_id")) == trazeni and model.tekst(r.get("zadaci_json")):
            return model.tekst(r.get("zadaci_json"))
    return ""


# ================================================================ pretvorbe

def _zadaci_iz_detalja(rezultati: list[dict], *, max_zadataka: int = 80) -> list[dict]:
    """Rekonstruiraj popis zadataka iz `detalji_json` (v1) — kad `zadaci_json` nije čitljiv.

    Uzima najpotpuniji rezultat (najviše detalja) i gradi v2 oblik zadatka:
    `{id, tekst, opcije, odgovor, bodovi, tip}`. Tekst pokušava dohvatiti iz baze.
    """
    import json

    najbolji = []
    for r in rezultati or []:
        try:
            d = json.loads(model.tekst(r.get("detalji_json")) or "[]")
        except Exception:                               # noqa: BLE001
            d = []
        if isinstance(d, list) and len(d) > len(najbolji):
            najbolji = d
    if not najbolji:
        return []

    iz_baze = {}
    try:
        import banka
        import veza

        sheet_baze = veza.sheet_baze()
        for d in najbolji[:max_zadataka]:
            zid = model.tekst(d.get("id"))
            if zid:
                z = banka.zadatak_iz_retka(banka.po_id(sheet_baze, zid) or {})
                if z:
                    iz_baze[zid] = z
    except Exception:                                   # noqa: BLE001
        iz_baze = {}

    izlaz = []
    for d in najbolji[:max_zadataka]:
        zid = model.tekst(d.get("id"))
        if not zid:
            continue
        baza = iz_baze.get(zid) or {}
        izlaz.append({
            "id": zid,
            "tekst": model.tekst(baza.get("tekst")) or f"Zadatak {zid}",
            "opcije": baza.get("opcije") or [],
            "odgovor": model.tekst(d.get("ocekivano")) or model.tekst(baza.get("odgovor")),
            "bodovi": model.broj(d.get("max"), model.broj(baza.get("bodovi"), 1)) or 1,
            "tip": model.tekst(baza.get("tip")) or "kratki_odgovor",
            "slika": model.tekst(baza.get("slika")),
        })
    return izlaz


def zadaci_iz_v1(zadaci_json) -> list[dict]:
    """v1 zamrznuti zadatak → v2 oblik (doda polja koja v2 čita, ništa ne mijenja)."""
    izlaz = []
    for z in model.kao_json(zadaci_json):
        if not isinstance(z, dict) or not model.tekst(z.get("id")):
            continue
        tekst = model.tekst(z.get("tekst"))
        if not tekst:
            continue
        opcije = [model.tekst(o) for o in (z.get("opcije") or []) if model.tekst(o)]
        tip = model.tekst(z.get("tip")) or ("visestruki_izbor" if len(opcije) >= 2
                                            else "kratki_odgovor")
        izlaz.append({
            "id": model.tekst(z.get("id")),
            "tekst": tekst,
            "tip": tip,
            "opcije": opcije if tip in ("visestruki_izbor", "vise_tocnih") else [],
            "odgovor": model.tekst(z.get("odgovor")),
            "bodovi": model.broj(z.get("bodovi"), 1) or 1,
            "slika": model.tekst(z.get("slika")),
            "video_url": model.tekst(z.get("video_url")),
            "video_naslov": model.tekst(z.get("video_naslov")),
            "cjelina": model.tekst(z.get("cjelina")),
            "potpoglavlje": model.tekst(z.get("potpoglavlje")),
            "tezina": model.tekst(z.get("tezina")),
            "bloom": model.tekst(z.get("bloom")),
            "izvor": model.tekst(z.get("izvor")),
            "razred": model.tekst(z.get("razred")),
        })
    return izlaz


def _nacrt_ocjena(pokusaj_id: str, detalji_json, zadaci: list[dict]) -> list[dict]:
    """v1 `detalji_json` → retci `Ocjene_zadataka` (v2)."""
    redoslijed = {model.tekst(z.get("id")): i for i, z in enumerate(zadaci or [])}
    ocjene = []
    for d in model.kao_json(detalji_json):
        if not isinstance(d, dict):
            continue
        zid = model.tekst(d.get("id"))
        b = model.broj(d.get("bodovi"))
        maks = model.broj(d.get("max"))
        ocjene.append({
            "pokusaj_id": pokusaj_id,
            "zadatak_id": zid,
            "redni_broj": redoslijed.get(zid, len(ocjene) + 1),
            "odgovor": model.tekst(d.get("odgovor")),
            "tocno": "Da" if (model.tekst(d.get("status")) == "tocno"
                              or d.get("tocno") is True) else "Ne",
            "bodovi": b,
            "max": maks,
            "izvor_ocjene": "uvoz_v1",
            "vrijeme_s": "",
            "komentar": _komentar_ocjene(d),
        })
    return ocjene


def _komentar_ocjene(d: dict) -> str:
    """Kratak trag uz ocjenu: je li v1 čekao provjeru ili je odgovor bio prazan."""
    status = model.tekst((d or {}).get("status"))
    if status == "ceka":
        return "uvezeno iz v1 — čekalo provjeru"
    if status == "prazno":
        return "uvezeno iz v1 — bez odgovora"
    return "uvezeno iz v1"


def _zadnji_po_uceniku(rezultati: list[dict]) -> tuple[list[dict], list[str]]:
    """Jedan rezultat po učeniku (zadnja predaja). Vraća (retci, upozorenja)."""
    po: dict[str, dict] = {}
    dupli = set()
    for r in rezultati or []:
        uid = model.tekst(r.get("ucenik_id")).upper()
        if not uid:
            continue
        stari = po.get(uid)
        kljuc = model.tekst(r.get("vrijeme_predaje")) or model.tekst(r.get("kreirano"))
        if stari is None:
            po[uid] = r
            continue
        stari_kljuc = model.tekst(stari.get("vrijeme_predaje")) or model.tekst(stari.get("kreirano"))
        if kljuc >= stari_kljuc:
            po[uid] = r
        dupli.add(uid)
    upozorenja = []
    if dupli:
        upozorenja.append(f"{len(dupli)} učenika ima više rezultata u v1 — uzet je **zadnji**.")
    return list(po.values()), upozorenja


# ================================================================ priprema uvoda

def _postojeci_uvoz(sheet, naziv: str) -> dict | None:
    """Definicija koja je već nastala ovim uvozom (po markeru u `napomena`)."""
    marker = f"{OZNAKA_UVOZA} {_kljuc_naziva(naziv)}"
    for d in tablice.ucitaj(sheet, tablice.TAB_DEFINICIJE):
        if marker in model.tekst(d.get("napomena")):
            return d
    return None


def pripremi(sheet, naziv: str) -> dict:
    """Nacrt uvoza — **ništa ne piše**. Vraća sve što će se upisati + što se preskače.

    `naziv` je naziv v1 testa (vidi `pronadji_testove`).
    """
    naziv = model.tekst(naziv)
    if not naziv:
        raise ValueError("Nedostaje naziv v1 testa.")
    kandidati = [g for g in pronadji_testove(sheet, upit=naziv)
                 if _kljuc_naziva(g["naziv"]) == _kljuc_naziva(naziv)]
    if not kandidati:
        raise ValueError(f"U v1 tabu `{V1_TEST_TAB}` nema testa „{naziv}”.")
    g = kandidati[0]

    rezultati, upozorenja = _zadnji_po_uceniku(_rezultati_za(sheet, g["test_idovi"]))
    if not rezultati:
        raise ValueError(f"Test „{naziv}” nema nijedan rezultat u `{V1_REZ_TAB}` — nema što uvesti.")

    # Zadaci po v1 testu: u v1 je svaki učenik imao SVOJ redak (i svoju zamrznutu kopiju
    # zadataka). Zato se svakom učeniku u pokušaj upisuje NJEGOVA kopija — inače bi u pregledu
    # vidio tuđi redoslijed. Definicija dobiva prvu kopiju (za PDF i popis testa).
    zadaci_po_testu: dict[str, list[dict]] = {}
    for tid in g["test_idovi"]:
        zadaci_po_testu[tid] = zadaci_iz_v1(_v1_zadaci_json_za_test(sheet, tid))
    razlicite = {model.u_json(z) for z in zadaci_po_testu.values() if z}
    if len(razlicite) > 1:
        upozorenja.append(
            f"U v1 su različiti retci imali **{len(razlicite)} verzije zadataka** (test je "
            "mijenjan dok su ga učenici rješavali). Svakom učeniku uvezeni su zadaci iz "
            "NJEGOVOG retka, pa pregled odgovara onome što je stvarno rješavao.")
    zadaci = next((z for z in zadaci_po_testu.values() if z), [])
    if not zadaci:
        # v1 nema `zadaci_json`, ali `detalji_json` po učenicima IMA id/max/ocekivano
        zadaci = _zadaci_iz_detalja(rezultati)
        if zadaci:
            upozorenja.append(
                f"v1 nije imao čitljive `zadaci_json`; popis od **{len(zadaci)} zadataka** "
                "rekonstruiran je iz `detalji_json` (bodovi i točni odgovori). Tekst zadatka "
                "dohvaćen je iz baze kad je bio dostupan.")
    if not zadaci:
        raise ValueError(f"Test „{naziv}” u v1 nema ni `zadaci_json` ni `detalji_json` — "
                         "uvoz nije moguć.")

    veca = _postojeci_uvoz(sheet, naziv)
    definicija_id = (model.tekst(veca.get("definicija_id")) if veca else
                     tablice.novi_id([model.tekst(d.get("definicija_id"))
                                      for d in tablice.ucitaj(sheet, tablice.TAB_DEFINICIJE)],
                                     "T26-"))
    postojeci_pokusaji = {
        (model.tekst(p.get("ucenik_id")).upper()) for p in
        tablice.ucitaj(sheet, tablice.TAB_POKUSAJI)
        if model.tekst(p.get("definicija_id")) == definicija_id
    }

    # --- definicija (samo ako je još nema)
    definicija = None
    if not veca:
        definicija = definicije.nova_definicija(
            definicija_id=definicija_id, naziv=naziv, predmet=g["predmet"], zadaci_=zadaci,
            trajanje_min=g["trajanje_min"], vrsta="ocjena", status="arhiviran",
            rok_od=g["rok_od"], rok_do=g["rok_do"], autor=AUTOR_UVOZA,
            napomena=f"{OZNAKA_UVOZA} {_kljuc_naziva(naziv)} | Uvezeno iz v1 "
                     f"({len(rezultati)} učenika).",
            ai_pomoc="ne",
        )

    # --- dodjele + pokušaji + ocjene
    dodjele, pokusaji, ocjene, ucenici, preskoceno = [], [], [], [], []
    svi_dodjela_idovi = tablice.svi_idovi(sheet, tablice.TAB_DODJELE, "dodjela_id")
    svi_pokusaj_idovi = tablice.svi_idovi(sheet, tablice.TAB_POKUSAJI, "pokusaj_id")
    prefiks_d = "D" + (definicija_id[1:3] if len(definicija_id) > 2 else "26") + "-"

    for r in sorted(rezultati, key=lambda x: model.tekst(x.get("ucenik_id"))):
        uid = model.tekst(r.get("ucenik_id")).upper()
        if not uid:
            continue
        if uid in postojeci_pokusaji:
            preskoceno.append({"ucenik_id": uid, "zasto": "već uvezen"})
            continue
        ime = model.tekst(r.get("ime_djeteta"))
        predaja = model.tekst(r.get("vrijeme_predaje")) or model.tekst(r.get("kreirano"))
        pocetak = model.tekst(r.get("vrijeme_pocetka")) or predaja
        # zadaci iz TOG učenikovog v1 retka (fallback: prva verzija testa)
        zadaci_u = zadaci_po_testu.get(model.tekst(r.get("test_id"))) or zadaci
        dodjela_id = tablice.novi_id(svi_dodjela_idovi, prefiks_d)
        svi_dodjela_idovi.append(dodjela_id)
        pokusaj_id = tablice.novi_id(svi_pokusaj_idovi, "P26-")
        svi_pokusaj_idovi.append(pokusaj_id)

        dodjele.append({
            "dodjela_id": dodjela_id, "definicija_id": definicija_id, "ucenik_id": uid,
            "ime_djeteta": ime, "grupa": GRUPA_UVOZA,
            "rok_od": model.iso_datum(g["rok_od"]), "rok_do": model.iso_datum(g["rok_do"]),
            "varijanta_seed": f"{definicija_id}:{uid}", "status": "predano",
            "dodijelio": AUTOR_UVOZA, "dodijeljeno": predaja or model.sada_iso(),
        })
        pokusaji.append({
            "pokusaj_id": pokusaj_id, "dodjela_id": dodjela_id, "definicija_id": definicija_id,
            "ucenik_id": uid, "pocetak": pocetak, "zadnja_aktivnost": predaja, "predaja": predaja,
            "trajanje_s": model.cijeli(r.get("trajanje_s"), 0),
            "odgovori_json": model.tekst(r.get("odgovori_json")) or "{}",
            "bodovi": model.broj(r.get("bodovi")), "bodovi_max": model.broj(r.get("bodovi_max")),
            "status": "predano", "predano_po_roku": "Ne",
            "zadaci_json": model.u_json(zadaci_u),
        })
        ocjene.extend(_nacrt_ocjena(pokusaj_id, r.get("detalji_json"), zadaci_u))
        if not model.tekst(r.get("detalji_json")):
            upozorenja.append(f"{uid}: v1 rezultat nema `detalji_json` — ocjene po zadatku "
                              "izostaju (bodovi su uvezeni).")
        ucenici.append({"ucenik_id": uid, "ime_djeteta": ime,
                        "bodovi": model.broj(r.get("bodovi")),
                        "bodovi_max": model.broj(r.get("bodovi_max"))})

    if not dodjele:
        upozorenja.append("Svi učenici su već uvezeni — nema novih redaka za upis.")

    return {
        "naziv": naziv, "v1_test_idovi": g["test_idovi"], "predmet": g["predmet"],
        "trajanje_min": g["trajanje_min"], "rok_od": g["rok_od"], "rok_do": g["rok_do"],
        "definicija_id": definicija_id, "definicija": definicija,
        "vec_uvezeno": model.tekst((veca or {}).get("definicija_id")),
        "zadaci": zadaci, "dodjele": dodjele, "pokusaji": pokusaji, "ocjene": ocjene,
        "ucenici": ucenici, "preskoceno": preskoceno, "upozorenja": upozorenja,
        "broj_zadataka": len(zadaci),
        "bodovi_ukupno": sum(model.broj(z.get("bodovi"), 1) for z in zadaci),
        "svi_rezultati": len(rezultati),
    }


def izvrsi(sheet, nacrt: dict) -> dict:
    """Upiši nacrt u v2 tabove. **Samo uz uključeno pisanje** (`tablice.PISANJE`)."""
    if not isinstance(nacrt, dict) or not model.tekst(nacrt.get("definicija_id")):
        raise ValueError("Nacrt uvoza nije ispravan — pokreni „Pripremi uvoz” ponovno.")
    if not tablice.PISANJE:
        raise PermissionError(
            "Upis u živu bazu je isključen. Uključi ga u ⚙️ Postavkama (sigurnosni prekidač) "
            "pa pokušaj uvoz ponovno.")

    for tab in (tablice.TAB_DEFINICIJE, tablice.TAB_DODJELE, tablice.TAB_POKUSAJI,
                tablice.TAB_OCJENE):
        tablice.osiguraj(sheet, tab)

    napisano = {"definicija": 0, "dodjele": 0, "pokusaji": 0, "ocjene": 0}
    if nacrt.get("definicija"):
        napisano["definicija"] = tablice.dodaj(sheet, tablice.TAB_DEFINICIJE,
                                               [nacrt["definicija"]])
    if nacrt.get("dodjele"):
        napisano["dodjele"] = tablice.dodaj(sheet, tablice.TAB_DODJELE, nacrt["dodjele"])
    if nacrt.get("pokusaji"):
        napisano["pokusaji"] = tablice.dodaj(sheet, tablice.TAB_POKUSAJI, nacrt["pokusaji"])
    if nacrt.get("ocjene"):
        napisano["ocjene"] = tablice.dodaj(sheet, tablice.TAB_OCJENE, nacrt["ocjene"])

    try:
        tablice.zapisi_radnju(sheet, AUTOR_UVOZA, "uvoz_v1",
                              model.tekst(nacrt.get("definicija_id")),
                              f"{napisano['dodjele']} učenika · „{model.tekst(nacrt.get('naziv'))}”")
    except Exception:                                   # noqa: BLE001 — dnevnik ne blokira uvoz
        pass
    return napisano

def dijagnostika(sheet, definicija_id: str) -> dict:
    """Točni brojevi zapisa za jedan test po svim relevantnim tabovima (za rješavanje zastoja)."""
    did = model.tekst(definicija_id)
    izlaz = {"definicija_id": did,
             "dodjele_ispita": 0, "pokusaji": 0, "ocjene": 0,
             "crm_dodjele_rezultati": 0, "crm_dodjele_nasi": 0}
    try:
        izlaz["dodjele_ispita"] = len([
            r for r in tablice.ucitaj(sheet, tablice.TAB_DODJELE)
            if model.tekst(r.get("definicija_id")) == did])
    except Exception:                                   # noqa: BLE001
        pass
    try:
        pok = [r for r in tablice.ucitaj(sheet, tablice.TAB_POKUSAJI)
               if model.tekst(r.get("definicija_id")) == did]
        izlaz["pokusaji"] = len(pok)
        pids = {model.tekst(p.get("pokusaj_id")) for p in pok}
        izlaz["ocjene"] = len([r for r in tablice.ucitaj(sheet, tablice.TAB_OCJENE)
                               if model.tekst(r.get("pokusaj_id")) in pids])
    except Exception:                                   # noqa: BLE001
        pass
    try:
        for r in tablice.ucitaj(sheet, tablice.TAB_DODJELE_CRM):
            if model.tekst(r.get("definicija_id")) == did:
                izlaz["crm_dodjele_rezultati"] += 1
            elif model.tekst(r.get("dodjela_id")).upper().startswith("D2"):
                izlaz["crm_dodjele_nasi"] += 1
    except Exception:                                   # noqa: BLE001
        pass
    return izlaz

def rekonstruiraj_dodjele(sheet, definicija_id: str) -> dict:
    """Napravi dodjele za pokušaje koji ih nemaju (ili im `dodjela_id` ne postoji u tabu).

    Ne dira postojeće dodjele; ne dira v1. Vraća {"nedostaje", "napravljeno", "postojece"}.
    """
    did = model.tekst(definicija_id)
    izlaz = {"nedostaje": 0, "napravljeno": 0, "postojece": 0, "dopunjeno": 0}
    if not did:
        return izlaz

    dodjele = tablice.ucitaj(sheet, tablice.TAB_DODJELE)
    po_id = {model.tekst(d.get("dodjela_id")) for d in dodjele}
    pokusaji = [p for p in tablice.ucitaj(sheet, tablice.TAB_POKUSAJI)
                if model.tekst(p.get("definicija_id")) == did]

    novi_idovi = tablice.svi_idovi(sheet, tablice.TAB_DODJELE, "dodjela_id")
    nove = []
    for p in pokusaji:
        did_p = model.tekst(p.get("dodjela_id"))
        if did_p and did_p in po_id:
            izlaz["postojece"] += 1
            # 02.11.2026.: dodjela postoji, ali joj `definicija_id` može biti prazan
            # (stari retci `D26-0001…0013`) → tada je Rezultati ne prikazuju.
            try:
                dodjela = next((d for d in dodjele
                                if model.tekst(d.get("dodjela_id")) == did_p), {})
                dopuna = {}
                if not model.tekst(dodjela.get("definicija_id")):
                    dopuna["definicija_id"] = did
                _uc_p = model.tekst(p.get("ucenik_id")).upper()
                _uc_d = model.tekst(dodjela.get("ucenik_id")).upper()
                # vlasnik je testni račun ili se ne poklapa → upiši učenika iz pokušaja
                if _uc_p and _uc_d != _uc_p:
                    dopuna["ucenik_id"] = _uc_p
                if not model.tekst(dodjela.get("status")):
                    dopuna["status"] = "predano"
                if dopuna:
                    tablice.azuriraj(sheet, tablice.TAB_DODJELE, "dodjela_id", did_p, dopuna)
                    izlaz["dopunjeno"] = izlaz.get("dopunjeno", 0) + 1
            except Exception:                       # noqa: BLE001
                pass
            continue
        izlaz["nedostaje"] += 1
        # 01.11.2026.: POKUŠAJ već ima svoj `dodjela_id` — napravi dodjelu s TOČNO tim ID-om
        novi = did_p or tablice.novi_id(novi_idovi, "D26-")
        if novi not in novi_idovi:
            novi_idovi.append(novi)
        nove.append({
            "dodjela_id": novi,
            "definicija_id": did,
            "ucenik_id": model.tekst(p.get("ucenik_id")).upper(),
            "ime_djeteta": "",
            "grupa": "v1",
            "rok_od": model.tekst(p.get("pocetak"))[:10],
            "rok_do": model.tekst(p.get("predaja"))[:10],
            "varijanta_seed": model.tekst(p.get("ucenik_id")).upper(),
            "status": "predano",
            "dodijelio": "rekonstrukcija",
            "dodijeljeno": model.sada_iso(),
        })
        # poveži pokušaj na novu dodjelu
        try:
            tablice.azuriraj(sheet, tablice.TAB_POKUSAJI, "pokusaj_id",
                             model.tekst(p.get("pokusaj_id")), {"dodjela_id": novi})
        except Exception:                               # noqa: BLE001
            pass

    if nove:
        tablice.dodaj(sheet, tablice.TAB_DODJELE, nove)
        izlaz["napravljeno"] = len(nove)
    return izlaz

def _detalji_iz_v1(sheet, ucenik_id: str, test_id: str = "") -> list:
    """`detalji_json` iz v1 `Rezultati_testova` za učenika (i test, ako je zadan)."""
    import json

    uid = model.tekst(ucenik_id).upper()
    tid = model.tekst(test_id).upper()
    for r in _v1_tablica(sheet, V1_REZ_TAB):
        if model.tekst(r.get("ucenik_id")).upper() != uid:
            continue
        if tid and model.tekst(r.get("test_id")).upper() != tid:
            continue
        try:
            d = json.loads(model.tekst(r.get("detalji_json")) or "[]")
        except Exception:                               # noqa: BLE001
            continue
        if isinstance(d, list) and d:
            return d
    return []


def dopuni_ocjene(sheet, definicija_id: str) -> dict:
    """Iz v1 `detalji_json` napravi `Ocjene_zadataka` za pokušaje koji ih nemaju.

    Claude (01.11.2026.): `detalji_json` je popunjen i sadrži
    `{"id", "tocno", "status", "bodovi", "max", "odgovor", "ocekivano", "izvor", "zasto"}`.
    Time „Uspjeh po zadatku" i „Uspjeh po cjelinama" rade i za uvezene testove.
    """
    import json

    did = model.tekst(definicija_id)
    izlaz = {"pokusaja": 0, "ocjena": 0, "bez_detalja": 0, "greske": []}
    svi = tablice.ucitaj(sheet, tablice.TAB_POKUSAJI)
    pokusaji = ([p for p in svi if model.tekst(p.get("definicija_id")) == did] if did else svi)
    postojeci = {model.tekst(r.get("pokusaj_id")) for r in
                 tablice.ucitaj(sheet, tablice.TAB_OCJENE)}

    novi = []
    for p in pokusaji:
        pid = model.tekst(p.get("pokusaj_id"))
        if pid in postojeci:
            continue
        izlaz["pokusaja"] += 1
        try:
            detalji = json.loads(model.tekst(p.get("detalji_json")) or "[]")
        except Exception:                               # noqa: BLE001
            detalji = []
        if not detalji:
            # rezerva: v1 redak po (`test_id`, `ucenik_id`) — tamo je `detalji_json` pun
            detalji = _detalji_iz_v1(sheet, model.tekst(p.get("ucenik_id")))
        if not detalji:
            izlaz["bez_detalja"] += 1
            continue
        for i, d in enumerate(detalji):
            if not isinstance(d, dict):
                continue
            tocno = d.get("tocno")
            novi.append({
                "pokusaj_id": pid,
                "zadatak_id": model.tekst(d.get("id")),
                "redni_broj": i + 1,
                "odgovor": model.tekst(d.get("odgovor")),
                "tocno": "Da" if tocno is True or model.tekst(d.get("status")) == "tocno" else "Ne",
                "bodovi": model.broj(d.get("bodovi"), 0),
                "max": model.broj(d.get("max"), 1),
                "izvor_ocjene": model.tekst(d.get("izvor")) or "string",
                "vrijeme_s": "",
                "komentar": model.tekst(d.get("zasto")),
            })
    if novi:
        tablice.dodaj(sheet, tablice.TAB_OCJENE, novi)
        izlaz["ocjena"] = len(novi)
    return izlaz

def povezi_po_uceniku(sheet, definicija_id: str) -> dict:
    """Poveži pokušaje na dodjele po `ucenik_id` (kad `dodjela_id` ne postoji u tabu).

    Vraća {"pokusaja", "povezano", "bez_dodjele"}.
    """
    did = model.tekst(definicija_id)
    izlaz = {"pokusaja": 0, "povezano": 0, "bez_dodjele": 0}
    dodjele = [d for d in tablice.ucitaj(sheet, tablice.TAB_DODJELE)
               if not did or model.tekst(d.get("definicija_id")) == did]
    po_uceniku = {model.tekst(d.get("ucenik_id")).upper(): model.tekst(d.get("dodjela_id"))
                  for d in dodjele if model.tekst(d.get("ucenik_id"))}
    postojeci_idovi = {model.tekst(d.get("dodjela_id")) for d in dodjele}
    po_vlasniku = {model.tekst(d.get("dodjela_id")): model.tekst(d.get("ucenik_id"))
                   for d in dodjele}

    for p in tablice.ucitaj(sheet, tablice.TAB_POKUSAJI):
        if did and model.tekst(p.get("definicija_id")) != did:
            continue
        izlaz["pokusaja"] += 1
        trenutni = model.tekst(p.get("dodjela_id"))
        uid = model.tekst(p.get("ucenik_id")).upper()
        if trenutni in postojeci_idovi:
            # dodjela postoji — provjeri pripada li ISTOM učeniku (testni računi!)
            vlasnik = model.tekst(po_vlasniku.get(trenutni, "")).upper()
            if not uid or vlasnik == uid:
                continue
        nova = po_uceniku.get(uid)
        if not nova:
            izlaz["bez_dodjele"] += 1
            continue
        try:
            if tablice.azuriraj(sheet, tablice.TAB_POKUSAJI, "pokusaj_id",
                                model.tekst(p.get("pokusaj_id")), {"dodjela_id": nova}):
                izlaz["povezano"] += 1
        except Exception:                               # noqa: BLE001
            pass
    return izlaz

def dijagnostika_veza(sheet, definicija_id: str) -> list[dict]:
    """Vrati pokušaje kojima se `ucenik_id` NE nalazi među dodjelama tog testa.

    Svaki redak: {"pokusaj_id", "ucenik_id", "dodjela_id"} — za ručno mapiranje.
    """
    did = model.tekst(definicija_id)
    dodjele = [d for d in tablice.ucitaj(sheet, tablice.TAB_DODJELE)
               if not did or model.tekst(d.get("definicija_id")) == did]
    ucenici = {model.tekst(d.get("ucenik_id")).upper() for d in dodjele
               if model.tekst(d.get("ucenik_id"))}

    izlaz = []
    for p in tablice.ucitaj(sheet, tablice.TAB_POKUSAJI):
        if did and model.tekst(p.get("definicija_id")) != did:
            continue
        uid = model.tekst(p.get("ucenik_id")).upper()
        if uid and uid not in ucenici:
            izlaz.append({"pokusaj_id": model.tekst(p.get("pokusaj_id")),
                          "ucenik_id": uid,
                          "dodjela_id": model.tekst(p.get("dodjela_id"))})
    return izlaz
