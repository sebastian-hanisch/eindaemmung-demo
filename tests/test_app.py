"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: lädt app.py mit den Standardeinstellungen, klickt jeden Button, fährt jeden Slider an seine Grenzen,
prüft Permalink, Netztypen, Strategien und alle fünf Experimente; es darf kein Python-Fehler auftreten."""

import os

import pytest
from streamlit.testing.v1 import AppTest

import eid_constants as C

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
EXPERIMENTS = ("strategies", "containment", "acquaintance", "strengths", "exact")


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _metric(at, label):
    return next(m.value for m in at.metric if m.label == label)


def test_app_loads_without_exception():
    at = _fresh_app()
    assert _metric(at, "Betriebe / Partnerschaften") == "150 / 450" and _metric(at, "Übertragungswahrscheinlichkeit p") == "0,246"
    assert _metric(at, "Ausbruchsgröße mit 15 Impfungen") == "17,9 %" and _metric(at, "Wissen (Abfragen)") == "0"
    assert not at.error and not at.warning


def test_every_preset_click_does_not_raise():
    for name in C.PRESETS:
        at = _fresh_app()
        at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
        assert not at.exception, (name, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            slider.set_value(int(value) if isinstance(slider.value, int) else value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


def test_all_sliders_at_their_minimum_and_all_at_their_maximum_do_not_raise():
    for edge in ("min", "max"):
        at = _fresh_app()
        for index in range(len(at.slider)):
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            slider.set_value(int(value) if isinstance(slider.value, int) else value)
        at.run(timeout=TIMEOUT)
        assert not at.exception, (edge, [str(e) for e in at.exception])


@pytest.mark.parametrize("typ", C.ALL_TYPES)
def test_every_network_type_renders_with_every_strategy(typ):
    at = _fresh_app()
    at.selectbox(key="netztyp_select").set_value(typ).run(timeout=TIMEOUT)
    assert not at.exception
    for strategy in C.STRATEGIES:
        at.selectbox(key="strategy_select").set_value(strategy).run(timeout=TIMEOUT)
        assert not at.exception, (typ, strategy, [str(e) for e in at.exception])


def test_a_strategy_worse_than_random_is_reported_as_warning():
    at = _fresh_app()
    at.sidebar.button(key="preset_Gitter: Betweenness schlechter als Zufall").click().run(timeout=TIMEOUT)
    assert not at.exception
    assert any("schlechter als Zufall" in w.value for w in at.warning)


def test_permalink_values_are_clamped_and_unknown_choices_ignored():
    at = AppTest.from_file(APP_PATH)
    at.query_params["n"] = "5"
    at.query_params["c"] = "99"
    at.query_params["f"] = "-3"
    at.query_params["staerke"] = "500"
    at.query_params["typ"] = "gibt es nicht"
    at.query_params["strategie"] = "Unsinn"
    at.run(timeout=TIMEOUT)
    assert not at.exception
    assert at.slider(key="n_slider").value == C.N_MIN and at.slider(key="c_slider").value == C.C_MAX and at.slider(key="f_slider").value == C.F_MIN
    assert at.slider(key="strength_slider").value == C.STRENGTH_MAX and at.selectbox(key="netztyp_select").value == C.T_RANDOM and at.selectbox(key="strategy_select").value == C.DEFAULT_STRATEGY


def test_permalink_selects_a_network_type_and_a_strategy():
    at = AppTest.from_file(APP_PATH)
    at.query_params["typ"] = C.T_GRID
    at.query_params["strategie"] = C.S_ACQ_HUB
    at.run(timeout=TIMEOUT)
    assert not at.exception and at.selectbox(key="netztyp_select").value == C.T_GRID and at.selectbox(key="strategy_select").value == C.S_ACQ_HUB


def test_every_experiment_runs_and_is_invalidated_by_a_setting_change():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    at.slider(key="n_slider").set_value(C.N_MIN).run(timeout=TIMEOUT)         # kleines Netz: schnell
    for name in EXPERIMENTS:
        at.button(key=f"run_{name}").click().run(timeout=TIMEOUT)
        assert not at.exception, (name, [str(e) for e in at.exception])
    texts = " ".join(x.value for x in list(at.info) + list(at.warning) + list(at.success))
    for fragment in ("Impfanteil senkt die Gradregel die Ausbruchsgröße", "Um die Ausbruchsgröße auf höchstens 5 %", "In „Zufallsnetz“ bei 10 % Impfanteil", "exakt gerechnet"):
        assert fragment in texts, fragment
    assert "bei 10 %: ohne Impfung" in texts
    at.slider(key="n_slider").set_value(C.N_MIN + 10).run(timeout=TIMEOUT)
    assert not at.exception
    assert sum("neu starten" in i.value for i in at.info) >= len(EXPERIMENTS) - 1       # alle von n abhängigen Ergebnisse sind ungültig (der exakte Vergleich hängt von keiner Einstellung ab)
