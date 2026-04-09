import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
 
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_prediction_results():
    """Load both Prophet and LSTM prediction results"""

    print("=" * 70)
    print("LOADING PREDICTION RESULTS")
    print("=" * 70)

    # Load Prophet results
    prophet_file = os.path.join(base_dir, 'results', 'prediction_results.csv')
    if not os.path.exists(prophet_file):
        print("✗ Prophet results not found! Please run prediction.py first.")
        return None, None

    prophet_df = pd.read_csv(prophet_file)
    print(f"✓ Loaded Prophet results: {len(prophet_df)} funds")

    # Load LSTM results
    lstm_file = os.path.join(base_dir, 'results', 'prediction_results_lstm.csv')
    if not os.path.exists(lstm_file):
        print("✗ LSTM results not found! Please run prediction_lstm.py first.")
        return None, None

    lstm_df = pd.read_csv(lstm_file)
    print(f"✓ Loaded LSTM results: {len(lstm_df)} funds")

    return prophet_df, lstm_df


def merge_results(prophet_df, lstm_df):
    """Merge Prophet and LSTM results for funds common to both"""

    print("\n" + "=" * 70)
    print("MERGING RESULTS")
    print("=" * 70)

    # Merge on scheme_code (only funds that have both predictions)
    merged = prophet_df.merge(
        lstm_df,
        on='scheme_code',
        suffixes=('_prophet', '_lstm'),
        how='inner'
    )

    print(f"✓ {len(merged)} funds have both Prophet and LSTM predictions")

    if len(merged) < len(prophet_df):
        print(f"⚠ {len(prophet_df) - len(merged)} funds only have Prophet predictions")

    if len(merged) < len(lstm_df):
        print(f"⚠ {len(lstm_df) - len(merged)} funds only have LSTM predictions")

    return merged


def calculate_ensemble_predictions(merged_df):
    """Calculate ensemble predictions using different methods"""

    print("\n" + "=" * 70)
    print("CALCULATING ENSEMBLE PREDICTIONS")
    print("=" * 70)

    # Method 1: Simple Average
    merged_df['ensemble_simple_return'] = (
                                                  merged_df['expected_return_6m_prophet'] +
                                                  merged_df['expected_return_6m_lstm']
                                          ) / 2

    merged_df['ensemble_simple_nav'] = (
                                               merged_df['predicted_nav_6m_prophet'] +
                                               merged_df['predicted_nav_6m_lstm']
                                       ) / 2

    print("✓ Method 1: Simple Average (Prophet + LSTM) / 2")

    # Method 2: Weighted Average (based on inverse MAPE - lower error = higher weight)
    # Handle infinite/nan MAPE values
    merged_df['mape_prophet_clean'] = merged_df['mape_prophet'].replace([np.inf, -np.inf], np.nan)
    merged_df['mape_lstm_clean'] = merged_df['mape_lstm'].replace([np.inf, -np.inf], np.nan)

    # Calculate weights (inverse of MAPE)
    merged_df['weight_prophet'] = 1 / (merged_df['mape_prophet_clean'] + 1e-6)
    merged_df['weight_lstm'] = 1 / (merged_df['mape_lstm_clean'] + 1e-6)

    # Normalize weights
    total_weight = merged_df['weight_prophet'] + merged_df['weight_lstm']
    merged_df['weight_prophet_norm'] = merged_df['weight_prophet'] / total_weight
    merged_df['weight_lstm_norm'] = merged_df['weight_lstm'] / total_weight

    # Weighted ensemble
    merged_df['ensemble_weighted_return'] = (
            merged_df['expected_return_6m_prophet'] * merged_df['weight_prophet_norm'] +
            merged_df['expected_return_6m_lstm'] * merged_df['weight_lstm_norm']
    )

    merged_df['ensemble_weighted_nav'] = (
            merged_df['predicted_nav_6m_prophet'] * merged_df['weight_prophet_norm'] +
            merged_df['predicted_nav_6m_lstm'] * merged_df['weight_lstm_norm']
    )

    print("✓ Method 2: Weighted Average (based on accuracy)")

    # Method 3: Best Model Selection (pick lowest MAPE, but penalize crazy hallucinations)
    def select_best_model(row):
        prophet_ret = row['expected_return_6m_prophet']
        lstm_ret = row['expected_return_6m_lstm']
        prophet_mape = row['mape_prophet_clean']
        lstm_mape = row['mape_lstm_clean']
        
        # Define what constitutes an "absurd/extreme" 6-month return for a mutual fund
        EXTREME_THRESHOLD = 35.0 
        
        prophet_absurd = abs(prophet_ret) > EXTREME_THRESHOLD
        lstm_absurd = abs(lstm_ret) > EXTREME_THRESHOLD
        
        # If one hallucinates and the other is conservative, pick the conservative one
        if lstm_absurd and not prophet_absurd:
            return 'Prophet'
        elif prophet_absurd and not lstm_absurd:
            return 'LSTM'
            
        # If both are safe (or both are crazy), default to the one with the better historical accuracy
        return 'Prophet' if prophet_mape < lstm_mape else 'LSTM'

    merged_df['best_model'] = merged_df.apply(select_best_model, axis=1)

    merged_df['best_model_return'] = merged_df.apply(
        lambda row: row['expected_return_6m_prophet'] if row['best_model'] == 'Prophet'
        else row['expected_return_6m_lstm'],
        axis=1
    )

    merged_df['best_model_nav'] = merged_df.apply(
        lambda row: row['predicted_nav_6m_prophet'] if row['best_model'] == 'Prophet'
        else row['predicted_nav_6m_lstm'],
        axis=1
    )

    merged_df['best_model_mape'] = merged_df.apply(
        lambda row: row['mape_prophet_clean'] if row['best_model'] == 'Prophet'
        else row['mape_lstm_clean'],
        axis=1
    )

    print("✓ Method 3: Best Model Selection (per fund)")

    return merged_df


def compare_model_performance(merged_df):
    """Compare Prophet vs LSTM performance"""

    print("\n" + "=" * 70)
    print("MODEL PERFORMANCE COMPARISON")
    print("=" * 70)

    # Overall statistics
    prophet_mape_mean = merged_df['mape_prophet_clean'].mean()
    lstm_mape_mean = merged_df['mape_lstm_clean'].mean()

    prophet_r2_mean = merged_df['r2_score_prophet'].mean()
    lstm_r2_mean = merged_df['r2_score_lstm'].mean()

    print(f"\nAverage Accuracy (Lower MAPE is better):")
    print(f"   Prophet MAPE: {prophet_mape_mean:.2f}%")
    print(f"   LSTM MAPE:    {lstm_mape_mean:.2f}%")

    if prophet_mape_mean < lstm_mape_mean:
        improvement = ((lstm_mape_mean - prophet_mape_mean) / lstm_mape_mean) * 100
        print(f"   ✓ Prophet is {improvement:.1f}% more accurate (lower error)")
    else:
        improvement = ((prophet_mape_mean - lstm_mape_mean) / prophet_mape_mean) * 100
        print(f"   ✓ LSTM is {improvement:.1f}% more accurate (lower error)")

    print(f"\nAverage Model Fit (Higher R² is better):")
    print(f"   Prophet R²: {prophet_r2_mean:.3f}")
    print(f"   LSTM R²:    {lstm_r2_mean:.3f}")

    # Win rates
    prophet_wins = (merged_df['mape_prophet_clean'] < merged_df['mape_lstm_clean']).sum()
    lstm_wins = (merged_df['mape_lstm_clean'] < merged_df['mape_prophet_clean']).sum()
    ties = len(merged_df) - prophet_wins - lstm_wins

    print(f"\nWin Rate (Lower MAPE):")
    print(f"   Prophet wins: {prophet_wins} funds ({prophet_wins / len(merged_df) * 100:.1f}%)")
    print(f"   LSTM wins:    {lstm_wins} funds ({lstm_wins / len(merged_df) * 100:.1f}%)")
    print(f"   Ties:         {ties} funds ({ties / len(merged_df) * 100:.1f}%)")

    # Prediction comparison
    prophet_return_mean = merged_df['expected_return_6m_prophet'].mean()
    lstm_return_mean = merged_df['expected_return_6m_lstm'].mean()

    print(f"\nAverage Predicted Returns:")
    print(f"   Prophet: {prophet_return_mean:.2f}%")
    print(f"   LSTM:    {lstm_return_mean:.2f}%")

    return {
        'prophet_mape': prophet_mape_mean,
        'lstm_mape': lstm_mape_mean,
        'prophet_r2': prophet_r2_mean,
        'lstm_r2': lstm_r2_mean,
        'prophet_wins': prophet_wins,
        'lstm_wins': lstm_wins,
        'prophet_return': prophet_return_mean,
        'lstm_return': lstm_return_mean
    }


def analyze_ensemble_performance(merged_df):
    """Analyze ensemble method performance"""

    print("\n" + "=" * 70)
    print("ENSEMBLE PERFORMANCE ANALYSIS")
    print("=" * 70)

    # Calculate average MAPE for best model selection
    best_model_mape = merged_df['best_model_mape'].mean()

    print(f"\nEnsemble Method Performance:")
    print(f"   Simple Average Return:    {merged_df['ensemble_simple_return'].mean():.2f}%")
    print(f"   Weighted Average Return:  {merged_df['ensemble_weighted_return'].mean():.2f}%")
    print(f"   Best Model Selection:     {merged_df['best_model_return'].mean():.2f}%")
    print(f"   Best Model Avg MAPE:      {best_model_mape:.2f}%")

    # Best model distribution
    print(f"\nBest Model Distribution:")
    best_counts = merged_df['best_model'].value_counts()
    for model, count in best_counts.items():
        print(f"   {model}: {count} funds ({count / len(merged_df) * 100:.1f}%)")


def create_comparison_visualizations(merged_df, stats):
    """Create comprehensive comparison visualizations"""

    print("\n" + "=" * 70)
    print("CREATING COMPARISON VISUALIZATIONS")
    print("=" * 70)

    sns.set_style("whitegrid")

    # Create large figure with multiple subplots
    fig = plt.figure(figsize=(20, 12))

    # Plot 1: Prediction Comparison Scatter
    ax1 = plt.subplot(2, 4, 1)
    ax1.scatter(merged_df['expected_return_6m_prophet'],
                merged_df['expected_return_6m_lstm'],
                alpha=0.6, s=80, edgecolors='black', linewidth=0.5)

    # Add diagonal line (perfect agreement)
    min_val = min(merged_df['expected_return_6m_prophet'].min(),
                  merged_df['expected_return_6m_lstm'].min())
    max_val = max(merged_df['expected_return_6m_prophet'].max(),
                  merged_df['expected_return_6m_lstm'].max())
    ax1.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect Agreement')

    ax1.set_xlabel('Prophet Prediction (%)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('LSTM Prediction (%)', fontsize=11, fontweight='bold')
    ax1.set_title('Prophet vs LSTM Predictions', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)

    # Plot 2: MAPE Comparison
    ax2 = plt.subplot(2, 4, 2)
    x = np.arange(2)
    heights = [stats['prophet_mape'], stats['lstm_mape']]
    colors = ['blue', 'red']
    bars = ax2.bar(x, heights, color=colors, edgecolor='black', alpha=0.7)
    ax2.set_xticks(x)
    ax2.set_xticklabels(['Prophet', 'LSTM'], fontsize=11)
    ax2.set_ylabel('Average MAPE (%)', fontsize=11, fontweight='bold')
    ax2.set_title('Model Accuracy Comparison\n(Lower is Better)', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')

    # Add values on bars
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2., height,
                 f'{height:.2f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Plot 3: R² Score Comparison
    ax3 = plt.subplot(2, 4, 3)
    x = np.arange(2)
    heights = [stats['prophet_r2'], stats['lstm_r2']]
    bars = ax3.bar(x, heights, color=colors, edgecolor='black', alpha=0.7)
    ax3.set_xticks(x)
    ax3.set_xticklabels(['Prophet', 'LSTM'], fontsize=11)
    ax3.set_ylabel('Average R² Score', fontsize=11, fontweight='bold')
    ax3.set_title('Model Fit Comparison\n(Higher is Better)', fontsize=13, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')

    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width() / 2., height,
                 f'{height:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Plot 4: Win Rate
    ax4 = plt.subplot(2, 4, 4)
    labels = ['Prophet\nWins', 'LSTM\nWins']
    sizes = [stats['prophet_wins'], stats['lstm_wins']]
    colors_pie = ['#3498db', '#e74c3c']
    explode = (0.05, 0.05)

    ax4.pie(sizes, explode=explode, labels=labels, colors=colors_pie,
            autopct='%1.1f%%', shadow=True, startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'})
    ax4.set_title('Win Rate by Model\n(Lower MAPE Wins)', fontsize=13, fontweight='bold')

    # Plot 5: Distribution of Prediction Differences
    ax5 = plt.subplot(2, 4, 5)
    diff = merged_df['expected_return_6m_prophet'] - merged_df['expected_return_6m_lstm']
    ax5.hist(diff, bins=25, color='purple', edgecolor='black', alpha=0.7)
    ax5.axvline(0, color='red', linestyle='--', linewidth=2, label='No Difference')
    ax5.axvline(diff.mean(), color='green', linestyle='--', linewidth=2, label=f'Mean: {diff.mean():.2f}%')
    ax5.set_xlabel('Prophet - LSTM Prediction (%)', fontsize=11, fontweight='bold')
    ax5.set_ylabel('Frequency', fontsize=11, fontweight='bold')
    ax5.set_title('Prediction Difference Distribution', fontsize=13, fontweight='bold')
    ax5.legend(fontsize=9)
    ax5.grid(True, alpha=0.3)

    # Plot 6: Ensemble Methods Comparison
    ax6 = plt.subplot(2, 4, 6)
    ensemble_returns = [
        merged_df['expected_return_6m_prophet'].mean(),
        merged_df['expected_return_6m_lstm'].mean(),
        merged_df['ensemble_simple_return'].mean(),
        merged_df['ensemble_weighted_return'].mean(),
        merged_df['best_model_return'].mean()
    ]
    labels = ['Prophet', 'LSTM', 'Simple\nAvg', 'Weighted\nAvg', 'Best\nModel']
    colors_bar = ['blue', 'red', 'green', 'orange', 'purple']

    bars = ax6.bar(range(5), ensemble_returns, color=colors_bar, edgecolor='black', alpha=0.7)
    ax6.set_xticks(range(5))
    ax6.set_xticklabels(labels, fontsize=10)
    ax6.set_ylabel('Avg Predicted Return (%)', fontsize=11, fontweight='bold')
    ax6.set_title('All Methods Comparison', fontsize=13, fontweight='bold')
    ax6.grid(True, alpha=0.3, axis='y')

    for bar in bars:
        height = bar.get_height()
        ax6.text(bar.get_x() + bar.get_width() / 2., height,
                 f'{height:.2f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Plot 7: MAPE Distribution Comparison
    ax7 = plt.subplot(2, 4, 7)
    ax7.hist(merged_df['mape_prophet_clean'], bins=20, alpha=0.5,
             color='blue', edgecolor='black', label='Prophet')
    ax7.hist(merged_df['mape_lstm_clean'], bins=20, alpha=0.5,
             color='red', edgecolor='black', label='LSTM')
    ax7.set_xlabel('MAPE (%)', fontsize=11, fontweight='bold')
    ax7.set_ylabel('Frequency', fontsize=11, fontweight='bold')
    ax7.set_title('MAPE Distribution by Model', fontsize=13, fontweight='bold')
    ax7.legend(fontsize=10)
    ax7.grid(True, alpha=0.3)

    # Plot 8: Best Model Distribution
    ax8 = plt.subplot(2, 4, 8)
    best_counts = merged_df['best_model'].value_counts()
    colors_best = ['#3498db' if model == 'Prophet' else '#e74c3c' for model in best_counts.index]
    bars = ax8.bar(range(len(best_counts)), best_counts.values,
                   color=colors_best, edgecolor='black', alpha=0.7)
    ax8.set_xticks(range(len(best_counts)))
    ax8.set_xticklabels(best_counts.index, fontsize=11)
    ax8.set_ylabel('Number of Funds', fontsize=11, fontweight='bold')
    ax8.set_title('Best Model per Fund\n(Lower MAPE)', fontsize=13, fontweight='bold')
    ax8.grid(True, alpha=0.3, axis='y')

    for bar in bars:
        height = bar.get_height()
        ax8.text(bar.get_x() + bar.get_width() / 2., height,
                 f'{int(height)}', ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(base_dir, 'results', 'prediction_comparison_detailed.png'), dpi=300, bbox_inches='tight')
    print("✓ Saved detailed comparison: results/prediction_comparison_detailed.png")
    plt.close()

    # Create simple comparison chart for presentation
    fig2, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

    # Simple comparison 1: Accuracy
    x = np.arange(2)
    ax1.bar(x, [stats['prophet_mape'], stats['lstm_mape']],
            color=['blue', 'red'], edgecolor='black', alpha=0.7, width=0.6)
    ax1.set_xticks(x)
    ax1.set_xticklabels(['Prophet', 'LSTM'], fontsize=13)
    ax1.set_ylabel('MAPE (%)', fontsize=13, fontweight='bold')
    ax1.set_title('Model Accuracy (Lower is Better)', fontsize=15, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')

    # Simple comparison 2: Predictions scatter
    ax2.scatter(merged_df['expected_return_6m_prophet'],
                merged_df['expected_return_6m_lstm'],
                alpha=0.6, s=100, edgecolors='black', linewidth=0.5, color='purple')
    min_val = min(merged_df['expected_return_6m_prophet'].min(),
                  merged_df['expected_return_6m_lstm'].min())
    max_val = max(merged_df['expected_return_6m_prophet'].max(),
                  merged_df['expected_return_6m_lstm'].max())
    ax2.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2)
    ax2.set_xlabel('Prophet Prediction (%)', fontsize=13, fontweight='bold')
    ax2.set_ylabel('LSTM Prediction (%)', fontsize=13, fontweight='bold')
    ax2.set_title('Prophet vs LSTM Predictions', fontsize=15, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # Simple comparison 3: Ensemble comparison
    ensemble_returns = [
        stats['prophet_return'],
        stats['lstm_return'],
        merged_df['ensemble_simple_return'].mean(),
        merged_df['best_model_return'].mean()
    ]
    ax3.bar(range(4), ensemble_returns,
            color=['blue', 'red', 'green', 'purple'],
            edgecolor='black', alpha=0.7, width=0.6)
    ax3.set_xticks(range(4))
    ax3.set_xticklabels(['Prophet', 'LSTM', 'Ensemble\nAverage', 'Best\nModel'], fontsize=11)
    ax3.set_ylabel('Avg Predicted Return (%)', fontsize=13, fontweight='bold')
    ax3.set_title('Method Comparison', fontsize=15, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')

    # Simple comparison 4: Win rate
    sizes = [stats['prophet_wins'], stats['lstm_wins']]
    colors_pie = ['#3498db', '#e74c3c']
    ax4.pie(sizes, labels=['Prophet', 'LSTM'], colors=colors_pie,
            autopct='%1.1f%%', shadow=True, startangle=90,
            textprops={'fontsize': 13, 'fontweight': 'bold'})
    ax4.set_title('Win Rate (Lower MAPE)', fontsize=15, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(base_dir, 'results', 'prediction_comparison_simple.png'), dpi=300, bbox_inches='tight')
    print("✓ Saved simple comparison: results/prediction_comparison_simple.png")
    plt.close()


def save_comparison_results(merged_df, stats):
    """Save comparison results and ensemble predictions"""

    print("\n" + "=" * 70)
    print("SAVING COMPARISON RESULTS")
    print("=" * 70)

    # Save ensemble predictions
    ensemble_df = merged_df[[
        'scheme_code', 'scheme_name_prophet',
        'current_nav_prophet',
        'expected_return_6m_prophet', 'expected_return_6m_lstm',
        'ensemble_simple_return', 'ensemble_weighted_return',
        'best_model', 'best_model_return',
        'mape_prophet_clean', 'mape_lstm_clean', 'best_model_mape'
    ]].copy()

    ensemble_df.columns = [
        'scheme_code', 'scheme_name', 'current_nav',
        'prophet_return', 'lstm_return',
        'ensemble_simple', 'ensemble_weighted',
        'recommended_model', 'recommended_return',
        'prophet_mape', 'lstm_mape', 'recommended_mape'
    ]

    ensemble_df = ensemble_df.sort_values('recommended_return', ascending=False)

    output_file = os.path.join(base_dir, 'results', 'prediction_ensemble.csv')
    ensemble_df.to_csv(output_file, index=False)
    print(f"✓ Saved ensemble predictions: {output_file}")

    # Save comparison report
    report_file = os.path.join(base_dir, 'results', 'prediction_comparison_report.txt')
    with open(report_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("PROPHET VS LSTM COMPARISON REPORT\n")
        f.write("=" * 70 + "\n\n")

        f.write(f"Total Funds Analyzed: {len(merged_df)}\n\n")

        f.write("MODEL ACCURACY COMPARISON\n")
        f.write("-" * 70 + "\n")
        f.write(f"Prophet Average MAPE: {stats['prophet_mape']:.2f}%\n")
        f.write(f"LSTM Average MAPE:    {stats['lstm_mape']:.2f}%\n\n")

        if stats['prophet_mape'] < stats['lstm_mape']:
            improvement = ((stats['lstm_mape'] - stats['prophet_mape']) / stats['lstm_mape']) * 100
            f.write(f"✓ Prophet is {improvement:.1f}% more accurate\n\n")
        else:
            improvement = ((stats['prophet_mape'] - stats['lstm_mape']) / stats['prophet_mape']) * 100
            f.write(f"✓ LSTM is {improvement:.1f}% more accurate\n\n")

        f.write("MODEL FIT COMPARISON\n")
        f.write("-" * 70 + "\n")
        f.write(f"Prophet Average R²: {stats['prophet_r2']:.3f}\n")
        f.write(f"LSTM Average R²:    {stats['lstm_r2']:.3f}\n\n")

        f.write("WIN RATE\n")
        f.write("-" * 70 + "\n")
        f.write(f"Prophet wins: {stats['prophet_wins']} funds ({stats['prophet_wins'] / len(merged_df) * 100:.1f}%)\n")
        f.write(f"LSTM wins:    {stats['lstm_wins']} funds ({stats['lstm_wins'] / len(merged_df) * 100:.1f}%)\n\n")

        f.write("PREDICTED RETURNS\n")
        f.write("-" * 70 + "\n")
        f.write(f"Prophet Average:         {stats['prophet_return']:.2f}%\n")
        f.write(f"LSTM Average:            {stats['lstm_return']:.2f}%\n")
        f.write(f"Ensemble Simple:         {merged_df['ensemble_simple_return'].mean():.2f}%\n")
        f.write(f"Ensemble Weighted:       {merged_df['ensemble_weighted_return'].mean():.2f}%\n")
        f.write(f"Best Model Selection:    {merged_df['best_model_return'].mean():.2f}%\n\n")

        f.write("=" * 70 + "\n")
        f.write("TOP 10 RECOMMENDED FUNDS (Best Model Selection)\n")
        f.write("=" * 70 + "\n\n")

        top_10 = ensemble_df.head(10)
        for idx, row in top_10.iterrows():
            f.write(f"{row['scheme_name'][:60]}\n")
            f.write(f"  Recommended Model: {row['recommended_model']}\n")
            f.write(f"  Predicted Return:  {row['recommended_return']:.2f}%\n")
            f.write(f"  Model MAPE:        {row['recommended_mape']:.2f}%\n")
            f.write(f"  Prophet: {row['prophet_return']:.2f}% | LSTM: {row['lstm_return']:.2f}%\n\n")

        f.write("=" * 70 + "\n")
        f.write("RECOMMENDATION\n")
        f.write("=" * 70 + "\n\n")

        if stats['prophet_wins'] > stats['lstm_wins']:
            f.write("✓ Prophet performs better overall (wins more funds)\n")
            f.write("  Recommended: Use Prophet as default, LSTM for specific cases\n")
        elif stats['lstm_wins'] > stats['prophet_wins']:
            f.write("✓ LSTM performs better overall (wins more funds)\n")
            f.write("  Recommended: Use LSTM as default, Prophet for specific cases\n")
        else:
            f.write("✓ Both models perform similarly\n")
            f.write("  Recommended: Use Best Model Selection or Ensemble Average\n")

        f.write("\n")
        f.write("For Web Interface: Recommend using 'Best Model Selection' method\n")
        f.write("This automatically picks the more accurate model for each fund.\n")

    print(f"✓ Saved comparison report: {report_file}")


def main():
    """Main execution"""

    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 12 + "PROPHET VS LSTM COMPARISON & ENSEMBLE" + " " * 18 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # Load results
    prophet_df, lstm_df = load_prediction_results()

    if prophet_df is None or lstm_df is None:
        print("\n✗ Cannot proceed without both Prophet and LSTM results!")
        return

    # Merge results
    merged_df = merge_results(prophet_df, lstm_df)

    if len(merged_df) == 0:
        print("\n✗ No common funds between Prophet and LSTM results!")
        return

    # Calculate ensemble predictions
    merged_df = calculate_ensemble_predictions(merged_df)

    # Compare performance
    stats = compare_model_performance(merged_df)

    # Analyze ensemble
    analyze_ensemble_performance(merged_df)

    # Create visualizations
    create_comparison_visualizations(merged_df, stats)

    # Save results
    save_comparison_results(merged_df, stats)

    # Final summary
    print("\n" + "=" * 70)
    print("✓ COMPARISON & ENSEMBLE COMPLETE!")
    print("=" * 70)

    print(f"\nKey Findings:")
    print(f"   • Funds analyzed: {len(merged_df)}")
    print(f"   • Prophet accuracy: {stats['prophet_mape']:.2f}% MAPE")
    print(f"   • LSTM accuracy: {stats['lstm_mape']:.2f}% MAPE")
    print(f"   • Prophet wins: {stats['prophet_wins']} funds")
    print(f"   • LSTM wins: {stats['lstm_wins']} funds")

    print(f"\nOutput files created:")
    print(f"   • prediction_ensemble.csv (recommended predictions)")
    print(f"   • prediction_comparison_report.txt (detailed report)")
    print(f"   • prediction_comparison_detailed.png (8 charts)")
    print(f"   • prediction_comparison_simple.png (presentation version)")

if __name__ == "__main__":
    main()