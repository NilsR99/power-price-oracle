import streamlit as st
import plotly.express as px

def render_lastprofil(df_master):
    st.header("Tageslastprofil (SLP) Deutschland")
    
    if "actual_total_load" not in df_master.columns:
        st.warning("⚠️ Für das Lastprofil fehlt die Spalte: actual_total_load")
    else:
        df_slp = df_master.dropna(subset=["actual_total_load"]).copy()
        # Zeitzonen-Korrektur
        df_slp['date_local'] = df_slp['date'].dt.tz_convert('Europe/Berlin')
        df_slp['hour_local'] = df_slp['date_local'].dt.hour
        df_slp['weekday'] = df_slp['date_local'].dt.dayofweek
        df_slp['Tagesart'] = df_slp['weekday'].apply(lambda x: 'Wochenende (Sa/So)' if x >= 5 else 'Werktag (Mo-Fr)')
        
        df_slp_agg = df_slp.groupby(['hour_local', 'Tagesart'])['actual_total_load'].mean().reset_index()

        fig_slp = px.line(
            df_slp_agg, x="hour_local", y="actual_total_load", color="Tagesart",
            labels={"hour_local": "Uhrzeit", "actual_total_load": "Ø Gesamtlast (MWh)"},
            markers=True
        )
        
        fig_slp.update_layout(
            height=500, xaxis=dict(tickmode='linear', tick0=0, dtick=1), 
            plot_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_slp, use_container_width=True)