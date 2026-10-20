"""Gemeinsame Fixtures und Hilfen (DEMO-PLAYBOOK §1b): Mini-Instanzen, an denen jede Einheit von Hand geprüft wird."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def make_adj(n, pairs):
    """Nachbarlisten (Tupel von sortierten Tupeln) aus einer Kantenliste."""
    sets = [set() for _ in range(n)]
    for a, b in pairs:
        if a != b:
            sets[a].add(b)
            sets[b].add(a)
    return tuple(tuple(sorted(s)) for s in sets)


def full_live(adj):
    """Nachbarlisten als Listen: alle Kanten bleiben (ein Schnappschuss mit p = 1)."""
    return [list(a) for a in adj]


@pytest.fixture
def path3():
    """Pfad 0 - 1 - 2. Mit allen Kanten: Größe 1; Impfung der Mitte: {0}, {2}, Summe 2, geteilt durch 2 und 3 = 1/3."""
    return make_adj(3, [(0, 1), (1, 2)])


@pytest.fixture
def star5():
    """Stern: Mitte 0, Blätter 1 bis 4. Impfung der Mitte: vier Einzelne, Summe 4, geteilt durch 4 und 5 = 0,2."""
    return make_adj(5, [(0, 1), (0, 2), (0, 3), (0, 4)])


@pytest.fixture
def two_triangles():
    """Dreiecke {0,1,2} und {3,4,5} mit Brücke 2 - 3. Impfung von Knoten 2: {0,1} und {3,4,5}, Summe 4 + 9 = 13, geteilt durch 5 und 6 = 13/30."""
    return make_adj(6, [(0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5), (2, 3)])


@pytest.fixture
def small_edges():
    """Kleines verbundenes Netz mit 9 Knoten und 12 Kanten (Ring mit drei Sehnen) für die exakte Aufzählung."""
    return 9, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (0, 8), (1, 5), (2, 6), (3, 7)]
