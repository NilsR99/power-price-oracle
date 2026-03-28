import streamlit as st
import plotly.express as px
import pandas as pd

def render_energiemix_pie(df_master, filter_container):
    """
    Rendert ein Kreisdiagramm des Energiemixes. 
    Der Nutzer kann Zeitraum UND die spezifischen Energieträger wählen.
    Das Diagramm zeigt immer das prozentuale Verhältnis der gewählten Quellen zueinander.
    """
    st.header("Relative Struktur-Analyse: Der selektive Energiemix")
    st.markdown(
        "Wähle spezifische Energiequellen aus, um deren **genaues Verhältnis zueinander** "
        "im ausgewählten Zeitraum zu analysieren."
    )

    # --- 1. Dynamisches Scanning der verfügbaren Erzeuger ---
    # Wir definieren alle potenziellen SMARD-Erzeuger, die wir in der Pipeline konfiguriert haben
    all_possible_cols = {
        "actual_wind_onshore": "Wind Onshore",
        "actual_wind_offshore": "Wind Offshore",
        "actual_pv": "Solar (PV)",
        "actual_brown_coal": "Braunkohle",
        "actual_gas": "Erdgas",
        "actual_nuclear": "Kernenergie",
        "actual_hydro": "Wasserkraft",
        "actual_biomass": "Biomasse",
        "actual_hard_coal": "Steinkohle",
        "actual_pumped_storage": "Pumpspeicher",
        "actual_other_conventional": "Sonstige Konventionelle",
        "actual_other_renewables": "Sonstige Erneuerbare"
    }

    # Wir filtern: Welche dieser Spalten existieren TATSÄCHLICH im aktuellen DataFrame?
    # (So stürzt das Skript nicht ab, wenn z.B. Atomkraft 2025 fehlt)
    available_cols = {k: v for k, v in all_possible_cols.items() if k in df_master.columns}

    if not available_cols:
        st.error("⚠️ Analytischer Fehler: Keine Erzeugungsdaten im Datensatz gefunden.")
        return

    # --- 2. Dynamische UI im Sidebar-Container ---
    
    # A) Der Zeit-Filter
    min_dt = df_master["date"].min().to_pydatetime()
    max_dt = df_master["date"].max().to_pydatetime()

    filter_container.write("**🕒 Zeitraum-Feinabstimmung**")
    selected_range = filter_container.slider(
        "Start- und Endzeitpunkt auswählen",
        min_value=min_dt,
        max_value=max_dt,
        value=(min_dt, max_dt),
        format="DD.MM.YY - HH:mm",
        step=pd.Timedelta(hours=1)
    )

    # B) Der neue Multiselect-Filter für die Energiequellen
    filter_container.write("**🔋 Energiequellen auswählen**")
    
    # Wir wählen standardmäßig die ersten 3 verfügbaren aus, damit das Diagramm nicht nackt startet
    default_selection = list(available_cols.values())[:3] 
    
    selected_friendly_names = filter_container.multiselect(
        "Welche Energieträger sollen verglichen werden?",
        options=list(available_cols.values()),
        default=default_selection
    )

    if not selected_friendly_names:
        st.warning("⚠️ Bitte wähle mindestens eine Energiequelle in der Sidebar aus.")
        return

    # Reverse Mapping: Vom "schönen Namen" (z.B. "Wind Onshore") zurück zum Datenbank-Spaltennamen
    selected_db_cols = [k for k, v in available_cols.items() if v in selected_friendly_names]

    # --- 3. Daten filtern und berechnen ---
    start_selection, end_selection = selected_range
    df_filtered = df_master[
        (df_master["date"] >= start_selection) & 
        (df_master["date"] <= end_selection)
    ]

    if df_filtered.empty:
        st.warning("⚠️ Keine Daten im ausgewählten Zeitraum vorhanden.")
        return

    # Wir summieren NUR die Spalten, die der Nutzer ausgewählt hat
    total_generation_series = df_filtered[selected_db_cols].sum().fillna(0)
    
    # DataFrame für Plotly vorbereiten
    plot_data = []
    for col_name in selected_db_cols:
        val = total_generation_series[col_name]
        if val > 0: # Wir ignorieren Quellen, die 0 MWh geliefert haben (z.B. PV nachts)
            plot_data.append({
                "Energiequelle": available_cols[col_name],
                "Erzeugung (MWh)": val
            })

    if not plot_data:
        st.warning("⚠️ Im gewählten Zeitraum wurde von den ausgewählten Quellen exakt 0 MWh erzeugt.")
        return

    df_pie = pd.DataFrame(plot_data)
    total_selected_sum = df_pie["Erzeugung (MWh)"].sum()

    # --- 4. Plotly Rendering ---
    st.markdown(f"**Analyse für:** `{start_selection.strftime('%d.%m.%Y, %H:%M')}` bis `{end_selection.strftime('%d.%m.%Y, %H:%M')}`")

    # Feste Farben für visuelle Konsistenz
    color_map = {
        "Wind Onshore": "#1f77b4", "Wind Offshore": "#17becf", "Solar (PV)": "#ff7f0e",
        "Braunkohle": "#8c564b", "Erdgas": "#d62728", "Kernenergie": "#e377c2",
        "Wasserkraft": "#2ca02c", "Biomasse": "#8c564b", "Steinkohle": "#7f7f7f",
        "Pumpspeicher": "#bcbd22", "Sonstige Konventionelle": "#c7c7c7", "Sonstige Erneuerbare": "#dbdb8d"
    }

    fig = px.pie(
        df_pie, 
        values="Erzeugung (MWh)", 
        names="Energiequelle",
        color="Energiequelle",
        color_discrete_map=color_map,
        hole=0.4,
        title=f"Verhältnis der Auswahl (Gesamt: {total_selected_sum:,.0f} MWh)"
    )
    
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(margin=dict(l=0, r=0, b=0, t=40))

    st.plotly_chart(fig, use_container_width=True)