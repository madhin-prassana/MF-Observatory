import pandas as pd
import numpy as np
import os
from glob import glob


def calculate_returns(nav_series):
    """
    Calculate returns for different time periods
    nav_series: pandas Series of NAV values (sorted newest to oldest)
    """
    returns = {}

    # Get latest NAV
    latest_nav = nav_series.iloc[0]

    # 1-month return (30 days ago)
    if len(nav_series) >= 30:
        old_nav = nav_series.iloc[29]  # 30 days ago (0-indexed)
        returns['return_1m'] = ((latest_nav - old_nav) / old_nav) * 100
    else:
        returns['return_1m'] = None

    # 3-month return (90 days ago)
    if len(nav_series) >= 90:
        old_nav = nav_series.iloc[89]
        returns['return_3m'] = ((latest_nav - old_nav) / old_nav) * 100
    else:
        returns['return_3m'] = None

    # 6-month return (180 days ago)
    if len(nav_series) >= 180:
        old_nav = nav_series.iloc[179]
        returns['return_6m'] = ((latest_nav - old_nav) / old_nav) * 100
    else:
        returns['return_6m'] = None

    # 1-year return (365 days ago)
    if len(nav_series) >= 365:
        old_nav = nav_series.iloc[364]
        returns['return_1y'] = ((latest_nav - old_nav) / old_nav) * 100
    else:
        returns['return_1y'] = None

    # 2-year return (730 days ago)
    if len(nav_series) >= 730:
        old_nav = nav_series.iloc[729]
        returns['return_2y'] = ((latest_nav - old_nav) / old_nav) * 100
    else:
        returns['return_2y'] = None

    return returns


def calculate_volatility(nav_series):
    """
    Calculate volatility (standard deviation of returns)
    Higher volatility = more risky
    """
    if len(nav_series) < 30:
        return None

    # Calculate daily returns (percentage change)
    daily_returns = nav_series.pct_change().dropna()

    # Calculate standard deviation
    daily_std = daily_returns.std()

    # Annualize it (multiply by sqrt of 252 trading days)
    annual_volatility = daily_std * np.sqrt(252) * 100

    return annual_volatility


def calculate_max_drawdown(nav_series):
    """
    Calculate maximum drawdown (worst loss from peak)
    Shows: "What's the worst loss you could have experienced?"
    """
    if len(nav_series) < 30:
        return None

    # Calculate cumulative maximum (highest point so far)
    cumulative_max = nav_series.expanding(min_periods=1).max()

    # Calculate drawdown at each point
    drawdown = ((nav_series - cumulative_max) / cumulative_max) * 100

    # Get the worst (most negative) drawdown
    max_drawdown = drawdown.min()

    return max_drawdown


def calculate_sharpe_ratio(nav_series, risk_free_rate=6.0):
    """
    Calculate Sharpe Ratio (return per unit of risk)
    Higher is better
    risk_free_rate: assumed safe return (like FD rate, default 6%)
    """
    if len(nav_series) < 365:
        return None

    # Calculate daily returns
    daily_returns = nav_series.pct_change().dropna()

    # Calculate average annual return
    avg_daily_return = daily_returns.mean()
    annual_return = (1 + avg_daily_return) ** 252 - 1
    annual_return_pct = annual_return * 100

    # Calculate volatility
    volatility = calculate_volatility(nav_series)

    if volatility is None or volatility == 0:
        return None

    # Sharpe Ratio = (Return - Risk Free Rate) / Volatility
    sharpe = (annual_return_pct - risk_free_rate) / volatility

    return sharpe


def process_single_fund(file_path):
    """
    Process one fund file and calculate all metrics
    """
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)

        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])

        # Sort by date (newest first)
        df = df.sort_values('date', ascending=False)

        # Get scheme code and name
        scheme_code = df['scheme_code'].iloc[0]
        scheme_name = df['scheme_name'].iloc[0]

        # Get NAV series
        nav_series = df['nav'].reset_index(drop=True)

        # Calculate all metrics
        returns = calculate_returns(nav_series)
        volatility = calculate_volatility(nav_series)
        max_dd = calculate_max_drawdown(nav_series)
        sharpe = calculate_sharpe_ratio(nav_series)

        # Get latest NAV and date
        latest_nav = nav_series.iloc[0]
        latest_date = df['date'].iloc[0]

        # Get oldest date
        oldest_date = df['date'].iloc[-1]

        # Combine everything
        metrics = {
            'scheme_code': scheme_code,
            'scheme_name': scheme_name,
            'latest_nav': latest_nav,
            'latest_date': latest_date,
            'oldest_date': oldest_date,
            'data_points': len(df),
            'volatility': volatility,
            'max_drawdown': max_dd,
            'sharpe_ratio': sharpe,
            **returns  # Adds all the return metrics
        }

        return metrics

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


def main():
    print("=" * 70)
    print("CALCULATING METRICS FOR ALL FUNDS")
    print("=" * 70)

    # Get all fund files
    data_folder = '../data'
    fund_files = glob(os.path.join(data_folder, 'fund_*.csv'))

    print(f"\nFound {len(fund_files)} fund files")
    print("\nProcessing...\n")

    # Process each fund
    all_metrics = []

    for i, file_path in enumerate(fund_files, 1):
        file_name = os.path.basename(file_path)
        print(f"[{i}/{len(fund_files)}] Processing {file_name}...")

        metrics = process_single_fund(file_path)

        if metrics is not None:
            all_metrics.append(metrics)
            print(f"  ✓ Done! Volatility: {metrics['volatility']:.2f}%, 1Y Return: {metrics['return_1y']:.2f}%")
        else:
            print(f"  ✗ Failed")

    # Create DataFrame
    metrics_df = pd.DataFrame(all_metrics)

    # Remove any rows with missing critical data
    metrics_df = metrics_df.dropna(subset=['volatility', 'return_1y', 'max_drawdown'])

    # Sort by volatility
    metrics_df = metrics_df.sort_values('volatility')

    # Save to CSV
    output_file = '../data/fund_metrics.csv'
    metrics_df.to_csv(output_file, index=False)

    print("\n" + "=" * 70)
    print(f"✓ DONE! Calculated metrics for {len(metrics_df)} funds")
    print(f"✓ Saved to: {output_file}")
    print("=" * 70)

    # Show summary statistics
    print("\nSUMMARY STATISTICS:")
    print("-" * 70)
    print(f"Average Volatility:    {metrics_df['volatility'].mean():.2f}%")
    print(f"Average 1Y Return:     {metrics_df['return_1y'].mean():.2f}%")
    print(f"Average Max Drawdown:  {metrics_df['max_drawdown'].mean():.2f}%")
    print(f"Average Sharpe Ratio:  {metrics_df['sharpe_ratio'].mean():.2f}")
    print("-" * 70)

    # Show top 5 and bottom 5 by returns
    print("\nTOP 5 PERFORMERS (1-Year Return):")
    top5 = metrics_df.nlargest(5, 'return_1y')[['scheme_name', 'return_1y', 'volatility']]
    for idx, row in top5.iterrows():
        print(f"  • {row['scheme_name'][:50]}")
        print(f"    Return: {row['return_1y']:.2f}%, Volatility: {row['volatility']:.2f}%")

    print("\nBOTTOM 5 PERFORMERS (1-Year Return):")
    bottom5 = metrics_df.nsmallest(5, 'return_1y')[['scheme_name', 'return_1y', 'volatility']]
    for idx, row in bottom5.iterrows():
        print(f"  • {row['scheme_name'][:50]}")
        print(f"    Return: {row['return_1y']:.2f}%, Volatility: {row['volatility']:.2f}%")

    print("\nLOWEST RISK FUNDS (Volatility):")
    low_risk = metrics_df.nsmallest(5, 'volatility')[['scheme_name', 'volatility', 'return_1y']]
    for idx, row in low_risk.iterrows():
        print(f"  • {row['scheme_name'][:50]}")
        print(f"    Volatility: {row['volatility']:.2f}%, Return: {row['return_1y']:.2f}%")

    print("\nHIGHEST RISK FUNDS (Volatility):")
    high_risk = metrics_df.nlargest(5, 'volatility')[['scheme_name', 'volatility', 'return_1y']]
    for idx, row in high_risk.iterrows():
        print(f"  • {row['scheme_name'][:50]}")
        print(f"    Volatility: {row['volatility']:.2f}%, Return: {row['return_1y']:.2f}%")


if __name__ == "__main__":
    main()