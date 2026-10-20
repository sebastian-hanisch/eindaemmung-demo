"""Einheiten des Kerns an Mini-Instanzen mit von Hand gerechneten Werten (DEMO-PLAYBOOK §1b)."""

import itertools
import warnings

import numpy as np
import pytest

import eid_algorithm as A
import eid_constants as C
from conftest import full_live, make_adj


def test_edge_arrays_and_degrees(path3):
    u, v = A.edge_arrays(path3)
    assert u.tolist() == [0, 1] and v.tolist() == [1, 2] and A.degrees(path3) == [1, 2, 1]
    u, v = A.edge_arrays(make_adj(3, []))
    assert len(u) == 0 and len(v) == 0


def test_snapshots_shape_probability_and_determinism():
    s = A.snapshots(1000, 0.3, 50, 7)
    assert s.shape == (50, 1000) and s.dtype == bool and s.mean() == pytest.approx(0.3, abs=0.01)
    assert np.array_equal(s, A.snapshots(1000, 0.3, 50, 7)) and not np.array_equal(s, A.snapshots(1000, 0.3, 50, 8))
    assert A.snapshots(5, 0.0, 3, 1).sum() == 0 and A.snapshots(5, 1.0, 3, 1).all()


def test_live_lists_keep_exactly_the_masked_edges(path3):
    u, v = A.edge_arrays(path3)
    lls = A.live_lists(3, u, v, np.array([[True, False], [False, False], [True, True]]))
    assert lls[0] == [[1], [0], []] and lls[1] == [[], [], []] and lls[2] == [[1], [0, 2], [1]]


def test_prefix_outbreak_hand_values_on_the_path(path3):
    # k = 0: eine Komponente der Größe 3: 9 / 3 / 3 = 1; k = 1 (Mitte): 1 + 1 = 2, / 2 / 3 = 1/3; k = 2 (Mitte, 0): Rest {2}: 1 / 1 / 3 = 1/3; k = 3: 0
    assert A.prefix_outbreak(3, full_live(path3), [1, 0, 2]).tolist() == pytest.approx([1.0, 1 / 3, 1 / 3, 0.0])
    assert A.prefix_outbreak(3, [[], [], []], []).tolist() == pytest.approx([3 / 3 / 3])               # drei Einzelne: 3 / 3 / 3 = 1/3


def test_prefix_outbreak_star_and_two_triangles(star5, two_triangles):
    assert A.prefix_outbreak(5, full_live(star5), [0]).tolist() == pytest.approx([1.0, 0.2])
    assert A.prefix_outbreak(5, full_live(star5), [1]).tolist() == pytest.approx([1.0, 16 / 4 / 5])    # Blatt geimpft: Rest ist ein Stern mit 4 Knoten
    assert A.prefix_outbreak(6, full_live(two_triangles), [2]).tolist() == pytest.approx([1.0, 13 / 30])
    # erst 3, dann 2 geimpft: nach 3 bleiben {0,1,2} und {4,5}: 9 + 4 = 13, / 5 / 6; nach 3 und 2 bleiben {0,1} und {4,5}: 4 + 4 = 8, / 4 / 6
    assert A.prefix_outbreak(6, full_live(two_triangles), [3, 2]).tolist() == pytest.approx([1.0, 13 / 30, 8 / 24])


def test_prefix_outbreak_rejects_bad_orders(path3):
    for bad in ([1, 1], [3], [-1]):
        with pytest.raises(ValueError):
            A.prefix_outbreak(3, full_live(path3), bad)


def test_prefix_outbreak_sum_of_squares_falls_in_k_and_matches_the_set_version(two_triangles):
    rng = np.random.default_rng(3)
    u, v = A.edge_arrays(two_triangles)
    for _ in range(20):
        mask = rng.random((1, len(u))) < 0.6
        ladj = A.live_lists(6, u, v, mask)[0]
        order = rng.permutation(6).tolist()
        out = A.prefix_outbreak(6, ladj, order)
        sums = [out[i] * (6 - i) * 6 for i in range(len(out))]                               # Summe der quadrierten Komponentengrößen: fällt in k (die Ausbruchsgröße selbst nicht immer)
        assert all(sums[i] >= sums[i + 1] - 1e-9 for i in range(len(sums) - 1)) and out[-1] == 0.0
        for k in range(1, 6):
            assert out[k] == pytest.approx(A.prefix_outbreak(6, ladj, sorted(order[:k]))[-1])


def test_outbreak_size_averages_over_snapshots(path3):
    u, v = A.edge_arrays(path3)
    lls = A.live_lists(3, u, v, np.array([[True, True], [False, False]]))
    assert A.outbreak_size(3, lls, []) == pytest.approx((1.0 + 1 / 3) / 2)
    assert A.outbreak_size(3, lls, [1]) == pytest.approx(1 / 3)
    assert A.outbreak_size(3, lls, [0, 1, 2]) == 0.0


def test_node_risk_hand_values(path3, two_triangles):
    assert A.node_risk(3, [full_live(path3)], [1]).tolist() == pytest.approx([0.5, 0.0, 0.5])
    assert A.node_risk(3, [full_live(path3), [[], [], []]], []).tolist() == pytest.approx([(1.0 + 1 / 3) / 2] * 3)
    assert A.node_risk(6, [full_live(two_triangles)], [2]).tolist() == pytest.approx([2 / 5, 2 / 5, 0.0, 3 / 5, 3 / 5, 3 / 5])
    assert A.node_risk(3, [full_live(path3)], [0, 1, 2]).tolist() == [0.0, 0.0, 0.0]


def test_calibrate_p_hits_the_target_and_is_monotone():
    from eid_scenario import make_instance

    inst = make_instance(C.T_RANDOM, 120, 6, 3, layout=False)
    u, v = A.edge_arrays(inst.adj)
    ps = []
    for target in (0.1, 0.3, 0.6):
        p = A.calibrate_p(120, u, v, target, 5)
        ps.append(p)
        lls = A.live_lists(120, u, v, A.snapshots(len(u), p, 400, 9))
        assert A.outbreak_size(120, lls, []) == pytest.approx(target, abs=0.04)
    assert ps == sorted(ps) and ps[0] > 0


def test_containment_k_finds_the_first_k_below_the_level():
    assert A.containment_k([0.3, 0.2, 0.05, 0.01], 0.05) == 2 and A.containment_k([0.3, 0.2], 0.05) is None and A.containment_k([0.04], 0.05) == 0
    assert A.containment_k([0.3, 0.05 + 1e-15], 0.05) == 1                                   # Rundung auf 12 Stellen: Rauschen gilt als gleich


# --- Strategien -------------------------------------------------------------------------------------------------------------------------------


def _hub_net():
    """Hub 0 (Grad 4: 1, 2, 3, 4), Knoten 1 (Grad 3: 0, 5, 6), Knoten 7 (Grad 2: 8, 9) und Blätter."""
    return make_adj(10, [(0, 1), (0, 2), (0, 3), (0, 4), (1, 5), (1, 6), (7, 8), (7, 9)])


def test_degree_core_and_betweenness_hand_values():
    adj = _hub_net()
    rng = np.random.default_rng(1)
    assert A.order_degree(adj, 3, rng) == [0, 1, 7]
    assert A.core_numbers(adj) == [1] * 10 and A.core_numbers(make_adj(4, [(0, 1), (1, 2), (0, 2), (2, 3)])) == [2, 2, 2, 1]
    assert A.betweenness(make_adj(3, [(0, 1), (1, 2)])) == pytest.approx([0.0, 1.0, 0.0])           # nur der mittlere Knoten liegt auf dem einzigen Weg
    assert A.order_betweenness(adj, 1, rng) == [0] or A.order_betweenness(adj, 1, rng) == [1]


def test_adaptive_degree_recounts_after_each_choice():
    # Hub 0 (Partner 1, 2, 3, 4), Knoten 1 (Partner 0, 5, 6, Grad 3) und Knoten 7 (Partner 8, 9, 10, Grad 3): nach der Wahl von 0 hat Knoten 1 nur noch zwei Partner, Knoten 7 weiter drei
    adj = make_adj(11, [(0, 1), (0, 2), (0, 3), (0, 4), (1, 5), (1, 6), (7, 8), (7, 9), (7, 10)])
    assert all(A.order_degree_adaptive(adj, 2, np.random.default_rng(s)) == [0, 7] for s in range(20))
    second = {A.order_degree(adj, 2, np.random.default_rng(s))[1] for s in range(20)}
    assert second == {1, 7}                                                                  # statisch entscheidet bei Grad 3 gegen 3 der Zufall


def test_adaptive_degree_on_a_path_and_with_a_single_pick():
    chain = make_adj(5, [(0, 1), (1, 2), (2, 3), (3, 4)])
    order = A.order_degree_adaptive(chain, 2, np.random.default_rng(2))
    assert order[0] in (1, 2, 3) and order[1] != order[0]
    assert A.order_degree_adaptive(chain, 0, np.random.default_rng(2)) == []


def test_every_order_is_a_selection_without_duplicates_and_checks_k():
    adj = _hub_net()
    for fn in (A.order_random, A.order_degree, A.order_degree_adaptive, A.order_betweenness, A.order_core, A.order_acquaintance, A.order_acquaintance_hub):
        for k in (0, 1, 4, 9):
            order = fn(adj, k, np.random.default_rng(5))
            assert len(order) == len(set(order)) and all(0 <= x < 10 for x in order), (fn.__name__, k)
            assert len(order) == k or fn in (A.order_acquaintance, A.order_acquaintance_hub)
        with pytest.raises(ValueError):
            fn(adj, 11, np.random.default_rng(5))
        with pytest.raises(ValueError):
            fn(adj, -1, np.random.default_rng(5))


def test_acquaintance_never_picks_a_node_without_partners_and_is_capped():
    adj = make_adj(6, [(0, 1), (1, 2), (3, 4)])                                              # Knoten 5 ohne Partner
    for fn in (A.order_acquaintance, A.order_acquaintance_hub):
        order = fn(adj, 6, np.random.default_rng(3))
        assert sorted(order) == [0, 1, 2, 3, 4] and 5 not in order and A.reachable_count(adj) == 5


def test_orders_are_deterministic_per_seed_and_differ_between_seeds():
    adj = _hub_net()
    for fn in (A.order_random, A.order_acquaintance, A.order_acquaintance_hub):
        assert fn(adj, 5, np.random.default_rng(4)) == fn(adj, 5, np.random.default_rng(4))
    assert any(A.order_random(adj, 5, np.random.default_rng(s)) != A.order_random(adj, 5, np.random.default_rng(4)) for s in range(5, 15))


def test_ranking_by_rounds_noise_before_ranking():
    values = [1.0, 1.0 + 1e-14, 0.5]
    assert A.ranking_by(values, [0.9, 0.1, 0.0]) == [1, 0, 2]                                # praktisch gleich: der kleinere Gleichstandswert zuerst


def test_knowledge_cost_hand_values():
    assert A.knowledge_cost("Zufall", 100, 300, 10) == 0.0 and A.knowledge_cost("Bekannte", 100, 300, 10) == 20.0
    assert A.knowledge_cost("Bekannte (Nachbar mit höchstem Grad)", 100, 300, 10) == pytest.approx(10 * (1 + 6))
    assert A.knowledge_cost("Grad", 100, 300, 10) == 100.0 and A.knowledge_cost("Betweenness", 100, 300, 10) == 400.0 and A.knowledge_cost("Kernzahl", 100, 300, 10) == 400.0
    assert A.knowledge_cost("Grad adaptiv", 100, 300, 10) == 400.0
    with pytest.raises(ValueError):
        A.knowledge_cost("Orakel", 10, 10, 1)


# --- Exakte Aufzählung ---------------------------------------------------------------------------------------------------------------------


def test_exact_outbreak_hand_values_on_the_path():
    states = A.exact_states(3, [(0, 1), (1, 2)], 0.5)
    assert states[0].sum() == pytest.approx(1.0) and states[1].shape == (4, 3, 3)
    # beide Kanten (1/4): 9; genau eine (1/2): 4 + 1 = 5; keine (1/4): 3 → 2,25 + 2,5 + 0,75 = 5,5; geteilt durch 3 und 3
    assert A.exact_outbreak(3, states, []) == pytest.approx(5.5 / 9)
    assert A.exact_outbreak(3, states, [1]) == pytest.approx(1 / 3)
    # Knoten 0 geimpft: Rest {1, 2}: Kante 1-2 bleibt (1/2): Summe 4, sonst 2 → 3; geteilt durch 2 und 3
    assert A.exact_outbreak(3, states, [0]) == pytest.approx(3 / 2 / 3)
    assert A.exact_outbreak(3, states, [0, 1, 2]) == 0.0


def test_exact_states_reject_too_many_edges_and_handle_no_edges():
    with pytest.raises(ValueError):
        A.exact_states(20, [(i, i + 1) for i in range(17)], 0.5)
    states = A.exact_states(3, [], 0.5)
    assert states[0].tolist() == [1.0] and A.exact_outbreak(3, states, []) == pytest.approx(3 / 3 / 3)


def test_exact_greedy_and_degree_tie_sets():
    states = A.exact_states(5, [(0, 1), (0, 2), (0, 3), (0, 4)], 1.0)
    assert A.exact_greedy(5, states, 1) == [0]                                               # die Mitte des Sterns
    assert A.degree_tie_sets([4, 1, 1, 1, 1], 1) == [(0,)] and A.degree_tie_sets([4, 1, 1, 1, 1], 2) == [(0, 1), (0, 2), (0, 3), (0, 4)]
    assert A.degree_tie_sets([2, 2, 2], 2) == [(0, 1), (0, 2), (1, 2)]


def test_exact_all_sets_has_every_k_set_once(small_edges):
    n, edges = small_edges
    vals = A.exact_all_sets(n, A.exact_states(n, edges, 0.5), 2)
    assert len(vals) == 36 and set(vals) == set(itertools.combinations(range(9), 2)) and min(vals.values()) > 0


def test_no_warnings_in_the_core(path3):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        A.prefix_outbreak(3, full_live(path3), [1])
        A.exact_outbreak(3, A.exact_states(3, [(0, 1), (1, 2)], 0.5), [0])
        A.node_risk(3, [full_live(path3)], [])


def test_outbreak_size_can_rise_when_an_isolated_node_is_vaccinated():
    # Start unter den Ungeimpften: die Impfung des einzelnen Knotens 3 entfernt eine Komponente der Größe 1 und lässt die größere in der Mitte
    adj = make_adj(4, [(0, 1), (1, 2)])
    out = A.prefix_outbreak(4, full_live(adj), [3])
    assert out.tolist() == pytest.approx([(9 + 1) / 4 / 4, 9 / 3 / 4]) and out[1] > out[0]


# --- Lücken aus der Mutationsprüfung ---------------------------------------------------------------------------------------------------------


def test_degree_tie_sets_with_distinct_and_tied_degrees():
    assert A.degree_tie_sets([3, 2, 2, 1], 2) == [(0, 1), (0, 2)]                            # Knoten 0 vorn, einer der beiden Knoten mit Grad 2
    assert A.degree_tie_sets([3, 3, 2, 1, 1], 2) == [(0, 1)]                                 # die zwei größten Grade sind eindeutig
    assert A.degree_tie_sets([3, 3, 2, 2, 1], 3) == [(0, 1, 2), (0, 1, 3)]


def test_exact_greedy_can_pick_the_last_node():
    states = A.exact_states(5, [(4, 0), (4, 1), (4, 2), (4, 3)], 1.0)                        # Stern mit der Mitte 4, dem letzten Knoten
    assert A.exact_greedy(5, states, 1) == [4]
    assert A.exact_greedy(5, states, 2)[0] == 4


def test_node_risk_of_the_single_unvaccinated_node_is_one():
    adj = make_adj(3, [(0, 1), (1, 2)])
    assert A.node_risk(3, [full_live(adj)], [0, 2]).tolist() == [0.0, 1.0, 0.0]


def test_acquaintance_orders_have_exactly_k_entries_below_the_cap():
    adj = _hub_net()
    for fn in (A.order_acquaintance, A.order_acquaintance_hub):
        for k in (0, 1, 3, 9):
            assert len(fn(adj, k, np.random.default_rng(k))) == k, (fn.__name__, k)


def test_acquaintance_gives_up_instead_of_looping_forever(monkeypatch):
    adj = make_adj(4, [(0, 1), (2, 3)])
    monkeypatch.setattr(A, "MAX_TRIES", 0)
    for fn in (A.order_acquaintance, A.order_acquaintance_hub):
        with pytest.raises(RuntimeError):
            fn(adj, 2, np.random.default_rng(1))
