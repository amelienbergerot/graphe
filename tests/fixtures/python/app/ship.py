from app import stock as st
from app.stock import Crate


def load(c: Crate, x):
    c.fill(st.Item())
    x.heavy()
    return st.LIMIT


def sail():
    load(Crate(), None)
    return [load(c, None) for c in (Crate(),)]
