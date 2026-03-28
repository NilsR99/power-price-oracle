import streamlit as st
import plotly.express as px
import pandas as pd

def render_heatmap(df_master):
    st.header("🔥 Heatmap: Wann kollabiert der Strompreis?")
    st.markdown(
        "**Ursachenforschung:** Dieses Diagramm beweist, dass negative Preise nicht nur von der bloßen "
        "Einspeisemenge (MWh) abhängen, sondern massiv vom **Zeitpunkt der Einspeisung**. "
        "Es zeigt die absolute Häufigkeit (Anzahl der Stunden) negativer Strompreise (< 0 €) im gewählten Datensatz."
    )

    if "price_day_ahead" not in df_master.columns:
        st.error("⚠️ Analytischer Fehler: Die Spalte 'price_day_ahead' fehlt im Datensatz.")
        return

    # --- 1. Daten bereinigen und Zeitzone anpassen ---
    df = df_master.dropna(subset=["price_day_ahead"]).copy()
    
    # Strommarkt ist strikt an die lokale Zeitzone gebunden (Sonne und Arbeitszeiten)
    if df['date'].dt.tz is None:
        df['date'] = df['date'].dt.tz_localize('UTC')
    df['date_local'] = df['date'].dt.tz_convert('Europe/Berlin')

    # --- 2. Feature Engineering (Wochentag und Stunde) ---
    df['Stunde'] = df['date_local'].dt.hour
    
    # Wir definieren die Wochentage fest als kategoriale Variable, 
    # damit Plotly sie später nicht alphabetisch (Dienstag, Donnerstag...) sortiert!
    wochentage = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    df['Wochentag'] = df['date_local'].dt.dayofweek.map(lambda x: wochentage[x])
    df['Wochentag'] = pd.Categorical(df['Wochentag'], categories=wochentage, ordered=True)

    # --- 3. Filterung auf negative Preise ---
    df_neg = df[df['price_day_ahead'] < 0]

    if df_neg.empty:
        st.success("🎉 Im analysierten Datensatz gab es **keine einzige Stunde** mit negativen Strompreisen!")
        return

    # --- 4. Mathematische Aggregation zur 7x24 Matrix ---
    # Wir zählen die Vorkommnisse. observed=False zwingt Pandas, auch Wochentage ohne Negativpreise zu behalten.
    df_agg = df_neg.groupby(['Wochentag', 'Stunde'], observed=False).size().unstack(fill_value=0)
    
    # Wir zwingen die Matrix, alle 24 Stunden (0-23) als Spalten zu haben, selbst wenn z.B. um 03:00 Uhr nie ein Preis negativ war.
    df_agg = df_agg.reindex(columns=range(24), fill_value=0)

    # --- 5. Plotly Rendering ---
    fig = px.imshow(
        df_agg,
        labels=dict(x="Uhrzeit (Lokalzeit)", y="Wochentag", color="Anzahl Negativ-Stunden"),
        x=df_agg.columns,
        y=df_agg.index,
        color_continuous_scale="Reds", # Rot signalisiert Gefahr/Anomalie
        aspect="auto",
        text_auto=True # Zeigt die genaue Anzahl als Zahl im Kästchen an
    )

    fig.update_layout(
        title="Verteilung negativer Strompreise nach Wochentag und Uhrzeit",
        xaxis=dict(tickmode='linear', tick0=0, dtick=1), # Zwingt alle 24 Zahlen auf die X-Achse
        plot_bgcolor="rgba(0,0,0,0)",
        height=500
    )

    # Die Y-Achse umdrehen, damit Montag oben und Sonntag unten ist (intuitiver)
    fig.update_yaxes(autorange="reversed")

    st.plotly_chart(fig, use_container_width=True)

    # --- 6. Die energiewirtschaftliche Erklärung ---
    st.info(
        "💡 **Energiewirtschaftliche Auswertung:**\n\n"
        "Wenn du dir diese Heatmap ansiehst, wirst du einen tiefroten Kern im Bereich **Sonntagmittag (12:00 - 15:00 Uhr)** erkennen. "
        "Das ist der sogenannte *'Inflexibilitäts-Kollaps'*:\n"
        "* **Die Last ist minimal:** Die Industrie hat Wochenende, der Verbrauch ist am Boden.\n"
        "* **Die Einspeisung ist maximal:** Die Sonne steht im Zenit, Photovoltaik flutet das Netz.\n"
        "* **Der Must-Run Sockel blockiert:** Konventionelle Großkraftwerke können nicht für 3 Stunden abschalten, ohne Millionen an Anfahrtskosten zu riskieren. Sie produzieren stur weiter und bieten ihren Strom zu negativen Preisen an, um nicht vom Netz gehen zu müssen.\n\n"
        "**Ergebnis:** Der Preis stürzt ins Bodenlose. Das Problem ist also nicht *zu viel* Erneuerbare Energie, sondern das Zusammentreffen mit mangelnder Nachfrage und unflexiblen Alt-Kraftwerken."
    )