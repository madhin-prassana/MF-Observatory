from fastapi import APIRouter, HTTPException
import pandas as pd
import numpy as np
import os

router = APIRouter()

# Get project root
current_file = os.path.abspath(__file__)
api_folder = os.path.dirname(current_file)
backend_folder = os.path.dirname(api_folder)
PROJECT_ROOT = os.path.dirname(backend_folder)

# Data paths
PROPHET_PATH = os.path.join(PROJECT_ROOT, "results", "prediction_results.csv")
LSTM_PATH = os.path.join(PROJECT_ROOT, "results", "prediction_results_lstm.csv")
ENSEMBLE_PATH = os.path.join(PROJECT_ROOT, "results", "prediction_ensemble.csv")

# ... rest of file stays the same

# Load prediction data
try:
    prophet_df = pd.read_csv(PROPHET_PATH)
    lstm_df = pd.read_csv(LSTM_PATH)
    ensemble_df = pd.read_csv(ENSEMBLE_PATH)

    print(f"✓ Loaded prediction data successfully")

except Exception as e:
    print(f"✗ Error loading prediction data: {e}")
    prophet_df = pd.DataFrame()
    lstm_df = pd.DataFrame()
    ensemble_df = pd.DataFrame()


@router.get("/{scheme_code}")
def get_predictions(scheme_code: str):
    """Get all prediction models for a specific fund"""

    if prophet_df.empty or lstm_df.empty or ensemble_df.empty:
        raise HTTPException(status_code=500, detail="Prediction data not loaded")

    # Convert to int if digit string
    scheme_code_value = int(scheme_code) if scheme_code.isdigit() else scheme_code

    # Get Prophet prediction
    prophet = prophet_df[prophet_df['scheme_code'] == scheme_code_value]
    if prophet.empty:
        prophet_data = None
    else:
        prophet_data = {
            "model": "Prophet",
            "predicted_return_6m": float(prophet.iloc[0]['expected_return_6m']),
            "predicted_nav_6m": float(prophet.iloc[0]['predicted_nav_6m']),
            "confidence_lower": float(prophet.iloc[0]['expected_return_lower']),
            "confidence_upper": float(prophet.iloc[0]['expected_return_upper']),
            "mape": float(prophet.iloc[0]['mape']),
            "r2_score": float(prophet.iloc[0]['r2_score'])
        }

    # Get LSTM prediction
    lstm = lstm_df[lstm_df['scheme_code'] == scheme_code_value]
    if lstm.empty:
        lstm_data = None
    else:
        lstm_data = {
            "model": "LSTM",
            "predicted_return_6m": float(lstm.iloc[0]['expected_return_6m']),
            "predicted_nav_6m": float(lstm.iloc[0]['predicted_nav_6m']),
            "confidence_lower": float(lstm.iloc[0]['expected_return_lower']),
            "confidence_upper": float(lstm.iloc[0]['expected_return_upper']),
            "mape": float(lstm.iloc[0]['mape']),
            "r2_score": float(lstm.iloc[0]['r2_score'])
        }

    # Get Ensemble prediction
    ensemble = ensemble_df[ensemble_df['scheme_code'] == scheme_code_value]
    if ensemble.empty:
        raise HTTPException(status_code=404, detail=f"Predictions for fund {scheme_code} not found")

    ensemble_row = ensemble.iloc[0]

    ensemble_data = {
        "prophet": prophet_data,
        "lstm": lstm_data,
        "ensemble_simple": float(ensemble_row['ensemble_simple']),
        "ensemble_weighted": float(ensemble_row['ensemble_weighted']),
        "recommended_model": ensemble_row['recommended_model'],
        "recommended_return": float(ensemble_row['recommended_return']),
        "recommended_mape": float(ensemble_row['recommended_mape'])
    }

    return ensemble_data


@router.get("/{scheme_code}/historical")
def get_historical_nav(scheme_code: str):
    """Get historical NAV data for charting"""

    # Get project root
    current_file = os.path.abspath(__file__)
    api_folder = os.path.dirname(current_file)
    backend_folder = os.path.dirname(api_folder)
    PROJECT_ROOT = os.path.dirname(backend_folder)

    # Find the fund file
    fund_file = os.path.join(PROJECT_ROOT, "data", f"fund_{scheme_code}.csv")

    # ... rest stays the same

    if not os.path.exists(fund_file):
        raise HTTPException(status_code=404, detail=f"Historical data for fund {scheme_code} not found")

    try:
        df = pd.read_csv(fund_file)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        # Get last 2 years for charting
        cutoff_date = df['date'].max() - pd.DateOffset(years=2)
        df = df[df['date'] >= cutoff_date]

        historical = df[['date', 'nav']].to_dict('records')

        # Convert dates to strings
        for record in historical:
            record['date'] = record['date'].strftime('%Y-%m-%d')

        return {
            "scheme_code": scheme_code,
            "data": historical
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading historical data: {str(e)}")


@router.get("/stats/comparison")
def get_model_comparison_stats():
    """Get Prophet vs LSTM comparison statistics"""

    if prophet_df.empty or lstm_df.empty:
        raise HTTPException(status_code=500, detail="Prediction data not loaded")

    # Merge on scheme_code
    merged = prophet_df.merge(
        lstm_df,
        on='scheme_code',
        suffixes=('_prophet', '_lstm')
    )

    prophet_mape = merged['mape_prophet'].mean()
    lstm_mape = merged['mape_lstm'].mean()

    prophet_wins = (merged['mape_prophet'] < merged['mape_lstm']).sum()
    lstm_wins = (merged['mape_lstm'] < merged['mape_prophet']).sum()

    return {
        "prophet": {
            "avg_mape": float(prophet_mape),
            "avg_r2": float(merged['r2_score_prophet'].mean()),
            "wins": int(prophet_wins),
            "win_rate": float(prophet_wins / len(merged) * 100)
        },
        "lstm": {
            "avg_mape": float(lstm_mape),
            "avg_r2": float(merged['r2_score_lstm'].mean()),
            "wins": int(lstm_wins),
            "win_rate": float(lstm_wins / len(merged) * 100)
        },
        "total_funds": len(merged)
    }