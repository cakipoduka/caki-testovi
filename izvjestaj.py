"""
CAKI testovi v2 — `izvjestaj.py`
📄 IZVJEŠTAJ ZA RODITELJE (i profesora) — jedan učenik, jedan dokument.

Zašto HTML, a ne PDF: PDF knjižnica (reportlab) dolazi bez fontova za **č, ć, ž, š, đ** — slova bi
ispala kao kvadratići ili bi ih trebalo transliterirati („Caki” umjesto „Čaki”). HTML nema taj
problem: otvori se u browseru i ispiše kao PDF (`Ctrl+P` → *Save as PDF*), s ispravnim hrvatskim
znakovima i bez ijednog dodatnog paketa.

Sadržaj: učenik · testovi (bodovi, postotak) · predlog ocjene · priloženi radovi · napomena.
Sve se **escapira** — tekst zadatka iz baze može sadržavati `<` i ostalo, ne smije pokvariti dokument.
"""
from __future__ import annotations

import html

import brend
import model
import zakljucna

CSS = """
body { font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 32px; color: #111; }
h1 { font-size: 22px; margin: 0 0 4px 0; }
h2 { font-size: 15px; margin: 22px 0 8px 0; color: #333; border-bottom: 1px solid #ddd; padding-bottom: 4px; }
.meta { color: #555; font-size: 13px; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { border: 1px solid #ccc; padding: 6px 8px; text-align: left; }
th { background: #f3f3f3; }
.big { font-size: 20px; font-weight: 600; }
.pass { color: #0a6b2d; } .fail { color: #a11; }
.note { font-size: 12px; color: #555; margin-top: 18px; }
@media print { body { margin: 12mm; } .noprint { display: none; } }
.brand { font-size: 15px; font-weight: 600; }
.slogan { font-size: 12px; color: #666; }
.foot { margin-top: 26px; border-top: 1px solid #ddd; padding-top: 8px; font-size: 11px; color: #666; text-align: center; }
"""


def _e(vrijednost) -> str:
    """HTML-escape — banka može sadržavati `<`, `&`, navodnike."""
    return html.escape(model.tekst(vrijednost), quote=True)


def _postotak(bodovi, maks) -> int:
    b, m = model.broj(bodovi), model.broj(maks)
    return int(round(100 * b / m)) if m else 0


def html_izvjestaj(*, ucenik: dict, testovi: list[dict], radovi: list[dict] | None = None,
                   napomena: str = "", datum: str = "") -> str:
    """Vrati cijeli HTML dokument za jednog učenika.

    `testovi` = [{"naziv", "bodovi", "maks", "postotak", "datum"}], `radovi` = redci iz taba `Radovi`.
    """
    ucenik = ucenik or {}
    ime = model.tekst(ucenik.get("ime")) or model.tekst(ucenik.get("ucenik_id")) or "Učenik"
    sifra = model.tekst(ucenik.get("ucenik_id"))
    grupa = model.tekst(ucenik.get("grupa"))

    postoci = [t.get("postotak", _postotak(t.get("bodovi"), t.get("maks"))) for t in (testovi or [])]
    prosjek = int(round(sum(postoci) / len(postoci))) if postoci else 0

    b = brend.ucitaj()
    kontakt = brend.kontakt_redak(b)

    dijelovi = [
        "<!DOCTYPE html><html lang='hr'><head><meta charset='utf-8'>",
        f"<title>Izvještaj — {_e(ime)}</title><style>{CSS}</style></head><body>",
        "<div class='noprint' style='margin-bottom:12px'>",
        "<b>Za PDF:</b> Ctrl+P → <i>Save as PDF</i> (ili Ispis → Spremi kao PDF).</div>",
        f"<div class='brand'>{_e(b.get('naziv'))}</div>",
        (f"<div class='slogan'>{_e(b.get('slogan'))}</div>" if model.tekst(b.get("slogan")) else ""),
        f"<h1>Izvještaj — {_e(ime)}</h1>",
        f"<div class='meta'>Šifra: {_e(sifra)}"
        + (f" · Grupa: {_e(grupa)}" if grupa else "")
        + (f" · {_e(datum)}" if datum else "")
        + "</div>",
    ]

    if postoci:
        boja = "pass" if prosjek >= 50 else "fail"
        dijelovi.append(
            f"<h2>Ostvareni rezultat</h2><div class='big {boja}'>{_e(zakljucna.ostvareno(prosjek))}"
            "</div><div class='meta'>Iz "
            f"{len(postoci)} predanih testova. Rezultat pokazuje koliko je usvojeno — "
            "služi kao putokaz za dalje, ne kao ocjena.</div>")
    else:
        dijelovi.append("<h2>Ostvareni rezultat</h2><div class='meta'>Nema predanih testova.</div>")

    dijelovi.append("<h2>Testovi</h2>")
    if testovi:
        dijelovi.append("<table><tr><th>Test</th><th>Datum</th><th>Bodovi</th>"
                        "<th>Postotak</th></tr>")
        for t in testovi:
            p = t.get("postotak", _postotak(t.get("bodovi"), t.get("maks")))
            dijelovi.append(
                f"<tr><td>{_e(t.get('naziv'))}</td><td>{_e(t.get('datum')) or '—'}</td>"
                f"<td>{model.broj(t.get('bodovi')):g} / {model.broj(t.get('maks')):g}</td>"
                f"<td>{p} %</td></tr>")
        dijelovi.append("</table>")
    else:
        dijelovi.append("<div class='meta'>Nema testova.</div>")

    if radovi:
        dijelovi.append("<h2>Priloženi radovi</h2><table><tr><th>Naziv</th>"
                        "<th>Pregledano</th></tr>")
        for r in radovi:
            pregled = "✅" if model.tekst(r.get("potvrdjeno")) else "⏳ čeka"
            dijelovi.append(f"<tr><td>{_e(r.get('naziv')) or 'Rad'}</td><td>{pregled}</td></tr>")
        dijelovi.append("</table>")

    if model.tekst(napomena):
        dijelovi.append(f"<h2>Napomena</h2><div>{_e(napomena)}</div>")

    if kontakt:
        dijelovi.append(f"<div class='foot'>{_e(kontakt)}"
                        + (f" · {_e(b.get('adresa'))}" if model.tekst(b.get("adresa")) else "")
                        + "</div>")
    dijelovi.append("<div class='note'>Izvještaj je generiran iz CAKI sustava testiranja. "
                    "Bodovi su iz predanih radova; prazan zadatak nosi 0 bodova.</div>")
    dijelovi.append("</body></html>")
    return "".join(dijelovi)


def ime_datoteke(ucenik: dict) -> str:
    """Sigurno ime datoteke: bez kvačica i razmaka (isti princip kao kod radova)."""
    ime = model.tekst((ucenik or {}).get("ime")) or model.tekst((ucenik or {}).get("ucenik_id")) or "ucenik"
    for lose, dobro in {"č": "c", "ć": "c", "ž": "z", "š": "s", "đ": "d",
                        "Č": "C", "Ć": "C", "Ž": "Z", "Š": "S", "Đ": "D"}.items():
        ime = ime.replace(lose, dobro)
    ocisceno = "".join(z if (z.isalnum() or z in "-_") else "_" for z in ime)
    return (ocisceno or "ucenik") + "_izvjestaj.html"


def prikazi_preuzimanje(st, *, ucenik: dict, testovi: list[dict], radovi=None,
                        napomena: str = "", kljuc: str = "") -> None:
    """Gumb za preuzimanje HTML izvještaja (radi bez ijednog paketa i bez fontova)."""
    dokument = html_izvjestaj(ucenik=ucenik, testovi=testovi, radovi=radovi,
                              napomena=napomena, datum=model.sada().strftime("%d.%m.%Y."))
    st.download_button(
        "📄 Izvještaj za roditelje (HTML → ispiši kao PDF)",
        data=dokument.encode("utf-8"),
        file_name=ime_datoteke(ucenik),
        mime="text/html",
        key="v2_izv_" + (kljuc or model.tekst((ucenik or {}).get("ucenik_id")) or "x"),
    )
