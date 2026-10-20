"""Netze: gültige Netze, Determinismus (auch über Prozesse), Positionen; kleine Netze für die exakte Aufzählung."""

import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

import eid_constants as C
import eid_evaluation as ev
import eid_scenario as S

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("typ", C.ALL_TYPES)
@pytest.mark.parametrize("n,c", [(C.N_MIN, C.C_MIN), (C.N_MIN, C.C_MAX), (C.DEFAULT_N, C.DEFAULT_C), (C.N_MAX, C.C_MAX)])
def test_every_corner_gives_a_valid_network(typ, n, c):
    inst = S.make_instance(typ, n, c, 35)
    assert inst.n >= 2 and len(inst.pos) == inst.n and inst.m >= 1
    for x, y in inst.pos:
        assert math.isfinite(x) and math.isfinite(y) and -1e-9 <= x <= 1 + 1e-9 and -1e-9 <= y <= 1 + 1e-9
    for a, nb in enumerate(inst.adj):
        assert list(nb) == sorted(set(nb)) and a not in nb
        for b in nb:
            assert a in inst.adj[b]


def test_instances_are_deterministic_per_seed_and_differ_between_seeds():
    a = S.make_instance(C.T_COMMUNITIES, 80, 6, 5)
    assert a.adj == S.make_instance(C.T_COMMUNITIES, 80, 6, 5).adj and a.pos == S.make_instance(C.T_COMMUNITIES, 80, 6, 5).pos
    assert S.make_instance(C.T_COMMUNITIES, 80, 6, 6, layout=False).adj != a.adj


def test_network_is_independent_of_the_hash_seed_of_the_process():
    code = ("import sys; sys.path.insert(0, sys.argv[1]); import hashlib, eid_scenario as S, eid_constants as C;"
            "h = hashlib.sha256();"
            "[h.update(repr(S.make_instance(t, 60, 5, 7, layout=False).adj).encode()) for t in C.ALL_TYPES];"
            "print(h.hexdigest())")
    outs = []
    for hashseed in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=hashseed)
        outs.append(subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", code, str(ROOT)], capture_output=True, text=True, env=env, check=True).stdout.strip())
    assert outs[0] == outs[1] and len(outs[0]) == 64


def test_layout_false_skips_the_force_layout_and_unknown_type_raises():
    inst = S.make_instance(C.T_RANDOM, 60, 4, 1, layout=False)
    assert set(inst.pos) == {(0.5, 0.5)}
    with pytest.raises(ValueError):
        S.make_instance("gibt es nicht", 60, 4, 1)


def test_groups_exist_only_for_communities_and_the_heavy_tail_is_heavy():
    assert S.make_instance(C.T_RANDOM, 60, 4, 1, layout=False).groups is None
    assert len(set(S.make_instance(C.T_COMMUNITIES, 60, 5, 1, layout=False).groups)) == C.BLOCKS
    deg = [len(a) for a in S.make_instance(C.T_BA, 250, 6, 1, layout=False).adj]
    flat = [len(a) for a in S.make_instance(C.T_RANDOM, 250, 6, 1, layout=False).adj]
    assert max(deg) > max(flat) and min(deg) >= 3                                  # skalenfrei: Hubs, aber jeder Betrieb hat mindestens m = 3 Partner


def test_small_network_is_connected_has_the_requested_size_and_is_deterministic():
    for seed in range(100000, 100010):
        n, edges = ev.small_network(seed)
        assert n == C.EXACT_N and len(edges) == C.EXACT_M == len(set(edges)) and all(a < b for a, b in edges)
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                x = parent[x]
            return x

        for a, b in edges:
            parent[find(a)] = find(b)
        assert len({find(i) for i in range(n)}) == 1
        assert ev.small_network(seed) == (n, edges)
    assert ev.small_network(100000) != ev.small_network(100001)
