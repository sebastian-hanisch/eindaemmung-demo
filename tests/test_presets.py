"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, jedes Preset zeigt, wofür es benannt ist."""

import eid_constants as C
import eid_evaluation as ev
import eid_presets as P


def _settings(name):
    return ev.Settings(**C.PRESETS[name])


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for name, p in C.PRESETS.items():
        assert p["netztyp"] in C.ALL_TYPES and C.N_MIN <= p["n"] <= C.N_MAX and C.C_MIN <= p["c"] <= C.C_MAX and 0 <= p["seed"] <= C.SEED_MAX, name
        assert C.STRENGTH_MIN <= p["strength"] <= C.STRENGTH_MAX and C.F_MIN <= p["f"] <= C.F_MAX and p["strategy"] in C.STRATEGIES, name


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS[C.DEFAULT_PRESET_NAME]) == ev.Settings()
    assert next(iter(C.PRESETS)) == C.DEFAULT_PRESET_NAME


def test_setting_specs_cover_every_preset_key_and_defaults_match():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    for key, state_key in P.PRESET_KEYS.items():
        assert P.SETTING_SPECS[state_key].default == C.PRESETS[C.DEFAULT_PRESET_NAME][key], key


def test_every_preset_differs_from_the_default_in_something_besides_the_network_type():
    default = C.PRESETS[C.DEFAULT_PRESET_NAME]
    for name, p in C.PRESETS.items():
        if name != C.DEFAULT_PRESET_NAME:
            assert any(p[k] != default[k] for k in p if k != "netztyp"), name


def test_each_preset_shows_what_its_name_says():
    an = {name: ev.analyse(_settings(name)) for name in C.PRESETS}
    d = an["Zufallsnetz ohne Wissen (Voreinstellung)"]
    assert d.value(C.S_RANDOM) < d.base and d.value(C.S_DEGREE) < 0.6 * d.value(C.S_RANDOM)           # Zufall wirkt, aber schwach
    s = an["Superspreader: Wissen lohnt"]
    assert s.value(C.S_DEGREE) < 0.2 * s.value(C.S_RANDOM) and s.value(C.S_CORE) > 0.9 * s.value(C.S_RANDOM)
    h = an["Nachbarwissen reicht fast"]
    assert h.value(C.S_ACQ_HUB) < 0.25 * h.value(C.S_RANDOM)
    g = an["Gitter: Betweenness schlechter als Zufall"]
    assert g.value(C.S_BETWEENNESS) > 1.05 * g.value(C.S_RANDOM)
    r = an["Ring: adaptiv hilft"]
    assert r.value(C.S_ADAPTIVE) < 0.95 * r.value(C.S_DEGREE)
    st = an["Starke Ausbreitung (60 %)"]
    assert abs(st.base - 0.6) < 0.03 and st.value(C.S_DEGREE) < 0.2 * st.value(C.S_RANDOM)


def test_every_preset_runs_and_the_verdict_is_a_known_kind():
    for name in C.PRESETS:
        an = ev.analyse(_settings(name))
        assert an.inst.n >= 2 and 1 <= an.k < an.inst.n and len(an.vaccinated) == an.k
        assert ev.verdict_main(an)[0] in ("success", "info", "warning"), name
