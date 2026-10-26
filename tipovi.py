"""
CAKI testovi v2 — `tipovi.py`
MODERNI TIPOVI ZADATAKA — katalog, provjera i automatsko ocjenjivanje po tipu.

Cakijeva napomena 26.10.2026.: stari „Dodaj ručni zadatak" ima samo tekst, video, bodove i
višestruki izbor. Moderni sustavi (ClassTime, Kahoot, Forms, Canvas) imaju **više tipova**, pa se
ovdje definira katalog na kojem će se graditi novi editor.

Za svaki tip: koja polja treba, što je „točno", može li se ocijeniti automatski i kako se boduje.

VAŽNO: ovo je **podloga za editor** (polja → forma) i za ocjenjivanje (`ocjeni`). Editor u
🎛️ kartici dolazi nakon ovoga — ali bez ovog sloja bio bi dupliran kod za svaki tip.
"""
from __future__ import annotations

import model
import ocjenjivanje

# ------------------------------------------------------------------ katalog

TIPOVI: dict[str, dict] = {
    "visestruki_izbor": {
        "naziv": "Višestruki izbor — jedan točan",
        "ikona": "🔘",
        "polja": ["tekst", "opcije", "odgovor", "bodovi", "slika", "video_url"],
        "auto": True,
        "opis": "Ponuđeni odgovori A–E; točan je jedan (slovo).",
    },
    "vise_tocnih": {
        "naziv": "Više točnih odgovora",
        "ikona": "☑️",
        "polja": ["tekst", "opcije", "odgovori", "bodovi", "slika", "video_url"],
        "auto": True,
        "opis": "Više točnih (npr. „BC”); djelomični bodovi po broju pogođenih minus promašeni.",
    },
    "tocno_netocno": {
        "naziv": "Točno / netočno",
        "ikona": "✅",
        "polja": ["tekst", "odgovor", "bodovi"],
        "auto": True,
        "opis": "Tvrdnja; učenik bira točno ili netočno.",
    },
    "kratki_odgovor": {
        "naziv": "Kratki odgovor (tekst ili formula)",
        "ikona": "✍️",
        "polja": ["tekst", "odgovor", "bodovi", "slika", "video_url"],
        "auto": True,
        "opis": "Učenik upisuje odgovor; ocjenjuje se string → SymPy → AI prijedlog.",
    },
    "brojcan": {
        "naziv": "Brojčani odgovor s tolerancijom",
        "ikona": "🔢",
        "polja": ["tekst", "odgovor", "tolerancija", "bodovi"],
        "auto": True,
        "opis": "Npr. „3,14” uz toleranciju 0,01 — prihvaća zaokruživanje.",
    },
    "popuni_praznine": {
        "naziv": "Popuni praznine",
        "ikona": "🧩",
        "polja": ["tekst", "praznine", "bodovi"],
        "auto": True,
        "opis": "Tekst s `{…}`; svaka praznina ima svoj točan odgovor.",
    },
    "povezivanje": {
        "naziv": "Povezivanje (lijevo ↔ desno)",
        "ikona": "🔗",
        "polja": ["tekst", "parovi", "bodovi"],
        "auto": True,
        "opis": "Parovi pojmova; ocjenjuje se broj ispravno povezanih.",
    },
    "poredak": {
        "naziv": "Poredak (posloži redom)",
        "ikona": "🔀",
        "polja": ["tekst", "opcije", "bodovi"],
        "auto": True,
        "opis": "Ponuđene stavke treba posložiti; točan poredak je u `opcije`.",
    },
    "otvoreni_odgovor": {
        "naziv": "Otvoreni odgovor (esej / postupak)",
        "ikona": "📝",
        "polja": ["tekst", "bodovi", "slika"],
        "auto": False,
        "opis": "Ocjenjuje profesor; sustav samo prikupi odgovor i označi „čeka provjeru”.",
    },
}

ZADANI = "kratki_odgovor"


def naziv(tip: str) -> str:
    return (TIPOVI.get(tip) or {}).get("naziv", model.tekst(tip))


def ikona(tip: str) -> str:
    return (TIPOVI.get(tip) or {}).get("ikona", "❓")


def polja(tip: str) -> list[str]:
    """Koja polja editor treba prikazati za taj tip (redoslijed je redoslijed forme)."""
    return list((TIPOVI.get(tip) or {}).get("polja", ["tekst", "odgovor", "bodovi"]))


def automatski(tip: str) -> bool:
    """Može li se ocijeniti bez profesora."""
    return bool((TIPOVI.get(tip) or {}).get("auto", False))


def svi_tipovi() -> list[str]:
    return list(TIPOVI)


# ------------------------------------------------------------------ provjera

def _bez_opcija(opcije) -> bool:
    return not [o for o in (opcije or []) if model.tekst(o)]


def validiraj(tip: str, zadatak: dict) -> list[str]:
    """Vrati popis grešaka za taj tip (prazno = ispravno)."""
    z = zadatak or {}
    greske: list[str] = []
    if tip not in TIPOVI:
        return [f"Nepoznat tip zadatka: {tip}"]
    if not model.tekst(z.get("tekst")):
        greske.append("Tekst zadatka je obavezan.")
    if model.broj(z.get("bodovi")) <= 0:
        greske.append("Bodovi moraju biti veći od 0.")

    if tip == "visestruki_izbor":
        if len([o for o in (z.get("opcije") or []) if model.tekst(o)]) < 2:
            greske.append("Potrebna su barem 2 ponuđena odgovora.")
        if not model.tekst(z.get("odgovor")):
            greske.append("Označi točan odgovor (A, B, C…).")
    elif tip == "vise_tocnih":
        if len([o for o in (z.get("opcije") or []) if model.tekst(o)]) < 3:
            greske.append("Potrebna su barem 3 ponuđena odgovora.")
        if len(model.tekst(z.get("odgovori"))) < 2:
            greske.append("Označi barem dva točna odgovora (npr. „BC”).")
    elif tip == "tocno_netocno":
        if model.tekst(z.get("odgovor")).lower() not in ("tocno", "točno", "netocno", "netočno"):
            greske.append("Odgovor mora biti „točno” ili „netočno”.")
    elif tip == "kratki_odgovor":
        if not model.tekst(z.get("odgovor")):
            greske.append("Konačan odgovor je obavezan (bez njega nema automatske ocjene).")
    elif tip == "brojcan":
        if not model.tekst(z.get("odgovor")):
            greske.append("Brojčani odgovor je obavezan.")
        try:
            float(model.tekst(z.get("odgovor")).replace(",", "."))
        except ValueError:
            greske.append("Odgovor mora biti broj (npr. 3,14).")
        try:
            if model.tekst(z.get("tolerancija")):
                float(model.tekst(z.get("tolerancija")).replace(",", "."))
        except ValueError:
            greske.append("Tolerancija mora biti broj (npr. 0,01).")
    elif tip == "popuni_praznine":
        praznine = z.get("praznine") or []
        if not praznine:
            greske.append("Dodaj barem jednu prazninu s odgovorom.")
        if "{…}" not in model.tekst(z.get("tekst")) and "{" not in model.tekst(z.get("tekst")):
            greske.append("U tekstu označi prazninu s `{…}`.")
    elif tip == "povezivanje":
        parovi = z.get("parovi") or []
        if len(parovi) < 2:
            greske.append("Potrebna su barem 2 para za povezivanje.")
    elif tip == "poredak":
        if len([o for o in (z.get("opcije") or []) if model.tekst(o)]) < 2:
            greske.append("Potrebne su barem 2 stavke za poredak.")
    elif tip == "otvoreni_odgovor":
        pass                                     # nema automatske provjere
    return greske


# ------------------------------------------------------------------ ocjenjivanje po tipu

def ocjeni(tip: str, zadatak: dict, odgovor) -> dict:
    """Vrati {tocno, bodovi, max, izvor, sigurnost, zasto} — jedinstveno za sve tipove.

    `otvoreni_odgovor` uvijek vraća „čeka provjeru” (izvor `?`), jer ga ocjenjuje profesor.
    """
    z = zadatak or {}
    maks = model.broj(z.get("bodovi"), 1)
    moj = model.tekst(odgovor)

    if tip == "otvoreni_odgovor":
        return {"tocno": None, "bodovi": 0, "max": maks, "izvor": "?",
                "sigurnost": "nema", "zasto": "Otvoreni odgovor ocjenjuje profesor."}

    if tip == "visestruki_izbor":
        return ocjenjivanje.ocjeni_zadatak({**z, "odgovor": model.tekst(z.get("odgovor"))}, moj)

    if tip in ("kratki_odgovor", "tocno_netocno"):
        return ocjenjivanje.ocjeni_zadatak(z, moj)

    if tip == "vise_tocnih":
        tocan = {z.upper() for z in model.tekst(z.get("odgovori")).replace(",", "").replace(" ", "")}
        nas = {z.upper() for z in moj.replace(",", "").replace(" ", "")}
        if not tocan:
            return {"tocno": False, "bodovi": 0, "max": maks, "izvor": "nema",
                    "sigurnost": "nema", "zasto": "Zadatak nema označene točne odgovore."}
        pogodeno = len(tocan & nas)
        promaseno = len(nas - tocan)
        bodovi = maks * max(0.0, (pogodeno - promaseno) / len(tocan))
        return {"tocno": pogodeno == len(tocan) and promaseno == 0,
                "bodovi": round(bodovi, 2), "max": maks, "izvor": "string",
                "sigurnost": "visoka", "zasto": f"{pogodeno}/{len(tocan)} točnih, {promaseno} promašenih."}

    if tip == "brojcan":
        try:
            tocno_broj = float(model.tekst(z.get("odgovor")).replace(",", "."))
            nas_broj = float(moj.replace(",", "."))
        except ValueError:
            return {"tocno": False, "bodovi": 0, "max": maks, "izvor": "nema",
                    "sigurnost": "nema", "zasto": "Odgovor nije broj."}
        tolerancija = 0.0
        try:
            tolerancija = abs(float(model.tekst(z.get("tolerancija")).replace(",", ".") or 0))
        except ValueError:
            tolerancija = 0.0
        tocno = abs(tocno_broj - nas_broj) <= tolerancija + 1e-9
        return {"tocno": tocno, "bodovi": maks if tocno else 0, "max": maks, "izvor": "string",
                "sigurnost": "visoka",
                "zasto": f"Razlika {abs(tocno_broj - nas_broj):.4g}, tolerancija {tolerancija:g}."}

    if tip == "popuni_praznine":
        praznine = [model.tekst(p) for p in (z.get("praznine") or [])]
        nas = [model.tekst(d) for d in model.tekst(moj).split("|")]
        if not praznine:
            return {"tocno": False, "bodovi": 0, "max": maks, "izvor": "nema",
                    "sigurnost": "nema", "zasto": "Zadatak nema praznine."}
        pogodeno = sum(1 for a, b in zip(praznine, nas) if a and ocjenjivanje.tocan_string(a, b))
        return {"tocno": pogodeno == len(praznine),
                "bodovi": round(maks * pogodeno / len(praznine), 2), "max": maks,
                "izvor": "string", "sigurnost": "visoka",
                "zasto": f"{pogodeno}/{len(praznine)} praznina točno."}

    if tip == "povezivanje":
        parovi = z.get("parovi") or []
        tocni = [model.tekst((p or {}).get("desno")) for p in parovi]
        nas = [model.tekst(x) for x in model.tekst(moj).split("|")]
        if not tocni:
            return {"tocno": False, "bodovi": 0, "max": maks, "izvor": "nema",
                    "sigurnost": "nema", "zasto": "Zadatak nema parove."}
        pogodeno = sum(1 for a, b in zip(tocni, nas)
                       if a and ocjenjivanje.tocan_string(a, b))
        return {"tocno": pogodeno == len(tocni),
                "bodovi": round(maks * pogodeno / len(tocni), 2), "max": maks,
                "izvor": "string", "sigurnost": "visoka",
                "zasto": f"{pogodeno}/{len(tocni)} parova točno."}

    if tip == "poredak":
        tocno = [model.tekst(o) for o in (z.get("opcije") or [])]
        nas = [model.tekst(x) for x in model.tekst(moj).split("|")]
        if not tocno:
            return {"tocno": False, "bodovi": 0, "max": maks, "izvor": "nema",
                    "sigurnost": "nema", "zasto": "Zadatak nema stavke."}
        poklapanja = sum(1 for i, (a, b) in enumerate(zip(tocno, nas)) if a == b)
        return {"tocno": poklapanja == len(tocno),
                "bodovi": round(maks * poklapanja / len(tocno), 2), "max": maks,
                "izvor": "string", "sigurnost": "visoka",
                "zasto": f"{poklapanja}/{len(tocno)} stavki na pravom mjestu."}

    return {"tocno": False, "bodovi": 0, "max": maks, "izvor": "nema",
            "sigurnost": "nema", "zasto": f"Tip `{tip}` se ne ocjenjuje automatski."}


def normaliziraj(zadatak: dict) -> dict:
    """Dopuni zadatak onim što svaki tip treba (da editor i baza imaju isti oblik)."""
    z = dict(zadatak or {})
    tip = model.tekst(z.get("tip")) or ZADANI
    z["tip"] = tip if tip in TIPOVI else ZADANI
    z.setdefault("opcije", [])
    z.setdefault("bodovi", 1)
    z.setdefault("odgovor", "")
    if z["tip"] == "tocno_netocno":
        z["opcije"] = ["Točno", "Netočno"]
    if z["tip"] == "vise_tocnih":
        z.setdefault("odgovori", "")
    if z["tip"] == "popuni_praznine":
        z.setdefault("praznine", [])
    if z["tip"] == "povezivanje":
        z.setdefault("parovi", [])
    if z["tip"] == "brojcan":
        z.setdefault("tolerancija", "")
    return z
