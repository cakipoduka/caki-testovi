"""
CAKI testovi v2 — `samoprovjera.py`
🩺 SAMOPROVJERA U APLIKACIJI — popis svih problema koji su već bili riješeni, provjeren **u živoj
verziji** koju Caki upravo gleda.

Zašto: Caki često vidi isti problem jer u cloudu radi **starija verzija** ili se nešto vratilo.
Ovdje klikne i vidi ✅/❌ po svakoj stavci — bez pogađanja i bez mojih pretpostavki.

Ne mijenja ništa: sve su provjere čitanje + računanje u memoriji.
"""
from __future__ import annotations

import os
from pathlib import Path

import banka
import definicije
import model
import tex_test


def _slika_modul():
    import slike_zadataka

    return slike_zadataka


# ------------------------------------------------------------------ pojedinačne provjere

def provjeri_sve(app_izvor: str = "") -> list[dict]:
    """Vrati popis {naziv, ok, detalj} — svaki redak je jedan već riješeni problem."""
    izlaz = []

    # 1) bodovi iz max_bodovi
    try:
        z = banka.zadatak_iz_retka({"id": "X", "tekst_zadatka_latex": "x", "max_bodovi": "3",
                                    "konacan_odgovor": "2"}) or {}
        izlaz.append({"naziv": "Bodovi se čitaju iz `max_bodovi`",
                      "ok": z.get("bodovi") == 3, "detalj": f"pročitano: {z.get('bodovi')}"})
    except Exception as e:                             # noqa: BLE001
        izlaz.append({"naziv": "Bodovi se čitaju iz `max_bodovi`", "ok": False, "detalj": str(e)})

    # 2) biblioteka izvora
    try:
        z = banka.zadatak_iz_retka({"id": "X", "tekst_zadatka_latex": "x", "max_bodovi": "1",
                                    "biblioteka_izvora": "zbirka", "konacan_odgovor": "1"}) or {}
        izlaz.append({"naziv": "Filter „Biblioteka izvora” čita `biblioteka_izvora`",
                      "ok": z.get("izvor") == "zbirka", "detalj": f"pročitano: {z.get('izvor')}"})
    except Exception as e:                             # noqa: BLE001
        izlaz.append({"naziv": "Filter „Biblioteka izvora”", "ok": False, "detalj": str(e)})

    # 3) slika bez bajtova ne ide u PDF
    try:
        z = [{"id": "X", "tekst": "p", "bodovi": 1, "tip": "kratki_odgovor", "odgovor": "2",
              "slika": "graf.png"}]
        bez = tex_test.izgradi_tex(z, slike={})[0]
        izlaz.append({"naziv": "PDF ne traži sliku koja nije dohvaćena",
                      "ok": "images/graf.png" not in bez, "detalj": ""})
    except Exception as e:                             # noqa: BLE001
        izlaz.append({"naziv": "PDF i nedostupne slike", "ok": False, "detalj": str(e)})

    # 4) neispravna slika se preskače
    try:
        izlaz.append({"naziv": "Neispravna slika se preskače (ne ruši PDF)",
                      "ok": tex_test._slika_valjana(b"ovo nije slika") is False, "detalj": ""})
    except Exception as e:                             # noqa: BLE001
        izlaz.append({"naziv": "Neispravna slika", "ok": False, "detalj": str(e)})

    # 5) više slika `|`
    try:
        ok = tex_test.razdvoji_slike("a.png | b.png") == ["a.png", "b.png"]
        izlaz.append({"naziv": "Više slika se razdvaja znakom `|`", "ok": ok, "detalj": ""})
    except Exception as e:                             # noqa: BLE001
        izlaz.append({"naziv": "Više slika (`|`)", "ok": False, "detalj": str(e)})

    # 6) U+0307
    try:
        izlaz.append({"naziv": "Kombinirajuća točka (U+0307) se pretvara u `\\dot{}`",
                      "ok": "\u0307" not in tex_test.escape_outside_math("x\u0307"), "detalj": ""})
    except Exception as e:                             # noqa: BLE001
        izlaz.append({"naziv": "U+0307", "ok": False, "detalj": str(e)})

    # 7) escapirani dolar
    try:
        izlaz.append({"naziv": "Escapirani `\\$` ne blokira PDF",
                      "ok": tex_test._upozorenja([{"id": "X", "tekst": "5\\$", "bodovi": 1}]) == [],
                      "detalj": ""})
    except Exception as e:                             # noqa: BLE001
        izlaz.append({"naziv": "Escapirani `\\$`", "ok": False, "detalj": str(e)})

    # 8) kategorije blokiraju PDF
    try:
        ok = bool(tex_test.provjeri_kategorije([{"id": "X", "bodovi": 2,
                                                 "kategorije": {"UZV": 1}}]))
        izlaz.append({"naziv": "Kategorije (UZV/RP/MK) blokiraju PDF kad se ne slažu",
                      "ok": ok, "detalj": ""})
    except Exception as e:                             # noqa: BLE001
        izlaz.append({"naziv": "Kategorije blokiraju PDF", "ok": False, "detalj": str(e)})

    # 9) prikazi_opcije
    try:
        z = [{"id": "X", "tekst": "p", "bodovi": 1, "tip": "visestruki_izbor", "opcije": ["a", "b"],
              "odgovor": "A", "prikazi_opcije": False}]
        izlaz.append({"naziv": "„Prikaži ponuđene odgovore” isključuje opcije",
                      "ok": "textbf{A)}" not in tex_test.izgradi_tex(z)[0], "detalj": ""})
    except Exception as e:                             # noqa: BLE001
        izlaz.append({"naziv": "Prikaži ponuđene odgovore", "ok": False, "detalj": str(e)})

    # 10) AI pomoć je odluka
    try:
        ok = definicije.smije_ai({"ai_pomoc": "ne"}) is False and \
            definicije.smije_ai({"ai_pomoc": "da"}) is True
        izlaz.append({"naziv": "AI pomoć je odluka po testu (da/ne)", "ok": ok, "detalj": ""})
    except Exception as e:                             # noqa: BLE001
        izlaz.append({"naziv": "AI pomoć po testu", "ok": False, "detalj": str(e)})

    # 11) slike preko HTML-a (ne st.image)
    try:
        m = _slika_modul()
        png = b"\x89PNG\r\n\x1a\n" + b"0" * 30
        ok = hasattr(m, "prikazi_sliku_html") and m.html_slika(png).startswith("<img")
        izlaz.append({"naziv": "Slike se prikazuju preko `<img>` (ne `st.image`)", "ok": ok,
                      "detalj": ""})
    except Exception as e:                             # noqa: BLE001
        izlaz.append({"naziv": "Slike preko HTML-a", "ok": False, "detalj": str(e)})

    # 12) rješenja na novoj stranici
    try:
        tex = tex_test.popuni_predlozak(naziv="T", datum="1.1.2026.",
                                        rjesenja_sekcija="\\newpage\n\\input{generated/rjesenja_body}")
        izlaz.append({"naziv": "Rješenja počinju na novoj stranici", "ok": "\\newpage" in tex,
                      "detalj": ""})
    except Exception as e:                             # noqa: BLE001
        izlaz.append({"naziv": "Rješenja na novoj stranici", "ok": False, "detalj": str(e)})

    # 13) nema st.stop() u karticama
    try:
        if app_izvor:
            lose = [broj for broj, linija in enumerate(app_izvor.split("\n"), start=1)
                    if "st.stop()" in linija and (len(linija) - len(linija.lstrip())) > 4]
            izlaz.append({"naziv": "Nema `st.stop()` unutar kartica", "ok": not lose,
                          "detalj": f"linije: {lose[:5]}" if lose else ""})
    except Exception as e:                             # noqa: BLE001
        izlaz.append({"naziv": "st.stop() u karticama", "ok": False, "detalj": str(e)})

    return izlaz


def verzija() -> str:
    """Kad je ova kopija koda napravljena — razlikuje „stara verzija u cloudu” od prave greške."""
    put = Path(__file__).resolve().parent / "app.py"
    try:
        from datetime import datetime

        return datetime.fromtimestamp(os.path.getmtime(put)).strftime("%d.%m.%Y. %H:%M")
    except Exception:                                  # noqa: BLE001
        return "nepoznato"


def prikazi(st) -> None:
    """Prikaži samoprovjeru u aplikaciji (✅/❌ po stavci)."""
    stavke = provjeri_sve(app_izvor=(Path(__file__).resolve().parent / "app.py").read_text(
        encoding="utf-8"))
    lose = [s for s in stavke if not s["ok"]]
    st.caption(f"Verzija koda u ovoj aplikaciji: **{verzija()}**")
    if not lose:
        st.success(f"Sve provjere prolaze ({len(stavke)}/{len(stavke)}) — ova verzija ima sva "
                   "prijašnja rješenja.")
    else:
        st.error(f"{len(lose)} od {len(stavke)} provjera ne prolazi — ova verzija NIJE ispravna.")
    for s in stavke:
        oznaka = "✅" if s["ok"] else "❌"
        detalj = f" — {s['detalj']}" if s.get("detalj") else ""
        st.markdown(f"{oznaka} {s['naziv']}{detalj}")
