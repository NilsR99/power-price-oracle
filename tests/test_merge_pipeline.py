import pytest
import pandas as pd
import numpy as np

from merge_script import validate_date_range, combine_master_data

# --- 1. TESTS FÜR DIE DATUMSVALIDIERUNG ---

def test_validate_date_range_success():
    """Prüft, ob korrekte Daten innerhalb der Grenzen (2020-2025) akzeptiert werden."""
    # ACT & ASSERT
    assert validate_date_range("2020-01-01", "2025-12-31") is True
    assert validate_date_range("2024-04-01", "2024-04-30") is True
    assert validate_date_range("2023-05-10", "2023-05-10") is True
    assert validate_date_range("2023-05-05", "2023-5-7") is True
    assert validate_date_range("2023-5-9", "2023-5-10") is True
    

def test_validate_date_range_out_of_bounds():
    """Prüft, ob die harte Grenze (2020 bis 2025) eingehalten wird."""
    # Wir erwarten einen ValueError, wenn der Nutzer 2019 auswählt
    with pytest.raises(ValueError, match="außerhalb des erlaubten Bereichs"):
        validate_date_range("2009-12-31", "2020-01-31")
        
    # Test für die obere Grenze
    with pytest.raises(ValueError, match="außerhalb des erlaubten Bereichs"):
        validate_date_range("2025-01-01", "2026-01-01")

def test_validate_date_range_chronological_error():
    """Prüft, ob abgefangen wird, dass das Startdatum nach dem Enddatum liegt."""
    with pytest.raises(ValueError, match="darf nicht nach dem Enddatum liegen"):
        validate_date_range("2024-12-31", "2024-01-01")

def test_validate_date_range_invalid_format():
    """Prüft, ob Quatsch-Eingaben sauber abgelehnt werden."""
    with pytest.raises(ValueError, match="Ungültiges Datumsformat"):
        validate_date_range("Morgen", "Übermorgen")


# --- 2. TESTS FÜR DIE MERGE-LOGIK ---

def test_combine_master_data_success():
    """
    Prüft, ob Wetter und SMARD korrekt über den Zeitstempel gemerged werden
    und die UTC-Normierung funktioniert.
    """
    # ARRANGE: Wir bauen künstliche (mock) DataFrames
    df_weather_mock = pd.DataFrame({
        "date": pd.to_datetime(["2025-01-01 12:00:00", "2025-01-01 13:00:00"]),
        "temperature_2m": [5.5, 6.1]
    })
    
    df_smard_mock = pd.DataFrame({
        "date": pd.to_datetime(["2025-01-01 12:00:00", "2025-01-01 14:00:00"]),
        "price_day_ahead": [45.2, 80.5]
    })

    # ACT: Die Funktion aufrufen
    df_result = combine_master_data(df_weather_mock, df_smard_mock)

    # ASSERT: Fachliche Prüfung der Resultate
    # Da es ein Outer-Join ist, müssen die Stunden 12, 13 und 14 vorhanden sein (3 Zeilen)
    assert len(df_result) == 3, "Fehler: Der Outer-Join hat Zeilen verschluckt."
    
    # Prüfen, ob die Spaltennamen korrekt zusammengeführt wurden
    assert "temperature_2m" in df_result.columns
    assert "price_day_ahead" in df_result.columns
    
    # Prüfen, ob die UTC-Zeitzonenkorrektur in der Funktion funktioniert hat
    assert str(df_result['date'].dt.tz) == 'UTC', "Fehler: Die Funktion hat die Zeitzone nicht auf UTC genormt."

def test_combine_master_data_empty_inputs():
    """Prüft die defensive Programmierung: Was passiert, wenn eine API leere Daten liefert?"""
    
    df_valid = pd.DataFrame({"date": [pd.Timestamp("2025-01-01")], "val": [1]})
    df_empty = pd.DataFrame()
    
    # Wenn Wetter fehlt
    with pytest.raises(ValueError, match="Wetterdaten fehlen"):
        combine_master_data(df_empty, df_valid)
        
    # Wenn SMARD fehlt
    with pytest.raises(ValueError, match="SMARD-Daten fehlen"):
        combine_master_data(df_valid, df_empty)