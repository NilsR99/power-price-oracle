import streamlit as st
import plotly.express as px
import pandas as pd

def render_lastprofil(df_master, filter_container):
    st.header("Tageslastprofil (SLP) Deutschland")
    st.markdown(
        "**Anomalie-Analyse:** Vergleiche das Lastprofil eines spezifischen Zeitraums "
        "(z.B. Feiertage, Lockdown, Hitzewelle) mit dem historischen Gesamtdurchschnitt."
    )
    
    if "actual_total_load" not in df_master.columns:
        st.error("Analytischer Fehler: Für das Lastprofil fehlt die Spalte 'actual_total_load'.")
        return

    df_slp = df_master.dropna(subset=["actual_total_load"]).copy()
    
    # --- 1. Zeitzonen-Korrektur für korrekte Stunden ---
    # Da Stromverbrauch stark vom Tageslicht (Lokalzeit) abhängt, ist UTC hier falsch.
    if df_slp['date'].dt.tz is None:
        df_slp['date'] = df_slp['date'].dt.tz_localize('UTC')
    
    df_slp['date_local'] = df_slp['date'].dt.tz_convert('Europe/Berlin')
    df_slp['hour_local'] = df_slp['date_local'].dt.hour
    df_slp['weekday'] = df_slp['date_local'].dt.dayofweek
    df_slp['Tagesart'] = df_slp['weekday'].apply(lambda x: 'Wochenende (Sa/So)' if x >= 5 else 'Werktag (Mo-Fr)')
    
    # --- 2. Dynamische UI: Der Zeit-Filter im Container ---
    min_dt = df_slp['date_local'].min().to_pydatetime()
    max_dt = df_slp['date_local'].max().to_pydatetime()

    filter_container.write("**🕒 Vergleichs-Zeitraum (Anomalie)**")
    selected_range = filter_container.slider(
        "Welcher Zeitraum soll gegen den Durchschnitt verglichen werden?",
        min_value=min_dt,
        max_value=max_dt,
        value=(min_dt, max_dt),
        format="DD.MM.YY - HH:mm",
        step=pd.Timedelta(hours=1)
    )
    start_sel, end_sel = selected_range

    # --- 3. Daten-Aggregation (Split in Baseline und Auswahl) ---
    # A) BASELINE: Der Durchschnitt über alle Jahre
    df_base_agg = df_slp.groupby(['hour_local', 'Tagesart'])['actual_total_load'].mean().reset_index()
    df_base_agg['Vergleich'] = 'Langjähriger Durchschnitt'

    # B) AUSWAHL: Der Durchschnitt des gefilterten Zeitraums
    df_filtered = df_slp[(df_slp['date_local'] >= start_sel) & (df_slp['date_local'] <= end_sel)]
    
    if df_filtered.empty:
        st.warning("Keine Daten im ausgewählten Zeitraum vorhanden.")
        return

    df_filt_agg = df_filtered.groupby(['hour_local', 'Tagesart'])['actual_total_load'].mean().reset_index()
    df_filt_agg['Vergleich'] = 'Ausgewählter Zeitraum'

    # C) MERGE: Zusammenführen für Plotly
    # Wenn der Nutzer nichts gefiltert hat, zeigen wir die Linien nicht doppelt an
    if start_sel == min_dt and end_sel == max_dt:
        df_plot = df_base_agg
    else:
        df_plot = pd.concat([df_base_agg, df_filt_agg], ignore_index=True)

    # --- 4. Plotly Rendering mit 4 Dimensionen ---

    color_map = {
        'Langjähriger Durchschnitt': '#0000ff', # dunkles blau
        'Ausgewählter Zeitraum': '#d62728'      # Signifikantes Klarrot
    }

    dash_map = {
        'Werktag (Mo-Fr)': 'solid',
        'Wochenende (Sa/So)': 'dash' 
    }
    fig_slp = px.line(
        df_plot, 
        x="hour_local", 
        y="actual_total_load", 
        color="Vergleich",           # 1. Dimension: Farbe trennt Werktag/Wochenende
        line_dash="Tagesart",      # 2. Dimension: Linienart trennt Baseline/Auswahl
        color_discrete_map=color_map, 
        line_dash_map=dash_map,
        labels={
            "hour_local": "Uhrzeit (Lokalzeit Berlin)", 
            "actual_total_load": "Ø Gesamtlast (MWh)"
        },
        markers=True,
        title="Lastprofil-Vergleich: Baseline vs. Anomalie"
    )
    
    # Styling für bessere Lesbarkeit
    fig_slp.update_layout(
        height=600, 
        xaxis=dict(tickmode='linear', tick0=0, dtick=1), # Zwingt Plotly, jede Stunde anzuzeigen
        plot_bgcolor="rgba(0,0,0,0)", 
        legend=dict(title=None, orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified" # Zeigt beim Hovern alle Linien für diese Stunde an
    )
    
    st.plotly_chart(fig_slp, use_container_width=True)