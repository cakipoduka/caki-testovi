"""
Zajedničke postavke za testove repoa `caki-testovi`.

1. Korijen repoa ide u `sys.path`, da testovi mogu `import definicije` bez trikova u svakoj datoteci.
2. Streamlitova predmemorija (`cache_data` / `cache_resource`) čisti se oko SVAKOG testa.
   Bez toga lažni Sheet iz jednog testa ostane u predmemoriji i obori sljedeći — to se već dogodilo
   u fazi A (12.11.2026.) i tada je popravak bio fixture u jednoj datoteci, što nije dovoljno.

Testovi žive UNUTAR repoa (dogovor 20.11.2026.), jer mapa `CAKI_razvoj/testovi/` nije u gitu i
kvar računala 19.11.2026. odnio je devet testnih datoteka koje Push nikad nije vidio.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

KORIJEN = pathlib.Path(__file__).resolve().parents[1]
if str(KORIJEN) not in sys.path:
    sys.path.insert(0, str(KORIJEN))


@pytest.fixture(autouse=True)
def _cisti_streamlit_cache():
    """Prije i poslije svakog testa isprazni Streamlitovu predmemoriju."""
    try:
        import streamlit as st
    except ModuleNotFoundError:                 # pragma: no cover
        yield
        return
    _cisti_tablice()
    st.cache_data.clear()
    st.cache_resource.clear()
    yield
    st.cache_data.clear()
    st.cache_resource.clear()
    _cisti_tablice()


def _cisti_tablice() -> None:
    """24.11.2026.: `tablice.py` ima i VLASTITU predmemoriju, s ključem `id(sheet)`. Python ponovo
    koristi isti id kad stari lažni Sheet nestane, pa novi test zna dobiti retke prethodnog
    (u portalu se to i dogodilo). Dosad je ovdje prolazilo slučajno."""
    try:
        import tablice
        tablice._ocisti_cache()
    except Exception:                           # noqa: BLE001
        pass


@pytest.fixture
def upis_dozvoljen():
    """Za vrijeme testa uključi `tablice.PISANJE` (lažni Sheet), poslije ga vrati na staro.

    Vraćeno 21.11.2026.: HANDOVER od 20.11. kaže da je ovaj fixture u conftestu, ali u datoteci
    na disku ga nije bilo, pa je 25 testova padalo već pri postavljanju („fixture not found").
    """
    import tablice

    staro = tablice.PISANJE
    tablice.postavi_pisanje(True)
    yield
    tablice.postavi_pisanje(staro)
