"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import eid_algorithm as A
import eid_constants as C
from eid_evaluation import de, pct


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=340, bottom=10):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=bottom), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _pct_axis(fig, title, top=None):
    fig.update_yaxes(title_text=title, ticksuffix=" %", rangemode="tozero", **({"range": [0, top]} if top else {}))
    return fig


def build_network(inst, risk, vaccinated, strategy, height=440):
    """Netz mit festen Positionen: Knoten nach der Wahrscheinlichkeit gefärbt, im Ausbruch befallen zu werden; die gesicherten Betriebe sind groß und rot umrandet."""
    n = inst.n
    size = 5 if n > 200 else 8
    u, v = A.edge_arrays(inst.adj)
    xs, ys = [], []
    for a, b in zip(u.tolist(), v.tolist()):
        xs += [inst.pos[a][0], inst.pos[b][0], None]
        ys += [inst.pos[a][1], inst.pos[b][1], None]
    vacc = set(int(x) for x in vaccinated)
    rest = [i for i in range(n) if i not in vacc]
    top = max([float(risk[i]) for i in rest] + [1e-9])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_EDGE, width=0.7), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=[inst.pos[i][0] for i in rest], y=[inst.pos[i][1] for i in rest], mode="markers", name="Betrieb",
                             marker=dict(size=size, color=[float(risk[i]) for i in rest], colorscale="YlOrRd", cmin=0, cmax=top, showscale=True,
                                         colorbar=dict(title=dict(text="Befall"), thickness=12, len=0.8, tickformat=".0%"), line=dict(color="rgba(40,40,40,0.45)", width=0.4)),
                             hovertext=[f"Betrieb {i}: {len(inst.adj[i])} Partner, Befall mit {100 * float(risk[i]):.1f} %" for i in rest], hoverinfo="text", showlegend=False))
    fig.add_trace(go.Scatter(x=[inst.pos[i][0] for i in vacc], y=[inst.pos[i][1] for i in vacc], mode="markers", name=f"gesichert ({strategy})",
                             marker=dict(size=size + 7, color="rgba(255,255,255,0.9)", line=dict(color=C.COLOR_VACC, width=2.5)),
                             hovertext=[f"gesichert: Betrieb {i}, {len(inst.adj[i])} Partner" for i in sorted(vacc)], hoverinfo="text"))
    fig.add_trace(go.Scatter(x=[-0.04, 1.04], y=[-0.04, 1.04], mode="markers", marker=dict(size=1, color="rgba(0,0,0,0)"), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, autorange=True)
    fig.update_yaxes(visible=False, autorange=True, scaleanchor="x", scaleratio=1)
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.02), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_methods(an):
    """Ausbruchsgröße aller Strategien bei k Impfungen (Balken), mit der Linie „ohne Impfung“."""
    names = list(C.STRATEGIES)
    ys = [100.0 * an.value(s) for s in names]
    fig = go.Figure(go.Bar(x=names, y=ys, marker_color=[C.STRATEGY_COLORS[s] for s in names], text=[de(y, 1) for y in ys], textposition="outside"))
    fig.add_hline(y=100.0 * an.base, line=dict(color="rgba(120,120,120,0.9)", dash="dash"), annotation_text="ohne Impfung", annotation_position="top left")
    fig.update_xaxes(tickangle=-25)
    _pct_axis(fig, "erwartete Ausbruchsgröße")
    return _base(fig, height=380, bottom=130)


def build_strategy_bars(rows, f):
    """Ausbruchsgröße je Netztyp und Strategie bei Impfanteil f."""
    fig = go.Figure()
    for s in C.STRATEGIES:
        ys = [100.0 * r["cells"][s][f] for r in rows]
        fig.add_trace(go.Bar(x=[r["typ"] for r in rows], y=ys, name=s, marker_color=C.STRATEGY_COLORS[s], text=[de(y, 0) for y in ys], textposition="outside"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(tickangle=-20)
    _pct_axis(fig, f"Ausbruchsgröße bei {pct(f)} % Impfanteil")
    return _base(fig, height=420, bottom=120)


def build_containment(rows, max_f=C.THRESHOLD_MAX_F):
    """Kleinster Impfanteil für die Eindämmung je Netztyp und Strategie; was bis `max_f` nicht reicht, wird als Balken bis zum Rand gezeigt."""
    fig = go.Figure()
    for s in C.STRATEGIES:
        ys = [100.0 * min(r["fstar"][s], max_f * 1.08) for r in rows]
        text = [f"> {pct(max_f)}" if r["fstar"][s] > max_f else de(100.0 * r["fstar"][s], 0) for r in rows]
        fig.add_trace(go.Bar(x=[r["typ"] for r in rows], y=ys, name=s, marker_color=C.STRATEGY_COLORS[s], text=text, textposition="outside"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(tickangle=-20)
    _pct_axis(fig, "nötiger Impfanteil")
    return _base(fig, height=420, bottom=120)


def build_acquaintance(result):
    """Ausbruchsgröße über den Impfanteil für Zufall, Bekannte, Bekannte mit Hub-Wahl und Grad."""
    fig = go.Figure()
    xs = [100.0 * f for f in result["fs"]]
    for s in (C.S_RANDOM, C.S_ACQ, C.S_ACQ_HUB, C.S_DEGREE):
        fig.add_trace(go.Scatter(x=xs, y=[100.0 * y for y in result["curves"][s]], mode="lines+markers", name=s, line=dict(color=C.STRATEGY_COLORS[s], width=3)))
    fig.update_xaxes(title_text="Impfanteil (%)")
    _pct_axis(fig, "Ausbruchsgröße")
    return _base(fig, height=360, bottom=50)


def build_strengths(rows):
    """Ausbruchsgröße je Strategie für verschiedene Ausbreitungsstärken."""
    fig = go.Figure()
    xs = [f"{r['strength']} % (ohne Impfung {pct(r['base'])} %)" for r in rows]
    for s in C.STRATEGIES:
        ys = [100.0 * r["cells"][s] for r in rows]
        fig.add_trace(go.Bar(x=xs, y=ys, name=s, marker_color=C.STRATEGY_COLORS[s], text=[de(y, 0) for y in ys], textposition="outside"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text="Ausbreitungsstärke")
    _pct_axis(fig, "Ausbruchsgröße")
    return _base(fig, height=380, bottom=60)


def build_exact(result, summary):
    """Auf kleinen Netzen: ohne Impfung, Zufall, Grad, Greedy und Optimum je Zahl der Impfungen (Mittel über die Netze)."""
    fig = go.Figure()
    ks = sorted(result["rows"])
    series = (("ohne Impfung", "base", "rgba(120,120,120,0.8)"), ("Zufall (Mittel aller Mengen)", "random", C.STRATEGY_COLORS[C.S_RANDOM]), ("Grad", "degree", C.STRATEGY_COLORS[C.S_DEGREE]),
              ("Greedy", "greedy", C.COLOR_C), ("Optimum", "optimum", C.COLOR_B))
    for label, key, color in series:
        ys = [100.0 * summary(result, k)[key] for k in ks]
        fig.add_trace(go.Bar(x=[f"k = {k}" for k in ks], y=ys, name=label, marker_color=color, text=[de(y, 1) for y in ys], textposition="outside"))
    fig.update_layout(barmode="group")
    _pct_axis(fig, "Ausbruchsgröße (exakt)")
    return _base(fig, height=340, bottom=60)
