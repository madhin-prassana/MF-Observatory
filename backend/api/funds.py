from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import pandas as pd
import os

router = APIRouter()

# Get project root (parent of backend/)
current_file = os.path.abspath(__file__)
api_folder = os.path.dirname(current_file)
backend_folder = os.path.dirname(api_folder)
PROJECT_ROOT = os.path.dirname(backend_folder)

# Data paths
DATA_DIR = os.path.join(PROJECT_ROOT, "results")
FUND_METRICS_PATH = os.path.join(PROJECT_ROOT, "data", "fund_metrics.csv")
CLUSTERED_FUNDS_PATH = os.path.join(DATA_DIR, "clustered_funds.csv")
ANOMALY_RESULTS_PATH = os.path.join(DATA_DIR, "anomaly_detection_results.csv")
ENSEMBLE_PREDICTIONS_PATH = os.path.join(DATA_DIR, "prediction_ensemble.csv")

# ... rest of file stays the same
print(f"Looking for files at:")
print(f"  FUND_METRICS_PATH: {FUND_METRICS_PATH}")
print(f"  Exists: {os.path.exists(FUND_METRICS_PATH)}")
print(f"  CLUSTERED_FUNDS_PATH: {CLUSTERED_FUNDS_PATH}")
print(f"  Exists: {os.path.exists(CLUSTERED_FUNDS_PATH)}")

# Load data once at startup
try:
    fund_metrics_df = pd.read_csv(FUND_METRICS_PATH)
    clustered_df = pd.read_csv(CLUSTERED_FUNDS_PATH)
    anomaly_df = pd.read_csv(ANOMALY_RESULTS_PATH)
    ensemble_df = pd.read_csv(ENSEMBLE_PREDICTIONS_PATH)

    # Rename the column for the frontend
    if 'performance_anomaly_score' in anomaly_df.columns:
        anomaly_df['anomaly_score'] = anomaly_df['performance_anomaly_score']

    # Merge all data
    master_df = fund_metrics_df.merge(
        clustered_df[['scheme_code', 'cluster', 'risk_category']],
        on='scheme_code',
        how='left'
    ).merge(
        anomaly_df[['scheme_code', 'anomaly_category', 'anomaly_score']],
        on='scheme_code',
        how='left'
    ).merge(
        ensemble_df[['scheme_code', 'prophet_return', 'lstm_return',
                     'ensemble_simple', 'ensemble_weighted', 'recommended_model', 'recommended_return']],
        on='scheme_code',
        how='left'
    )

    print(f"✓ Loaded {len(master_df)} funds successfully")

except Exception as e:
    print(f"✗ Error loading data: {e}")
    master_df = pd.DataFrame()


@router.get("/")
def get_all_funds(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        search: Optional[str] = None,
        risk_category: Optional[str] = None,
        anomaly_status: Optional[str] = None,
        min_return: Optional[float] = None,
        max_return: Optional[float] = None,
        sort_by: Optional[str] = "recommended_return",
        sort_order: Optional[str] = "desc"
):
    """
    Get all funds with optional filtering and sorting

    Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    - search: Search by fund name
    - risk_category: Filter by risk category
    - anomaly_status: Filter by anomaly status
    - min_return: Minimum predicted return
    - max_return: Maximum predicted return
    - sort_by: Field to sort by
    - sort_order: 'asc' or 'desc'
    """

    if master_df.empty:
        raise HTTPException(status_code=500, detail="Data not loaded")

    df = master_df.copy()

    # Apply filters
    if search:
        df = df[df['scheme_name'].str.contains(search, case=False, na=False)]

    if risk_category:
        df = df[df['risk_category'] == risk_category]

    if anomaly_status:
        if anomaly_status.lower() == 'normal':
            df = df[df['anomaly_category'] == 'Normal']
        else:
            df = df[df['anomaly_category'] != 'Normal']

    if min_return is not None:
        df = df[df['recommended_return'] >= min_return]

    if max_return is not None:
        df = df[df['recommended_return'] <= max_return]

    # Sort
    if sort_by in df.columns:
        ascending = (sort_order.lower() == 'asc')
        df = df.sort_values(by=sort_by, ascending=ascending)

    # Pagination
    total = len(df)
    df = df.iloc[skip:skip + limit]

    # Convert to dict
    funds = df.to_dict('records')

    # Clean NaN values
    for fund in funds:
        for key, value in fund.items():
            if pd.isna(value):
                fund[key] = None

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "funds": funds
    }


@router.get("/{scheme_code}")
def get_fund_by_code(scheme_code: str):
    """Get detailed information for a specific fund"""

    if master_df.empty:
        raise HTTPException(status_code=500, detail="Data not loaded")

    # Convert to int if it's a digit string
    if scheme_code.isdigit():
        scheme_code_value = int(scheme_code)
    else:
        scheme_code_value = scheme_code

    fund = master_df[master_df['scheme_code'] == scheme_code_value]

    if fund.empty:
        raise HTTPException(status_code=404, detail=f"Fund {scheme_code} not found")

    fund_dict = fund.iloc[0].to_dict()

    # Clean NaN values
    for key, value in fund_dict.items():
        if pd.isna(value):
            fund_dict[key] = None

    return fund_dict


@router.get("/search/suggest")
def search_suggestions(q: str = Query(..., min_length=2)):
    """Get search suggestions based on query"""

    if master_df.empty:
        raise HTTPException(status_code=500, detail="Data not loaded")

    suggestions = master_df[
        master_df['scheme_name'].str.contains(q, case=False, na=False)
    ]['scheme_name'].head(10).tolist()

    return {"suggestions": suggestions}


@router.post("/compare")
def compare_funds(scheme_codes: List[str]):
    """Compare multiple funds side by side"""

    if master_df.empty:
        raise HTTPException(status_code=500, detail="Data not loaded")

    if len(scheme_codes) < 2:
        raise HTTPException(status_code=400, detail="At least 2 funds required for comparison")

    if len(scheme_codes) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 funds can be compared")

    funds = master_df[master_df['scheme_code'].isin(scheme_codes)]

    if len(funds) != len(scheme_codes):
        raise HTTPException(status_code=404, detail="One or more funds not found")

    comparison = funds.to_dict('records')

    # Clean NaN values
    for fund in comparison:
        for key, value in fund.items():
            if pd.isna(value):
                fund[key] = None

    return {"funds": comparison}


@router.get("/stats/summary")
def get_summary_stats():
    """Get overall statistics"""

    if master_df.empty:
        raise HTTPException(status_code=500, detail="Data not loaded")

    # Calculate anomaly rate
    flagged_count = len(master_df[master_df['anomaly_category'] != 'Normal'])
    anomaly_rate = (flagged_count / len(master_df)) * 100 if len(master_df) > 0 else 0

    # Get top 5 performers
    top_5 = master_df.sort_values(by='recommended_return', ascending=False).head(5)
    top_performers = []
    for _, row in top_5.iterrows():
        top_performers.append({
            "scheme_code": int(row['scheme_code']),
            "name": row['scheme_name'],
            "return": float(row['recommended_return']),
            "risk": row['risk_category']
        })

    # Get last sync date from file modification time
    try:
        mtime = os.path.getmtime(FUND_METRICS_PATH)
        import datetime
        last_sync = datetime.datetime.fromtimestamp(mtime).strftime('%d %B %Y')
    except:
        last_sync = "07 April 2026"

    return {
        "total_funds": len(master_df),
        "avg_predicted_return": float(master_df['recommended_return'].mean()),
        "total_forecasts": len(master_df) * 180,
        "anomaly_rate": float(anomaly_rate),
        "last_sync": last_sync,
        "risk_distribution": master_df['risk_category'].value_counts().to_dict(),
        "top_performers": top_performers
    }