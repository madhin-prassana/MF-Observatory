import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import seaborn as sns
import os


def load_data():
    """Load the fund metrics data"""
    print("=" * 70)
    print("LOADING DATA")
    print("=" * 70)

    df = pd.read_csv('../data/fund_metrics.csv')

    # Remove any rows with missing values in key columns
    df = df.dropna(subset=['volatility', 'return_1y', 'max_drawdown'])

    print(f"✓ Loaded {len(df)} funds with complete data")
    print(f"✓ Date range: {df['oldest_date'].min()} to {df['latest_date'].max()}")

    return df


def find_optimal_clusters(X_scaled, max_k=10):
    """
    Use Elbow Method to find optimal number of clusters
    """
    print("\n" + "=" * 70)
    print("FINDING OPTIMAL NUMBER OF CLUSTERS")
    print("=" * 70)

    inertias = []
    silhouette_scores = []
    K_range = range(2, max_k + 1)

    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X_scaled)
        inertias.append(kmeans.inertia_)
        silhouette_scores.append(silhouette_score(X_scaled, kmeans.labels_))

    # Plot elbow curve
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Inertia plot
    ax1.plot(K_range, inertias, 'bo-', linewidth=2, markersize=8)
    ax1.set_xlabel('Number of Clusters (k)', fontsize=12)
    ax1.set_ylabel('Inertia (Within-cluster sum of squares)', fontsize=12)
    ax1.set_title('Elbow Method: Inertia', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # Silhouette plot
    ax2.plot(K_range, silhouette_scores, 'ro-', linewidth=2, markersize=8)
    ax2.set_xlabel('Number of Clusters (k)', fontsize=12)
    ax2.set_ylabel('Silhouette Score', fontsize=12)
    ax2.set_title('Elbow Method: Silhouette Score', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('../results/elbow_method.png', dpi=300, bbox_inches='tight')
    print("✓ Saved elbow method plot: results/elbow_method.png")
    plt.close()

    # Recommend k=5 (good balance for risk categories)
    recommended_k = 5
    print(f"\n✓ Recommended clusters: {recommended_k}")
    print(f"  (Common risk categories: Very Low, Low, Moderate, High, Very High)")

    return recommended_k


def perform_clustering(df, n_clusters=5):
    """
    Apply K-Means clustering on fund data
    """
    print("\n" + "=" * 70)
    print(f"PERFORMING K-MEANS CLUSTERING (k={n_clusters})")
    print("=" * 70)

    # Select features for clustering
    # Using: volatility, max_drawdown, and return_1y
    features = ['volatility', 'max_drawdown', 'return_1y']
    X = df[features].copy()

    print(f"\nFeatures used for clustering:")
    for i, feature in enumerate(features, 1):
        print(f"  {i}. {feature}")

    print(f"\n✓ Data shape: {X.shape[0]} funds × {X.shape[1]} features")

    # Standardize features (important for K-Means!)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print("✓ Features standardized (mean=0, std=1)")

    # Apply K-Means
    print(f"\n⚙️  Running K-Means algorithm...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10, max_iter=300)
    df['cluster'] = kmeans.fit_predict(X_scaled)

    # Calculate quality metrics
    sil_score = silhouette_score(X_scaled, df['cluster'])

    print(f"✓ Clustering complete!")
    print(f"\nilhouette Score: {sil_score:.3f}")
    print(f"   (Range: -1 to 1, higher is better)")
    print(f"   (>0.5 = Good, >0.7 = Excellent)")

    if sil_score > 0.5:
        print("   ✓ Good cluster separation!")
    elif sil_score > 0.3:
        print("   ⚠ Moderate cluster separation")
    else:
        print("   ⚠ Weak cluster separation (consider different features)")

    return df, kmeans, scaler, sil_score


def assign_risk_labels(df):
    """
    Assign risk category labels based on cluster characteristics
    """
    print("\n" + "=" * 70)
    print("ASSIGNING RISK LABELS")
    print("=" * 70)

    # Calculate average volatility for each cluster
    cluster_volatility = df.groupby('cluster')['volatility'].mean().sort_values()

    # Map clusters to risk levels (lowest volatility = lowest risk)
    risk_mapping = {}
    risk_labels = ['Very Low Risk', 'Low Risk', 'Moderate Risk', 'High Risk', 'Very High Risk']

    # Assign labels based on sorted volatility
    for i, (cluster_num, avg_vol) in enumerate(cluster_volatility.items()):
        risk_mapping[cluster_num] = risk_labels[min(i, len(risk_labels) - 1)]

    df['risk_category'] = df['cluster'].map(risk_mapping)

    print("\n✓ Risk categories assigned based on volatility")
    print("\nCluster → Risk Category Mapping:")
    for cluster_num in sorted(df['cluster'].unique()):
        risk = df[df['cluster'] == cluster_num]['risk_category'].iloc[0]
        avg_vol = df[df['cluster'] == cluster_num]['volatility'].mean()
        print(f"   Cluster {cluster_num} → {risk:20s} (Avg Volatility: {avg_vol:.2f}%)")

    return df


def analyze_clusters(df):
    """
    Analyze and display detailed cluster statistics
    """
    print("\n" + "=" * 70)
    print("CLUSTER ANALYSIS")
    print("=" * 70)

    for cluster in sorted(df['cluster'].unique()):
        cluster_data = df[df['cluster'] == cluster]
        risk_cat = cluster_data['risk_category'].iloc[0]

        print(f"\n{'─' * 70}")
        print(f"CLUSTER {cluster}: {risk_cat} ({len(cluster_data)} funds)")
        print(f"{'─' * 70}")

        print(f"  Volatility:      {cluster_data['volatility'].mean():.2f}% "
              f"(range: {cluster_data['volatility'].min():.2f}% - {cluster_data['volatility'].max():.2f}%)")

        print(f"  1Y Return:       {cluster_data['return_1y'].mean():.2f}% "
              f"(range: {cluster_data['return_1y'].min():.2f}% - {cluster_data['return_1y'].max():.2f}%)")

        print(f"  Max Drawdown:    {cluster_data['max_drawdown'].mean():.2f}% "
              f"(range: {cluster_data['max_drawdown'].min():.2f}% - {cluster_data['max_drawdown'].max():.2f}%)")

        print(f"  Sharpe Ratio:    {cluster_data['sharpe_ratio'].mean():.2f}")

        print(f"\n  Sample funds:")
        sample_funds = cluster_data.nlargest(3, 'return_1y')[['scheme_name', 'return_1y', 'volatility']]
        for idx, row in sample_funds.iterrows():
            print(f"    • {row['scheme_name'][:55]}")
            print(f"      Return: {row['return_1y']:.2f}%, Volatility: {row['volatility']:.2f}%")


def create_visualizations(df):
    """
    Create comprehensive visualizations
    """
    print("\n" + "=" * 70)
    print("CREATING VISUALIZATIONS")
    print("=" * 70)

    # Set style
    sns.set_style("whitegrid")
    colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c', '#9b59b6']

    # Create a large figure with multiple subplots
    fig = plt.figure(figsize=(18, 12))

    # Plot 1: Volatility vs Returns (Main scatter plot)
    ax1 = plt.subplot(2, 3, 1)
    for i, cluster in enumerate(sorted(df['cluster'].unique())):
        cluster_data = df[df['cluster'] == cluster]
        risk_label = cluster_data['risk_category'].iloc[0]
        ax1.scatter(cluster_data['volatility'], cluster_data['return_1y'],
                    c=colors[i], label=f'{risk_label}',
                    s=100, alpha=0.6, edgecolors='black', linewidth=0.5)

    ax1.set_xlabel('Volatility (%)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('1-Year Return (%)', fontsize=11, fontweight='bold')
    ax1.set_title('Risk-Return Profile by Cluster', fontsize=13, fontweight='bold')
    ax1.legend(loc='best', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=0, color='red', linestyle='--', linewidth=0.8, alpha=0.5)

    # Plot 2: Max Drawdown vs Volatility
    ax2 = plt.subplot(2, 3, 2)
    for i, cluster in enumerate(sorted(df['cluster'].unique())):
        cluster_data = df[df['cluster'] == cluster]
        ax2.scatter(cluster_data['volatility'], cluster_data['max_drawdown'],
                    c=colors[i], s=100, alpha=0.6, edgecolors='black', linewidth=0.5)

    ax2.set_xlabel('Volatility (%)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Max Drawdown (%)', fontsize=11, fontweight='bold')
    ax2.set_title('Drawdown vs Volatility', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # Plot 3: Cluster Distribution (Bar chart)
    ax3 = plt.subplot(2, 3, 3)
    cluster_counts = df.groupby(['cluster', 'risk_category']).size().reset_index(name='count')
    cluster_counts = cluster_counts.sort_values('cluster')

    bars = ax3.bar(range(len(cluster_counts)), cluster_counts['count'],
                   color=[colors[i] for i in cluster_counts['cluster']],
                   edgecolor='black', linewidth=1)
    ax3.set_xlabel('Risk Category', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Number of Funds', fontsize=11, fontweight='bold')
    ax3.set_title('Fund Distribution Across Risk Categories', fontsize=13, fontweight='bold')
    ax3.set_xticks(range(len(cluster_counts)))
    ax3.set_xticklabels(cluster_counts['risk_category'], rotation=45, ha='right', fontsize=9)
    ax3.grid(True, alpha=0.3, axis='y')

    # Add count labels on bars
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width() / 2., height,
                 f'{int(height)}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Plot 4: Box plot of Returns by Cluster
    ax4 = plt.subplot(2, 3, 4)
    df_sorted = df.sort_values('cluster')
    bp = ax4.boxplot([df[df['cluster'] == c]['return_1y'].values for c in sorted(df['cluster'].unique())],
                     labels=[df[df['cluster'] == c]['risk_category'].iloc[0] for c in sorted(df['cluster'].unique())],
                     patch_artist=True)

    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)

    ax4.set_xlabel('Risk Category', fontsize=11, fontweight='bold')
    ax4.set_ylabel('1-Year Return (%)', fontsize=11, fontweight='bold')
    ax4.set_title('Return Distribution by Risk Category', fontsize=13, fontweight='bold')
    ax4.set_xticklabels(ax4.get_xticklabels(), rotation=45, ha='right', fontsize=9)
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.axhline(y=0, color='red', linestyle='--', linewidth=0.8, alpha=0.5)

    # Plot 5: Box plot of Volatility by Cluster
    ax5 = plt.subplot(2, 3, 5)
    bp2 = ax5.boxplot([df[df['cluster'] == c]['volatility'].values for c in sorted(df['cluster'].unique())],
                      labels=[df[df['cluster'] == c]['risk_category'].iloc[0] for c in sorted(df['cluster'].unique())],
                      patch_artist=True)

    for patch, color in zip(bp2['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)

    ax5.set_xlabel('Risk Category', fontsize=11, fontweight='bold')
    ax5.set_ylabel('Volatility (%)', fontsize=11, fontweight='bold')
    ax5.set_title('Volatility Distribution by Risk Category', fontsize=13, fontweight='bold')
    ax5.set_xticklabels(ax5.get_xticklabels(), rotation=45, ha='right', fontsize=9)
    ax5.grid(True, alpha=0.3, axis='y')

    # Plot 6: Heatmap of average metrics by cluster
    ax6 = plt.subplot(2, 3, 6)
    cluster_summary = df.groupby('cluster')[['volatility', 'return_1y', 'max_drawdown']].mean()
    cluster_summary = cluster_summary.T

    sns.heatmap(cluster_summary, annot=True, fmt='.1f', cmap='RdYlGn',
                center=0, cbar_kws={'label': 'Value'}, ax=ax6, linewidths=0.5)
    ax6.set_xlabel('Cluster', fontsize=11, fontweight='bold')
    ax6.set_ylabel('Metric', fontsize=11, fontweight='bold')
    ax6.set_title('Average Metrics by Cluster', fontsize=13, fontweight='bold')
    ax6.set_yticklabels(['Volatility', '1Y Return', 'Max Drawdown'], rotation=0)

    plt.tight_layout()
    plt.savefig('../results/clustering_analysis.png', dpi=300, bbox_inches='tight')
    print("✓ Saved main visualization: results/clustering_analysis.png")
    plt.close()

    # Create a simpler summary chart for presentations
    fig2, ax = plt.subplots(figsize=(12, 8))

    for i, cluster in enumerate(sorted(df['cluster'].unique())):
        cluster_data = df[df['cluster'] == cluster]
        risk_label = cluster_data['risk_category'].iloc[0]
        ax.scatter(cluster_data['volatility'], cluster_data['return_1y'],
                   c=colors[i], label=f'{risk_label} ({len(cluster_data)} funds)',
                   s=150, alpha=0.7, edgecolors='black', linewidth=1)

    ax.set_xlabel('Volatility (Risk) %', fontsize=14, fontweight='bold')
    ax.set_ylabel('1-Year Return %', fontsize=14, fontweight='bold')
    ax.set_title('Mutual Fund Risk-Return Clusters', fontsize=16, fontweight='bold', pad=20)
    ax.legend(loc='best', fontsize=11, framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Zero return')

    plt.tight_layout()
    plt.savefig('../results/clustering_simple.png', dpi=300, bbox_inches='tight')
    print("✓ Saved presentation chart: results/clustering_simple.png")
    plt.close()


def save_results(df):
    """
    Save clustering results to files
    """
    print("\n" + "=" * 70)
    print("SAVING RESULTS")
    print("=" * 70)

    # Save full results with clusters
    output_file = '../results/clustered_funds.csv'
    df_output = df[['scheme_code', 'scheme_name', 'cluster', 'risk_category',
                    'volatility', 'return_1y', 'max_drawdown', 'sharpe_ratio',
                    'latest_nav', 'latest_date']].copy()
    df_output = df_output.sort_values(['cluster', 'volatility'])
    df_output.to_csv(output_file, index=False)
    print(f"✓ Saved detailed results: {output_file}")

    # Create cluster summary
    summary = df.groupby(['cluster', 'risk_category']).agg({
        'scheme_name': 'count',
        'volatility': ['mean', 'min', 'max'],
        'return_1y': ['mean', 'min', 'max'],
        'max_drawdown': ['mean', 'min', 'max'],
        'sharpe_ratio': 'mean'
    }).round(2)

    summary.columns = ['Fund_Count',
                       'Avg_Volatility', 'Min_Volatility', 'Max_Volatility',
                       'Avg_Return', 'Min_Return', 'Max_Return',
                       'Avg_Drawdown', 'Min_Drawdown', 'Max_Drawdown',
                       'Avg_Sharpe']

    summary_file = '../results/cluster_summary.csv'
    summary.to_csv(summary_file)
    print(f"✓ Saved cluster summary: {summary_file}")

    # Create a text report
    report_file = '../results/clustering_report.txt'
    with open(report_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("MUTUAL FUND CLUSTERING ANALYSIS REPORT\n")
        f.write("=" * 70 + "\n\n")

        f.write(f"Total Funds Analyzed: {len(df)}\n")
        f.write(f"Number of Clusters: {df['cluster'].nunique()}\n")
        f.write(f"Features Used: Volatility, 1-Year Return, Max Drawdown\n\n")

        f.write("=" * 70 + "\n")
        f.write("CLUSTER BREAKDOWN\n")
        f.write("=" * 70 + "\n\n")

        for cluster in sorted(df['cluster'].unique()):
            cluster_data = df[df['cluster'] == cluster]
            risk_cat = cluster_data['risk_category'].iloc[0]

            f.write(f"\nCluster {cluster}: {risk_cat}\n")
            f.write(f"{'-' * 70}\n")
            f.write(f"Number of Funds: {len(cluster_data)}\n")
            f.write(f"Average Volatility: {cluster_data['volatility'].mean():.2f}%\n")
            f.write(f"Average 1Y Return: {cluster_data['return_1y'].mean():.2f}%\n")
            f.write(f"Average Max Drawdown: {cluster_data['max_drawdown'].mean():.2f}%\n")
            f.write(f"Average Sharpe Ratio: {cluster_data['sharpe_ratio'].mean():.2f}\n")

            f.write(f"\nTop 3 Performers in this cluster:\n")
            top3 = cluster_data.nlargest(3, 'return_1y')[['scheme_name', 'return_1y', 'volatility']]
            for idx, row in top3.iterrows():
                f.write(f"  • {row['scheme_name']}\n")
                f.write(f"    Return: {row['return_1y']:.2f}%, Volatility: {row['volatility']:.2f}%\n")

    print(f"✓ Saved text report: {report_file}")


def main():
    """
    Main execution function
    """
    # Create results folder
    os.makedirs('../results', exist_ok=True)

    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "MUTUAL FUND CLUSTERING ANALYSIS" + " " * 22 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # Step 1: Load data
    df = load_data()

    # Step 2: Find optimal clusters (creates elbow plot)
    features = ['volatility', 'max_drawdown', 'return_1y']
    X = df[features].copy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    optimal_k = find_optimal_clusters(X_scaled)

    # Step 3: Perform clustering with k=5
    df, model, scaler, sil_score = perform_clustering(df, n_clusters=5)

    # Step 4: Assign risk labels
    df = assign_risk_labels(df)

    # Step 5: Analyze clusters
    analyze_clusters(df)

    # Step 6: Create visualizations
    create_visualizations(df)

    # Step 7: Save results
    save_results(df)

    # Final summary
    print("\n" + "=" * 70)
    print("✓ CLUSTERING COMPLETE!")
    print("=" * 70)
    print(f"\nSummary:")
    print(f"   • Analyzed: {len(df)} mutual funds")
    print(f"   • Created: 5 risk-based clusters")
    print(f"   • Silhouette Score: {sil_score:.3f}")
    print(f"\nOutput files created in 'results/' folder:")
    print(f"   • clustering_analysis.png (detailed charts)")
    print(f"   • clustering_simple.png (presentation chart)")
    print(f"   • clustered_funds.csv (full data with clusters)")
    print(f"   • cluster_summary.csv (statistics)")
    print(f"   • clustering_report.txt (text report)")
    print(f"   • elbow_method.png (optimal k analysis)")

    print("\n" + "=" * 70)
    print("1. Open 'results/clustering_simple.png' - simple analysis")
    print("2. Open 'results/clustering_analysis.png' - detailed analysis")
    print("3. Open 'results/clustered_funds.csv' - see which fund is in which cluster")
    print("4. Read 'results/clustering_report.txt' - text summary")


if __name__ == "__main__":
    main()