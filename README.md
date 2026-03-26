# BIA Power Oracle: Strommarkt & Wetter Analyse

Dieses Projekt ist eine Business-Intelligence- und Data-Science-Pipeline zur Analyse des deutschen Strommarktes (Day-Ahead-Preise). Es verknüpft meteorologische physikalische Treiber (Open-Meteo API) mit marktökonomischen Ist-Werten (SMARD API) in einem denormalisierten Datenmodell, um preissetzende Mechanismen (wie den Merit-Order-Effekt) visuell und statistisch zu beweisen.

Das Frontend besteht aus einem interaktiven, modularen **Streamlit-Dashboard**, das die komplexen, nicht-linearen Zusammenhänge des Energiemarktes explorierbar macht.

## Analytische Features & Diagramme

Das Dashboard ist in vier logische Analyse-Module unterteilt, die über die linke Seitenleiste (Sidebar) navigiert werden können:

### 1. Dynamische Korrelations-Matrix (Pearson)
Eine Heatmap zur explorativen Datenanalyse (EDA). Sie berechnet lineare Zusammenhänge zwischen selbst wählbaren Variablen (z. B. Temperatur, Windgeschwindigkeit, Preis, Residuallast). 
* **Besonderheit:** Integrierte Live-Prüfung der Datenqualität (Missing Values Report für die gewählten Spalten).

### 2. Hypothese 1: Der Merit-Order-Effekt (Scatter-Plot)
**Hypothese:** *Senken Erneuerbare Energien kurzfristig den Strompreis?*
Das Diagramm plottet die kumulierte Einspeisung aus Wind und Solar gegen den Day-Ahead-Preis, farblich kodiert nach der aktuellen Gesamtlast. 
* **Erkenntnis:** Visueller Beweis des Preisverfalls (bis in den negativen Bereich) bei hoher Einspeisung von Grenzkosten-Null-Kraftwerken, unabhängig vom aktuellen Verbrauch.

### 3. Hypothese 2: Hitzeextreme und Preisstruktur (Aggregierter Bubble-Chart)
**Hypothese:** *Führen extreme Temperaturen (>30°C) zu höheren Strompreisen?*
Um das Rauschen der 8760 Jahresstunden zu minimieren, werden die Daten auf ganze Temperaturgrade aggregiert. Die Blasengröße gibt die statistische Relevanz (Anzahl der Stunden) an.
* **Erkenntnis:** Visualisierung der "U-Kurve" des Strommarktes, bei der extreme Hitze (Kühllast/Sommerflaute) sowie extreme Kälte (Heizlast) zu Preissprüngen führen.

### 4. Tageslastprofil / SLP (Line-Chart)
Zeitreihenanalyse des deutschen Stromverbrauchs im Tagesverlauf. 
* **Besonderheit:** Die UTC-Rohdaten der API werden on-the-fly in die deutsche Lokalzeit (`Europe/Berlin`) konvertiert, um menschliche Verhaltensmuster korrekt abzubilden. Zudem trennt die Analyse strikt zwischen Werktagen (Industrielast) und Wochenenden.