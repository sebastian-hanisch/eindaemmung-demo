"""Kern: Ausbruchsgröße einer SIR-Ausbreitung nach Impfung (Perkolationsfassung), Impfstrategien als Wahlreihenfolgen, exakte Aufzählung für kleine Netze.

Modell: auf einem ungerichteten Netz überträgt ein befallener Betrieb den Befall an jeden Partner mit gleicher Wahrscheinlichkeit p und ist nur einen Schritt lang ansteckend (SIR). Das ist gleichbedeutend
mit Erreichbarkeit im Netz, in dem jede Kante unabhängig mit Wahrscheinlichkeit p bleibt (Schnappschuss; Bond-Perkolation). Geimpfte (abgesicherte) Betriebe fallen aus dem Netz. Beginnt der Befall in einem
zufälligen Ungeimpften, ist seine erwartete Größe die mittlere Summe der quadrierten Komponentengrößen geteilt durch die Zahl der Ungeimpften; geteilt durch n heißt sie Ausbruchsgröße (Anteil der Betriebe).

Netze sind Nachbarlisten `adj` (Tupel von sortierten Tupeln, Knoten 0 bis n - 1, ungerichtet). Zufall nur über `numpy.random.default_rng(Seed)`."""

import itertools
import math

import numpy as np

MAX_TRIES = 2000   # Obergrenze der Versuche je Betrieb bei der Bekannten-Impfung (Schutz vor Endlosschleifen; erwartet braucht der letzte Betrieb höchstens einige Zehntausend)
ROUND = 12   # Werte werden vor Vergleichen und Rankings auf 12 Stellen gerundet: Gleitkomma-Summen mathematisch gleicher Knoten unterscheiden sich um ~1e-16


# --- Netze und Schnappschüsse ----------------------------------------------------------------------------------------------------------------------


def edge_arrays(adj):
    """Kanten (a < b) als zwei Arrays."""
    pairs = [(a, b) for a in range(len(adj)) for b in adj[a] if a < b]
    if not pairs:
        return np.zeros(0, dtype=int), np.zeros(0, dtype=int)
    u, v = zip(*pairs)
    return np.array(u, dtype=int), np.array(v, dtype=int)


def degrees(adj):
    return [len(a) for a in adj]


def snapshots(m, p, runs, seed):
    """`runs` Schnappschüsse: Kantenmasken (runs, m), jede Kante bleibt mit Wahrscheinlichkeit p."""
    return np.random.default_rng(int(seed)).random((runs, m)) < p


def live_lists(n, u, v, live):
    """Je Schnappschuss die Nachbarlisten der bleibenden Kanten."""
    out = []
    for mask in live:
        ladj = [[] for _ in range(n)]
        for a, b in zip(u[mask].tolist(), v[mask].tolist()):
            ladj[a].append(b)
            ladj[b].append(a)
        out.append(ladj)
    return out


# --- Ausbruchsgröße -------------------------------------------------------------------------------------------------------------------------------


def prefix_outbreak(n, ladj, order):
    """Ausbruchsgröße eines Schnappschusses nach Impfung der ersten k Betriebe von `order`, für k = 0 bis len(order) (Feld der Länge len(order) + 1).
    Rückwärts gerechnet: alle Betriebe der Reihenfolge sind zunächst geimpft; dann werden sie in umgekehrter Reihenfolge wieder eingesetzt und die Komponenten mit Union-Find zusammengeführt,
    die Summe der Quadrate der Komponentengrößen wächst dabei fortlaufend. Sind alle n Betriebe geimpft, ist die Größe 0."""
    order = [int(x) for x in order]
    if len(set(order)) != len(order) or any(not 0 <= x < n for x in order):
        raise ValueError("die Reihenfolge enthält Doppelte oder Knoten außerhalb des Netzes")
    k_all = len(order)
    out = np.zeros(k_all + 1)
    active = [True] * n
    for x in order:
        active[x] = False
    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return 0
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        gain = 2 * size[ra] * size[rb]
        parent[rb] = ra
        size[ra] += size[rb]
        return gain

    ssum = n - k_all
    for a in range(n):
        if active[a]:
            for b in ladj[a]:
                if b > a and active[b]:
                    ssum += union(a, b)
    out[k_all] = ssum / (n - k_all) / n if n > k_all else 0.0
    for j in range(k_all - 1, -1, -1):
        x = order[j]
        active[x] = True
        ssum += 1
        for w in ladj[x]:
            if active[w]:
                ssum += union(x, w)
        out[j] = ssum / (n - j) / n
    return out


def mean_prefix_outbreak(n, lls, order):
    """Mittel von `prefix_outbreak` über die Schnappschüsse `lls` (Liste von Nachbarlisten-Listen)."""
    return np.mean([prefix_outbreak(n, ladj, order) for ladj in lls], axis=0)


def outbreak_size(n, lls, vaccinated):
    """Mittlere Ausbruchsgröße (Anteil der Betriebe) bei Impfung der Menge `vaccinated`."""
    order = sorted(int(x) for x in vaccinated)
    return float(mean_prefix_outbreak(n, lls, order)[-1])


def node_risk(n, lls, vaccinated):
    """Wahrscheinlichkeit je Betrieb, im Ausbruch befallen zu werden (Start zufällig unter den Ungeimpften): mittlere Größe seiner Komponente geteilt durch die Zahl der Ungeimpften; Geimpfte 0."""
    vacc = set(int(x) for x in vaccinated)
    rest = n - len(vacc)
    risk = np.zeros(n)
    if rest <= 0:
        return risk
    for ladj in lls:
        seen = set(vacc)
        for s in range(n):
            if s in seen:
                continue
            members = [s]
            seen.add(s)
            for x in members:
                for w in ladj[x]:
                    if w not in seen:
                        seen.add(w)
                        members.append(w)
            for x in members:
                risk[x] += len(members) / rest
    return risk / len(lls)


def calibrate_p(n, u, v, target, seed, runs=40, iters=14):
    """p so, dass die Ausbruchsgröße ohne Impfung im Mittel `target` (Anteil der Betriebe) beträgt (Bisektion mit `runs` Schnappschüssen je Schritt)."""
    lo, hi = 0.0, 1.0
    for _ in range(iters):
        mid = (lo + hi) / 2.0
        lls = live_lists(n, u, v, snapshots(len(u), mid, runs, seed))
        if mean_prefix_outbreak(n, lls, [])[0] < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def containment_k(curve, level):
    """Kleinste Zahl k mit curve[k] <= level (Ausbruchsgröße nach k Impfungen); None, wenn es keine gibt."""
    for k, x in enumerate(curve):
        if round(float(x), ROUND) <= level:
            return k
    return None


# --- Maße für die Auswahlregeln ------------------------------------------------------------------------------------------------------------------------


def betweenness(adj):
    """Betweenness nach Brandes (2001), normiert wie `networkx.betweenness_centrality`."""
    n = len(adj)
    cb = [0.0] * n
    for s in range(n):
        stack = []
        pred = [[] for _ in range(n)]
        sigma = [0.0] * n
        sigma[s] = 1.0
        dist = [-1] * n
        dist[s] = 0
        queue = [s]
        for x in queue:
            stack.append(x)
            for w in adj[x]:
                if dist[w] < 0:
                    dist[w] = dist[x] + 1
                    queue.append(w)
                if dist[w] == dist[x] + 1:
                    sigma[w] += sigma[x]
                    pred[w].append(x)
        delta = [0.0] * n
        while stack:
            w = stack.pop()
            for x in pred[w]:
                delta[x] += sigma[x] / sigma[w] * (1.0 + delta[w])
            if w != s:
                cb[w] += delta[w]
    scale = 1.0 / ((n - 1) * (n - 2)) if n > 2 else 1.0
    return [x * scale for x in cb]


def core_numbers(adj):
    """Kernzahl je Knoten durch Schälen: für k = 0, 1, ... werden Knoten mit höchstens k verbliebenen Nachbarn entfernt (und ihre Nachbarn abgewertet), bis nichts mehr geht."""
    n = len(adj)
    deg = [len(a) for a in adj]
    removed = [False] * n
    core = [0] * n
    remaining = n
    k = 0
    while remaining:
        stack = [v for v in range(n) if not removed[v] and deg[v] <= k]
        if not stack:
            k += 1
            continue
        while stack:
            v = stack.pop()
            if removed[v]:
                continue
            removed[v] = True
            core[v] = k
            remaining -= 1
            for w in adj[v]:
                if not removed[w]:
                    deg[w] -= 1
                    if deg[w] <= k:
                        stack.append(w)
    return core


# --- Strategien: Wahlreihenfolgen ----------------------------------------------------------------------------------------------------------------------


def tiebreak_vector(n, rng):
    """Rangfolge der Knoten bei Gleichstand: zufällig, aus `rng`."""
    return rng.random(n)


def ranking_by(values, tie):
    """Alle Knoten nach Wert absteigend (auf 12 Stellen gerundet), Gleichstand nach `tie` (kleinerer Wert zuerst)."""
    return sorted(range(len(values)), key=lambda i: (-round(float(values[i]), ROUND), float(tie[i]), i))


def _check_k(n, k):
    if not 0 <= k <= n:
        raise ValueError(f"k = {k} liegt außerhalb von 0 bis {n}")


def order_random(adj, k, rng):
    """Zufällige Betriebe ohne Wiederholung."""
    n = len(adj)
    _check_k(n, k)
    return [int(x) for x in rng.permutation(n)[:k]]


def order_degree(adj, k, rng):
    """Die k Betriebe mit den meisten Partnern, Gleichstände zufällig."""
    n = len(adj)
    _check_k(n, k)
    return ranking_by(degrees(adj), tiebreak_vector(n, rng))[:k]


def order_degree_adaptive(adj, k, rng):
    """Nach jeder Wahl werden die Partner der Übrigen ohne die schon Gewählten neu gezählt; der Betrieb mit den meisten verbliebenen Partnern kommt als Nächster (Gleichstand zufällig)."""
    n = len(adj)
    _check_k(n, k)
    tie = tiebreak_vector(n, rng)
    alive = set(range(n))
    deg = {i: len(adj[i]) for i in range(n)}
    order = []
    for _ in range(k):
        best = min(alive, key=lambda i: (-deg[i], float(tie[i]), i))
        order.append(best)
        alive.discard(best)
        for w in adj[best]:
            if w in alive:
                deg[w] -= 1
    return order


def order_betweenness(adj, k, rng):
    """Die k Betriebe mit der höchsten Betweenness, Gleichstände zufällig."""
    n = len(adj)
    _check_k(n, k)
    return ranking_by(betweenness(adj), tiebreak_vector(n, rng))[:k]


def order_core(adj, k, rng):
    """Die k Betriebe mit der höchsten Kernzahl, Gleichstände zufällig."""
    n = len(adj)
    _check_k(n, k)
    return ranking_by([float(c) for c in core_numbers(adj)], tiebreak_vector(n, rng))[:k]


def reachable_count(adj):
    """Zahl der Betriebe mit mindestens einem Partner: nur diese können als Partner eines Zufallsbetriebs gewählt werden."""
    return sum(1 for a in adj if a)


def order_acquaintance(adj, k, rng):
    """Bekannten-Impfung (Cohen u. a. 2003): zufälliger Betrieb mit Partnern, daraus ein zufälliger Partner; schon Gewählte werden übersprungen (neuer Versuch).
    Betriebe ohne Partner können nie gewählt werden: die Reihenfolge ist höchstens so lang wie ihre Zahl."""
    n = len(adj)
    _check_k(n, k)
    cand = [i for i in range(n) if adj[i]]
    k = min(k, len(cand))
    chosen, order = set(), []
    tries = 0
    while len(order) < k:
        tries += 1
        if tries > MAX_TRIES * (n + 1):
            raise RuntimeError("keine weitere Wahl gefunden")
        x = int(rng.choice(cand))
        y = int(rng.choice(adj[x]))
        if y not in chosen:
            chosen.add(y)
            order.append(y)
    return order


def order_acquaintance_hub(adj, k, rng):
    """Wie die Bekannten-Impfung, aber unter den noch nicht gewählten Partnern des Zufallsbetriebs wird der mit den meisten Partnern gesichert (Gleichstand zufällig)."""
    n = len(adj)
    _check_k(n, k)
    cand = [i for i in range(n) if adj[i]]
    k = min(k, len(cand))
    chosen, order = set(), []
    tries = 0
    while len(order) < k:
        tries += 1
        if tries > MAX_TRIES * (n + 1):
            raise RuntimeError("keine weitere Wahl gefunden")
        x = int(rng.choice(cand))
        free = [w for w in adj[x] if w not in chosen]
        if not free:
            continue
        top = max(len(adj[w]) for w in free)
        y = int(rng.choice([w for w in free if len(adj[w]) == top]))
        chosen.add(y)
        order.append(y)
    return order


def knowledge_cost(strategy_name, n, m, k):
    """Erwartete Zahl der Abfragen (Betriebe oder Partnerschaften, deren Daten die Strategie liest): Zufall 0; Bekannte 2 je Impfung; Bekannte mit Hub-Wahl je Impfung 1 + Partner des Zufallsbetriebs
    (im Mittel 2 m / n); Grad n (alle Partnerzahlen); die übrigen drei brauchen das ganze Netz: n + m. Eine Zählung, kein Maß der Güte."""
    if strategy_name == "Zufall":
        return 0.0
    if strategy_name == "Bekannte":
        return 2.0 * k
    if strategy_name == "Bekannte (Nachbar mit höchstem Grad)":
        return k * (1.0 + (2.0 * m / n if n else 0.0))
    if strategy_name == "Grad":
        return float(n)
    if strategy_name in ("Grad adaptiv", "Betweenness", "Kernzahl"):
        return float(n + m)
    raise ValueError(f"unbekannte Strategie: {strategy_name}")


# --- Exakte Aufzählung für kleine Netze -----------------------------------------------------------------------------------------------------------------


def exact_states(n, edges, p):
    """Alle 2^m Kantenzustände: Wahrscheinlichkeiten (S,) und Nachbarschaftsmatrizen (S, n, n) der bleibenden Kanten (m höchstens 16)."""
    m = len(edges)
    if m > 16:
        raise ValueError("exact_states ist nur für höchstens 16 Kanten gedacht")
    states = 1 << m
    bits = ((np.arange(states)[:, None] >> np.arange(m)[None, :]) & 1).astype(bool)
    live = bits.sum(axis=1)
    probs = p**live * (1.0 - p) ** (m - live)
    mats = np.zeros((states, n, n), dtype=np.float32)
    for i, (a, b) in enumerate(edges):
        mats[:, a, b] = bits[:, i]
        mats[:, b, a] = bits[:, i]
    return probs, mats


def exact_outbreak(n, states, vaccinated):
    """Exakte Ausbruchsgröße: erwartete Summe der quadrierten Komponentengrößen (Zahl der verbundenen geordneten Paare Ungeimpfter) geteilt durch (n - k) und n, über alle Kantenzustände."""
    probs, mats = states
    vacc = sorted(set(int(x) for x in vaccinated))
    keep = np.ones(n, dtype=bool)
    keep[vacc] = False
    rest = int(keep.sum())
    if rest == 0:
        return 0.0
    sub = mats[:, keep][:, :, keep] + np.eye(rest, dtype=np.float32)[None, :, :]
    reach = (sub > 0).astype(np.float32)
    for _ in range(max(1, math.ceil(math.log2(max(rest, 2))))):
        reach = (np.matmul(reach, reach) > 0).astype(np.float32)
    pairs = reach.sum(axis=(1, 2))
    return float((probs * pairs).sum() / rest / n)


def exact_all_sets(n, states, k):
    """Exakte Ausbruchsgröße jeder k-Menge: {Menge (Tupel): Wert}."""
    return {s: exact_outbreak(n, states, s) for s in itertools.combinations(range(n), k)}


def exact_greedy(n, states, k):
    """Greedy: in jeder Runde der Betrieb, dessen Impfung die Ausbruchsgröße am stärksten senkt (Werte auf 12 Stellen gerundet, Gleichstand: kleinere Nummer)."""
    chosen = []
    for _ in range(k):
        best = min((i for i in range(n) if i not in chosen), key=lambda i: (round(exact_outbreak(n, states, chosen + [i]), ROUND), i))
        chosen.append(best)
    return chosen


def degree_tie_sets(deg, k):
    """Alle k-Mengen, die eine Rangfolge nach Grad (Gleichstände beliebig aufgelöst) liefern kann: alle Betriebe über dem k-größten Grad plus beliebige Betriebe mit genau diesem Grad."""
    kth = sorted(deg, reverse=True)[k - 1]
    above = [i for i, d in enumerate(deg) if d > kth]
    tied = [i for i, d in enumerate(deg) if d == kth]
    return [tuple(sorted(above + list(c))) for c in itertools.combinations(tied, k - len(above))]
