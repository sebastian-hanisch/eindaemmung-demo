"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

# --- Netztypen -----------------------------------------------------------------------------------------------------------------------------------
T_RANDOM = "Zufallsnetz"
T_POWER = "Potenzgesetz-Netz"
T_BA = "Skalenfreies Netz (BA)"
T_COMMUNITIES = "Verbünde"
T_RING = "Ring mit Abkürzungen"
T_GRID = "Gitter"
ALL_TYPES = (T_RANDOM, T_POWER, T_BA, T_COMMUNITIES, T_RING, T_GRID)
BLOCKS = 6

C_MEANING = {
    T_RANDOM: "mittlerer Grad des Zufallsnetzes",
    T_POWER: "mittlerer Grad (Gradfolge mit Potenzgesetz-Exponent 2,5, Konfigurationsmodell)",
    T_BA: "zwei Kanten je neuem Knoten, also m = c / 2 gerundet (jeder Knoten hat mindestens m Nachbarn)",
    T_COMMUNITIES: "mittlerer Grad; 80 % der Kanten bleiben im eigenen Verbund (6 Verbünde)",
    T_RING: "Nachbarn auf dem Ring (c gerade gerundet), dazu Abkürzungen mit 5 % je Ringkante",
    T_GRID: "Nachbarschaft: unter 6 vier Nachbarn, 6 bis 7 mit einer Diagonale, ab 8 mit beiden Diagonalen",
}

N_MIN, N_MAX, DEFAULT_N = 60, 250, 150
C_MIN, C_MAX, DEFAULT_C = 3, 12, 6
SEED_MAX, DEFAULT_SEED = 999999, 35
STRENGTH_MIN, STRENGTH_MAX, DEFAULT_STRENGTH = 10, 60, 30   # Ausbreitungsstärke: erwartete Ausbruchsgröße ohne Impfung in Prozent der Betriebe
F_MIN, F_MAX, DEFAULT_F = 1, 40, 10                         # Impfanteil in Prozent der Betriebe
SWEEP_SEEDS = tuple(range(100000, 100008))                  # feste Netze für alle Sweeps: nie ein einzelner Seed als Befund
LIVE_SEEDS = SWEEP_SEEDS[:4]                                # so viele feste Netze je Zelle rechnet die App live (die README-Zahlen nutzen alle acht)

# --- Strategien ----------------------------------------------------------------------------------------------------------------------------------
S_RANDOM, S_DEGREE, S_ADAPTIVE, S_BETWEENNESS, S_CORE, S_ACQ, S_ACQ_HUB = (
    "Zufall", "Grad", "Grad adaptiv", "Betweenness", "Kernzahl", "Bekannte", "Bekannte (Nachbar mit höchstem Grad)")
STRATEGIES = (S_RANDOM, S_DEGREE, S_ADAPTIVE, S_BETWEENNESS, S_CORE, S_ACQ, S_ACQ_HUB)
DEFAULT_STRATEGY = S_RANDOM
DRAWS = {S_RANDOM: 10, S_DEGREE: 10, S_ADAPTIVE: 5, S_BETWEENNESS: 10, S_CORE: 10, S_ACQ: 10, S_ACQ_HUB: 10}   # Ziehungen (Gleichstände bzw. Zufall), über die gemittelt wird
STRATEGY_HELP = {
    S_RANDOM: "Wissen: keins. Wählt zufällige Betriebe.",
    S_DEGREE: "Wissen: die Zahl der Partner jedes Betriebs. Sichert die Betriebe mit den meisten Partnern (Gleichstände zufällig).",
    S_ADAPTIVE: "Wissen: das ganze Netz, laufend. Nach jeder Wahl wird die Zahl der Partner der Übrigen neu gezählt (wie in Stück 8 der Graphen-Reihe).",
    S_BETWEENNESS: "Wissen: das ganze Netz. Sichert die Betriebe, über die die meisten kürzesten Wege laufen.",
    S_CORE: "Wissen: das ganze Netz. Sichert die Betriebe mit der höchsten Kernzahl (Stück 1).",
    S_ACQ: "Wissen: nur die Partner eines Zufallsbetriebs. Wählt einen zufälligen Betrieb und sichert einen seiner Partner (Cohen u. a. 2003).",
    S_ACQ_HUB: "Wissen: die Partner eines Zufallsbetriebs und deren Partnerzahl. Wählt einen zufälligen Betrieb und sichert unter seinen Partnern den mit den meisten Partnern.",
}

# --- Messungen -----------------------------------------------------------------------------------------------------------------------------------
EXP_DRAWS = {S_RANDOM: 5, S_DEGREE: 5, S_ADAPTIVE: 3, S_BETWEENNESS: 5, S_CORE: 5, S_ACQ: 5, S_ACQ_HUB: 5}   # Ziehungen je Strategie in den Experimenten (schneller als im Hauptlauf)
MAIN_RUNS = 100        # Schnappschüsse im Hauptlauf
EXP_RUNS = 60          # Schnappschüsse je Netz in den Experimenten
CALIB_RUNS, CALIB_ITERS = 40, 14
CONTAIN_LEVEL = 0.05   # „eingedämmt“: erwartete Ausbruchsgröße höchstens 5 % der Betriebe
WORSE_FACTOR = 1.10     # eine Strategie gilt als „schlechter als Zufall“, wenn ihre Ausbruchsgröße um mehr als 10 % über der von Zufall liegt (Ziehungen schwanken um einige Prozent)
CURVE_FS = (0.05, 0.10, 0.20)        # Impfanteile in Experiment 1
ACQ_FS = (0.02, 0.05, 0.10, 0.15, 0.20, 0.30)   # Impfanteile in Experiment 3
STRENGTHS = (10, 30, 60)             # Ausbreitungsstärken in Experiment 4
THRESHOLD_MAX_F = 0.40               # Experiment 2 sucht den Impfanteil bis zu diesem Wert
EXACT_N, EXACT_M, EXACT_P = 9, 12, 0.5
EXACT_NETS, EXACT_KS = 10, (2, 3)

# --- Darstellung ---------------------------------------------------------------------------------------------------------------------------------
COLOR_EDGE = "rgba(120,120,120,0.30)"
COLOR_VACC = "#d62728"
COLOR_A = "#2F6B65"
COLOR_B = "#c4623b"
COLOR_C = "#6b5b95"
STRATEGY_COLORS = {S_RANDOM: "#8c8c8c", S_DEGREE: "#2F6B65", S_ADAPTIVE: "#4c9a8f", S_BETWEENNESS: "#6b5b95", S_CORE: "#9d755d", S_ACQ: "#e0a458", S_ACQ_HUB: "#c4623b"}

PRESETS = {
    "Zufallsnetz ohne Wissen (Voreinstellung)": {"netztyp": T_RANDOM, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED, "strength": DEFAULT_STRENGTH, "f": DEFAULT_F, "strategy": S_RANDOM},
    "Superspreader: Wissen lohnt": {"netztyp": T_BA, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED, "strength": DEFAULT_STRENGTH, "f": DEFAULT_F, "strategy": S_DEGREE},
    "Nachbarwissen reicht fast": {"netztyp": T_BA, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED, "strength": DEFAULT_STRENGTH, "f": DEFAULT_F, "strategy": S_ACQ_HUB},
    "Gitter: Betweenness schlechter als Zufall": {"netztyp": T_GRID, "n": 250, "c": DEFAULT_C, "seed": DEFAULT_SEED, "strength": DEFAULT_STRENGTH, "f": DEFAULT_F, "strategy": S_BETWEENNESS},
    "Ring: adaptiv hilft": {"netztyp": T_RING, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED, "strength": DEFAULT_STRENGTH, "f": DEFAULT_F, "strategy": S_ADAPTIVE},
    "Starke Ausbreitung (60 %)": {"netztyp": T_POWER, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED, "strength": 60, "f": DEFAULT_F, "strategy": S_DEGREE},
}
PRESET_HELP = {
    "Zufallsnetz ohne Wissen (Voreinstellung)": "Zufällige Betriebe absichern: im Zufallsnetz wirkt das, aber schwach.",
    "Superspreader: Wissen lohnt": "Im skalenfreien Netz sichert die Gradregel die wenigen Betriebe mit sehr vielen Partnern: der Ausbruch bricht fast ganz zusammen.",
    "Nachbarwissen reicht fast": "Ohne das ganze Netz zu kennen: zufälligen Betrieb wählen, unter seinen Partnern den mit den meisten Partnern sichern.",
    "Gitter: Betweenness schlechter als Zufall": "Im Gitter hilft Wissen kaum; die Betweenness sichert eine Mitte, die zufällige Wahl übertrifft sie.",
    "Ring: adaptiv hilft": "Im Ring mit Abkürzungen verbessert die laufend neu gezählte Gradregel die statische.",
    "Starke Ausbreitung (60 %)": "Ohne Impfung erreicht ein Ausbruch im Mittel 60 % der Betriebe; die Gradregel im Potenzgesetz-Netz hält ihn fast auf.",
}
DEFAULT_PRESET_NAME = "Zufallsnetz ohne Wissen (Voreinstellung)"
