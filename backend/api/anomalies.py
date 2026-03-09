from fastapi import APIRouter, HTTPException
import pandas as pd
import os

router = APIRouter()

# Get project root
current_file = os.path.abspath(__file__)
api_folder = os.path.dirname(current_file)
backend_folder = os.path.dirname(api_folder)
PROJECT_ROOT = os.path.dirname(backend_folder)

# Data path
ANOMALY_PATH = os.path.join(PROJECT_ROOT, "results", "anomaly_detection_results.csv")

# ... rest of file stays the same

# Load anomaly data
try:
    anomaly_df = pd.read_csv(ANOMALY_PATH)
    print(f"✓ Loaded anomaly data successfully")
except Exception as e:
    print(f"✗ Error loading anomaly data: {e}")
    anomaly_df = pd.DataFrame()


@router.get("/")
def get_all_anomalies():
    """Get all anomaly detection results"""

    if anomaly_df.empty:
        raise HTTPException(status_code=500, detail="Anomaly data not loaded")

    # Anomaly statistics
    anomaly_counts = anomaly_df['anomaly_category'].value_counts().to_dict()

    # Get flagged funds (not normal)
    flagged = anomaly_df[anomaly_df['anomaly_category'] != 'Normal'].to_dict('records')

    # Clean NaN values
    for fund in flagged:
        for key, value in fund.items():
            if pd.isna(value):
                fund[key] = None

    return {
        "total_funds": len(anomaly_df),
        "anomaly_distribution": anomaly_counts,
        "flagged_count": len(flagged),
        "flagged_funds": flagged
    }


@router.get("/{scheme_code}")
def get_fund_anomaly_status(scheme_code: str):
    """Get anomaly status for a specific fund"""

    if anomaly_df.empty:
        raise HTTPException(status_code=500, detail="Anomaly data not loaded")

    # Convert to int if digit string
    scheme_code_value = int(scheme_code) if scheme_code.isdigit() else scheme_code

    fund = anomaly_df[anomaly_df['scheme_code'] == scheme_code_value]

    if fund.empty:
        raise HTTPException(status_code=404, detail=f"Anomaly data for fund {scheme_code} not found")

    fund_dict = fund.iloc[0].to_dict()

    # Clean NaN values
    for key, value in fund_dict.items():
        if pd.isna(value):
            fund_dict[key] = None

    return fund_dict

@router.get("/category/{category}")
def get_funds_by_anomaly_category(category: str):
    """Get all funds with specific anomaly category"""

    if anomaly_df.empty:
        raise HTTPException(status_code=500, detail="Anomaly data not loaded")

    valid_categories = ['Normal', 'Performance Issue', 'Risk Issue', 'High Priority']

    if category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
        )

    funds = anomaly_df[anomaly_df['anomaly_category'] == category].to_dict('records')

    # Clean NaN values
    for fund in funds:
        for key, value in fund.items():
            if pd.isna(value):
                fund[key] = None

    return {
        "category": category,
        "count": len(funds),
        "funds": funds
    }