# korrelationsmatrix.py
import streamlit as st
import plotly.express as px

def render_korrelationsmatrix(df_master, df_numeric):
    st.header("Korrelations-Matrix")
    
    all_available_columns = df_numeric.columns.tolist()
    
    default_selection = ["price_day_ahead", "temperature_2m"]
    valid_defaults = [col for col in default_selection if col in all_available_columns]
    
    selected_columns = st.sidebar.multiselect(
        "Metriken auswählen (Mindestens 2)",
        options=all_available_columns,
        default=valid_defaults if valid_defaults else None
    )

    if len(selected_columns) < 2:
        st.error("⚠️ Analytischer Fehler: Du musst mindestens 2 Variablen auswählen, um eine Korrelation zu berechnen.")
    else:
        df_filtered = df_numeric[selected_columns]
        
        missing_data_ratio = df_filtered.isna().sum() / len(df_filtered) * 100
        st.sidebar.markdown("---")
        st.sidebar.write("📉 **Datenlücken (NaN) der Auswahl:**")
        st.sidebar.dataframe(missing_data_ratio.round(2))

        st.markdown("*Achtung: Ausgeblendete Variablen können zu einer verzerrten Kausalitätswahrnehmung führen.*")

        corr_matrix = df_filtered.corr()

        fig = px.imshow(
            corr_matrix, text_auto=".2f", aspect="auto",
            color_continuous_scale="RdBu_r", zmin=-1, zmax=1
        )
        fig.update_layout(height=max(400, len(selected_columns) * 60), margin=dict(l=0, r=0, b=0, t=30))
        st.plotly_chart(fig, use_container_width=True)
