"""Verdikte und Messhilfen an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier."""

import dataclasses
import math

import numpy as np
import pytest

import eid_algorithm as A
import eid_constants as C
import eid_evaluation as ev

NAN = float("nan")


def _an(values, strategy=C.S_RANDOM, k=6, base=0.3, p=0.239, cost=0.0, edges=True):
    """Analyse mit handgesetzten Ausbruchsgrößen bei k Impfungen (Strategie -> Wert; nicht genannte wie Zufall 0,2) auf einem echten Netz mit n = 60."""
    real = ev.analyse(ev.Settings(C.T_RANDOM, C.N_MIN, 4, 3, 30, 10, strategy))
    inst = real.inst if edges else dataclasses.replace(real.inst, adj=tuple(() for _ in real.inst.adj))
    full = {s: 0.2 for s in C.STRATEGIES}
    full.update(values)
    curves = {s: np.array([base] * k + [v]) for s, v in full.items()}
    st = dataclasses.replace(real.settings, strategy=strategy, f=10)
    return dataclasses.replace(real, inst=inst, settings=st, p=p, k=k, base=base, curves=curves, cost=cost)


def test_de_pct_k_of_and_at_helpers():
    assert ev.de(1.26, 1) == "1,3" and ev.de(0.9487, 3) == "0,949" and ev.de(3, 0) == "3" and ev.de(NAN, 2) == "–" and ev.de(None) == "–"
    assert ev.pct(0.1234, 1) == "12,3" and ev.pct(0.5) == "50"
    assert ev.k_of(250, 0.1) == 25 and ev.k_of(60, 0.01) == 1 and ev.k_of(10, 1.0) == 9 and ev.k_of(10, 0.0) == 1
    assert ev.at([0.3, 0.2, 0.1], 1) == 0.2 and ev.at([0.3, 0.2, 0.1], 9) == 0.1


def test_best_strategy_picks_the_smallest_and_breaks_ties_by_order():
    an = _an({C.S_DEGREE: 0.05, C.S_ADAPTIVE: 0.05, C.S_ACQ: 0.07})
    assert an.best() == C.S_DEGREE
    assert _an({C.S_DEGREE: 0.05, C.S_ADAPTIVE: 0.05 - 1e-14}).best() == C.S_DEGREE            # Rauschen gilt als gleich
    assert _an({}).best() == C.S_RANDOM


def test_main_verdict_for_random_names_the_best_strategy():
    kind, text = ev.verdict_main(_an({C.S_DEGREE: 0.05, C.S_RANDOM: 0.2}, cost=0.0))
    assert kind == "info"
    assert text == ("Ohne Impfung erreicht ein Ausbruch im Mittel 30 % der Betriebe (p = 0,239). Mit 6 gesicherten Betrieben (10 %) nach „Zufall“ bleiben 20,0 %. "
                    "Die beste Strategie wäre hier „Grad“ mit 5,0 % (Faktor 4,0 besser). Wissen: im Mittel 0 Abfragen.")
    kind, text = ev.verdict_main(_an({C.S_RANDOM: 0.1, C.S_DEGREE: 0.2, C.S_ADAPTIVE: 0.2, C.S_BETWEENNESS: 0.2, C.S_CORE: 0.2, C.S_ACQ: 0.2, C.S_ACQ_HUB: 0.2}))
    assert kind == "info" and "Die beste Strategie wäre hier „Zufall“ mit 10,0 %." in text and "Faktor" not in text


def test_main_verdict_success_info_warning_by_thresholds():
    kind, text = ev.verdict_main(_an({C.S_DEGREE: 0.05}, strategy=C.S_DEGREE, cost=60.0))
    assert kind == "success" and "nach „Grad“ bleiben 5,0 %." in text and "Zufall käme auf 20,0 %, die Strategie ist 4,0-mal so gut." in text and "Wissen: im Mittel 60 Abfragen." in text
    assert ev.verdict_main(_an({C.S_DEGREE: 0.0500001}, strategy=C.S_DEGREE))[0] == "info"                  # knapp über der Eindämmungsgrenze 5 %
    kind, text = ev.verdict_main(_an({C.S_DEGREE: 0.15}, strategy=C.S_DEGREE))
    assert kind == "info" and "1,3-mal so gut" in text
    kind, text = ev.verdict_main(_an({C.S_BETWEENNESS: 0.23}, strategy=C.S_BETWEENNESS))
    assert kind == "warning" and "**schlechter als Zufall** (20,0 %)" in text                              # 0,23 > 1,10 · 0,2 = 0,22
    kind, text = ev.verdict_main(_an({C.S_BETWEENNESS: 0.22}, strategy=C.S_BETWEENNESS))
    assert kind == "info" and "etwa so gut wie Zufall" in text                                             # genau 10 % über Zufall: noch keine Warnung
    kind, text = ev.verdict_main(_an({C.S_CORE: 0.197}, strategy=C.S_CORE))
    assert "etwa so gut wie Zufall" in text                                                                 # 0,197 ≥ 0,98 · 0,2 = 0,196
    kind, text = ev.verdict_main(_an({C.S_CORE: 0.195}, strategy=C.S_CORE))
    assert "1,0-mal so gut" in text


def test_main_verdict_with_zero_outbreak_and_without_edges():
    kind, text = ev.verdict_main(_an({C.S_DEGREE: 0.0}, strategy=C.S_DEGREE))
    assert kind == "success" and "bleiben 0,0 %. Zufall käme auf 20,0 %." in text and "-mal" not in text
    kind, text = ev.verdict_main(_an({}, edges=False))
    assert kind == "warning" and "keine Kanten" in text


# --- Verdikte der Experimente -----------------------------------------------------------------------------------------------------------------------


def _cells(random, degree, others=None, f=0.10):
    cells = {s: {f: 0.5 * random} for s in C.STRATEGIES}
    cells[C.S_RANDOM] = {f: random}
    cells[C.S_DEGREE] = {f: degree}
    for s, v in (others or {}).items():
        cells[s] = {f: v}
    return cells


def test_verdict_strategies_counts_halving_and_names_strongest_weakest_and_worse():
    rows = [{"typ": "A", "base": 0.3, "cells": _cells(0.20, 0.02)}, {"typ": "B", "base": 0.3, "cells": _cells(0.16, 0.08, {C.S_BETWEENNESS: 0.20})}, {"typ": "C", "base": 0.3, "cells": _cells(0.12, 0.11)}]
    kind, text = ev.verdict_strategies(rows, 0.10)
    assert kind == "info"
    assert text == ("Bei 10 % Impfanteil senkt die Gradregel die Ausbruchsgröße in 2 von 3 Netztypen auf höchstens die Hälfte von Zufall; am stärksten in „A“ (2,0 % gegen 20,0 %), am schwächsten in „C“ (11,0 % gegen 12,0 %). "
                    "Schlechter als Zufall: „Betweenness“ in „B“.")
    clean = ev.verdict_strategies(rows[:1], 0.10)[1]
    assert "Keine Strategie ist in einem Netztyp schlechter als Zufall." in clean and "in 1 von 1 Netztypen" in clean
    assert ev.verdict_strategies(rows, 0.20)[0] == "warning" and ev.verdict_strategies([], 0.1)[0] == "warning"
    edge = ev.verdict_strategies([{"typ": "A", "base": 0.3, "cells": _cells(0.20, 0.10)}], 0.10)[1]
    assert "in 1 von 1" in edge                                                                           # genau die Hälfte zählt mit
    assert "Schlechter als" not in ev.verdict_strategies([{"typ": "A", "base": 0.3, "cells": _cells(0.20, 0.10, {C.S_CORE: 0.204})}], 0.10)[1]     # 2 % über Zufall gilt als gleich


def _frow(typ, **values):
    f = {s: 0.2 for s in C.STRATEGIES}
    f.update({{"deg": C.S_DEGREE, "rand": C.S_RANDOM, "adp": C.S_ADAPTIVE}[k]: v for k, v in values.items()})
    return {"typ": typ, "fstar": f}


def test_verdict_containment_picks_best_and_worst_rows_and_prints_over_forty():
    rows = [_frow("A", deg=0.03, rand=1.0, adp=0.04), _frow("B", deg=0.16, rand=0.23, adp=0.158)]
    kind, text = ev.verdict_containment(rows)
    assert kind == "info"
    assert text == ("Um die Ausbruchsgröße auf höchstens 5 % zu drücken, braucht im günstigsten Netztyp („A“) die beste Strategie („Grad“) 3 % Impfanteil, Zufall über 40 %; "
                    "im ungünstigsten („B“) braucht die beste („Grad adaptiv“) 16 %, Zufall 23 %.")
    assert ev.verdict_containment([])[0] == "warning"
    assert "über 40 %" not in ev.verdict_containment([_frow("A", deg=0.4, rand=0.4, adp=0.4)])[1]       # genau 40 % ist erreicht


def _acq(random, acq, hub, deg, typ="X"):
    fs = [0.05, 0.10]
    return {"typ": typ, "fs": fs, "base": 0.3, "curves": {C.S_RANDOM: [0.3, random], C.S_ACQ: [0.3, acq], C.S_ACQ_HUB: [0.3, hub], C.S_DEGREE: [0.3, deg]}}


def test_gap_closed_and_verdict_acquaintance_by_hand():
    res = _acq(0.20, 0.12, 0.04, 0.02)
    assert ev.gap_closed(res, C.S_ACQ, 0.10) == pytest.approx((0.20 - 0.12) / 0.18) and ev.gap_closed(res, C.S_ACQ_HUB, 0.10) == pytest.approx(0.16 / 0.18)
    kind, text = ev.verdict_acquaintance(res)
    assert kind == "info" and text == ("In „X“ bei 10 % Impfanteil: Zufall 20,0 %, Grad 2,0 %. Die Bekannten-Impfung (12,0 %) schließt 44 % dieser Lücke, "
                                       "die Variante mit dem Nachbarn des höchsten Grades (4,0 %) 89 %.")
    flat = _acq(0.20, 0.19, 0.20, 0.21)
    assert math.isnan(ev.gap_closed(flat, C.S_ACQ, 0.10)) and "keine Lücke" in ev.verdict_acquaintance(flat)[1]
    assert ev.verdict_acquaintance(res, f=0.5)[0] == "warning"


def test_verdict_strengths_names_best_and_detects_a_changing_best_strategy():
    def row(strength, base, rand, deg, adp):
        cells = {s: 0.3 for s in C.STRATEGIES}
        cells.update({C.S_RANDOM: rand, C.S_DEGREE: deg, C.S_ADAPTIVE: adp})
        return {"strength": strength, "base": base, "cells": cells}

    same = [row(10, 0.1, 0.05, 0.03, 0.02), row(30, 0.3, 0.12, 0.06, 0.05)]
    kind, text = ev.verdict_strengths(same, "Ring mit Abkürzungen", 0.10)
    assert kind == "info" and text == ("In „Ring mit Abkürzungen“ bei 10 % Impfanteil: bei 10 %: ohne Impfung 10 %, Zufall 5,0 %, Grad 3,0 %, beste „Grad adaptiv“ (2,0 %); "
                                       "bei 30 %: ohne Impfung 30 %, Zufall 12,0 %, Grad 6,0 %, beste „Grad adaptiv“ (5,0 %). Die beste Strategie ist in allen Ausbreitungsstärken „Grad adaptiv“.")
    changed = same + [row(60, 0.6, 0.12, 0.04, 0.05)]
    assert "bei 60 %: ohne Impfung 60 %, Zufall 12,0 %, Grad 4,0 %, beste „Grad“ (4,0 %). Die beste Strategie wechselt mit der Ausbreitungsstärke." in ev.verdict_strengths(changed, "X", 0.1)[1]
    assert ev.verdict_strengths([], "X", 0.1)[0] == "warning"


def test_exact_summary_and_verdict_by_hand():
    rows = [{"base": 0.5, "optimum": 0.2, "greedy": 0.2, "degree": 0.22, "random": 0.3}, {"base": 0.5, "optimum": 0.1, "greedy": 0.12, "degree": 0.15, "random": 0.2}]
    res = {"rows": {2: rows}, "nets": 2, "p": 0.5}
    s = ev.exact_summary(res, 2)
    assert s["base"] == 0.5 and s["optimum"] == pytest.approx(0.15) and s["greedy"] == pytest.approx(0.16) and s["degree"] == pytest.approx(0.185) and s["random"] == pytest.approx(0.25)
    assert s["greedy_hits"] == 1 and s["nets"] == 2 and s["degree_over"] == pytest.approx((0.1 + 0.5) / 2) and s["worst_greedy"] == pytest.approx(0.1 / 0.12)
    kind, text = ev.verdict_exact(res)
    assert kind == "info" and text.endswith("k = 2: Optimum 15,0 %, Greedy 16,0 % (trifft das Optimum in 1 von 2 Netzen), Grad 18,5 % (im Median 30,0 % über dem Optimum), Zufall 25,0 %.")
    assert "Auf 2 kleinen Netzen (9 Betriebe, 12 Partnerschaften, p = 0,5; ohne Impfung 50,0 %)" in text
    assert ev.verdict_exact({"rows": {}, "nets": 0, "p": 0.5})[0] == "warning"


def test_strategy_orders_have_independent_streams_and_the_right_lengths():
    adj = ev.make_instance(C.T_RANDOM, 60, 4, 1, layout=False).adj
    full = ev.strategy_orders(adj, 5, 7)
    part = ev.strategy_orders(adj, 5, 7, names=(C.S_DEGREE,))
    assert full[C.S_DEGREE] == part[C.S_DEGREE] and all(len(full[s]) == C.DRAWS[s] and all(len(o) == 5 for o in full[s]) for s in C.STRATEGIES)
    fast = ev.strategy_orders(adj, 5, 7, draws=C.EXP_DRAWS)
    assert all(len(fast[s]) == C.EXP_DRAWS[s] for s in C.STRATEGIES) and fast[C.S_RANDOM] == full[C.S_RANDOM][: C.EXP_DRAWS[C.S_RANDOM]]


def test_knowledge_cost_is_reported_for_every_strategy():
    for s in C.STRATEGIES:
        assert A.knowledge_cost(s, 100, 300, 10) >= 0.0


def test_orders_do_not_depend_on_kmax_or_on_the_number_of_draws():
    adj = ev.make_instance(C.T_BA, 60, 4, 1, layout=False).adj
    short = ev.strategy_orders(adj, 5, 7)
    long = ev.strategy_orders(adj, 12, 7)
    for s in C.STRATEGIES:
        assert [o[:5] for o in long[s]] == short[s], s
    fewer = ev.strategy_orders(adj, 5, 7, draws=C.EXP_DRAWS)
    for s in C.STRATEGIES:
        assert fewer[s] == short[s][: C.EXP_DRAWS[s]], s
