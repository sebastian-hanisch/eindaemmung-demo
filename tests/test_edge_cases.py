"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): kleinste und größte Regler, alle Netztypen und Strategien, Warnungen als Fehler, kleinste Netze in allen Experimenten, Abbildungen."""

import warnings

import numpy as np
import pytest

import eid_algorithm as A
import eid_constants as C
import eid_evaluation as ev
import eid_visualization as V
from conftest import make_adj


@pytest.mark.parametrize("typ", C.ALL_TYPES)
@pytest.mark.parametrize("strategy", C.STRATEGIES)
def test_every_network_type_and_strategy_at_the_slider_corners_runs_without_warnings(typ, strategy):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        for n, c, strength, f in ((C.N_MIN, C.C_MIN, C.STRENGTH_MIN, C.F_MIN), (C.N_MIN, C.C_MAX, C.STRENGTH_MAX, C.F_MAX), (C.N_MAX, C.C_MAX, C.STRENGTH_MAX, C.F_MAX)):
            an = ev.analyse(ev.Settings(typ, n, c, 3, strength, f, strategy))
            assert 1 <= an.k < an.inst.n and len(an.vaccinated) <= an.k and len(set(an.vaccinated)) == len(an.vaccinated)
            assert all(0.0 <= an.value(s) <= 1.0 for s in C.STRATEGIES) and len(an.risk) == an.inst.n
            assert all(an.risk[i] == 0.0 for i in an.vaccinated) and ev.verdict_main(an)[0] in ("success", "info", "warning")


def test_vaccinating_nearly_everybody_leaves_a_tiny_outbreak_by_hand():
    ladj = [[1], [0, 2], [1, 3], [2]]                                                        # Pfad 0 - 1 - 2 - 3, alle Kanten bleiben
    # k = 0: 16 / 4 / 4 = 1; k = 1 (Knoten 1): {0}, {2, 3}: 1 + 4 = 5, / 3 / 4; k = 2 (1, 2): {0}, {3}: 2 / 2 / 4; k = 3 (1, 2, 0): {3}: 1 / 1 / 4
    assert A.prefix_outbreak(4, ladj, [1, 2, 0]).tolist() == pytest.approx([1.0, 5 / 12, 0.25, 0.25])
    assert len(A.order_degree(make_adj(4, [(0, 1), (1, 2), (2, 3)]), 3, np.random.default_rng(1))) == 3


def test_a_network_without_edges_has_outbreak_one_over_n_and_acquaintance_finds_nobody():
    adj = make_adj(5, [])
    ladj = [[] for _ in range(5)]
    assert A.prefix_outbreak(5, ladj, [0]).tolist() == pytest.approx([5 / 5 / 5, 4 / 4 / 5])
    assert A.reachable_count(adj) == 0
    for fn in (A.order_acquaintance, A.order_acquaintance_hub):
        assert fn(adj, 3, np.random.default_rng(1)) == []


def test_calibrate_p_handles_the_extreme_targets():
    inst = ev.make_instance(C.T_RANDOM, 80, 6, 3, layout=False)
    u, v = A.edge_arrays(inst.adj)
    p_low = A.calibrate_p(80, u, v, 0.02, 1)
    p_high = A.calibrate_p(80, u, v, 0.99, 1)
    assert 0.0 < p_low < p_high <= 1.0


def test_experiments_run_on_the_smallest_networks_without_warnings():
    seeds = C.LIVE_SEEDS[:2]
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        s = ev.strategy_rows(C.N_MIN, C.C_MIN, C.STRENGTH_MIN, fs=(0.05, 0.4), seeds=seeds, runs=10)
        k = ev.containment_rows(C.N_MIN, C.C_MAX, C.STRENGTH_MAX, seeds=seeds, runs=10)
        a = ev.acquaintance_rows(C.T_BA, C.N_MIN, C.C_MIN, 30, seeds=seeds, runs=10)
        t = ev.strength_rows(C.T_GRID, C.N_MIN, 6, 0.4, strengths=(10, 60), seeds=seeds, runs=10)
        e = ev.exact_rows(nets=2)
    assert len(s) == len(C.ALL_TYPES) and len(k) == len(C.ALL_TYPES) and len(t) == 2 and set(e["rows"]) == set(C.EXACT_KS)
    for row in s:
        assert all(0.0 <= v <= 1.0 for cells in row["cells"].values() for v in cells.values())
    for verdict in (ev.verdict_strategies(s, 0.4), ev.verdict_containment(k), ev.verdict_acquaintance(a, 0.10), ev.verdict_strengths(t, C.T_GRID, 0.4), ev.verdict_exact(e)):
        assert verdict[0] in ("success", "info", "warning") and verdict[1]


def test_figures_are_built_for_the_analysis_and_the_experiment_rows():
    an = ev.analyse(ev.Settings(C.T_COMMUNITIES, 80, 6, 3, 30, 10, C.S_ACQ_HUB))
    seeds = C.LIVE_SEEDS[:2]
    s = ev.strategy_rows(C.N_MIN, 4, 30, fs=(0.1,), seeds=seeds, runs=10, types=(C.T_RANDOM, C.T_RING))
    k = ev.containment_rows(C.N_MIN, 4, 30, seeds=seeds, runs=10, types=(C.T_RANDOM, C.T_RING))
    a = ev.acquaintance_rows(C.T_RING, C.N_MIN, 4, 30, seeds=seeds, runs=10)
    t = ev.strength_rows(C.T_RANDOM, C.N_MIN, 4, 0.1, strengths=(10, 60), seeds=seeds, runs=10)
    e = ev.exact_rows(nets=2)
    for fig in (V.build_network(an.inst, an.risk, an.vaccinated, an.settings.strategy), V.build_methods(an), V.build_strategy_bars(s, 0.1), V.build_containment(k), V.build_acquaintance(a),
                V.build_strengths(t), V.build_exact(e, ev.exact_summary)):
        assert fig.data and all(ax.fixedrange for ax in (fig.layout.xaxis, fig.layout.yaxis))


def test_the_network_figure_colours_only_unvaccinated_nodes_and_marks_the_vaccinated():
    an = ev.analyse(ev.Settings())
    fig = V.build_network(an.inst, an.risk, an.vaccinated, an.settings.strategy)
    nodes = next(tr for tr in fig.data if tr.name == "Betrieb")
    marked = next(tr for tr in fig.data if tr.name and tr.name.startswith("gesichert"))
    assert len(nodes.x) == an.inst.n - an.k and len(marked.x) == an.k


def test_de_and_pct_handle_extremes():
    assert ev.de(1234.5678, 1) == "1234,6" and ev.pct(0.0, 1) == "0,0" and ev.pct(1.0) == "100"
