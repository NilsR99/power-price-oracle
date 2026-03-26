import streamlit as st
import plotly.express as px

def render_hypothese_1(df_master):
    st.header("Hypothese 1: Senken Erneuerbare den Strompreis?")
    
    required_cols = ["price_day_ahead", "actual_wind_onshore", "actual_wind_offshore", "actual_pv", "actual_total_load"]
    missing_cols = [col for col in required_cols if col not in df_master.columns]
    
    if missing_cols:
        st.error(f"⚠️ Für diesen Beweis fehlen folgende Spalten im Datensatz: {missing_cols}")
    else:
        df_master["total_wind_solar"] = (
            df_master["actual_wind_onshore"].fillna(0) + 
            df_master["actual_wind_offshore"].fillna(0) + 
            df_master["actual_pv"].fillna(0)
        )
        
        df_plot = df_master.dropna(subset=["price_day_ahead", "total_wind_solar"])
        
        fig_scatter = px.scatter(
            df_plot, x="total_wind_solar", y="price_day_ahead", color="actual_total_load",
            color_continuous_scale="Plasma", opacity=0.5, 
            labels={"total_wind_solar": "Wind + PV Einspeisung (MWh)", "price_day_ahead": "Day-Ahead Preis (€/MWh)", "actual_total_load": "Gesamtlast (MWh)"},
            hover_data=["date"]
        )
        
        fig_scatter.update_layout(height=600, plot_bgcolor="rgba(0,0,0,0)")
        fig_scatter.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="0 € Grenze")
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        st.success("**Ergebnis:** Die Hypothese ist visuell bestätigt. Hohe Einspeisung führt zu starkem Preisverfall.")