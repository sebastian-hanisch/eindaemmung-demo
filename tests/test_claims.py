"""Jede Zahl aus der README wird hier über dieselben Auswertungsfunktionen wie in der App nachgerechnet (DEMO-PLAYBOOK §4).

Netze der Messreihen: die acht festen Netze `SWEEP_SEEDS` je Zelle, n = 250, c = 6, Ausbreitungsstärke 30 %, wo nichts anderes steht; erwartete Ausbruchsgröße (Anteil der Betriebe), Median über die acht Netze,
je Netz 60 Schnappschüsse und 3 bis 5 Ziehungen je Strategie (`EXP_DRAWS`). Zufall läuft über seedbare Generatoren und ist plattformstabil; Werte stehen auf drei Nachkommastellen (Anteil), das Band 0,0006
fängt die Rundung."""

from functools import lru_cache

import pytest

import eid_algorithm as A
import eid_constants as C
import eid_evaluation as ev

SW = C.SWEEP_SEEDS
TOL = 0.0006
BA, RANDOM, POWER, COMM, RING, GRID = C.T_BA, C.T_RANDOM, C.T_POWER, C.T_COMMUNITIES, C.T_RING, C.T_GRID

EXPECT = {'V': {'E1': 'Bei 10 % Impfanteil senkt die Gradregel die Ausbruchsgröße in 4 von 6 Netztypen auf höchstens die Hälfte von Zufall; am stärksten in „Potenzgesetz-Netz“ '
             '(0,7 % gegen 22,5 %), am schwächsten in „Gitter“ (10,3 % gegen 12,3 %). Schlechter als Zufall: „Betweenness“ in „Gitter“.',
       'E2': 'Um die Ausbruchsgröße auf höchstens 5 % zu drücken, braucht im günstigsten Netztyp („Potenzgesetz-Netz“) die beste Strategie („Grad“) 2 % Impfanteil, '
             'Zufall über 40 %; im ungünstigsten („Gitter“) braucht die beste („Grad adaptiv“) 16 %, Zufall 23 %.',
       'E3 Skalenfreies Netz (BA)': 'In „Skalenfreies Netz (BA)“ bei 10 % Impfanteil: Zufall 20,8 %, Grad 1,1 %. Die Bekannten-Impfung (8,1 %) schließt 64 % dieser '
                                    'Lücke, die Variante mit dem Nachbarn des höchsten Grades (1,8 %) 97 %.',
       'E3 Zufallsnetz': 'In „Zufallsnetz“ bei 10 % Impfanteil: Zufall 15,9 %, Grad 5,6 %. Die Bekannten-Impfung (13,6 %) schließt 22 % dieser Lücke, die Variante mit '
                         'dem Nachbarn des höchsten Grades (7,0 %) 86 %.',
       'E5': 'Auf 10 kleinen Netzen (9 Betriebe, 12 Partnerschaften, p = 0,5; ohne Impfung 51,1 %), exakt gerechnet: k = 2: Optimum 20,8 %, Greedy 20,8 % (trifft das '
             'Optimum in 9 von 10 Netzen), Grad 21,9 % (im Median 1,5 % über dem Optimum), Zufall 33,3 %; k = 3: Optimum 15,3 %, Greedy 15,6 % (trifft das Optimum in 8 '
             'von 10 Netzen), Grad 16,9 % (im Median 9,1 % über dem Optimum), Zufall 27,0 %.'},
 'E1': {'Zufallsnetz': {'base': 0.292,
                        'cells': {'Zufall': {'0.05': 0.221, '0.1': 0.159, '0.2': 0.077},
                                  'Grad': {'0.05': 0.127, '0.1': 0.056, '0.2': 0.018},
                                  'Grad adaptiv': {'0.05': 0.125, '0.1': 0.05, '0.2': 0.014},
                                  'Betweenness': {'0.05': 0.134, '0.1': 0.06, '0.2': 0.019},
                                  'Kernzahl': {'0.05': 0.217, '0.1': 0.145, '0.2': 0.055},
                                  'Bekannte': {'0.05': 0.21, '0.1': 0.136, '0.2': 0.055},
                                  'Bekannte (Nachbar mit höchstem Grad)': {'0.05': 0.153, '0.1': 0.07, '0.2': 0.022}}},
        'Potenzgesetz-Netz': {'base': 0.3,
                              'cells': {'Zufall': {'0.05': 0.26, '0.1': 0.225, '0.2': 0.151},
                                        'Grad': {'0.05': 0.013, '0.1': 0.007, '0.2': 0.006},
                                        'Grad adaptiv': {'0.05': 0.014, '0.1': 0.007, '0.2': 0.005},
                                        'Betweenness': {'0.05': 0.015, '0.1': 0.008, '0.2': 0.006},
                                        'Kernzahl': {'0.05': 0.047, '0.1': 0.011, '0.2': 0.007},
                                        'Bekannte': {'0.05': 0.098, '0.1': 0.036, '0.2': 0.011},
                                        'Bekannte (Nachbar mit höchstem Grad)': {'0.05': 0.05, '0.1': 0.014, '0.2': 0.007}}},
        'Skalenfreies Netz (BA)': {'base': 0.303,
                                   'cells': {'Zufall': {'0.05': 0.251, '0.1': 0.208, '0.2': 0.132},
                                             'Grad': {'0.05': 0.026, '0.1': 0.011, '0.2': 0.007},
                                             'Grad adaptiv': {'0.05': 0.026, '0.1': 0.01, '0.2': 0.006},
                                             'Betweenness': {'0.05': 0.029, '0.1': 0.011, '0.2': 0.007},
                                             'Kernzahl': {'0.05': 0.25, '0.1': 0.201, '0.2': 0.128},
                                             'Bekannte': {'0.05': 0.185, '0.1': 0.081, '0.2': 0.022},
                                             'Bekannte (Nachbar mit höchstem Grad)': {'0.05': 0.068, '0.1': 0.018, '0.2': 0.008}}},
        'Verbünde': {'base': 0.291,
                     'cells': {'Zufall': {'0.05': 0.22, '0.1': 0.154, '0.2': 0.069},
                               'Grad': {'0.05': 0.126, '0.1': 0.052, '0.2': 0.017},
                               'Grad adaptiv': {'0.05': 0.121, '0.1': 0.043, '0.2': 0.014},
                               'Betweenness': {'0.05': 0.132, '0.1': 0.057, '0.2': 0.022},
                               'Kernzahl': {'0.05': 0.207, '0.1': 0.134, '0.2': 0.055},
                               'Bekannte': {'0.05': 0.202, '0.1': 0.129, '0.2': 0.051},
                               'Bekannte (Nachbar mit höchstem Grad)': {'0.05': 0.155, '0.1': 0.072, '0.2': 0.023}}},
        'Ring mit Abkürzungen': {'base': 0.295,
                                 'cells': {'Zufall': {'0.05': 0.193, '0.1': 0.122, '0.2': 0.057},
                                           'Grad': {'0.05': 0.108, '0.1': 0.062, '0.2': 0.033},
                                           'Grad adaptiv': {'0.05': 0.105, '0.1': 0.051, '0.2': 0.028},
                                           'Betweenness': {'0.05': 0.121, '0.1': 0.072, '0.2': 0.034},
                                           'Kernzahl': {'0.05': 0.191, '0.1': 0.12, '0.2': 0.06},
                                           'Bekannte': {'0.05': 0.194, '0.1': 0.128, '0.2': 0.058},
                                           'Bekannte (Nachbar mit höchstem Grad)': {'0.05': 0.155, '0.1': 0.082, '0.2': 0.036}}},
        'Gitter': {'base': 0.295,
                   'cells': {'Zufall': {'0.05': 0.191, '0.1': 0.123, '0.2': 0.058},
                             'Grad': {'0.05': 0.172, '0.1': 0.103, '0.2': 0.044},
                             'Grad adaptiv': {'0.05': 0.167, '0.1': 0.091, '0.2': 0.033},
                             'Betweenness': {'0.05': 0.194, '0.1': 0.15, '0.2': 0.103},
                             'Kernzahl': {'0.05': 0.187, '0.1': 0.124, '0.2': 0.058},
                             'Bekannte': {'0.05': 0.19, '0.1': 0.123, '0.2': 0.059},
                             'Bekannte (Nachbar mit höchstem Grad)': {'0.05': 0.174, '0.1': 0.112, '0.2': 0.052}}}},
 'E2': {'Zufallsnetz': {'Zufall': 0.262,
                        'Grad': 0.11,
                        'Grad adaptiv': 0.102,
                        'Betweenness': 0.114,
                        'Kernzahl': 0.214,
                        'Bekannte': 0.214,
                        'Bekannte (Nachbar mit höchstem Grad)': 0.126},
        'Potenzgesetz-Netz': {'Zufall': 1.0,
                              'Grad': 0.024,
                              'Grad adaptiv': 0.024,
                              'Betweenness': 0.024,
                              'Kernzahl': 0.046,
                              'Bekannte': 0.088,
                              'Bekannte (Nachbar mit höchstem Grad)': 0.05},
        'Skalenfreies Netz (BA)': {'Zufall': 0.364,
                                   'Grad': 0.036,
                                   'Grad adaptiv': 0.034,
                                   'Betweenness': 0.034,
                                   'Kernzahl': 0.382,
                                   'Bekannte': 0.136,
                                   'Bekannte (Nachbar mit höchstem Grad)': 0.06},
        'Verbünde': {'Zufall': 0.248,
                     'Grad': 0.104,
                     'Grad adaptiv': 0.096,
                     'Betweenness': 0.112,
                     'Kernzahl': 0.214,
                     'Bekannte': 0.204,
                     'Bekannte (Nachbar mit höchstem Grad)': 0.128},
        'Ring mit Abkürzungen': {'Zufall': 0.222,
                                 'Grad': 0.132,
                                 'Grad adaptiv': 0.104,
                                 'Betweenness': 0.142,
                                 'Kernzahl': 0.228,
                                 'Bekannte': 0.22,
                                 'Bekannte (Nachbar mit höchstem Grad)': 0.158},
        'Gitter': {'Zufall': 0.227,
                   'Grad': 0.188,
                   'Grad adaptiv': 0.16,
                   'Betweenness': 0.383,
                   'Kernzahl': 0.227,
                   'Bekannte': 0.23,
                   'Bekannte (Nachbar mit höchstem Grad)': 0.207}},
 'E3': {'Skalenfreies Netz (BA)': {'base': 0.303,
                                   'curves': {'Zufall': [0.277, 0.251, 0.208, 0.165, 0.132, 0.073],
                                              'Bekannte': [0.249, 0.185, 0.081, 0.041, 0.022, 0.01],
                                              'Bekannte (Nachbar mit höchstem Grad)': [0.184, 0.068, 0.018, 0.011, 0.008, 0.006],
                                              'Grad': [0.101, 0.026, 0.011, 0.008, 0.007, 0.005]},
                                   'gap': {'Bekannte': 0.641, 'Bekannte (Nachbar mit höchstem Grad)': 0.965}},
        'Zufallsnetz': {'base': 0.292,
                        'curves': {'Zufall': [0.264, 0.221, 0.159, 0.112, 0.077, 0.036],
                                   'Bekannte': [0.256, 0.21, 0.136, 0.085, 0.055, 0.024],
                                   'Bekannte (Nachbar mit höchstem Grad)': [0.232, 0.153, 0.07, 0.036, 0.022, 0.012],
                                   'Grad': [0.203, 0.127, 0.056, 0.028, 0.018, 0.01]},
                        'gap': {'Bekannte': 0.225, 'Bekannte (Nachbar mit höchstem Grad)': 0.859}}},
 'E4': {'Skalenfreies Netz (BA)': {'10': {'base': 0.096,
                                          'cells': {'Zufall': 0.062,
                                                    'Grad': 0.007,
                                                    'Grad adaptiv': 0.007,
                                                    'Betweenness': 0.007,
                                                    'Kernzahl': 0.059,
                                                    'Bekannte': 0.021,
                                                    'Bekannte (Nachbar mit höchstem Grad)': 0.009}},
                                   '30': {'base': 0.303,
                                          'cells': {'Zufall': 0.208,
                                                    'Grad': 0.011,
                                                    'Grad adaptiv': 0.01,
                                                    'Betweenness': 0.011,
                                                    'Kernzahl': 0.201,
                                                    'Bekannte': 0.081,
                                                    'Bekannte (Nachbar mit höchstem Grad)': 0.018}},
                                   '60': {'base': 0.605,
                                          'cells': {'Zufall': 0.47,
                                                    'Grad': 0.031,
                                                    'Grad adaptiv': 0.028,
                                                    'Betweenness': 0.032,
                                                    'Kernzahl': 0.47,
                                                    'Bekannte': 0.301,
                                                    'Bekannte (Nachbar mit höchstem Grad)': 0.084}}},
        'Zufallsnetz': {'10': {'base': 0.101,
                               'cells': {'Zufall': 0.052,
                                         'Grad': 0.022,
                                         'Grad adaptiv': 0.02,
                                         'Betweenness': 0.022,
                                         'Kernzahl': 0.047,
                                         'Bekannte': 0.043,
                                         'Bekannte (Nachbar mit höchstem Grad)': 0.026}},
                        '30': {'base': 0.292,
                               'cells': {'Zufall': 0.159,
                                         'Grad': 0.056,
                                         'Grad adaptiv': 0.05,
                                         'Betweenness': 0.06,
                                         'Kernzahl': 0.145,
                                         'Bekannte': 0.136,
                                         'Bekannte (Nachbar mit höchstem Grad)': 0.07}},
                        '60': {'base': 0.604,
                               'cells': {'Zufall': 0.446,
                                         'Grad': 0.254,
                                         'Grad adaptiv': 0.235,
                                         'Betweenness': 0.26,
                                         'Kernzahl': 0.418,
                                         'Bekannte': 0.414,
                                         'Bekannte (Nachbar mit höchstem Grad)': 0.297}}},
        'Ring mit Abkürzungen': {'10': {'base': 0.111,
                                        'cells': {'Zufall': 0.055,
                                                  'Grad': 0.036,
                                                  'Grad adaptiv': 0.031,
                                                  'Betweenness': 0.04,
                                                  'Kernzahl': 0.054,
                                                  'Bekannte': 0.054,
                                                  'Bekannte (Nachbar mit höchstem Grad)': 0.042}},
                                 '30': {'base': 0.295,
                                        'cells': {'Zufall': 0.122,
                                                  'Grad': 0.062,
                                                  'Grad adaptiv': 0.051,
                                                  'Betweenness': 0.072,
                                                  'Kernzahl': 0.12,
                                                  'Bekannte': 0.128,
                                                  'Bekannte (Nachbar mit höchstem Grad)': 0.082}},
                                 '60': {'base': 0.603,
                                        'cells': {'Zufall': 0.271,
                                                  'Grad': 0.11,
                                                  'Grad adaptiv': 0.086,
                                                  'Betweenness': 0.14,
                                                  'Kernzahl': 0.284,
                                                  'Bekannte': 0.284,
                                                  'Bekannte (Nachbar mit höchstem Grad)': 0.166}}},
        'Gitter': {'10': {'base': 0.098,
                          'cells': {'Zufall': 0.05,
                                    'Grad': 0.043,
                                    'Grad adaptiv': 0.041,
                                    'Betweenness': 0.06,
                                    'Kernzahl': 0.049,
                                    'Bekannte': 0.05,
                                    'Bekannte (Nachbar mit höchstem Grad)': 0.047}},
                   '30': {'base': 0.295,
                          'cells': {'Zufall': 0.123,
                                    'Grad': 0.103,
                                    'Grad adaptiv': 0.091,
                                    'Betweenness': 0.15,
                                    'Kernzahl': 0.124,
                                    'Bekannte': 0.123,
                                    'Bekannte (Nachbar mit höchstem Grad)': 0.112}},
                   '60': {'base': 0.567,
                          'cells': {'Zufall': 0.268,
                                    'Grad': 0.222,
                                    'Grad adaptiv': 0.198,
                                    'Betweenness': 0.338,
                                    'Kernzahl': 0.264,
                                    'Bekannte': 0.26,
                                    'Bekannte (Nachbar mit höchstem Grad)': 0.251}}}},
 'E5': {'2': {'base': 0.511,
              'optimum': 0.208,
              'greedy': 0.208,
              'degree': 0.219,
              'random': 0.333,
              'greedy_hits': 9,
              'nets': 10,
              'degree_over': 0.015,
              'worst_greedy': 0.982},
        '3': {'base': 0.511,
              'optimum': 0.153,
              'greedy': 0.156,
              'degree': 0.169,
              'random': 0.27,
              'greedy_hits': 8,
              'nets': 10,
              'degree_over': 0.091,
              'worst_greedy': 0.875}},
 'grid': {'150': [[0.151, 0.143, 0.123],
                  [0.126, 0.129, 0.104],
                  [0.166, 0.165, 0.136],
                  [0.146, 0.142, 0.125],
                  [0.159, 0.165, 0.131],
                  [0.169, 0.174, 0.144],
                  [0.142, 0.133, 0.114],
                  [0.155, 0.158, 0.127]],
          '250': [[0.152, 0.127, 0.107],
                  [0.152, 0.119, 0.101],
                  [0.159, 0.134, 0.107],
                  [0.17, 0.127, 0.114],
                  [0.156, 0.129, 0.108],
                  [0.145, 0.122, 0.098],
                  [0.129, 0.1, 0.086],
                  [0.145, 0.117, 0.099]]},
 'presets': {'Zufallsnetz ohne Wissen (Voreinstellung)': {'n': 150,
                                                          'm': 450,
                                                          'k': 15,
                                                          'p': 0.246,
                                                          'base': 0.308,
                                                          'value': 0.179,
                                                          'random': 0.179,
                                                          'degree': 0.09,
                                                          'best': 'Grad adaptiv',
                                                          'cost': 0.0,
                                                          'verdict': 'info',
                                                          'all': {'Zufall': 0.179,
                                                                  'Grad': 0.09,
                                                                  'Grad adaptiv': 0.074,
                                                                  'Betweenness': 0.087,
                                                                  'Kernzahl': 0.164,
                                                                  'Bekannte': 0.166,
                                                                  'Bekannte (Nachbar mit höchstem Grad)': 0.097}},
             'Superspreader: Wissen lohnt': {'n': 150,
                                             'm': 444,
                                             'k': 15,
                                             'p': 0.239,
                                             'base': 0.305,
                                             'value': 0.021,
                                             'random': 0.195,
                                             'degree': 0.021,
                                             'best': 'Grad adaptiv',
                                             'cost': 150.0,
                                             'verdict': 'success',
                                             'all': {'Zufall': 0.195,
                                                     'Grad': 0.021,
                                                     'Grad adaptiv': 0.021,
                                                     'Betweenness': 0.021,
                                                     'Kernzahl': 0.203,
                                                     'Bekannte': 0.116,
                                                     'Bekannte (Nachbar mit höchstem Grad)': 0.039}},
             'Nachbarwissen reicht fast': {'n': 150,
                                           'm': 444,
                                           'k': 15,
                                           'p': 0.239,
                                           'base': 0.305,
                                           'value': 0.039,
                                           'random': 0.195,
                                           'degree': 0.021,
                                           'best': 'Grad adaptiv',
                                           'cost': 103.8,
                                           'verdict': 'success',
                                           'all': {'Zufall': 0.195,
                                                   'Grad': 0.021,
                                                   'Grad adaptiv': 0.021,
                                                   'Betweenness': 0.021,
                                                   'Kernzahl': 0.203,
                                                   'Bekannte': 0.116,
                                                   'Bekannte (Nachbar mit höchstem Grad)': 0.039}},
             'Gitter: Betweenness schlechter als Zufall': {'n': 256,
                                                           'm': 705,
                                                           'k': 26,
                                                           'p': 0.355,
                                                           'base': 0.307,
                                                           'value': 0.15,
                                                           'random': 0.13,
                                                           'degree': 0.105,
                                                           'best': 'Grad adaptiv',
                                                           'cost': 961.0,
                                                           'verdict': 'warning',
                                                           'all': {'Zufall': 0.13,
                                                                   'Grad': 0.105,
                                                                   'Grad adaptiv': 0.095,
                                                                   'Betweenness': 0.15,
                                                                   'Kernzahl': 0.123,
                                                                   'Bekannte': 0.124,
                                                                   'Bekannte (Nachbar mit höchstem Grad)': 0.127}},
             'Ring: adaptiv hilft': {'n': 150,
                                     'm': 471,
                                     'k': 15,
                                     'p': 0.312,
                                     'base': 0.271,
                                     'value': 0.066,
                                     'random': 0.138,
                                     'degree': 0.086,
                                     'best': 'Grad adaptiv',
                                     'cost': 621.0,
                                     'verdict': 'info',
                                     'all': {'Zufall': 0.138,
                                             'Grad': 0.086,
                                             'Grad adaptiv': 0.066,
                                             'Betweenness': 0.088,
                                             'Kernzahl': 0.129,
                                             'Bekannte': 0.133,
                                             'Bekannte (Nachbar mit höchstem Grad)': 0.09}},
             'Starke Ausbreitung (60 %)': {'n': 150,
                                           'm': 416,
                                           'k': 15,
                                           'p': 0.386,
                                           'base': 0.6,
                                           'value': 0.075,
                                           'random': 0.469,
                                           'degree': 0.075,
                                           'best': 'Grad adaptiv',
                                           'cost': 150.0,
                                           'verdict': 'info',
                                           'all': {'Zufall': 0.469,
                                                   'Grad': 0.075,
                                                   'Grad adaptiv': 0.065,
                                                   'Betweenness': 0.082,
                                                   'Kernzahl': 0.34,
                                                   'Bekannte': 0.325,
                                                   'Bekannte (Nachbar mit höchstem Grad)': 0.207}}}}


@lru_cache(maxsize=None)
def _e1():
    return {r["typ"]: r for r in ev.strategy_rows(250, 6, 30, seeds=SW)}


@lru_cache(maxsize=None)
def _e2():
    return {r["typ"]: r for r in ev.containment_rows(250, 6, 30, seeds=SW)}


@lru_cache(maxsize=None)
def _e3(typ):
    return ev.acquaintance_rows(typ, 250, 6, 30, seeds=SW)


@lru_cache(maxsize=None)
def _e4(typ):
    return ev.strength_rows(typ, 250, 6, 0.10, seeds=SW)


@lru_cache(maxsize=None)
def _e5():
    return ev.exact_rows()


def _approx(x):
    return pytest.approx(x, abs=TOL)


# --- E1: Strategien und Netztypen --------------------------------------------------------------------------------------------------------------


def test_outbreak_sizes_of_every_strategy_network_type_and_vaccination_share():
    rows = _e1()
    for typ, exp in EXPECT["E1"].items():
        assert rows[typ]["base"] == _approx(exp["base"]), typ
        for s, cells in exp["cells"].items():
            for f, value in cells.items():
                assert rows[typ]["cells"][s][float(f)] == _approx(value), (typ, s, f)


def test_the_degree_rule_wins_by_a_wide_margin_in_heavy_tailed_networks_at_ten_percent():
    rows = _e1()
    for typ in (POWER, BA):
        deg, rnd = rows[typ]["cells"][C.S_DEGREE][0.1], rows[typ]["cells"][C.S_RANDOM][0.1]
        assert deg < 0.06 * rnd and rnd > 0.2
    assert rows[GRID]["cells"][C.S_DEGREE][0.1] > 0.8 * rows[GRID]["cells"][C.S_RANDOM][0.1]                   # im Gitter kaum besser als Zufall


def test_the_core_number_is_no_better_than_random_in_scale_free_networks_but_good_in_the_power_law_net():
    rows = _e1()
    assert rows[BA]["cells"][C.S_CORE][0.1] > 0.95 * rows[BA]["cells"][C.S_RANDOM][0.1]
    assert rows[POWER]["cells"][C.S_CORE][0.1] < 0.06 * rows[POWER]["cells"][C.S_RANDOM][0.1]


def test_betweenness_is_worse_than_random_only_in_the_grid_at_ten_and_twenty_percent():
    rows = _e1()
    worse = {(typ, f) for typ, r in rows.items() for f in (0.05, 0.1, 0.2) if r["cells"][C.S_BETWEENNESS][f] > C.WORSE_FACTOR * r["cells"][C.S_RANDOM][f]}
    assert worse == {(GRID, 0.1), (GRID, 0.2)}                                                      # bei 5 % liegt sie gleichauf mit Zufall (Verhältnis 1,02)


def test_the_adaptive_degree_beats_the_static_one_most_clearly_in_ring_and_grid():
    rows = _e1()
    gain = {typ: 1 - r["cells"][C.S_ADAPTIVE][0.1] / r["cells"][C.S_DEGREE][0.1] for typ, r in rows.items()}
    assert gain[RING] > 0.15 and gain[GRID] > 0.10 and gain[BA] < 0.12 and gain[POWER] < 0.12


def test_verdict_of_experiment_one_at_ten_percent():
    text = ev.verdict_strategies(list(_e1().values()), 0.10)[1]
    assert text == EXPECT["V"]["E1"]


# --- E2: Impfanteil für die Eindämmung ----------------------------------------------------------------------------------------------------------


def test_vaccination_share_needed_for_containment():
    rows = _e2()
    for typ, exp in EXPECT["E2"].items():
        for s, value in exp.items():
            assert rows[typ]["fstar"][s] == _approx(value), (typ, s)
    assert ev.verdict_containment(list(rows.values()))[1] == EXPECT["V"]["E2"]


# --- E3: Bekannten-Impfung ------------------------------------------------------------------------------------------------------------------------


def test_acquaintance_immunization_closes_part_of_the_gap_between_random_and_degree():
    for typ, exp in EXPECT["E3"].items():
        res = _e3(typ)
        assert res["base"] == _approx(exp["base"])
        for s, curve in exp["curves"].items():
            assert res["curves"][s] == [_approx(x) for x in curve], (typ, s)
        for s, gap in exp["gap"].items():
            assert ev.gap_closed(res, s, 0.10) == _approx(gap), (typ, s)
    for typ in (BA, RANDOM):
        assert ev.verdict_acquaintance(_e3(typ))[1] == EXPECT["V"]["E3 " + typ]


# --- E4: Ausbreitungsstärke ----------------------------------------------------------------------------------------------------------------------------


def test_strategies_at_ten_thirty_and_sixty_percent_spread():
    for typ, exp in EXPECT["E4"].items():
        rows = {str(r["strength"]): r for r in _e4(typ)}
        for strength, x in exp.items():
            assert rows[strength]["base"] == _approx(x["base"]), (typ, strength)
            for s, value in x["cells"].items():
                assert rows[strength]["cells"][s] == _approx(value), (typ, strength, s)


def test_the_adaptive_degree_is_the_best_strategy_in_every_network_type_and_spread_strength():
    for typ in (BA, RANDOM, RING, GRID):
        text = ev.verdict_strengths(_e4(typ), typ, 0.10)[1]
        assert "Die beste Strategie ist in allen Ausbreitungsstärken „Grad adaptiv“." in text, typ


def test_betweenness_in_the_grid_is_worse_than_random_at_every_spread_strength():
    for r in _e4(GRID):
        assert r["cells"][C.S_BETWEENNESS] > C.WORSE_FACTOR * r["cells"][C.S_RANDOM], r["strength"]


# --- E5: exakt auf kleinen Netzen ----------------------------------------------------------------------------------------------------------------------


def test_exact_comparison_on_small_networks():
    res = _e5()
    for k, exp in EXPECT["E5"].items():
        s = ev.exact_summary(res, int(k))
        for key, value in exp.items():
            assert s[key] == (_approx(value) if isinstance(value, float) else value), (k, key)
    for k in (2, 3):
        s = ev.exact_summary(res, k)
        assert s["optimum"] <= s["greedy"] + 1e-12 <= s["degree"] + 1e-9 <= s["random"] + 1e-9 < s["base"]
    assert ev.verdict_exact(res)[1] == EXPECT["V"]["E5"]


# --- Gitter: Größe -------------------------------------------------------------------------------------------------------------------------------------


@lru_cache(maxsize=None)
def _grid(n):
    out = []
    for s in SW:
        an = ev.analyse(ev.Settings(GRID, n, 6, s, 30, 10, C.S_BETWEENNESS))
        out.append([an.value(C.S_BETWEENNESS), an.value(C.S_RANDOM), an.value(C.S_DEGREE)])
    return out


def test_betweenness_in_the_grid_is_worse_than_random_at_250_nodes_but_not_systematically_at_150():
    for n, pairs in EXPECT["grid"].items():
        got = _grid(int(n))
        for g, e in zip(got, pairs):
            assert g == [_approx(x) for x in e], n
    big, small = _grid(250), _grid(150)
    assert all(b > r for b, r, _ in big) and min(b / r for b, r, _ in big) > 1.15 and max(b / r for b, r, _ in big) < 1.35
    assert sum(1 for b, r, _ in small if b > r) == 4 and max(b / r for b, r, _ in small) < 1.08


# --- Standardnetz und Presets ---------------------------------------------------------------------------------------------------------------------


def test_default_network_and_presets():
    for name, exp in EXPECT["presets"].items():
        an = ev.analyse(ev.Settings(**C.PRESETS[name]))
        assert (an.inst.n, an.inst.m, an.k) == (exp["n"], exp["m"], exp["k"]), name
        assert an.p == _approx(exp["p"]) and an.base == _approx(exp["base"]) and an.cost == pytest.approx(exp["cost"], abs=0.06), name
        for s, value in exp["all"].items():
            assert an.value(s) == _approx(value), (name, s)
        assert an.best() == exp["best"] and ev.verdict_main(an)[0] == exp["verdict"], name


def test_preset_help_and_calibration():
    s60 = ev.analyse(ev.Settings(**C.PRESETS["Starke Ausbreitung (60 %)"]))
    assert abs(s60.base - 0.6) < 0.01
    assert A.knowledge_cost(C.S_DEGREE, 150, 444, 15) == 150.0
