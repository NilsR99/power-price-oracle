import streamlit as st
import plotly.express as px

def render_hypothese_2(df_master):
    st.header("Hypothese 2: Hitze führt zu höheren Preisen")
    
    required_cols = ["temperature_2m", "price_day_ahead"]
    missing_cols = [col for col in required_cols if col not in df_master.columns]
    
    if missing_cols:
        st.warning(f"Für diesen Beweis fehlen folgende Spalten im Datensatz: {missing_cols}")
    else:
        df_clean = df_master.dropna(subset=required_cols).copy()
        df_clean["temp_rounded"] = df_clean["temperature_2m"].round()
        
        df_agg = df_clean.groupby("temp_rounded").agg(
            mean_price=("price_day_ahead", "mean"),
            hour_count=("price_day_ahead", "count") 
        ).reset_index()

        fig_scatter = px.scatter(
            df_agg, x="temp_rounded", y="mean_price", size="hour_count",
            color_discrete_sequence=["#1f77b4"], 
            labels={"temp_rounded": "Temperatur (°C)", "mean_price": "Ø Preis (€/MWh)"},
            hover_data=["hour_count"] 
        )
        
        fig_scatter.update_layout(height=650, plot_bgcolor="rgba(0,0,0,0)")
        fig_scatter.add_hline(y=0, line_dash="dash", line_color="red")
        fig_scatter.add_vline(x=30, line_dash="solid", line_color="firebrick", line_width=2)
        fig_scatter.add_vrect(x0=30, x1=df_agg["temp_rounded"].max(), fillcolor="lightsalmon", opacity=0.3, layer="below")
        st.plotly_chart(fig_scatter, use_container_width=True)