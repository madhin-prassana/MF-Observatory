import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
import os
 
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_data():
    """Load the fund metrics data"""
    print("=" * 70)
    print("LOADING DATA FOR ANOMALY DETECTION")
    print("=" * 70)

    df = pd.read_csv(os.path.join(base_dir, 'data', 'fund_metrics.csv'))

    # Remove any rows with missing values
    df = df.dropna(subset=['volatility', 'return_1y', 'max_drawdown', 'return_3m', 'return_6m'])

    print(f"✓ Loaded {len(df)} funds with complete data")

    return df


def detect_performance_anomalies(df):
    """
    Detect funds with unusual performance patterns
    """
    print("\n" + "=" * 70)
    print("DETECTING PERFORMANCE ANOMALIES")
    print("=" * 70)

    # Features for performance anomaly detection
    features = ['return_1y', 'return_6m', 'return_3m', 'volatility']
    X = df[features].copy()

    print(f"\nFeatures used:")
    for i, feature in enumerate(features, 1):
        print(f"  {i}. {feature}")

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Apply Isolation Forest
    # contamination=0.15 means we expect ~15% of data to be anomalies
    iso_forest = IsolationForest(contamination=0.15, random_state=42, n_estimators=100)

    # Predict: -1 for anomalies, 1 for normal
    df['performance_anomaly'] = iso_forest.fit_predict(X_scaled)

    # Get anomaly scores (more negative = more anomalous)
    df['performance_anomaly_score'] = iso_forest.score_samples(X_scaled)

    # Count anomalies
    anomalies = df[df['performance_anomaly'] == -1]
    normal = df[df['performance_anomaly'] == 1]

    print(f"\n✓ Analysis complete:")
    print(f"   Normal funds: {len(normal)} ({len(normal) / len(df) * 100:.1f}%)")
    print(f"   Anomalous funds: {len(anomalies)} ({len(anomalies) / len(df) * 100:.1f}%)")

    return df


def detect_risk_anomalies(df):
    """
    Detect funds with unusual risk characteristics
    """
    print("\n" + "=" * 70)
    print("DETECTING RISK ANOMALIES")
    print("=" * 70)

    # Features for risk anomaly detection
    features = ['volatility', 'max_drawdown', 'sharpe_ratio']
    X = df[features].copy()

    print(f"\nFeatures used:")
    for i, feature in enumerate(features, 1):
        print(f"  {i}. {feature}")

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Apply Isolation Forest
    iso_forest = IsolationForest(contamination=0.15, random_state=42, n_estimators=100)

    df['risk_anomaly'] = iso_forest.fit_predict(X_scaled)
    df['risk_anomaly_score'] = iso_forest.score_samples(X_scaled)

    # Count anomalies
    anomalies = df[df['risk_anomaly'] == -1]
    normal = df[df['risk_anomaly'] == 1]

    print(f"\n✓ Analysis complete:")
    print(f"   Normal funds: {len(normal)} ({len(normal) / len(df) * 100:.1f}%)")
    print(f"   Anomalous funds: {len(anomalies)} ({len(anomalies) / len(df) * 100:.1f}%)")

    return df


def detect_combined_anomalies(df):
    """
    Detect funds that are anomalous in both performance AND risk
    """
    print("\n" + "=" * 70)
    print("IDENTIFYING HIGH-PRIORITY ANOMALIES")
    print("=" * 70)

    # Funds that are anomalous in BOTH categories = HIGH RISK
    df['is_high_priority_anomaly'] = (
            (df['performance_anomaly'] == -1) &
            (df['risk_anomaly'] == -1)
    )

    # Categorize anomaly severity
    def categorize_anomaly(row):
        if row['is_high_priority_anomaly']:
            return 'High Priority'
        elif row['performance_anomaly'] == -1:
            return 'Performance Issue'
        elif row['risk_anomaly'] == -1:
            return 'Risk Issue'
        else:
            return 'Normal'

    df['anomaly_category'] = df.apply(categorize_anomaly, axis=1)

    # Count by category
    category_counts = df['anomaly_category'].value_counts()

    print(f"\nAnomaly Breakdown:")
    for category, count in category_counts.items():
        print(f"   {category:20s}: {count:2d} funds ({count / len(df) * 100:.1f}%)")

    return df


def analyze_anomalies(df):
    """
    Detailed analysis of detected anomalies
    """
    print("\n" + "=" * 70)
    print("DETAILED ANOMALY ANALYSIS")
    print("=" * 70)

    # Get all anomalous funds
    anomalies = df[df['anomaly_category'] != 'Normal'].copy()

    if len(anomalies) == 0:
        print("\n✓ No significant anomalies detected!")
        return

    # Sort by severity (combined score)
    anomalies['combined_score'] = (
            anomalies['performance_anomaly_score'] +
            anomalies['risk_anomaly_score']
    )
    anomalies = anomalies.sort_values('combined_score')

    print(f"\n10 MOST ANOMALOUS FUNDS:\n")
    print("─" * 70)

    top_anomalies = anomalies.head(10)

    for idx, (i, row) in enumerate(top_anomalies.iterrows(), 1):
        print(f"\n{idx}. {row['scheme_name'][:60]}")
        print(f"   Category: {row['anomaly_category']}")
        print(f"   1Y Return: {row['return_1y']:.2f}% | Volatility: {row['volatility']:.2f}%")
        print(f"   Max Drawdown: {row['max_drawdown']:.2f}% | Sharpe: {row['sharpe_ratio']:.2f}")

        # Explain why it's anomalous
        reasons = []

        # Performance anomaly reasons
        if row['performance_anomaly'] == -1:
            if row['return_1y'] < df['return_1y'].quantile(0.25):
                reasons.append("Returns significantly below average")
            if row['return_3m'] < df['return_3m'].quantile(0.25):
                reasons.append("Recent performance declining")

        # Risk anomaly reasons
        if row['risk_anomaly'] == -1:
            if row['volatility'] > df['volatility'].quantile(0.75):
                reasons.append("Unusually high volatility")
            if row['max_drawdown'] < df['max_drawdown'].quantile(0.25):
                reasons.append("Severe drawdown experienced")
            if row['sharpe_ratio'] < df['sharpe_ratio'].quantile(0.25):
                reasons.append("Poor risk-adjusted returns")

        if reasons:
            print(f"   Reasons:")
            for reason in reasons:
                print(f"     {reason}")

    # High priority analysis
    high_priority = df[df['is_high_priority_anomaly'] == True]

    if len(high_priority) > 0:
        print(f"\n" + "=" * 70)
        print(f"HIGH PRIORITY ALERTS ({len(high_priority)} funds)")
        print("=" * 70)
        print("\nThese funds show unusual patterns in BOTH performance AND risk.")
        print("Recommend detailed investigation before investing.\n")

        for idx, row in high_priority.iterrows():
            print(f"{row['scheme_name'][:65]}")
            print(
                f"    Return: {row['return_1y']:.2f}% | Volatility: {row['volatility']:.2f}% | Drawdown: {row['max_drawdown']:.2f}%")


def create_visualizations(df):
    """
    Create comprehensive anomaly visualizations
    """
    print("\n" + "=" * 70)
    print("CREATING ANOMALY VISUALIZATIONS")
    print("=" * 70)

    # Set style
    sns.set_style("whitegrid")

    # Color mapping
    color_map = {
        'Normal': '#2ecc71',
        'Performance Issue': '#f39c12',
        'Risk Issue': '#e67e22',
        'High Priority': '#e74c3c'
    }

    # Create main figure with subplots
    fig = plt.figure(figsize=(18, 12))

    # Plot 1: Performance Anomalies - Volatility vs Returns
    ax1 = plt.subplot(2, 3, 1)

    for category in df['anomaly_category'].unique():
        subset = df[df['anomaly_category'] == category]
        marker = 'X' if category != 'Normal' else 'o'
        size = 150 if category != 'Normal' else 80
        alpha = 0.8 if category != 'Normal' else 0.5

        ax1.scatter(subset['volatility'], subset['return_1y'],
                    c=color_map[category], label=category,
                    marker=marker, s=size, alpha=alpha,
                    edgecolors='black', linewidth=1)

    ax1.set_xlabel('Volatility (%)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('1-Year Return (%)', fontsize=11, fontweight='bold')
    ax1.set_title('Performance Anomalies: Volatility vs Returns', fontsize=13, fontweight='bold')
    ax1.legend(loc='best', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='red', linestyle='--', linewidth=0.8, alpha=0.5)

    # Plot 2: Risk Anomalies - Max Drawdown vs Volatility
    ax2 = plt.subplot(2, 3, 2)

    for category in df['anomaly_category'].unique():
        subset = df[df['anomaly_category'] == category]
        marker = 'X' if category != 'Normal' else 'o'
        size = 150 if category != 'Normal' else 80
        alpha = 0.8 if category != 'Normal' else 0.5

        ax2.scatter(subset['volatility'], subset['max_drawdown'],
                    c=color_map[category],
                    marker=marker, s=size, alpha=alpha,
                    edgecolors='black', linewidth=1)

    ax2.set_xlabel('Volatility (%)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Max Drawdown (%)', fontsize=11, fontweight='bold')
    ax2.set_title('Risk Anomalies: Drawdown vs Volatility', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # Plot 3: Anomaly Distribution
    ax3 = plt.subplot(2, 3, 3)

    category_counts = df['anomaly_category'].value_counts()
    colors_list = [color_map[cat] for cat in category_counts.index]

    bars = ax3.bar(range(len(category_counts)), category_counts.values,
                   color=colors_list, edgecolor='black', linewidth=1)

    ax3.set_xlabel('Anomaly Category', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Number of Funds', fontsize=11, fontweight='bold')
    ax3.set_title('Anomaly Distribution', fontsize=13, fontweight='bold')
    ax3.set_xticks(range(len(category_counts)))
    ax3.set_xticklabels(category_counts.index, rotation=45, ha='right', fontsize=9)
    ax3.grid(True, alpha=0.3, axis='y')

    # Add count labels
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width() / 2., height,
                 f'{int(height)}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Plot 4: Anomaly Scores Distribution (Performance)
    ax4 = plt.subplot(2, 3, 4)

    normal_scores = df[df['performance_anomaly'] == 1]['performance_anomaly_score']
    anomaly_scores = df[df['performance_anomaly'] == -1]['performance_anomaly_score']

    ax4.hist(normal_scores, bins=20, alpha=0.6, color='#2ecc71',
             label=f'Normal ({len(normal_scores)})', edgecolor='black')
    ax4.hist(anomaly_scores, bins=20, alpha=0.6, color='#e74c3c',
             label=f'Anomalies ({len(anomaly_scores)})', edgecolor='black')

    ax4.set_xlabel('Performance Anomaly Score', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Frequency', fontsize=11, fontweight='bold')
    ax4.set_title('Performance Anomaly Score Distribution', fontsize=13, fontweight='bold')
    ax4.legend(loc='best', fontsize=9)
    ax4.grid(True, alpha=0.3, axis='y')

    # Plot 5: Anomaly Scores Distribution (Risk)
    ax5 = plt.subplot(2, 3, 5)

    normal_risk = df[df['risk_anomaly'] == 1]['risk_anomaly_score']
    anomaly_risk = df[df['risk_anomaly'] == -1]['risk_anomaly_score']

    ax5.hist(normal_risk, bins=20, alpha=0.6, color='#2ecc71',
             label=f'Normal ({len(normal_risk)})', edgecolor='black')
    ax5.hist(anomaly_risk, bins=20, alpha=0.6, color='#e74c3c',
             label=f'Anomalies ({len(anomaly_risk)})', edgecolor='black')

    ax5.set_xlabel('Risk Anomaly Score', fontsize=11, fontweight='bold')
    ax5.set_ylabel('Frequency', fontsize=11, fontweight='bold')
    ax5.set_title('Risk Anomaly Score Distribution', fontsize=13, fontweight='bold')
    ax5.legend(loc='best', fontsize=9)
    ax5.grid(True, alpha=0.3, axis='y')

    # Plot 6: Sharpe Ratio vs Volatility (highlight anomalies)
    ax6 = plt.subplot(2, 3, 6)

    for category in df['anomaly_category'].unique():
        subset = df[df['anomaly_category'] == category]
        marker = 'X' if category != 'Normal' else 'o'
        size = 150 if category != 'Normal' else 80
        alpha = 0.8 if category != 'Normal' else 0.5

        ax6.scatter(subset['volatility'], subset['sharpe_ratio'],
                    c=color_map[category],
                    marker=marker, s=size, alpha=alpha,
                    edgecolors='black', linewidth=1)

    ax6.set_xlabel('Volatility (%)', fontsize=11, fontweight='bold')
    ax6.set_ylabel('Sharpe Ratio', fontsize=11, fontweight='bold')
    ax6.set_title('Risk-Adjusted Performance', fontsize=13, fontweight='bold')
    ax6.grid(True, alpha=0.3)
    ax6.axhline(y=0, color='red', linestyle='--', linewidth=0.8, alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(base_dir, 'results', 'anomaly_detection_detailed.png'), dpi=300, bbox_inches='tight')
    print("✓ Saved detailed visualization: results/anomaly_detection_detailed.png")
    plt.close()

    # Create simple visualization for presentation
    fig2, ax = plt.subplots(figsize=(12, 8))

    # Plot normal funds first (so anomalies appear on top)
    normal = df[df['anomaly_category'] == 'Normal']
    ax.scatter(normal['volatility'], normal['return_1y'],
               c='#2ecc71', label=f'Normal Funds ({len(normal)})',
               s=100, alpha=0.5, edgecolors='black', linewidth=0.5)

    # Plot anomalies
    for category in ['Performance Issue', 'Risk Issue', 'High Priority']:
        if category in df['anomaly_category'].values:
            subset = df[df['anomaly_category'] == category]
            ax.scatter(subset['volatility'], subset['return_1y'],
                       c=color_map[category], label=f'{category} ({len(subset)})',
                       marker='X', s=200, alpha=0.9, edgecolors='black', linewidth=1.5)

    ax.set_xlabel('Volatility (Risk) %', fontsize=14, fontweight='bold')
    ax.set_ylabel('1-Year Return %', fontsize=14, fontweight='bold')
    ax.set_title('Mutual Fund Anomaly Detection', fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='best', fontsize=11, framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='red', linestyle='--', linewidth=1, alpha=0.5)

    plt.tight_layout()
    plt.savefig(os.path.join(base_dir, 'results', 'anomaly_detection_simple.png'), dpi=300, bbox_inches='tight')
    print("✓ Saved presentation chart: results/anomaly_detection_simple.png")
    plt.close()


def save_results(df):
    """
    Save anomaly detection results
    """
    print("\n" + "=" * 70)
    print("SAVING ANOMALY DETECTION RESULTS")
    print("=" * 70)

    # Save full results
    output_file = os.path.join(base_dir, 'results', 'anomaly_detection_results.csv')
    df_output = df[['scheme_code', 'scheme_name', 'anomaly_category',
                    'performance_anomaly_score', 'risk_anomaly_score',
                    'volatility', 'return_1y', 'max_drawdown', 'sharpe_ratio',
                    'latest_nav', 'latest_date']].copy()

    # Sort: anomalies first, then by combined severity
    df_output['combined_score'] = (
            df_output['performance_anomaly_score'] + df_output['risk_anomaly_score']
    )
    df_output = df_output.sort_values(['anomaly_category', 'combined_score'])
    df_output = df_output.drop('combined_score', axis=1)

    df_output.to_csv(output_file, index=False)
    print(f"✓ Saved detailed results: {output_file}")

    # Create anomaly summary
    summary = df.groupby('anomaly_category').agg({
        'scheme_name': 'count',
        'volatility': 'mean',
        'return_1y': 'mean',
        'max_drawdown': 'mean',
        'sharpe_ratio': 'mean',
        'performance_anomaly_score': 'mean',
        'risk_anomaly_score': 'mean'
    }).round(2)

    summary.columns = ['Count', 'Avg_Volatility', 'Avg_Return',
                       'Avg_Drawdown', 'Avg_Sharpe',
                       'Avg_Perf_Score', 'Avg_Risk_Score']

    summary_file = os.path.join(base_dir, 'results', 'anomaly_summary.csv')
    summary.to_csv(summary_file)
    print(f"✓ Saved anomaly summary: {summary_file}")

    # Create text report
    report_file = os.path.join(base_dir, 'results', 'anomaly_report.txt')
    with open(report_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("MUTUAL FUND ANOMALY DETECTION REPORT\n")
        f.write("=" * 70 + "\n\n")

        f.write(f"Total Funds Analyzed: {len(df)}\n")
        f.write(f"Detection Method: Isolation Forest Algorithm\n")
        f.write(f"Features Used: Returns, Volatility, Drawdown, Sharpe Ratio\n\n")

        # Summary by category
        f.write("=" * 70 + "\n")
        f.write("ANOMALY BREAKDOWN\n")
        f.write("=" * 70 + "\n\n")

        for category in ['Normal', 'Performance Issue', 'Risk Issue', 'High Priority']:
            if category in df['anomaly_category'].values:
                count = len(df[df['anomaly_category'] == category])
                pct = count / len(df) * 100
                f.write(f"{category:20s}: {count:2d} funds ({pct:.1f}%)\n")

        # Top anomalies
        f.write("\n" + "=" * 70 + "\n")
        f.write("TOP 10 MOST ANOMALOUS FUNDS\n")
        f.write("=" * 70 + "\n\n")

        anomalies = df[df['anomaly_category'] != 'Normal'].copy()
        if len(anomalies) > 0:
            anomalies['combined_score'] = (
                    anomalies['performance_anomaly_score'] +
                    anomalies['risk_anomaly_score']
            )
            top_10 = anomalies.nsmallest(10, 'combined_score')

            for idx, row in top_10.iterrows():
                f.write(f"\n{row['scheme_name']}\n")
                f.write(f"  Category: {row['anomaly_category']}\n")
                f.write(f"  1Y Return: {row['return_1y']:.2f}%\n")
                f.write(f"  Volatility: {row['volatility']:.2f}%\n")
                f.write(f"  Max Drawdown: {row['max_drawdown']:.2f}%\n")
                f.write(f"  Sharpe Ratio: {row['sharpe_ratio']:.2f}\n")
                f.write(f"  Performance Score: {row['performance_anomaly_score']:.3f}\n")
                f.write(f"  Risk Score: {row['risk_anomaly_score']:.3f}\n")

        # High priority alerts
        high_priority = df[df['anomaly_category'] == 'High Priority']
        if len(high_priority) > 0:
            f.write("\n" + "=" * 70 + "\n")
            f.write("HIGH PRIORITY ALERTS\n")
            f.write("=" * 70 + "\n\n")
            f.write("These funds show unusual patterns in BOTH performance AND risk.\n")
            f.write("Detailed investigation recommended before investing.\n\n")

            for idx, row in high_priority.iterrows():
                f.write(f"{row['scheme_name']}\n")
                f.write(f"   Return: {row['return_1y']:.2f}% | ")
                f.write(f"Volatility: {row['volatility']:.2f}% | ")
                f.write(f"Drawdown: {row['max_drawdown']:.2f}%\n\n")

    print(f"✓ Saved text report: {report_file}")


def main():
    """
    Main execution function
    """
    # Create results folder
    os.makedirs(os.path.join(base_dir, 'results'), exist_ok=True)

    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 14 + "MUTUAL FUND ANOMALY DETECTION" + " " * 25 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # Step 1: Load data
    df = load_data()

    # Step 2: Detect performance anomalies
    df = detect_performance_anomalies(df)

    # Step 3: Detect risk anomalies
    df = detect_risk_anomalies(df)

    # Step 4: Identify combined anomalies
    df = detect_combined_anomalies(df)

    # Step 5: Analyze anomalies
    analyze_anomalies(df)

    # Step 6: Create visualizations
    create_visualizations(df)

    # Step 7: Save results
    save_results(df)

    # Final summary
    print("\n" + "=" * 70)
    print("✓ ANOMALY DETECTION COMPLETE!")
    print("=" * 70)

    anomaly_count = len(df[df['anomaly_category'] != 'Normal'])
    high_priority = len(df[df['anomaly_category'] == 'High Priority'])

    print(f"\nSummary:")
    print(f"   • Analyzed: {len(df)} mutual funds")
    print(f"   • Anomalies detected: {anomaly_count} funds ({anomaly_count / len(df) * 100:.1f}%)")
    print(f"   • High priority alerts: {high_priority} funds")

    print(f"\nOutput files created in 'results/' folder:")
    print(f"   • anomaly_detection_detailed.png (detailed charts)")
    print(f"   • anomaly_detection_simple.png (presentation chart)")
    print(f"   • anomaly_detection_results.csv (full data with flags)")
    print(f"   • anomaly_summary.csv (statistics)")
    print(f"   • anomaly_report.txt (text report)")

    print("\n" + "=" * 70)
    print("OUPUT:")
    print("=" * 70)
    print("1. Open 'results/anomaly_detection_simple.png' - simple analysis")
    print("2. Open 'results/anomaly_detection_detailed.png' - detailed analysis")
    print("3. Open 'results/anomaly_detection_results.csv' - see flagged funds")
    print("4. Read 'results/anomaly_report.txt' - text summary")

    if high_priority > 0:
        print(f"\nWARNING: {high_priority} HIGH PRIORITY anomalies detected!")
        print("   Review these funds carefully before any investment decisions.")


if __name__ == "__main__":
    main()