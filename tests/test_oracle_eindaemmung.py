"""Orakel-Test eindaemmung-demo: das Verfahren (Ausbruchsgröße nach Impfung, Strategien) gegen andere Rechenwege.

* Die Summe der quadrierten Komponentengrößen eines Schnappschusses stimmt mit `networkx` (Zusammenhangskomponenten des Netzes ohne die Geimpften) überein (60 Zufallsnetze, alle Präfixe).
* Die exakte Ausbruchsgröße (Aufzählung aller Kantenzustände, vektorisiert) stimmt mit einer unabhängig geschriebenen Aufzählung mit Union-Find in reinem Python überein (Netze bis 8 Knoten, 40 Fälle).
* Der Schnappschuss-Schätzer liegt auf einem kleinen Netz im Band um den exakten Wert; eine direkte SIR-Simulation (befallene Betriebe geben an jeden Partner mit Wahrscheinlichkeit p weiter) liegt ebenfalls im Band.
* Optimum ≤ Greedy ≤ Mittel über alle k-Mengen; das Optimum durch Aufzählung aller Mengen gegen eine Aufzählung im Python-Rechenweg.
* Die Wahrscheinlichkeit der ersten Wahl der Bekannten-Impfung stimmt mit der geschlossenen Formel überein (zufälliger Betrieb, dann zufälliger Partner), ebenso die Hub-Variante.
* Betweenness und Kernzahl stimmen mit `networkx` überein."""

import itertools

import numpy as np
import pytest

import eid_algorithm as A
from conftest import full_live, make_adj


def _random_net(rng, n_lo, n_hi, p_lo=0.1, p_hi=0.5):
    n = int(rng.integers(n_lo, n_hi))
    p = float(rng.uniform(p_lo, p_hi))
    pairs = [(a, b) for a in range(n) for b in range(a + 1, n) if rng.random() < p]
    return n, pairs, make_adj(n, pairs)


def test_sum_of_squared_components_against_networkx_for_every_prefix():
    nx = pytest.importorskip("networkx")
    for t in range(60):
        rng = np.random.default_rng(t)
        n, pairs, adj = _random_net(rng, 6, 30)
        order = rng.permutation(n)[: int(rng.integers(0, n))].tolist()
        out = A.prefix_outbreak(n, full_live(adj), order)
        for k in range(len(order) + 1):
            g = nx.Graph()
            g.add_nodes_from(set(range(n)) - set(order[:k]))
            g.add_edges_from((a, b) for a, b in pairs if a not in order[:k] and b not in order[:k])
            ssum = sum(len(c) ** 2 for c in nx.connected_components(g))
            expect = ssum / (n - k) / n if n > k else 0.0
            assert out[k] == pytest.approx(expect), (t, k)


def _python_exact(n, edges, p, vacc):
    """Unabhängige Aufzählung: Union-Find in reinem Python je Kantenzustand."""
    m = len(edges)
    vacc = set(vacc)
    total = 0.0
    for mask in range(1 << m):
        live = [edges[i] for i in range(m) if mask >> i & 1]
        prob = p ** len(live) * (1 - p) ** (m - len(live))
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for a, b in live:
            if a not in vacc and b not in vacc:
                parent[find(a)] = find(b)
        counts = {}
        for i in range(n):
            if i not in vacc:
                counts[find(i)] = counts.get(find(i), 0) + 1
        total += prob * sum(c * c for c in counts.values())
    rest = n - len(vacc)
    return total / rest / n if rest else 0.0


def test_exact_outbreak_against_an_independent_enumeration():
    for t in range(40):
        rng = np.random.default_rng(500 + t)
        n = int(rng.integers(4, 9))
        pairs = [(a, b) for a in range(n) for b in range(a + 1, n)]
        edges = [pairs[i] for i in rng.permutation(len(pairs))[: int(rng.integers(3, min(10, len(pairs)) + 1))]]
        p = float(rng.choice([0.2, 0.5, 0.8]))
        vacc = rng.permutation(n)[: int(rng.integers(0, n))].tolist()
        assert A.exact_outbreak(n, A.exact_states(n, edges, p), vacc) == pytest.approx(_python_exact(n, edges, p, vacc), rel=1e-5), t


def test_snapshot_estimator_and_direct_sir_simulation_match_the_exact_value(small_edges):
    n, edges = small_edges
    p = 0.5
    vacc = [1, 5]
    exact = A.exact_outbreak(n, A.exact_states(n, edges, p), vacc)
    u = np.array([a for a, _ in edges])
    v = np.array([b for _, b in edges])
    lls = A.live_lists(n, u, v, A.snapshots(len(edges), p, 6000, 3))
    assert A.outbreak_size(n, lls, vacc) == pytest.approx(exact, abs=0.01)
    adj = make_adj(n, edges)
    rng = np.random.default_rng(11)
    start_pool = [i for i in range(n) if i not in vacc]
    sizes = []
    for _ in range(20000):
        s = int(rng.choice(start_pool))
        infected, frontier = {s}, [s]
        while frontier:
            new = []
            for x in frontier:
                for y in adj[x]:
                    if y not in vacc and y not in infected and rng.random() < p:
                        infected.add(y)
                        new.append(y)
            frontier = new
        sizes.append(len(infected))
    assert float(np.mean(sizes)) / n == pytest.approx(exact, abs=0.012)


def test_optimum_greedy_and_random_mean_are_ordered_and_the_optimum_matches_a_python_search(small_edges):
    n, edges = small_edges
    states = A.exact_states(n, edges, 0.5)
    for k in (1, 2, 3):
        vals = A.exact_all_sets(n, states, k)
        best = min(vals.values())
        greedy = A.exact_outbreak(n, states, A.exact_greedy(n, states, k))
        assert best <= greedy + 1e-9 and greedy <= float(np.mean(list(vals.values()))) + 1e-9
        py_best = min(_python_exact(n, edges, 0.5, s) for s in itertools.combinations(range(n), k))
        assert best == pytest.approx(py_best, rel=1e-5)


def test_first_pick_of_the_acquaintance_strategy_follows_the_closed_formula():
    adj = make_adj(7, [(0, 1), (0, 2), (0, 3), (3, 4), (4, 5), (4, 6), (5, 6)])
    cand = [i for i in range(7) if adj[i]]
    expect = {y: sum(1.0 / len(cand) / len(adj[x]) for x in adj[y]) for y in range(7)}
    runs = 30000
    counts = np.zeros(7)
    rng = np.random.default_rng(1)
    for _ in range(runs):
        counts[A.order_acquaintance(adj, 1, rng)[0]] += 1
    for y in range(7):
        se = (expect[y] * (1 - expect[y]) / runs) ** 0.5
        assert counts[y] / runs == pytest.approx(expect[y], abs=4 * se + 1e-3), y


def test_first_pick_of_the_hub_variant_follows_the_closed_formula():
    adj = make_adj(7, [(0, 1), (0, 2), (0, 3), (3, 4), (4, 5), (4, 6), (5, 6)])
    cand = [i for i in range(7) if adj[i]]
    expect = np.zeros(7)
    for x in cand:
        top = max(len(adj[w]) for w in adj[x])
        best = [w for w in adj[x] if len(adj[w]) == top]
        for w in best:
            expect[w] += 1.0 / len(cand) / len(best)
    runs = 30000
    counts = np.zeros(7)
    rng = np.random.default_rng(2)
    for _ in range(runs):
        counts[A.order_acquaintance_hub(adj, 1, rng)[0]] += 1
    for y in range(7):
        se = (expect[y] * (1 - expect[y]) / runs) ** 0.5
        assert counts[y] / runs == pytest.approx(expect[y], abs=4 * se + 1e-3), y


def test_betweenness_and_core_numbers_against_networkx():
    nx = pytest.importorskip("networkx")
    for t in range(30):
        rng = np.random.default_rng(900 + t)
        n, pairs, adj = _random_net(rng, 5, 25)
        g = nx.Graph()
        g.add_nodes_from(range(n))
        g.add_edges_from(pairs)
        bet = nx.betweenness_centrality(g)
        core = nx.core_number(g)
        assert A.betweenness(adj) == pytest.approx([bet[i] for i in range(n)], abs=1e-9), t
        assert A.core_numbers(adj) == [core[i] for i in range(n)], t
