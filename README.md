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

## Installation und lokales Setup

Dieses Projekt erfordert eine strikte Reihenfolge bei der Ausführung: Zuerst muss die Datengrundlage über die APIs generiert werden (ETL-Pipeline), erst danach kann die Visualisierung gestartet werden. Befolge diese Schritte exakt, um das Dashboard lokal auszuführen.

### Voraussetzungen
* **Python:** Version 3.9 oder neuer muss auf dem System installiert sein.
* **Git:** Zum Herunterladen des Quellcodes.

### 1. Repository klonen
Lade den Code auf deinen lokalen Rechner herunter und wechsle in das Projektverzeichnis:
```bash
git clone https://github.com/NilsR99/power-price-oracle.git
cd power-price-oracle
```

### 2. Virtuelle Umgebung einrichten (Best Practice)

Installiere die Projektabhängigkeiten niemals global auf deinem Betriebssystem. Nutze eine isolierte Umgebung (venv), um Versionskonflikte mit anderen Python-Projekten zu vermeiden:
```bash
# Virtuelle Umgebung erstellen
python -m venv .venv

# Umgebung aktivieren (Windows Command Prompt / PowerShell)
.venv\Scripts\activate

# Umgebung aktivieren (macOS / Linux)
source .venv/bin/activate
```

### 3. Abhängigkeiten installieren

Sobald die virtuelle Umgebung aktiv ist (sichtbar am (.venv) Präfix in deinem Terminal), installiere die exakten Versionen der benötigten Bibliotheken:
```bash
pip install -r requirements.txt
```

### Datengrundlage generieren (WICHTIG!)

Das Dashboard enthält keine vorkompilierten Daten. Du musst zwingend vor dem ersten Start die Daten-Pipeline ausführen, um die aktuellen API-Daten (SMARD Strommarkt & Open-Meteo Wetter) live abzurufen und zu mergen.
```bash
python merge_pipeline.py
```

Hinweis: Dieses Skript benötigt je nach Internetverbindung einige Sekunden. Es erstellt automatisch den Pfad data/merged/ und legt dort die resultierende Master-JSON ab. Das Dashboard findet die aktuellste Datei bei jedem Start automatisch (Auto-Discovery).

5. Dashboard starten

Starte nun den lokalen Streamlit-Server, um die grafische Oberfläche zu laden:
```bash
streamlit run app.py
```

Das Analyse-Dashboard öffnet sich anschließend automatisch in deinem Standard-Webbrowser unter der lokalen Adresse http://localhost:8501.