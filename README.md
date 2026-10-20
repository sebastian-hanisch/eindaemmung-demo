# Eindämmung: wie viel Wissen braucht man? – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-eindaemmung-demo.streamlit.app/)** -->

Siebtes Stück der **Netzwerkanalyse-Reihe** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, im Ausbreitungs-Arm der Kontrast zu Stück 5 (Einflussmaximierung: dieselbe Auswahlaufgabe „*k* Betriebe wählen“, umgekehrtes Ziel) und die Gegenmaßnahme zu Stück 6 (komplexe Ansteckung). Die [Demo zu Kaskaden](https://sebastianhanisch-kaskaden-demo.streamlit.app/) rechnet SIR ohne Impfung, die [Robustheits-Demo](https://sebastianhanisch-robustheit-demo.streamlit.app/) entfernt Knoten zufällig und gezielt und misst die größte Komponente, die [Härtungs-Demo](https://sebastianhanisch-haertung-demo.streamlit.app/) baut das Netz um; neu hier sind die Impfung vor dem Ausbruch, die Ausbruchsgröße als Maß und die **Stufen des Wissens** über das Netz.

In einem Netz von Subunternehmern und Lieferanten breitet sich ein Befall über Partnerschaften aus: ein befallener Betrieb gibt ihn an jeden Partner mit Wahrscheinlichkeit *p* weiter und ist einen Schritt lang ansteckend (SIR in der Fassung der **Bond-Perkolation**, wie in Stück 5). Die Demo sichert („impft“) *k* Betriebe vorab und misst die erwartete **Ausbruchsgröße**, für Strategien mit steigendem Wissen: Zufall, **Bekannten-Impfung** (Cohen u. a. 2003), Grad, adaptiver Grad, Betweenness, Kernzahl.

## Kernfrage

**Wie viel Wissen über das Netz braucht eine Impfstrategie, und wo lohnt es sich?** Der Gesamtplan nannte als Risiko „die Gradregel gewinnt überall“. Die Vormessung schärfte das auf den Hook, der in der Demo steht: **in Netzen mit stark schwankendem Grad lohnt Wissen enorm, und Nachbarwissen reicht fast; in homogenen Netzen (Ring, Gitter) bringt Wissen wenig, und die Betweenness kann sogar schlechter sein als Zufall.**

## Befunde und Korrekturen gegenüber dem Plan

- **Wissen lohnt nur in heterogenen Netzen:** bei 10 % Impfanteil bleiben in den beiden Netzen mit schwankendem Grad (Potenzgesetz, skalenfrei) 0,7 % bzw. 1,1 % Ausbruchsgröße mit der Gradregel, mit Zufall 22,5 % bzw. 20,8 %; im Gitter 10,3 % gegen 12,3 %.
- **Die Bekannten-Impfung (zufälliger Partner eines Zufallsbetriebs) kommt nicht nahe an die Gradregel** (anders als die Plan-Vermutung nach Cohen u. a.): im skalenfreien Netz 8,1 % gegen 20,8 % (Zufall) und 1,1 % (Grad), sie schließt 64 % der Lücke; im Zufallsnetz nur 22 %. **Wählt man unter den Partnern den mit den meisten Partnern** (Variante nach Holme 2004 und Gallos u. a. 2007), sind es 97 % bzw. 86 % der Lücke.
- **Die Gradregel gewinnt nicht überall gleich:** im Gitter wird sie nur wenig besser als Zufall, und die **Betweenness ist dort schlechter als Zufall** (15,0 % gegen 12,3 % bei 10 % Impfanteil, bei *n* = 250 in allen acht Netzen; bei *n* = 150 ist der Unterschied nicht systematisch).
- **Die Kernzahl (Stück 1) ist als Impfregel in skalenfreien Netzen so schwach wie Zufall** (20,1 % gegen 20,8 %), im Potenzgesetz-Netz brauchbar (1,1 %).
- **Die adaptive Gradregel hilft vor allem im Ring und im Gitter** (Ring 5,1 % gegen 6,2 %, Gitter 9,1 % gegen 10,3 %), kaum in Netzen mit schwankendem Grad.
- **Die Ausbruchsgröße fällt nicht immer mit jeder Impfung** (Korrektur am Plan, der „Impfen schadet nie“ als Eigenschaft vorsah): der Befall beginnt in einem zufälligen **Ungeimpften**; wer einen isolierten Betrieb sichert, ändert die Summe der quadrierten Komponentengrößen, aber nicht die Zahl der Ungeimpften im Nenner. Die Summe selbst fällt immer.
- **Greedy nur exakt und klein:** auf Netzen mit 9 Betrieben liegt Greedy beim Optimum (Optimum in 9 bzw. 8 von 10 Netzen), die Gradregel 1,5 % bzw. 9,1 % darüber (Median); live ist Greedy zu teuer.

## Modell

Ungerichtete Netze, jede Partnerschaft überträgt mit gleicher Wahrscheinlichkeit *p*, ein befallener Betrieb steckt nur einmal an. Das ist gleichbedeutend mit Erreichbarkeit im Netz, in dem jede Kante unabhängig mit Wahrscheinlichkeit *p* **bleibt** (Schnappschuss). Geimpfte Betriebe fallen aus dem Netz; der Befall beginnt in einem zufälligen Ungeimpften und erreicht dessen Zusammenhangskomponente. Die **Ausbruchsgröße** ist der Anteil aller Betriebe, den er im Mittel erreicht: Σ |*C*|² über die Komponenten, geteilt durch (*n* − |*U*|) und *n*, gemittelt über die Schnappschüsse. Statt *p* stellt man die **Ausbreitungsstärke** ein (Ausbruchsgröße ohne Impfung); *p* wird per Bisektion berechnet. Jede Strategie liefert eine Wahlreihenfolge, so dass **eine** Rechnung je Schnappschuss alle Impfanteile bedient (Betriebe rückwärts wieder einsetzen, Union-Find).

## Methodik

| Baustein | Inhalt |
|---|---|
| **Netze** | Generatoren aus `k-core-demo` (Stück 1) als Kopie: Zufallsnetz, Potenzgesetz-Netz, skalenfrei (BA), Verbünde, Ring mit Abkürzungen, Gitter |
| **Strategien** | Zufall, Grad, adaptiver Grad, Betweenness (Brandes), Kernzahl, Bekannte, Bekannte mit Hub-Wahl; Ziehungen gemittelt (Zufall und Gleichstände) |
| **Wissen** | Zählung der abgefragten Betriebe je Strategie (Zufall 0, Bekannte 2 je Impfung, Grad *n*, die übrigen *n* + *m*), kein Maß der Güte |
| **Experiment 1** | Ausbruchsgröße je Strategie und Netztyp bei 5, 10 und 20 % Impfanteil |
| **Experiment 2** | kleinster Impfanteil, der die Ausbruchsgröße auf höchstens 5 % drückt (bis 40 % gesucht) |
| **Experiment 3** | Bekannten-Impfung gegen Zufall und Grad im gewählten Netztyp über den Impfanteil |
| **Experiment 4** | beste Strategie bei Ausbreitungsstärke 10, 30 und 60 % |
| **Experiment 5** | exakt auf 10 kleinen Netzen (9 Betriebe, 12 Partnerschaften, *p* = 0,5): Optimum, Greedy, Grad, Zufall |

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`. Netze der Messreihen: die acht festen Netze `SWEEP_SEEDS` je Zelle, *n* = 250, *c* = 6, Ausbreitungsstärke 30 %, wo nichts anderes steht; erwartete Ausbruchsgröße (Anteil der Betriebe), Median über die acht Netze mit je 60 Schnappschüssen und 3 bis 5 Ziehungen je Strategie.

| Frage | Befund |
|---|---|
| **Stimmen die Bausteine?** | Die Summe der quadrierten Komponentengrößen stimmt für jedes Präfix mit `networkx` überein (60 Zufallsnetze); die exakte Ausbruchsgröße (Aufzählung aller Kantenzustände, vektorisiert) mit einer unabhängig geschriebenen Aufzählung mit Union-Find (40 Fälle); der Schnappschuss-Schätzer (6 000 Schnappschüsse, Band 0,01) und eine direkte SIR-Simulation (20 000 Läufe, Band 0,012) mit dem exakten Wert; Optimum ≤ Greedy ≤ Mittel aller Mengen, das Optimum auch gegen eine Suche im Python-Rechenweg; die Wahrscheinlichkeit der ersten Wahl der Bekannten-Impfung und ihrer Hub-Variante mit der geschlossenen Formel; Betweenness und Kernzahl mit `networkx` (30 Netze) (`tests/test_oracle_eindaemmung.py`) |
| **Wo lohnt Wissen?** | siehe Tabelle zu Experiment 1: bei schwankendem Grad (Potenzgesetz, skalenfrei) liegen Grad, adaptiver Grad, Betweenness und die Hub-Variante der Bekannten-Impfung bei 0,7 bis 1,8 %, Zufall bei 22,5 und 20,8 %; im Gitter liegen alle Strategien zwischen 9,1 % und 15,0 % |
| **Gibt es einen Impfanteil, der den Ausbruch eindämmt?** | siehe Tabelle zu Experiment 2: bei schwankendem Grad genügen mit der Gradregel 2,4 % (Potenzgesetz) bzw. 3,6 % (skalenfrei), mit Zufall sind es im Potenzgesetz-Netz **mehr als 40 %** (der Median der acht Netze erreicht die 5 % bis dahin nicht); im Gitter braucht selbst die beste Strategie (adaptiver Grad) 16,0 %, Zufall 22,7 % |
| **Reicht Nachbarwissen?** | siehe Tabelle zu Experiment 3 |
| **Bleibt die beste Strategie bei anderer Ausbreitungsstärke die beste?** | Ja: in allen vier geprüften Netztypen (skalenfrei, Zufallsnetz, Ring, Gitter) ist bei 10, 30 und 60 % der adaptive Grad am besten; die Betweenness bleibt im Gitter bei jeder Stärke schlechter als Zufall (Tabelle zu Experiment 4) |
| **Wie weit sind Greedy und Grad vom Optimum?** (kleine Netze, exakt) | siehe Tabelle zu Experiment 5 |
| **Standardnetz** (Zufallsnetz, *n* = 150, *c* = 6, Seed 35, Ausbreitungsstärke 30 %, 10 % Impfanteil, Zufall) | 450 Kanten, *p* = 0,246; ohne Impfung 30,8 %, mit 15 zufällig gesicherten Betrieben 17,9 %; Grad 9,0 %, die beste Strategie ist der adaptive Grad |
| **Preset Superspreader** (skalenfrei, *n* = 150, Grad) | 444 Kanten, *p* = 0,239; ohne Impfung 30,5 %, Grad **2,1 %** gegen Zufall 19,5 %; 150 Abfragen |
| **Preset Nachbarwissen reicht fast** (skalenfrei, Bekannte mit Hub-Wahl) | 3,9 % gegen Grad 2,1 % und Zufall 19,5 %; im Mittel 103,8 Abfragen |
| **Preset Gitter** (*n* = 250, Betweenness, Seed 35) | 705 Kanten (256 Betriebe), *p* = 0,355; ohne Impfung 30,7 %, Betweenness **15,0 %** gegen Zufall 13,0 % und Grad 10,5 % |
| **Preset Ring** (*n* = 150, adaptiver Grad) | 471 Kanten, *p* = 0,312; ohne Impfung 27,1 %, adaptiver Grad 6,6 % gegen Grad 8,6 % und Zufall 13,8 % |
| **Preset Starke Ausbreitung** (Potenzgesetz, Ausbreitungsstärke 60 %, Grad) | 416 Kanten, *p* = 0,386; ohne Impfung 60,0 %, Grad **7,5 %** gegen Zufall 46,9 % |

**Experiment 1: Ausbruchsgröße bei 10 % Impfanteil** (Prozent der Betriebe):

| Netztyp | ohne Impfung | Zufall | Grad | Grad adaptiv | Betweenness | Kernzahl | Bekannte | Bekannte, Hub-Wahl |
|---|---|---|---|---|---|---|---|---|
| Zufallsnetz | 29,2 | 15,9 | 5,6 | 5,0 | 6,0 | 14,5 | 13,6 | 7,0 |
| Potenzgesetz-Netz | 30,0 | 22,5 | 0,7 | 0,7 | 0,8 | 1,1 | 3,6 | 1,4 |
| Skalenfreies Netz (BA) | 30,3 | 20,8 | 1,1 | 1,0 | 1,1 | 20,1 | 8,1 | 1,8 |
| Verbünde | 29,1 | 15,4 | 5,2 | 4,3 | 5,7 | 13,4 | 12,9 | 7,2 |
| Ring mit Abkürzungen | 29,5 | 12,2 | 6,2 | 5,1 | 7,2 | 12,0 | 12,8 | 8,2 |
| Gitter | 29,5 | 12,3 | 10,3 | 9,1 | 15,0 | 12,4 | 12,3 | 11,2 |

**Experiment 2: kleinster Impfanteil für höchstens 5 % Ausbruchsgröße** (Prozent der Betriebe; „über 40“: der Median der acht Netze erreicht die Grenze bis 40 % nicht):

| Netztyp | Zufall | Grad | Grad adaptiv | Betweenness | Kernzahl | Bekannte | Bekannte, Hub-Wahl |
|---|---|---|---|---|---|---|---|
| Zufallsnetz | 26,2 | 11,0 | 10,2 | 11,4 | 21,4 | 21,4 | 12,6 |
| Potenzgesetz-Netz | über 40 | 2,4 | 2,4 | 2,4 | 4,6 | 8,8 | 5,0 |
| Skalenfreies Netz (BA) | 36,4 | 3,6 | 3,4 | 3,4 | 38,2 | 13,6 | 6,0 |
| Verbünde | 24,8 | 10,4 | 9,6 | 11,2 | 21,4 | 20,4 | 12,8 |
| Ring mit Abkürzungen | 22,2 | 13,2 | 10,4 | 14,2 | 22,8 | 22,0 | 15,8 |
| Gitter | 22,7 | 18,8 | 16,0 | 38,3 | 22,7 | 23,0 | 20,7 |

**Experiment 3: Bekannten-Impfung** (Ausbruchsgröße in Prozent bei 2 / 5 / 10 / 15 / 20 / 30 % Impfanteil; „Lücke“: Anteil der Differenz zwischen Zufall und Grad, den die Strategie bei 10 % schließt):

*Skalenfreies Netz (BA)* (ohne Impfung 30,3 %):

| Strategie | 2 % | 5 % | 10 % | 15 % | 20 % | 30 % | Lücke bei 10 % |
|---|---|---|---|---|---|---|---|
| Zufall | 27,7 | 25,1 | 20,8 | 16,5 | 13,2 | 7,3 |  |
| Bekannte | 24,9 | 18,5 | 8,1 | 4,1 | 2,2 | 1,0 | 64 % |
| Bekannte, Hub-Wahl | 18,4 | 6,8 | 1,8 | 1,1 | 0,8 | 0,6 | 97 % |
| Grad | 10,1 | 2,6 | 1,1 | 0,8 | 0,7 | 0,5 |  |

*Zufallsnetz* (ohne Impfung 29,2 %):

| Strategie | 2 % | 5 % | 10 % | 15 % | 20 % | 30 % | Lücke bei 10 % |
|---|---|---|---|---|---|---|---|
| Zufall | 26,4 | 22,1 | 15,9 | 11,2 | 7,7 | 3,6 |  |
| Bekannte | 25,6 | 21,0 | 13,6 | 8,5 | 5,5 | 2,4 | 22 % |
| Bekannte, Hub-Wahl | 23,2 | 15,3 | 7,0 | 3,6 | 2,2 | 1,2 | 86 % |
| Grad | 20,3 | 12,7 | 5,6 | 2,8 | 1,8 | 1,0 |  |

**Experiment 4: Strategien bei Ausbreitungsstärke 10 / 30 / 60 %** (Ausbruchsgröße in Prozent bei 10 % Impfanteil; die Spalte „ohne“ ist die Ausbruchsgröße ohne Impfung):

| Netztyp | Stärke | ohne | Zufall | Grad | Grad adaptiv | Betweenness | Kernzahl | Bekannte | Bekannte, Hub-Wahl |
|---|---|---|---|---|---|---|---|---|---|
| Skalenfreies Netz (BA) | 10 % | 9,6 | 6,2 | 0,7 | 0,7 | 0,7 | 5,9 | 2,1 | 0,9 |
| Skalenfreies Netz (BA) | 30 % | 30,3 | 20,8 | 1,1 | 1,0 | 1,1 | 20,1 | 8,1 | 1,8 |
| Skalenfreies Netz (BA) | 60 % | 60,5 | 47,0 | 3,1 | 2,8 | 3,2 | 47,0 | 30,1 | 8,4 |
| Zufallsnetz | 10 % | 10,1 | 5,2 | 2,2 | 2,0 | 2,2 | 4,7 | 4,3 | 2,6 |
| Zufallsnetz | 30 % | 29,2 | 15,9 | 5,6 | 5,0 | 6,0 | 14,5 | 13,6 | 7,0 |
| Zufallsnetz | 60 % | 60,4 | 44,6 | 25,4 | 23,5 | 26,0 | 41,8 | 41,4 | 29,7 |
| Ring mit Abkürzungen | 10 % | 11,1 | 5,5 | 3,6 | 3,1 | 4,0 | 5,4 | 5,4 | 4,2 |
| Ring mit Abkürzungen | 30 % | 29,5 | 12,2 | 6,2 | 5,1 | 7,2 | 12,0 | 12,8 | 8,2 |
| Ring mit Abkürzungen | 60 % | 60,3 | 27,1 | 11,0 | 8,6 | 14,0 | 28,4 | 28,4 | 16,6 |
| Gitter | 10 % | 9,8 | 5,0 | 4,3 | 4,1 | 6,0 | 4,9 | 5,0 | 4,7 |
| Gitter | 30 % | 29,5 | 12,3 | 10,3 | 9,1 | 15,0 | 12,4 | 12,3 | 11,2 |
| Gitter | 60 % | 56,7 | 26,8 | 22,2 | 19,8 | 33,8 | 26,4 | 26,0 | 25,1 |

**Experiment 5: exakt auf kleinen Netzen** (Mittel über 10 Netze mit 9 Betrieben und 12 Partnerschaften, *p* = 0,5; „Grad über Optimum“: Median der relativen Abweichung):

| Impfungen | ohne | Optimum | Greedy | Greedy trifft Optimum | Grad | Grad über Optimum | Zufall |
|---|---|---|---|---|---|---|---|
| k = 2 | 51,1 | 20,8 | 20,8 | 9 von 10 | 21,9 | 1,5 | 33,3 |
| k = 3 | 51,1 | 15,3 | 15,6 | 8 von 10 | 16,9 | 9,1 | 27,0 |

### Hypothesen des Einzelplans

| | Hypothese | Ergebnis |
|---|---|---|
| H1 | In Netzen mit stark schwankendem Grad ist die Gradregel die beste einfache Strategie und schlägt Zufall um ein Vielfaches | ✅ Potenzgesetz 0,7 % gegen 22,5 %, skalenfrei 1,1 % gegen 20,8 % (10 % Impfanteil); nötiger Impfanteil 2,4 % und 3,6 % gegen > 40 % und 36,4 % |
| H2 | Die Bekannten-Impfung kommt ohne Netzwissen nahe an die Gradregel (Cohen u. a. 2003) | ⚠ nur teilweise: sie hilft (8,1 % gegen 20,8 % im skalenfreien Netz), erreicht die Gradregel aber nicht (1,1 %), schließt 64 % bzw. 22 % der Lücke |
| H3 | Mit der Hub-Wahl unter den Partnern liegt man fast bei der Gradregel | ✅ 1,8 % gegen 1,1 % (skalenfrei), 1,4 % gegen 0,7 % (Potenzgesetz), 97 % der Lücke; im Zufallsnetz 86 % der Lücke (7,0 % gegen 5,6 %); Wissen: Partner eines Zufallsbetriebs und deren Partnerzahl |
| H4 | Die Gradregel gewinnt überall (Risiko im Plan) | ❌ im Gitter nur 10,3 % gegen 12,3 % (Zufall), die Betweenness mit 15,0 % schlechter als Zufall; im Ring 6,2 % gegen 12,2 % |
| H5 | Die Kernzahl ist als Impfregel schwach (Stück 1 und 5) | ✅ skalenfrei 20,1 % gegen 20,8 % (Zufall); im Potenzgesetz-Netz brauchbar (1,1 %) |
| H6 | Greedy liegt nahe am Optimum, die Gradregel darüber | ✅ auf kleinen exakten Netzen: *k* = 2 Optimum 20,8 %, Greedy 20,8 %, Grad 21,9 %; *k* = 3 15,3 %, 15,6 %, 16,9 % (nur ein Beleg für die Rechnung, nicht für große Netze) |
| H7 | Die adaptive Gradregel schlägt die statische nur schwach | ✅ in Netzen mit schwankendem Grad kaum (1,0 % gegen 1,1 %), im Ring (5,1 % gegen 6,2 %) und im Gitter (9,1 % gegen 10,3 %) deutlicher |
| H8 | Der Vorteil hängt von der Ausbreitungsstärke ab | ⚠ die beste Strategie bleibt der adaptive Grad (vier Netztypen, 10, 30 und 60 %), die Betweenness im Gitter bei jeder Stärke schlechter als Zufall; die absolute Lücke zu Zufall wächst im Zufallsnetz mit der Stärke (bei 10 %: 5,2 gegen 2,2 %; bei 60 %: 44,6 gegen 25,4 %) |

## Ehrliche Grenzen

- **Gleiches *p*, ein Schritt ansteckend, vollständig wirksame und sofortige Impfung ohne Kosten je Betrieb.** Mit Genesungsdauer, Wirkung unter 100 % oder Kosten je Betrieb sind die Zahlen andere; die Rangfolge der Strategien wurde nur für die Ausbreitungsstärken 10, 30 und 60 % geprüft.
- **Der Befall beginnt in einem zufälligen Ungeimpften.** Beginnt er gezielt in einem Hub, sind die Werte andere. Die Ausbruchsgröße kann mit mehr Impfungen steigen (Handbeispiel im Test).
- **Wissen als Zählung:** die Abfragen sind kein Maß der Güte; Grad, Betweenness und Kernzahl setzen voraus, dass das Netz vollständig bekannt ist.
- **Synthetische Netze** mit *n* bis 250, Mediane über acht feste Netze; die Streuung zwischen den Netzen ist nicht ausgewiesen. **Der Nachteil der Betweenness im Gitter zeigt sich bei *n* = 250** (acht von acht Netzen, Verhältnis 1,19 bis 1,34 zu Zufall), **bei *n* = 150 nicht systematisch** (vier von acht Netzen schlechter, höchstens 1,07); eine Erklärung ist nicht untersucht.
- **Exakter Vergleich nur auf winzigen Netzen** (9 Betriebe, 10 Netze); Greedy ist auf großen Netzen nicht gerechnet.
- **Zufalls-Strategien sind Mittel über wenige Ziehungen** (3 bis 5 in den Experimenten, 3 bis 10 im Hauptlauf).
- **Experiment 4 rechnet den gewählten Netztyp;** die README nennt die Befunde für skalenfrei, Zufallsnetz, Ring und Gitter.
- **Literatur:** die bibliografischen Angaben im 📐-Expander sind nachgeschlagen (Pastor-Satorras und Vespignani, PRE 65, 036104; Cohen u. a., PRL 91, 247901; Holme, EPL 68(6), 908–914; Gallos u. a., PRE 75, 045104(R)); die Arbeiten selbst sind nicht vollständig gelesen.

## Verifikation

- **Kern:** Handwerte auf Mini-Instanzen (`tests/conftest.py`, `tests/test_algorithm.py`): Pfad (Größe 1 und 1/3), Stern (0,2), zwei Dreiecke mit Brücke (13/30), vollständig geimpft (0), Gegenbeispiel zur Monotonie, Befallsrisiko, Strategien (Grad, adaptiv, Kern, Betweenness, Bekannte), Wissenszählung, exakte Aufzählung (5,5/9 auf dem Pfad).
- **Orakel:** `tests/test_oracle_eindaemmung.py` – Komponenten gegen `networkx`, exakte Ausbruchsgröße gegen eine unabhängige Aufzählung, Schnappschuss-Schätzer und direkte SIR-Simulation gegen den exakten Wert, Optimum gegen Python-Suche, Wahlwahrscheinlichkeiten der Bekannten-Impfung gegen die geschlossene Formel, Maße gegen `networkx`.
- **Netze:** gültig in allen Ecken der Regler, deterministisch je Seed (auch über Prozesse mit verschiedenem Hash-Seed), kleine Netze verbunden und mit der verlangten Größe (`tests/test_scenario.py`).
- **Verdikte:** jede Schwelle und jede Zahl im Text an von Hand gesetzten Werten (`tests/test_verdicts.py`), Randfälle (Regler-Ecken für alle Netztypen und Strategien ohne Warnungen, Netz ohne Kanten, kleinste Netze in allen Experimenten, alle Abbildungen) in `tests/test_edge_cases.py`.
- **Befunde:** jede Zahl dieser README in `tests/test_claims.py`.
- **Mutationsprüfung des Kerns:** (`eid_algorithm.py`, 144 Stellen, ohne die langsamen Aussagen-Tests in der Suite der Überlebenden): 44 Stellen sind durch wortgleiche Zeilen in Nachbar-Demos gesichert, die übrigen nach Ergänzung von Tests und eines Schleifenschutzes in der Bekannten-Impfung gefangen oder als äquivalent festgehalten (20 Einträge, z. B. Schrittzahl der Bisektion, Gleichheit zweier Fließkommazahlen bei stetigem Zufall, Reihenfolge einer Menge, Grenzen des Schleifenschutzes); zwei Mutanten laufen in Endlosschleifen (Zeitüberschreitung in der Union-Find-Suche und im Abstand der Betweenness) und werden durch das Hängen der Suite erkannt. Zustand in `tests/mutation_state.json`.
- **Presets:** vollständig, Werte innerhalb der Reglergrenzen, Standard-Preset gleich Standardeinstellung, jedes Preset zeigt, wofür es benannt ist.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum, jeder Netztyp mit jeder Strategie, Permalink, alle fünf Experimente) und Footer-Test.
- **Layout:** Schnellstart oben in der Seitenleiste, fester Kopf, aktives Preset hervorgehoben; jede Änderung eines Reglers hebt die Markierung auf (`tests/test_layout.py`).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `eid_algorithm.py` | Kern: Schnappschüsse, Ausbruchsgröße (rückwärts mit Union-Find), Strategien als Wahlreihenfolgen, Befallsrisiko, Wissenszählung, exakte Aufzählung |
| `eid_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `eid_evaluation.py` | Analyse, Verdikt-Logik, Messreihen über feste Netze |
| `eid_layout.py` | Fester Kopf (Stylesheet) |
| `eid_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `eid_scenario.py` | Netze: Generatoren (Kopie aus `k-core-demo`), Anordnung |
| `eid_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest, networkx, scipy (nur für die Gegenproben) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Mini-Instanzen und Handwerte, Orakel, Netze, Verdikte, Randfälle, Presets, Layout, AppTest-Smoke-Test, Footer, Laufzeit-Importe, Befunde |

## Bewusst nicht umgesetzt

- **Greedy auf großen Netzen live:** jede Auswertung braucht alle Schnappschüsse; Greedy läuft nur im exakten Experiment auf kleinen Netzen.
- **Teilweise wirksame oder verzögerte Impfung, Kosten je Betrieb, Genesung:** eigene Fragen; als möglicher Ausbau (gelb).
- **Gezielter Start des Befalls** (in einem Hub) und die Frage, woher ein Ausbruch kam: Stück 8 (Quellensuche).
- **Zeitliche Netze:** Stück 13.
- **Netze über 250 Betriebe live:** die Messreihen rechnen im Browser, die Dauer wächst mit Netzgröße und Zahl der Läufe.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
