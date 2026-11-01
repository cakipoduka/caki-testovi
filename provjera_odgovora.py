"""
CAKI testovi v2 — `provjera_odgovora.py`
🧮 PROVJERA ALGEBARSKOG ODGOVORA — čista jezgra (bez Streamlita, bez tajni, bez Sheeta).

Podrijetlo: `caki-baza-zadataka/provjera_odgovora.py` (550 redaka, 23 funkcije) — **preuzeto je
jezgro** (normalizacija, jedinice, brojevi, tolerancija), a **odbačeni** su `napravi_pozivac`
(v2 ne daje `secrets` u module) i `_sigurno_razlicita_vrijednost` (zamjenjuje je numerička provjera).
Detalji: `upute/ANALIZA_G1_provjera_odgovora.md`.

Slojevi (redom):
  1. `normalizuj()` — LaTeX → običan izraz,
  2. `sympy_jednako()` — simbolička jednakost (`simplify(a - b) == 0`),
  3. `numericki_jednako()` — uvrtanje 3–5 vrijednosti (kad SymPy ne pojednostavi),
  4. `uporedi()` — spaja slojeve; **`sumnja`** kad nije sigurno (nikad lažna nula).
"""
from __future__ import annotations

import re

import model

# --- LaTeX → Python -------------------------------------------------------------

ZAMJENE = (
    (r"\\left\s*", ""), (r"\\right\s*", ""), (r"\\!", ""), (r"\\,", " "), (r"\\;", " "),
    (r"\\displaystyle", ""), (r"\\textstyle", ""),
    (r"\\mathrm\s*\{([^{}]*)\}", r"\1"),
    (r"\\text\s*\{([^{}]*)\}", r"\1"),
    (r"\\cdot", "*"), (r"\\times", "*"), (r"\\div", "/"),
    (r"\\pi", "pi"), (r"\\infty", "oo"),
    (r"\\degree", "*pi/180"), (r"\\circ", "*pi/180"),
    (r"\\cup", "|"), (r"\\cap", "&"),
    (r"\\leq?", "<="), (r"\\geq?", ">="), (r"\\neq?", "!="),
    (r"\\sqrt\s*\{([^{}]*)\}", r"sqrt(\1)"),
    (r"\\sqrt\s*\[(\d+)\]\s*\{([^{}]*)\}", r"root(\2, \1)"),
)

MJERNE = ("cm", "mm", "dm", "km", "m", "kg", "g", "t", "l", "dl", "ml",
          "s", "min", "h", "km/h", "m/s", "cm2", "cm3", "m2", "m3", "kn", "eur", "%")


def skini_omotace(tekst) -> str:
    """Skini `$…$`, `\\(…\\)`, `\\[…\\]`, `$$…$$` (v1 `skini_omotace`)."""
    s = model.tekst(tekst)
    for lijevo, desno in (("$$", "$$"), ("\\(", "\\)"), ("\\[", "\\]"),
                          ("$", "$")):
        if s.startswith(lijevo) and s.endswith(desno) and len(s) > len(lijevo) + len(desno):
            s = s[len(lijevo):-len(desno)].strip()
    return s


def _razrijesi_latex(tekst: str) -> str:
    """Iterativno razriješi `\\mathrm{}`, `\\text{}`, `\\frac{}{}` — i kad su ugniježđeni."""
    s = model.tekst(tekst)
    for _ in range(25):
        novo = re.sub(r"\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}", r"((\1)/(\2))", s)
        novo = re.sub(r"\\(?:mathrm|text|operatorname|mathit)\s*\{([^{}]*)\}", r"\1", novo)
        novo = re.sub(r"\\sqrt\s*\{([^{}]*)\}", r"sqrt(\1)", novo)
        if novo == s:
            break
        s = novo
    return s


def normalizuj(tekst) -> str:
    """LaTeX iz baze → običan izraz za usporedbu (v1 `normalizuj`, prošireno).

    Rješava slučajeve iz §1: ugniježđeni `\\mathrm{}`, `\\frac78`, `\\degree`, `\\cup`, `\\infty`.
    """
    s = _razrijesi_latex(skini_omotace(tekst))
    for obrazac, zamjena in ZAMJENE:
        s = re.sub(obrazac, zamjena, s)

    # \frac78 (bez zagrada) i \frac{7}{8}
    s = re.sub(r"\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}", r"(\1)/(\2)", s)
    s = re.sub(r"\\frac\s*(\d)\s*(\d)", r"(\1)/(\2)", s)

    s = s.replace("{,}", "{,}").replace("\\%", "%")
    s = s.replace(",", ".").replace(" ", "").replace("{", "").replace("}", "")
    s = s.replace("^", "**").replace("·", "*").replace("×", "*").replace("÷", "/")
    s = re.sub(r"(?<=\d)\s*(cm|mm|dm|km|kg|min|kn|eur|m|g|l|s|h)\b", "", s)
    return s.strip()


def bez_jedinice(tekst) -> str:
    """Ukloni mjernu jedinicu (`5 cm` → `5`) — v1 `razdvoji_jedinicu` + `_je_mjerna`."""
    s = model.tekst(tekst).lower().replace(" ", "")
    for jed in sorted(MJERNE, key=len, reverse=True):
        if s.endswith(jed) and len(s) > len(jed):
            return s[: -len(jed)]
    return s


# --- SymPy ----------------------------------------------------------------------

def _sympy():
    try:
        import sympy

        return sympy
    except Exception:                                   # noqa: BLE001
        return None


def _implicitno_mnozenje(izraz: str) -> str:
    """`2x` → `2*x`, `x(` → `x*(`, `)(` → `)*(`, `2(pi)` → `2*(pi)`.

    SymPy traži eksplicitno `*`; učenici (i baza) pišu bez njega.
    """
    s = model.tekst(izraz)
    s = re.sub(r"(\d)\s*([a-zA-Z(])", r"\1*\2", s)     # 2x, 3(x+1)
    s = re.sub(r"([a-zA-Z)])\s*(\()", r"\1*\2", s)     # x(, )(
    s = re.sub(r"([a-zA-Z])\s*([a-zA-Z])", r"\1*\2", s)  # xy -> x*y
    s = s.replace("**", "^^").replace("*", "*").replace("^^", "**")
    return s


def u_sympy(izraz: str):
    """Tekst → SymPy izraz. `None` ako nije moguće (tada slijedi `sumnja`)."""
    sp = _sympy()
    if sp is None:
        return None
    tekst = model.tekst(izraz)
    if not tekst:
        return None
    try:
        from sympy.parsing.latex import parse_latex

        return parse_latex(tekst)
    except Exception:                                   # noqa: BLE001 — antlr nije tu
        pass
    try:
        lokalno = {"sqrt": sp.sqrt, "pi": sp.pi, "oo": sp.oo, "root": sp.root,
                   "Abs": sp.Abs, "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
                   "log": sp.log, "ln": sp.log, "exp": sp.exp, "E": sp.E}
        return sp.sympify(_implicitno_mnozenje(normalizuj(tekst)), locals=lokalno)
    except Exception:                                   # noqa: BLE001
        return None


def sympy_jednako(tocan, odgovor) -> bool | None:
    """Simbolička jednakost. `None` = ne mogu odlučiti."""
    a, b = u_sympy(tocan), u_sympy(odgovor)
    if a is None or b is None:
        return None
    try:
        sp = _sympy()
        razlika = sp.simplify(a - b)
        if razlika == 0:
            return True
        if sp.simplify(razlika).is_zero is True:
            return True
        if getattr(razlika, "is_zero", None) is False:
            return False
    except Exception:                                   # noqa: BLE001
        return None
    return None


# --- numerička provjera ---------------------------------------------------------

def _vrijednosti(sp, simbol) -> list:
    """3–5 „ružnih" racionalnih vrijednosti — izbjegavaju 0 i ±1 (lažne jednakosti)."""
    from sympy import Rational

    return [Rational(2, 3), Rational(5, 7), Rational(11, 13), Rational(-3, 4)]


def numericki_jednako(tocan, odgovor, *, tolerancija: float = 1e-9) -> bool | None:
    """Uvrsti iste vrijednosti u oba izraza i usporedi. `None` = ne mogu odlučiti."""
    a, b = u_sympy(tocan), u_sympy(odgovor)
    sp = _sympy()
    if a is None or b is None or sp is None:
        return None
    try:
        simboli = sorted(set(a.free_symbols) | set(b.free_symbols), key=lambda s: s.name)
        if len(simboli) > 2:
            return None                                 # previše varijabli — prepusti profesoru
        vrijednosti = _vrijednosti(sp, None)[:3]
        for i, v in enumerate(vrijednosti):
            zamjena = {simbol: v if i % 2 == 0 else 1 / v for simbol in simboli}
            try:
                va = complex(a.subs(zamjena).evalf())
                vb = complex(b.subs(zamjena).evalf())
            except Exception:                           # noqa: BLE001
                return None
            if abs(va - vb) > tolerancija * max(1.0, abs(va)):
                return False
        return True
    except Exception:                                   # noqa: BLE001
        return None


# --- spajanje slojeva -----------------------------------------------------------

def _kao_broj(tekst) -> float | None:
    try:
        return float(model.tekst(tekst).replace(",", ".").replace(" ", ""))
    except (TypeError, ValueError):
        return None


def uporedi(tocan, odgovor, *, tolerancija: float = 1e-9) -> dict:
    """Spoji slojeve. Vraća `{"tocno": True/False/None, "nacin": ..., "zasto": ...}`.

    `tocno = None` znači **sumnja** (profesor odlučuje) — nikad lažna nula.
    """
    t = model.tekst(tocan)
    o = model.tekst(odgovor)
    if not o.strip():
        return {"tocno": False, "nacin": "prazno", "zasto": "Nema odgovora."}
    if not t.strip():
        return {"tocno": None, "nacin": "sumnja", "zasto": "Zadatak nema konačan odgovor."}

    # 0) jednako nakon normalizacije
    nt, no = normalizuj(t), normalizuj(o)
    if nt and nt.lower() == no.lower():
        return {"tocno": True, "nacin": "string", "zasto": "Isto nakon normalizacije."}

    # 1) brojevi (s jedinicama i bez)
    bt, bo = _kao_broj(bez_jedinice(t)), _kao_broj(bez_jedinice(o))
    if bt is not None and bo is not None:
        if abs(bt - bo) <= tolerancija * max(1.0, abs(bt)):
            return {"tocno": True, "nacin": "broj", "zasto": f"{bt} = {bo} (tolerancija)."}
        return {"tocno": False, "nacin": "broj", "zasto": f"{bt} != {bo}."}

    # 2) SymPy
    rez = sympy_jednako(t, o)
    if rez is True:
        return {"tocno": True, "nacin": "sympy", "zasto": "Simbolički jednaki."}
    if rez is False:
        return {"tocno": False, "nacin": "sympy", "zasto": "Simbolički različiti."}

    # 3) numerička provjera
    rez_n = numericki_jednako(t, o, tolerancija=tolerancija)
    if rez_n is True:
        return {"tocno": True, "nacin": "numericki", "zasto": "Slažu se na više točaka."}
    if rez_n is False:
        return {"tocno": False, "nacin": "numericki", "zasto": "Razlikuju se numerički."}

    # 4) sumnja — profesor (ili AI kao treći sloj)
    return {"tocno": None, "nacin": "sumnja", "zasto": "Nije moguće sigurno provjeriti."}
