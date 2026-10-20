"""Eindämmung: wie viel Wissen braucht man? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Siebtes Stück der Reihe „Netzwerkanalyse“: k Betriebe absichern („impfen“), bevor sich ein Befall über Partnerschaften ausbreitet (SIR in der Perkolationsfassung). Die Demo stellt Strategien mit steigendem
Wissen über das Netz nebeneinander (zufällig, Bekannten-Impfung, Grad, Betweenness, Kernzahl) und misst die erwartete Ausbruchsgröße; dazu der nötige Impfanteil, die Rangfolge bei verschiedener
Ausbreitungsstärke und ein exakter Vergleich mit dem Optimum auf kleinen Netzen. Aufbau und Regeln stehen im DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import eid_constants as C
from eid_evaluation import (
    Settings,
    acquaintance_rows,
    analyse,
    containment_rows,
    de,
    exact_rows,
    exact_summary,
    pct,
    strategy_rows,
    strength_rows,
    verdict_acquaintance,
    verdict_containment,
    verdict_exact,
    verdict_main,
    verdict_strategies,
    verdict_strengths,
)
from eid_layout import dunkles_design, kopf_css
from eid_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from eid_visualization import (
    build_acquaintance,
    build_containment,
    build_exact,
    build_methods,
    build_network,
    build_strategy_bars,
    build_strengths,
)

st.set_page_config(page_title="Eindämmung – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _strategies(n, c, strength):
    return strategy_rows(n, c, strength)


@st.cache_data(show_spinner=False)
def _containment(n, c, strength):
    return containment_rows(n, c, strength)


@st.cache_data(show_spinner=False)
def _acquaintance(typ, n, c, strength):
    return acquaintance_rows(typ, n, c, strength)


@st.cache_data(show_spinner=False)
def _strengths(typ, n, c, f):
    return strength_rows(typ, n, c, f)


@st.cache_data(show_spinner=False)
def _exact():
    return exact_rows()


def experiment(name, label, key, compute, show, hint):
    """Teure Zusatzansicht erst auf Klick; das Ergebnis bleibt nur für genau diese Einstellungen stehen (Session State)."""
    state_key = f"exp_{name}"
    if st.button(label, key=f"run_{name}", help=hint):
        with st.spinner("Rechne …"):
            result = compute()
        st.session_state[state_key] = (key, result)
    state = st.session_state.get(state_key)
    if state is None:
        st.caption(f"Noch nicht gerechnet. {hint}")
        return
    if state[0] != key:
        st.info("Die Einstellungen haben sich seit der letzten Rechnung geändert. Bitte neu starten.")
        return
    show(state[1])


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in eid_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🛡️ Eindämmung: wie viel Wissen braucht man?")
st.markdown(
    """
**Siebtes Stück** der Reihe „Netzwerkanalyse“, im Ausbreitungs-Arm der Kontrast zu Stück 5 (Einflussmaximierung): dieselbe Auswahlaufgabe („*k* Betriebe wählen“), aber das umgekehrte Ziel, dort möglichst viel erreichen, hier möglichst wenig. In einem Netz von Subunternehmern und Lieferanten breitet sich ein **Befall** (Schadsoftware, ein Qualitätsproblem) über Partnerschaften aus. Sie können *k* Betriebe **absichern („impfen“)**, bevor er beginnt. Wen wählen Sie, und **wie viel müssen Sie dafür über das Netz wissen?** Die [Kaskaden-Demo](https://sebastianhanisch-kaskaden-demo.streamlit.app/) rechnet SIR ohne Impfung, die [Robustheits-Demo](https://sebastianhanisch-robustheit-demo.streamlit.app/) entfernt Knoten und misst die größte Komponente, die [Härtungs-Demo](https://sebastianhanisch-haertung-demo.streamlit.app/) baut das Netz um; hier geht es um die Auswahl der Betriebe und um das Wissen, das sie braucht.

Die Kernfrage: **Wie viel Wissen braucht eine Impfstrategie, und wo lohnt es sich?** Die Demo stellt Strategien mit steigendem Wissen nebeneinander: nichts (zufällig), nur die Partner eines Zufallsbetriebs (**Bekannten-Impfung**), alle Partnerzahlen (**Grad**), das ganze Netz (**Betweenness, Kernzahl, adaptiver Grad**). Die Ergebnisse sind **Modellbefunde**, keine Aussagen über die Wirklichkeit.

Weiter unten: fünf Experimente (**🔬**), der Abschnitt **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert die Impfung", expanded=True):
    st.markdown(
        """
1. **Befall als Zufallsnetz:** ein befallener Betrieb gibt den Befall an jeden Partner mit Wahrscheinlichkeit *p* weiter und ist nur einen Schritt lang ansteckend (SIR). Das ist gleichbedeutend damit, dass jede Partnerschaft mit Wahrscheinlichkeit *p* „bleibt“ und der Befall die Zusammenhangskomponente des ersten Betriebs erreicht: ein **Schnappschuss** des Netzes.
2. **Ausbreitungsstärke:** statt *p* stellen Sie ein, wie viel Prozent der Betriebe ein Ausbruch **ohne Impfung** im Mittel erreicht; die Demo rechnet daraus *p* aus (Bisektion) und zeigt es an.
3. **Impfung:** abgesicherte Betriebe fallen aus dem Netz. Der Befall beginnt in einem zufälligen **ungeimpften** Betrieb.
4. **Ausbruchsgröße:** der Anteil der Betriebe, den der Befall im Mittel erreicht, gemittelt über 100 Schnappschüsse. Sie kann bei mehr Impfungen auch steigen, wenn man nur unwichtige Betriebe sichert (der Befall beginnt dann in einer größeren Restgruppe); die Summe der quadrierten Komponentengrößen fällt dagegen immer.
5. **Strategien** liefern eine Wahlreihenfolge; die ersten *k* Einträge sind die Auswahl. Strategien mit Zufall oder Gleichständen werden über mehrere Ziehungen gemittelt.
        """
    )
    st.markdown(
        """
| Strategie | Was sie wissen muss | Abfragen (Erwartung) |
|---|---|---|
| **Zufall** | nichts | 0 |
| **Bekannte** (Cohen u. a. 2003) | die Partner eines Zufallsbetriebs | 2 je Impfung |
| **Bekannte (Nachbar mit höchstem Grad)** | Partner des Zufallsbetriebs und deren Partnerzahl | 1 + Partner des Zufallsbetriebs je Impfung |
| **Grad** | die Partnerzahl jedes Betriebs | *n* |
| **Grad adaptiv** | das ganze Netz, laufend neu gezählt | *n* + *m* |
| **Betweenness** | das ganze Netz | *n* + *m* |
| **Kernzahl** | das ganze Netz | *n* + *m* |
        """
    )
    st.caption("Die Abfragen sind eine Zählung, kein Maß der Güte: *n* Betriebe, *m* Partnerschaften.")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Netz zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Netz**")
    typ = st.selectbox("Netztyp", C.ALL_TYPES, key="netztyp_select", help="Welches Netz erzeugt wird.")
    n = st.slider("Betriebe n", *bounds("n_slider"), key="n_slider", help="Zahl der Betriebe (beim Gitter auf ein Quadrat gerundet).")
    c = st.slider("Partner je Betrieb c", *bounds("c_slider"), key="c_slider", help="Was c bedeutet, hängt vom Netztyp ab (siehe darunter).")
    st.caption(C.C_MEANING[typ])
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1, help="Bestimmt das Netz, die Schnappschüsse und die Ziehungen.")
    st.button("🎲 Neu würfeln", width="stretch", on_click=randomize_seed)
    st.markdown("**Ausbreitung und Impfung**")
    strength = st.slider("Ausbreitungsstärke (%)", *bounds("strength_slider"), key="strength_slider",
                         help="Anteil der Betriebe, den ein Ausbruch ohne Impfung im Mittel erreicht. Daraus wird die Übertragungswahrscheinlichkeit p berechnet.")
    f = st.slider("Impfanteil (%)", *bounds("f_slider"), key="f_slider", help="Anteil der Betriebe, die vorab abgesichert werden.")
    strategy = st.selectbox("Strategie", C.STRATEGIES, key="strategy_select", help="Welche Auswahl im Netz gezeigt wird; die Ausbruchsgrößen aller Strategien stehen im Diagramm darunter.")
    st.caption(C.STRATEGY_HELP[strategy])

sync_query_params({"netztyp_select": typ, "n_slider": int(n), "c_slider": int(c), "seed_input": int(seed), "strength_slider": int(strength), "f_slider": int(f), "strategy_select": strategy})

settings = Settings(typ, int(n), int(c), int(seed), int(strength), int(f), strategy)
with st.spinner("Rechne Schnappschüsse und Auswahlen …"):
    an = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Wer wird gesichert, und was bleibt vom Ausbruch?")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Betriebe / Partnerschaften", f"{an.inst.n} / {an.inst.m}")
m2.metric("Übertragungswahrscheinlichkeit p", de(an.p, 3), delta=f"Ausbreitungsstärke {settings.strength} %", delta_color="off")
m3.metric(f"Ausbruchsgröße mit {an.k} Impfungen", f"{pct(an.value(strategy), 1)} %", delta=f"{pct(an.value(strategy) - an.base, 1)} Prozentpunkte gegen ohne Impfung", delta_color="inverse")
m4.metric("Wissen (Abfragen)", de(an.cost, 0), delta="im Mittel", delta_color="off")
st.markdown(f"**{strategy}: die {an.k} gesicherten Betriebe** (rot umrandet; Farbe der übrigen = Wahrscheinlichkeit, im Ausbruch befallen zu werden)")
st.plotly_chart(build_network(an.inst, an.risk, an.vaccinated, strategy), width="stretch", key="net_chart")
st.markdown("**Alle Strategien im Vergleich** (derselbe Satz Schnappschüsse; Strategien mit Zufall als Mittel über mehrere Ziehungen)")
st.plotly_chart(build_methods(an), width="stretch", key="methods_chart")
st.caption(f"Ohne Impfung erreicht ein Ausbruch im Mittel {pct(an.base, 1)} % der Betriebe. Die beste Strategie bei diesem Impfanteil ist „{an.best()}“ mit {pct(an.value(an.best()), 1)} %.")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie viel Wissen braucht man?")
kind, text = verdict_main(an)
getattr(st, kind)(text)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

n_exp, c_exp, s_exp, f_exp = settings.n, settings.c, settings.strength, settings.f
runs_info = f"Median über {len(C.LIVE_SEEDS)} feste Netze je Typ"
st.subheader("🔬 Experiment 1: Wo lohnt Wissen?")
f_show = min(C.CURVE_FS, key=lambda x: abs(x - f_exp / 100.0))
st.caption(f"Ausbruchsgröße je Strategie und Netztyp bei {pct(f_show)} % Impfanteil (der den Reglerwert am nächsten liegende von {', '.join(pct(x) for x in C.CURVE_FS)} %); {runs_info}, n = {n_exp}, c = {c_exp}, Ausbreitungsstärke {s_exp} %.")


def show_strategies(rows):
    st.plotly_chart(build_strategy_bars(rows, f_show), width="stretch", key="strategy_chart")
    kind_, text_ = verdict_strategies(rows, f_show)
    getattr(st, kind_)(text_)


experiment("strategies", "Strategien vergleichen", (n_exp, c_exp, s_exp), lambda: _strategies(n_exp, c_exp, s_exp), show_strategies, "Rechnet sechs Netztypen mit je vier Netzen und allen Strategien, etwa 15 Sekunden.")

st.markdown("---")

st.subheader("🔬 Experiment 2: Wie viel Impfanteil braucht die Eindämmung?")
st.caption(f"Kleinster Impfanteil, der die Ausbruchsgröße auf höchstens {pct(C.CONTAIN_LEVEL)} % drückt (bis {pct(C.THRESHOLD_MAX_F)} % gesucht); {runs_info}, n = {n_exp}, c = {c_exp}, Ausbreitungsstärke {s_exp} %.")


def show_containment(rows):
    st.plotly_chart(build_containment(rows), width="stretch", key="containment_chart")
    kind_, text_ = verdict_containment(rows)
    getattr(st, kind_)(text_)


experiment("containment", "Impfanteil suchen", (n_exp, c_exp, s_exp), lambda: _containment(n_exp, c_exp, s_exp), show_containment, "Rechnet sechs Netztypen mit je vier Netzen und allen Strategien, etwa 15 Sekunden.")

st.markdown("---")

st.subheader("🔬 Experiment 3: Reicht Nachbarwissen?")
st.caption(f"Im gewählten Netztyp („{typ}“): Zufall, Bekannten-Impfung, Bekannte mit Hub-Wahl und Grad über den Impfanteil; {runs_info}, n = {n_exp}, c = {c_exp}, Ausbreitungsstärke {s_exp} %.")


def show_acquaintance(result):
    st.plotly_chart(build_acquaintance(result), width="stretch", key="acquaintance_chart")
    kind_, text_ = verdict_acquaintance(result)
    getattr(st, kind_)(text_)


experiment("acquaintance", "Nachbarwissen prüfen", (typ, n_exp, c_exp, s_exp), lambda: _acquaintance(typ, n_exp, c_exp, s_exp), show_acquaintance, "Rechnet vier Netze mit vier Strategien, wenige Sekunden.")

st.markdown("---")

st.subheader("🔬 Experiment 4: Bleibt die beste Strategie bei anderer Ausbreitungsstärke die beste?")
st.caption(f"Im gewählten Netztyp („{typ}“) bei {f_exp} % Impfanteil: Ausbreitungsstärke {', '.join(str(x) for x in C.STRENGTHS)} %; {runs_info}, n = {n_exp}, c = {c_exp}.")


def show_strengths(rows):
    st.plotly_chart(build_strengths(rows), width="stretch", key="strengths_chart")
    kind_, text_ = verdict_strengths(rows, typ, f_exp / 100.0)
    getattr(st, kind_)(text_)


experiment("strengths", "Ausbreitungsstärken vergleichen", (typ, n_exp, c_exp, f_exp), lambda: _strengths(typ, n_exp, c_exp, f_exp / 100.0), show_strengths, "Rechnet drei Ausbreitungsstärken mit vier Netzen und allen Strategien, etwa 8 Sekunden.")

st.markdown("---")

st.subheader("🔬 Experiment 5: Wie weit liegen Greedy und Grad vom Optimum?")
st.caption(f"{C.EXACT_NETS} kleine verbundene Zufallsnetze ({C.EXACT_N} Betriebe, {C.EXACT_M} Partnerschaften, p = {de(C.EXACT_P, 1)}) mit **exakter** Ausbruchsgröße (Aufzählung aller {2 ** C.EXACT_M} Kantenzustände): "
           f"Optimum durch Aufzählung aller Mengen aus k = {C.EXACT_KS[0]} und {C.EXACT_KS[1]} Betrieben, Greedy (jeweils der Betrieb mit der größten Senkung), Gradregel (Mittel über alle Gleichstandsauflösungen), Zufall (Mittel über alle Mengen).")


def show_exact(result):
    st.plotly_chart(build_exact(result, exact_summary), width="stretch", key="exact_chart")
    kind_, text_ = verdict_exact(result)
    getattr(st, kind_)(text_)


experiment("exact", "Exakt rechnen", "fest", _exact, show_exact, "Rechnet zehn Netze mit je 4 096 Kantenzuständen und allen 2- und 3-Mengen, etwa 6 Sekunden.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Gleiche Übertragungswahrscheinlichkeit, ein Schritt ansteckend** | Jede Partnerschaft hat dasselbe *p*, ein befallener Betrieb steckt nur einmal an (SIR als Perkolation). Mit Genesungsdauer, Gewichten oder Verzögerung ändern sich die Zahlen; die Rangfolge der Strategien wurde nur für die Ausbreitungsstärken 10, 30 und 60 % geprüft (Experiment 4). | – |
| **Impfung wirkt vollständig, sofort und vor dem Ausbruch** | In der Wirklichkeit schützt eine Maßnahme nur teilweise und kommt zu spät. | – |
| **Keine Kosten je Betrieb** | Alle Betriebe kosten gleich viel zu sichern. Gerade die Hubs könnten teurer sein. | – |
| **Wissen als Zählung** | Die Abfragen sind eine Zählung der gelesenen Betriebe, kein Maß der Güte; Grad, Betweenness und Kernzahl setzen voraus, dass das Netz vollständig bekannt und richtig ist. | – |
| **Der Befall beginnt in einem zufälligen Ungeimpften** | Beginnt er gezielt in einem Hub, oder in einem gesicherten Betrieb (der dann nichts auslöst), sind die Werte andere. Die Ausbruchsgröße kann bei mehr Impfungen steigen, weil sich die Restgruppe ändert. | Stück 8 (Quellensuche fragt umgekehrt, woher ein Ausbruch kam) |
| **Statisches Netz** | Die Partnerschaften ändern sich während des Ausbruchs nicht. | Stück 13 (zeitliche Netze) |
| **Netztypen und Größe** | Die Befunde gelten für diese sechs synthetischen Netztypen bei *n* bis 250 (Median über feste Netze). Der Nachteil der Betweenness im Gitter zeigt sich bei *n* = 250, bei *n* = 150 nicht. | – |
| **Exakter Vergleich nur auf winzigen Netzen** | Das Optimum durch Aufzählung braucht kleine Netze (9 Betriebe); auf großen ist Greedy nicht gerechnet. | – |
| **Modellbefund** | Die Demo zeigt Verhalten im Modell, nicht die Wirkung einer Maßnahme in der Wirklichkeit. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Befall als Perkolation.** Jede Kante von $G$ bleibt unabhängig mit Wahrscheinlichkeit $p$; das Ergebnis heißt $G_p$. Sind die Betriebe der Menge $U$ geimpft, wird der Befall in einem zufälligen ungeimpften Betrieb auf dessen Zusammenhangskomponente in $G_p - U$ ausbreiten. Die **Ausbruchsgröße** (Anteil aller Betriebe) ist

$$s(U) = \frac{1}{n}\,\mathbb{E}\!\left[\frac{1}{n - |U|} \sum_{C} |C|^2\right]$$

wobei $C$ die Zusammenhangskomponenten von $G_p - U$ durchläuft. Jede Komponente $C$ wird von $|C|$ der $n - |U|$ möglichen Startbetriebe aus erreicht und hat dann die Größe $|C|$.

**Ausbreitungsstärke.** Die Demo wählt $p$ so, dass $s(\emptyset)$ den eingestellten Wert hat.

**Bekannten-Impfung.** Ist $N(y)$ die Menge der Partner von $y$, $d_x$ die Partnerzahl von $x$ und $n'$ die Zahl der Betriebe mit mindestens einem Partner, wird bei der ersten Wahl der Betrieb $y$ mit Wahrscheinlichkeit

$$P(y) = \sum_{x \in N(y)} \frac{1}{n'}\,\frac{1}{d_x}$$

gesichert: Betriebe mit vielen Partnern werden öfter als Partner eines Zufallsbetriebs gezogen, ohne dass jemand die Partnerzahlen kennt (Cohen u. a. 2003).

**Rechenweg.** Für jede Wahlreihenfolge werden alle Impfanteile mit einer einzigen Rechnung je Schnappschuss bestimmt: zunächst sind alle gewählten Betriebe geimpft, dann werden sie in umgekehrter Reihenfolge wieder eingesetzt und die Komponenten mit Union-Find zusammengeführt.

**Literatur.**
- Pastor-Satorras, R., Vespignani, A. (2002): *Immunization of complex networks.* Physical Review E 65, 036104.
- Cohen, R., Havlin, S., ben-Avraham, D. (2003): *Efficient immunization strategies for computer networks and populations.* Physical Review Letters 91, 247901.
- Holme, P. (2004): *Efficient local strategies for vaccination and network attack.* Europhysics Letters 68(6), 908–914.
- Gallos, L. K., Liljeros, F., Argyrakis, P., Bunde, A., Havlin, S. (2007): *Improving immunization strategies.* Physical Review E 75, 045104(R).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
