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
CLUSTERED_PATH = os.path.join(PROJECT_ROOT, "results", "clustered_funds.csv")

# ... rest of file stays the same

# Load clustering data
try:
    clustered_df = pd.read_csv(CLUSTERED_PATH)
    print(f"✓ Loaded clustering data successfully")
except Exception as e:
    print(f"✗ Error loading clustering data: {e}")
    clustered_df = pd.DataFrame()


@router.get("/")
def get_all_clusters():
    """Get all cluster information"""

    if clustered_df.empty:
        raise HTTPException(status_code=500, detail="Clustering data not loaded")

    # Cluster statistics
    cluster_stats = []

    for cluster in sorted(clustered_df['cluster'].unique()):
        cluster_data = clustered_df[clustered_df['cluster'] == cluster]

        stats = {
            "cluster_id": int(cluster),
            "risk_category": cluster_data['risk_category'].iloc[0],
            "fund_count": len(cluster_data),
            "avg_volatility": float(cluster_data['volatility'].mean()),
            "avg_return": float(cluster_data['return_1y'].mean()),
            "avg_max_drawdown": float(cluster_data['max_drawdown'].mean()),
            "avg_sharpe": float(cluster_data['sharpe_ratio'].mean())
        }

        cluster_stats.append(stats)

    return {
        "total_clusters": len(cluster_stats),
        "clusters": cluster_stats
    }


@router.get("/{cluster_id}")
def get_cluster_funds(cluster_id: int):
    """Get all funds in a specific cluster"""

    if clustered_df.empty:
        raise HTTPException(status_code=500, detail="Clustering data not loaded")

    cluster_funds = clustered_df[clustered_df['cluster'] == cluster_id]

    if cluster_funds.empty:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")

    funds = cluster_funds.to_dict('records')

    # Clean NaN values
    for fund in funds:
        for key, value in fund.items():
            if pd.isna(value):
                fund[key] = None

    return {
        "cluster_id": cluster_id,
        "risk_category": cluster_funds['risk_category'].iloc[0],
        "fund_count": len(cluster_funds),
        "funds": funds
    }


@router.get("/visualization/data")
def get_cluster_visualization_data():
    """Get data for cluster visualization (scatter plot)"""

    if clustered_df.empty:
        raise HTTPException(status_code=500, detail="Clustering data not loaded")

    viz_data = clustered_df[['scheme_code', 'scheme_name', 'cluster', 'risk_category',
                             'volatility', 'return_1y', 'max_drawdown']].to_dict('records')

    return {"data": viz_data}