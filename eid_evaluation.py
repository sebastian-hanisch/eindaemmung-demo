"""Kennzahlen, Messreihen und Verdikte der Demo „Eindämmung“. Verdikte sind reine Funktionen (Art, Text); jede Zahl im Text kommt aus der Rechnung.

Protokoll: SIR in der Perkolationsfassung (Übertragungswahrscheinlichkeit p je Kante, ein Schritt ansteckend); p wird so kalibriert, dass die erwartete Ausbruchsgröße ohne Impfung („Ausbreitungsstärke“) den
Zielwert trifft. Geimpfte Betriebe fallen aus dem Netz, der Befall beginnt in einem zufälligen Ungeimpften. Ausgewiesen wird die erwartete Ausbruchsgröße als Anteil aller Betriebe. Jede Strategie liefert eine
Wahlreihenfolge; die ersten k Einträge sind die Auswahl für k Impfungen, so dass eine einzige Rechnung alle Impfanteile bedient. Strategien mit Zufall oder Gleichständen werden über mehrere Ziehungen
gemittelt. Jede Messreihe nimmt den Median über feste Netze (`LIVE_SEEDS` in der App, `SWEEP_SEEDS` für die README-Zahlen)."""

import math
from dataclasses import dataclass
from statistics import median

import numpy as np

import eid_algorithm as A
import eid_constants as C
from eid_scenario import Instance, make_instance

NAN = float("nan")
ORDER_FUNCS = {C.S_RANDOM: A.order_random, C.S_DEGREE: A.order_degree, C.S_ADAPTIVE: A.order_degree_adaptive, C.S_BETWEENNESS: A.order_betweenness, C.S_CORE: A.order_core,
               C.S_ACQ: A.order_acquaintance, C.S_ACQ_HUB: A.order_acquaintance_hub}


def de(x, digits=1) -> str:
    """Dezimalzahl mit Komma (deutsche Texte); eine nicht definierte Zahl erscheint als Gedankenstrich."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{x:.{digits}f}".replace(".", ",")


def pct(x, digits=0) -> str:
    return de(100.0 * x, digits)


def _med(values) -> float:
    vals = [v for v in values if not math.isnan(v)]
    return float(median(vals)) if vals else NAN


def at(curve, k) -> float:
    """Wert der Kurve bei k Impfungen; reicht die Kurve nicht so weit (Bekannte kennen nur Betriebe mit Partnern), gilt ihr letzter Wert."""
    return float(curve[min(int(k), len(curve) - 1)])


def k_of(n, f) -> int:
    """Zahl der Impfungen zum Impfanteil f (Anteil, nicht Prozent): gerundet, mindestens 1, höchstens n - 1."""
    return max(1, min(int(round(f * n)), n - 1))


# --- Vorbereitung eines Netzes ---------------------------------------------------------------------------------------------------------------------


def strategy_orders(adj, kmax, seed, draws=None, names=C.STRATEGIES) -> dict:
    """Je Strategie eine Liste von Wahlreihenfolgen der Länge kmax (so viele Ziehungen, wie `draws` angibt). Jede Ziehung jeder Strategie hat ihren eigenen Zufallsstrom (Seed, Platz in STRATEGIES, Nummer der Ziehung):
    das Weglassen anderer Strategien, weniger Ziehungen oder ein kleineres kmax ändern die übrigen Reihenfolgen nicht, die ersten k Einträge einer Reihenfolge sind unabhängig von kmax."""
    draws = draws or C.DRAWS
    out = {}
    for name in names:
        out[name] = [ORDER_FUNCS[name](adj, kmax, np.random.default_rng(int(seed) + 31 + 1000 * C.STRATEGIES.index(name) + 7919 * d)) for d in range(draws[name])]
    return out


def strategy_curves(n, lls, orders) -> dict:
    """Je Strategie die mittlere Ausbruchsgröße nach 0 bis kmax Impfungen (Mittel über Ziehungen und Schnappschüsse)."""
    return {name: np.mean([A.mean_prefix_outbreak(n, lls, o) for o in lst], axis=0) for name, lst in orders.items()}


def prepare(adj, strength, seed, runs):
    """Kantenlisten, kalibriertes p und die Schnappschüsse (als Nachbarlisten) eines Netzes."""
    n = len(adj)
    u, v = A.edge_arrays(adj)
    p = A.calibrate_p(n, u, v, strength / 100.0, seed, runs=C.CALIB_RUNS, iters=C.CALIB_ITERS)
    lls = A.live_lists(n, u, v, A.snapshots(len(u), p, runs, int(seed) + 1000))
    return p, lls


# --- Hauptanalyse ----------------------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Settings:
    netztyp: str = C.T_RANDOM
    n: int = C.DEFAULT_N
    c: int = C.DEFAULT_C
    seed: int = C.DEFAULT_SEED
    strength: int = C.DEFAULT_STRENGTH
    f: int = C.DEFAULT_F
    strategy: str = C.DEFAULT_STRATEGY


@dataclass(frozen=True, eq=False)
class Analysis:
    inst: Instance
    settings: Settings
    p: float
    k: int                  # wirksame Zahl der Impfungen
    base: float             # Ausbruchsgröße ohne Impfung
    curves: dict            # Strategie -> Ausbruchsgröße nach 0 bis k Impfungen
    vaccinated: tuple       # die Impfungen der gewählten Strategie (erste Ziehung)
    risk: np.ndarray        # Wahrscheinlichkeit je Betrieb, im Ausbruch befallen zu werden (Geimpfte 0)
    cost: float             # erwartete Zahl der Abfragen der gewählten Strategie

    def value(self, strategy) -> float:
        return at(self.curves[strategy], self.k)

    def best(self) -> str:
        """Strategie mit der kleinsten Ausbruchsgröße bei k Impfungen (auf 12 Stellen gerundet, Gleichstand: Reihenfolge in STRATEGIES)."""
        return min(C.STRATEGIES, key=lambda s: (round(self.value(s), A.ROUND), C.STRATEGIES.index(s)))


def analyse(settings: Settings) -> Analysis:
    inst = make_instance(settings.netztyp, settings.n, settings.c, settings.seed, layout=True)
    n = inst.n
    p, lls = prepare(inst.adj, settings.strength, settings.seed, C.MAIN_RUNS)
    k = k_of(n, settings.f / 100.0)
    orders = strategy_orders(inst.adj, k, settings.seed)
    curves = strategy_curves(n, lls, orders)
    chosen = tuple(orders[settings.strategy][0][:k])
    risk = A.node_risk(n, lls, chosen)
    m = inst.m
    return Analysis(inst, settings, p, k, float(curves[C.S_RANDOM][0]), curves, chosen, risk, A.knowledge_cost(settings.strategy, n, m, k))


def verdict_main(an: Analysis) -> tuple[str, str]:
    """Verdikt der Kernfrage: wie viel bringt die gewählte Strategie gegenüber Zufall, und was kostet ihr Wissen?"""
    st = an.settings
    if an.inst.m == 0:
        return "warning", "Das Netz hat keine Kanten: ein Befall bleibt bei einem Betrieb."
    head = (f"Ohne Impfung erreicht ein Ausbruch im Mittel {pct(an.base)} % der Betriebe (p = {de(an.p, 3)}). Mit {an.k} gesicherten Betrieben ({st.f} %) nach „{st.strategy}“ bleiben "
            f"{pct(an.value(st.strategy), 1)} %.")
    rnd = an.value(C.S_RANDOM)
    best = an.best()
    know = f" Wissen: im Mittel {de(an.cost, 0)} Abfragen."
    if st.strategy == C.S_RANDOM:
        return "info", (head + f" Die beste Strategie wäre hier „{best}“ mit {pct(an.value(best), 1)} %" + (f" (Faktor {de(rnd / an.value(best), 1)} besser)." if an.value(best) > 0 and best != C.S_RANDOM else ".") + know)
    mine = an.value(st.strategy)
    if round(mine, A.ROUND) > round(rnd * C.WORSE_FACTOR, A.ROUND):
        return "warning", head + f" Das ist **schlechter als Zufall** ({pct(rnd, 1)} %)." + know
    if round(mine, A.ROUND) >= round(rnd * 0.98, A.ROUND):
        factor = f" Zufall käme auf {pct(rnd, 1)} %: die Strategie ist hier etwa so gut wie Zufall."
    else:
        factor = f" Zufall käme auf {pct(rnd, 1)} %" + (f", die Strategie ist {de(rnd / mine, 1)}-mal so gut." if mine > 0 else ".")
    kind = "success" if mine <= C.CONTAIN_LEVEL else "info"
    return kind, head + factor + know


# --- E1: Strategien über Impfanteile und Netztypen -------------------------------------------------------------------------------------------------


def strategy_rows(n, c, strength, fs=C.CURVE_FS, seeds=C.LIVE_SEEDS, types=C.ALL_TYPES, runs=C.EXP_RUNS) -> list[dict]:
    """Je Netztyp: Ausbruchsgröße ohne Impfung und je Strategie und Impfanteil (Median über die festen Netze)."""
    rows = []
    for typ in types:
        base, cells = [], {s: {f: [] for f in fs} for s in C.STRATEGIES}
        for seed in seeds:
            adj = make_instance(typ, n, c, seed, layout=False).adj
            nn = len(adj)
            _, lls = prepare(adj, strength, seed, runs)
            kmax = k_of(nn, max(fs))
            curves = strategy_curves(nn, lls, strategy_orders(adj, kmax, seed, draws=C.EXP_DRAWS))
            base.append(float(curves[C.S_RANDOM][0]))
            for s in C.STRATEGIES:
                for f in fs:
                    cells[s][f].append(at(curves[s], k_of(nn, f)))
        rows.append({"typ": typ, "base": _med(base), "cells": {s: {f: _med(v) for f, v in d.items()} for s, d in cells.items()}})
    return rows


def verdict_strategies(rows: list[dict], f) -> tuple[str, str]:
    """Verdikt zu E1: wo lohnt Wissen, und wo ist eine Strategie schlechter als Zufall?"""
    valid = [r for r in rows if f in r["cells"][C.S_RANDOM] and not math.isnan(r["cells"][C.S_RANDOM][f])]
    if not valid:
        return "warning", "Keine Messung für diesen Impfanteil."
    ratios = [(r["typ"], r["cells"][C.S_DEGREE][f] / r["cells"][C.S_RANDOM][f] if r["cells"][C.S_RANDOM][f] > 0 else NAN) for r in valid]
    ratios = [x for x in ratios if not math.isnan(x[1])]
    halves = [t for t, x in ratios if x <= 0.5]
    strong = min(ratios, key=lambda x: x[1])
    weak = max(ratios, key=lambda x: x[1])
    r_strong = next(r for r in valid if r["typ"] == strong[0])
    r_weak = next(r for r in valid if r["typ"] == weak[0])
    worse = [(s, r["typ"]) for r in valid for s in C.STRATEGIES if s != C.S_RANDOM and round(r["cells"][s][f], A.ROUND) > round(r["cells"][C.S_RANDOM][f] * C.WORSE_FACTOR, A.ROUND)]
    text = (f"Bei {pct(f)} % Impfanteil senkt die Gradregel die Ausbruchsgröße in {len(halves)} von {len(valid)} Netztypen auf höchstens die Hälfte von Zufall; am stärksten in „{strong[0]}“ "
            f"({pct(r_strong['cells'][C.S_DEGREE][f], 1)} % gegen {pct(r_strong['cells'][C.S_RANDOM][f], 1)} %), am schwächsten in „{weak[0]}“ ({pct(r_weak['cells'][C.S_DEGREE][f], 1)} % gegen {pct(r_weak['cells'][C.S_RANDOM][f], 1)} %).")
    if worse:
        text += " Schlechter als Zufall: " + "; ".join(f"„{s}“ in „{t}“" for s, t in worse) + "."
    else:
        text += " Keine Strategie ist in einem Netztyp schlechter als Zufall."
    return "info", text


# --- E2: Impfanteil für die Eindämmung ------------------------------------------------------------------------------------------------------------


def containment_rows(n, c, strength, seeds=C.LIVE_SEEDS, types=C.ALL_TYPES, runs=C.EXP_RUNS, level=C.CONTAIN_LEVEL, max_f=C.THRESHOLD_MAX_F) -> list[dict]:
    """Je Netztyp und Strategie: kleinster Impfanteil, der die Ausbruchsgröße auf höchstens `level` drückt (Median über die festen Netze; wo ein Netz bis `max_f` nicht reicht, zählt 1,0)."""
    rows = []
    for typ in types:
        found = {s: [] for s in C.STRATEGIES}
        for seed in seeds:
            adj = make_instance(typ, n, c, seed, layout=False).adj
            nn = len(adj)
            _, lls = prepare(adj, strength, seed, runs)
            curves = strategy_curves(nn, lls, strategy_orders(adj, k_of(nn, max_f), seed, draws=C.EXP_DRAWS))
            for s in C.STRATEGIES:
                k = A.containment_k(curves[s], level)
                found[s].append(1.0 if k is None else k / nn)
        rows.append({"typ": typ, "fstar": {s: _med(v) for s, v in found.items()}})
    return rows


def verdict_containment(rows: list[dict], level=C.CONTAIN_LEVEL, max_f=C.THRESHOLD_MAX_F) -> tuple[str, str]:
    """Verdikt zu E2: wie viel Impfanteil braucht die beste Strategie, wie viel Zufall?"""
    if not rows:
        return "warning", "Keine Läufe."

    def show(x):
        return f"über {pct(max_f)} %" if x > max_f else f"{pct(x)} %"

    best_row = min(rows, key=lambda r: min(r["fstar"][s] for s in C.STRATEGIES))
    best_s = min(C.STRATEGIES, key=lambda s: (round(best_row["fstar"][s], A.ROUND), C.STRATEGIES.index(s)))
    worst_row = max(rows, key=lambda r: min(r["fstar"][s] for s in C.STRATEGIES))
    worst_s = min(C.STRATEGIES, key=lambda s: (round(worst_row["fstar"][s], A.ROUND), C.STRATEGIES.index(s)))
    return "info", (f"Um die Ausbruchsgröße auf höchstens {pct(level)} % zu drücken, braucht im günstigsten Netztyp („{best_row['typ']}“) die beste Strategie („{best_s}“) {show(best_row['fstar'][best_s])} Impfanteil, "
                    f"Zufall {show(best_row['fstar'][C.S_RANDOM])}; im ungünstigsten („{worst_row['typ']}“) braucht die beste („{worst_s}“) {show(worst_row['fstar'][worst_s])}, Zufall {show(worst_row['fstar'][C.S_RANDOM])}.")


# --- E3: Bekannten-Impfung ----------------------------------------------------------------------------------------------------------------------------


def acquaintance_rows(typ, n, c, strength, fs=C.ACQ_FS, seeds=C.LIVE_SEEDS, runs=C.EXP_RUNS) -> dict:
    """Im Netztyp `typ`: Ausbruchsgröße von Zufall, Bekannten, Bekannten mit Hub-Wahl und Grad über den Impfanteil (Median über die festen Netze)."""
    names = (C.S_RANDOM, C.S_ACQ, C.S_ACQ_HUB, C.S_DEGREE)
    acc = {s: {f: [] for f in fs} for s in names}
    base = []
    for seed in seeds:
        adj = make_instance(typ, n, c, seed, layout=False).adj
        nn = len(adj)
        _, lls = prepare(adj, strength, seed, runs)
        curves = strategy_curves(nn, lls, strategy_orders(adj, k_of(nn, max(fs)), seed, draws=C.EXP_DRAWS, names=names))
        base.append(float(curves[C.S_RANDOM][0]))
        for s in names:
            for f in fs:
                acc[s][f].append(at(curves[s], k_of(nn, f)))
    return {"typ": typ, "fs": list(fs), "base": _med(base), "curves": {s: [_med(acc[s][f]) for f in fs] for s in names}}


def gap_closed(result: dict, strategy, f) -> float:
    """Anteil der Lücke zwischen Zufall und Grad, den `strategy` bei Impfanteil f schließt: (Zufall - Strategie) / (Zufall - Grad); nan, wenn Grad nicht besser ist als Zufall."""
    i = result["fs"].index(f)
    rnd, deg, mine = (result["curves"][s][i] for s in (C.S_RANDOM, C.S_DEGREE, strategy))
    return (rnd - mine) / (rnd - deg) if rnd - deg > 1e-12 else NAN


def verdict_acquaintance(result: dict, f=0.10) -> tuple[str, str]:
    """Verdikt zu E3: wie viel der Lücke zwischen Zufall und Gradregel schließt Nachbarwissen?"""
    if f not in result["fs"]:
        return "warning", "Für diesen Impfanteil liegt keine Messreihe vor."
    i = result["fs"].index(f)
    cur = result["curves"]
    a, h = gap_closed(result, C.S_ACQ, f), gap_closed(result, C.S_ACQ_HUB, f)
    if math.isnan(a):
        return "info", f"In „{result['typ']}“ ist die Gradregel bei {pct(f)} % nicht besser als Zufall ({pct(cur[C.S_DEGREE][i], 1)} % gegen {pct(cur[C.S_RANDOM][i], 1)} %): es gibt keine Lücke, die Nachbarwissen schließen könnte."
    return "info", (f"In „{result['typ']}“ bei {pct(f)} % Impfanteil: Zufall {pct(cur[C.S_RANDOM][i], 1)} %, Grad {pct(cur[C.S_DEGREE][i], 1)} %. Die Bekannten-Impfung ({pct(cur[C.S_ACQ][i], 1)} %) schließt {pct(a)} % dieser Lücke, "
                    f"die Variante mit dem Nachbarn des höchsten Grades ({pct(cur[C.S_ACQ_HUB][i], 1)} %) {pct(h)} %.")


# --- E4: Ausbreitungsstärke ---------------------------------------------------------------------------------------------------------------------------


def strength_rows(typ, n, c, f, strengths=C.STRENGTHS, seeds=C.LIVE_SEEDS, runs=C.EXP_RUNS) -> list[dict]:
    """Im Netztyp `typ` und bei Impfanteil f (Anteil): Ausbruchsgröße je Strategie für verschiedene Ausbreitungsstärken (Median über die festen Netze)."""
    rows = []
    for strength in strengths:
        base, cells = [], {s: [] for s in C.STRATEGIES}
        for seed in seeds:
            adj = make_instance(typ, n, c, seed, layout=False).adj
            nn = len(adj)
            _, lls = prepare(adj, strength, seed, runs)
            k = k_of(nn, f)
            curves = strategy_curves(nn, lls, strategy_orders(adj, k, seed, draws=C.EXP_DRAWS))
            base.append(float(curves[C.S_RANDOM][0]))
            for s in C.STRATEGIES:
                cells[s].append(at(curves[s], k))
        rows.append({"strength": strength, "base": _med(base), "cells": {s: _med(v) for s, v in cells.items()}})
    return rows


def verdict_strengths(rows: list[dict], typ, f) -> tuple[str, str]:
    """Verdikt zu E4: bleibt die beste Strategie bei verschiedener Ausbreitungsstärke dieselbe?"""
    if not rows:
        return "warning", "Keine Läufe."
    parts, bests = [], []
    for r in rows:
        best = min(C.STRATEGIES, key=lambda s: (round(r["cells"][s], A.ROUND), C.STRATEGIES.index(s)))
        bests.append(best)
        parts.append(f"bei {r['strength']} %: ohne Impfung {pct(r['base'])} %, Zufall {pct(r['cells'][C.S_RANDOM], 1)} %, Grad {pct(r['cells'][C.S_DEGREE], 1)} %, beste „{best}“ ({pct(r['cells'][best], 1)} %)")
    same = len(set(bests)) == 1
    return "info", f"In „{typ}“ bei {pct(f)} % Impfanteil: " + "; ".join(parts) + ". " + (f"Die beste Strategie ist in allen Ausbreitungsstärken „{bests[0]}“." if same else "Die beste Strategie wechselt mit der Ausbreitungsstärke.")


# --- E5: Exakt auf kleinen Netzen -----------------------------------------------------------------------------------------------------------------------


def small_network(seed, n=C.EXACT_N, m=C.EXACT_M):
    """Verbundenes Zufallsnetz mit n Knoten und m verschiedenen Kanten (Ablehnungsverfahren). Rückgabe (n, Kantenliste)."""
    rng = np.random.default_rng(int(seed))
    while True:
        pairs = set()
        while len(pairs) < m:
            a, b = sorted(rng.choice(n, size=2, replace=False).tolist())
            pairs.add((a, b))
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for a, b in pairs:
            parent[find(a)] = find(b)
        if len({find(i) for i in range(n)}) == 1:
            return n, sorted(pairs)


def exact_rows(nets=C.EXACT_NETS, ks=C.EXACT_KS, p=C.EXACT_P, first_seed=100000) -> dict:
    """Auf kleinen Netzen mit exakter Ausbruchsgröße: Optimum (Aufzählung aller k-Mengen), Greedy, Gradregel (Mittel über alle Gleichstandsauflösungen) und Zufall (Mittel über alle k-Mengen).
    Rückgabe je k die Liste der Zeilen (je Netz ein Wörterbuch)."""
    out = {k: [] for k in ks}
    for i in range(nets):
        n, edges = small_network(first_seed + i)
        states = A.exact_states(n, edges, p)
        deg = [0] * n
        for a, b in edges:
            deg[a] += 1
            deg[b] += 1
        base = A.exact_outbreak(n, states, [])
        for k in ks:
            vals = A.exact_all_sets(n, states, k)
            greedy_set = tuple(sorted(A.exact_greedy(n, states, k)))
            out[k].append({"base": base, "optimum": min(vals.values()), "greedy": vals[greedy_set], "degree": float(np.mean([vals[s] for s in A.degree_tie_sets(deg, k)])), "random": float(np.mean(list(vals.values())))})
    return {"rows": out, "nets": nets, "p": p}


def exact_summary(result: dict, k) -> dict:
    rows = result["rows"][k]
    opt = [r["optimum"] for r in rows]
    return {"base": float(np.mean([r["base"] for r in rows])), "optimum": float(np.mean(opt)), "greedy": float(np.mean([r["greedy"] for r in rows])), "degree": float(np.mean([r["degree"] for r in rows])),
            "random": float(np.mean([r["random"] for r in rows])), "greedy_hits": sum(1 for r in rows if math.isclose(r["greedy"], r["optimum"], rel_tol=1e-9)), "nets": len(rows),
            "degree_over": _med([(r["degree"] - r["optimum"]) / r["optimum"] for r in rows if r["optimum"] > 0]), "worst_greedy": min((r["optimum"] / r["greedy"] for r in rows if r["greedy"] > 0), default=NAN)}


def verdict_exact(result: dict) -> tuple[str, str]:
    """Verdikt zu E5: wie weit sind Greedy und die Gradregel vom exakten Optimum entfernt?"""
    ks = sorted(result["rows"])
    if not ks:
        return "warning", "Keine Läufe."
    parts = []
    for k in ks:
        s = exact_summary(result, k)
        parts.append(f"k = {k}: Optimum {pct(s['optimum'], 1)} %, Greedy {pct(s['greedy'], 1)} % (trifft das Optimum in {s['greedy_hits']} von {s['nets']} Netzen), Grad {pct(s['degree'], 1)} % (im Median {pct(s['degree_over'], 1)} % über dem Optimum), "
                     f"Zufall {pct(s['random'], 1)} %")
    return "info", f"Auf {result['nets']} kleinen Netzen ({C.EXACT_N} Betriebe, {C.EXACT_M} Partnerschaften, p = {de(result['p'], 1)}; ohne Impfung {pct(exact_summary(result, ks[0])['base'], 1)} %), exakt gerechnet: " + "; ".join(parts) + "."
