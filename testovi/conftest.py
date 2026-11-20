"""
Zajedničke postavke za testove repoa `caki-testovi`.

**Zašto su testovi od 20.11.2026. ovdje, a ne u `CAKI_razvoj/testovi/`:** ta je mapa izvan gita,
pa ju re-clone nakon kvara računala 19./20.11. nije vratio — odnijela je 9 testnih datoteka faze A
i ~105 testova. Što je u repou, Push čuva.

Svaki test odavde dobiva dvije stvari:

1. **`caki-testovi` na `sys.path`** — `import definicije` radi bez obzira odakle se pytest zove.
2. **Čistu predmemoriju prije i poslije svakog testa.** Bez toga lažni Sheet iz jednog testa
   procuri u drugi: `tablice` pamti retke po `id(sheet)`, a CPython rado dodijeli isti `id`
   novom objektu nakon što je stari pospremljen. To se već dogodilo i tražilo pola dana.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _ocisti_predmemoriju() -> None:
    """Prazni `tablice` keš i Streamlitove kešove. Nijedan propust ne smije pasti test."""
    try:
        import tablice
        tablice._ocisti_cache()
    except Exception:                                   # noqa: BLE001
        pass
    try:
        import streamlit as st
        for ime in ("cache_data", "cache_resource"):
            try:
                getattr(st, ime).clear()
            except Exception:                           # noqa: BLE001
                pass
    except Exception:                                   # noqa: BLE001
        pass


@pytest.fixture(autouse=True)
def cisto_stanje():
    """Automatski: prazna predmemorija prije I poslije svakog testa."""
    _ocisti_predmemoriju()
    yield
    _ocisti_predmemoriju()


@pytest.fixture
def upis_dozvoljen():
    """Uključi pisanje u `tablice` samo za ovaj test, pa vrati kako je bilo.

    Zadano je `tablice.PISANJE = False` (ARHITEKTURA §1, pravilo 2) i svaka funkcija pisanja
    baca `PermissionError`. Testovi koji provjeravaju brisanje moraju ga uključiti namjerno.
    """
    import tablice
    prije = tablice.PISANJE
    tablice.postavi_pisanje(True)
    yield
    tablice.postavi_pisanje(prije)
