import pandas as pd
import numpy as np
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
import matplotlib.pyplot as plt
import seaborn as sns
import os
from glob import glob
import warnings

warnings.filterwarnings('ignore')


def load_fund_data(fund_file):
    """Load and prepare data for a single fund"""
    try:
        df = pd.read_csv(fund_file)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        # Prophet requires columns named 'ds' and 'y'
        prophet_df = pd.DataFrame({
            'ds': df['date'],
            'y': df['nav']
        })

        return prophet_df, df['scheme_name'].iloc[0], df['scheme_code'].iloc[0]

    except Exception as e:
        print(f"Error loading {fund_file}: {e}")
        return None, None, None


def train_prophet_model(df, scheme_name):
    """Train Prophet model for a fund"""
    try:
        # Initialize Prophet with parameters
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            changepoint_prior_scale=0.05,  # Flexibility of trend changes
            seasonality_prior_scale=10.0,  # Flexibility of seasonality
            interval_width=0.80  # 80% confidence interval
        )

        # Fit the model
        model.fit(df)

        return model

    except Exception as e:
        print(f"  Error training model for {scheme_name}: {e}")
        return None


def make_predictions(model, periods=180):
    """Make future predictions (default 180 days = ~6 months)"""
    try:
        # Create future dataframe
        future = model.make_future_dataframe(periods=periods)

        # Predict
        forecast = model.predict(future)

        return forecast

    except Exception as e:
        print(f"  Error making predictions: {e}")
        return None


def calculate_accuracy_metrics(actual_df, forecast_df):
    """Calculate prediction accuracy on historical data"""
    try:
        # Merge actual and predicted values
        merged = actual_df.merge(
            forecast_df[['ds', 'yhat', 'yhat_lower', 'yhat_upper']],
            on='ds',
            how='inner'
        )

        # Calculate metrics
        mae = np.mean(np.abs(merged['y'] - merged['yhat']))
        rmse = np.sqrt(np.mean((merged['y'] - merged['yhat']) ** 2))
        mape = np.mean(np.abs((merged['y'] - merged['yhat']) / merged['y'])) * 100

        # R-squared
        ss_res = np.sum((merged['y'] - merged['yhat']) ** 2)
        ss_tot = np.sum((merged['y'] - merged['y'].mean()) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        return {
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'r2_score': r2
        }

    except Exception as e:
        print(f"  Error calculating metrics: {e}")
        return None


def calculate_predicted_return(current_nav, predicted_nav):
    """Calculate expected return from current to predicted NAV"""
    return ((predicted_nav - current_nav) / current_nav) * 100


def create_prediction_chart(actual_df, forecast_df, scheme_name, scheme_code, metrics):
    """Create visualization for individual fund prediction"""
    try:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # Plot 1: Full timeline with predictions
        # Historical data
        ax1.plot(actual_df['ds'], actual_df['y'],
                 'b-', label='Historical NAV', linewidth=2)

        # Future predictions
        future_forecast = forecast_df[forecast_df['ds'] > actual_df['ds'].max()]
        ax1.plot(future_forecast['ds'], future_forecast['yhat'],
                 'r--', label='Predicted NAV', linewidth=2)

        # Confidence interval for future
        ax1.fill_between(future_forecast['ds'],
                         future_forecast['yhat_lower'],
                         future_forecast['yhat_upper'],
                         alpha=0.3, color='red', label='80% Confidence Interval')

        ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax1.set_ylabel('NAV', fontsize=12, fontweight='bold')
        ax1.set_title(f'{scheme_name[:60]}\n6-Month Prediction',
                      fontsize=14, fontweight='bold')
        ax1.legend(loc='best', fontsize=10)
        ax1.grid(True, alpha=0.3)

        # Plot 2: Recent history + prediction (zoomed in)
        # Last 1 year + 6 months prediction
        recent_cutoff = actual_df['ds'].max() - pd.DateOffset(years=1)
        recent_actual = actual_df[actual_df['ds'] >= recent_cutoff]

        ax2.plot(recent_actual['ds'], recent_actual['y'],
                 'b-', label='Recent Historical NAV', linewidth=2, marker='o', markersize=3)
        ax2.plot(future_forecast['ds'], future_forecast['yhat'],
                 'r--', label='6-Month Prediction', linewidth=2, marker='s', markersize=3)
        ax2.fill_between(future_forecast['ds'],
                         future_forecast['yhat_lower'],
                         future_forecast['yhat_upper'],
                         alpha=0.3, color='red')

        ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax2.set_ylabel('NAV', fontsize=12, fontweight='bold')
        ax2.set_title('Recent Trend & Forecast (Zoomed)', fontsize=13, fontweight='bold')
        ax2.legend(loc='best', fontsize=10)
        ax2.grid(True, alpha=0.3)

        # Add metrics text box
        metrics_text = f"Accuracy Metrics:\n"
        metrics_text += f"MAE: {metrics['mae']:.2f}\n"
        metrics_text += f"RMSE: {metrics['rmse']:.2f}\n"
        metrics_text += f"MAPE: {metrics['mape']:.2f}%\n"
        metrics_text += f"R²: {metrics['r2_score']:.3f}"

        ax2.text(0.02, 0.98, metrics_text,
                 transform=ax2.transAxes,
                 fontsize=10,
                 verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()

        # Save
        os.makedirs('../results/predictions', exist_ok=True)
        plt.savefig(f'../results/predictions/prediction_{scheme_code}.png',
                    dpi=200, bbox_inches='tight')
        plt.close()

        return True

    except Exception as e:
        print(f"  Error creating chart: {e}")
        plt.close()
        return False


def process_all_funds():
    """Main function to process all funds"""

    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 12 + "MUTUAL FUND PERFORMANCE PREDICTION" + " " * 23 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # Get all fund files
    fund_files = glob('../data/fund_*.csv')

    print("=" * 70)
    print(f"PROCESSING {len(fund_files)} FUNDS")
    print("=" * 70)
    print(f"\nThis will take approximately {len(fund_files) * 0.7:.0f} minutes")
    print("Please be patient...\n")

    results = []
    successful = 0
    failed = 0

    for i, fund_file in enumerate(fund_files, 1):
        # Load data
        prophet_df, scheme_name, scheme_code = load_fund_data(fund_file)

        if prophet_df is None or len(prophet_df) < 365:
            print(f"[{i}/{len(fund_files)}] ✗ Skipped {os.path.basename(fund_file)} (insufficient data)")
            failed += 1
            continue

        # Check if fund is inactive
        cutoff_date = pd.Timestamp.now() - pd.DateOffset(years=2)
        if prophet_df['ds'].max() < cutoff_date:
            print(f"[{i}/{len(fund_files)}] ✗ Skipped {os.path.basename(fund_file)} (inactive fund, last date: {prophet_df['ds'].max().date()})")
            failed += 1
            continue

        print(f"[{i}/{len(fund_files)}] Processing: {scheme_name[:55]}...")

        # Train model
        model = train_prophet_model(prophet_df, scheme_name)

        if model is None:
            print(f"  ✗ Failed to train model")
            failed += 1
            continue

        print(f"  ✓ Model trained")

        # Make predictions
        forecast = make_predictions(model, periods=180)

        if forecast is None:
            print(f"  ✗ Failed to generate predictions")
            failed += 1
            continue

        # Calculate accuracy metrics
        metrics = calculate_accuracy_metrics(prophet_df, forecast)

        if metrics is None:
            print(f"  ✗ Failed to calculate metrics")
            failed += 1
            continue

        print(f"  ✓ Accuracy - MAE: {metrics['mae']:.2f}, MAPE: {metrics['mape']:.2f}%")

        # Get current and predicted values
        current_nav = prophet_df['y'].iloc[-1]
        current_date = prophet_df['ds'].iloc[-1]

        # 6-month prediction (180 days from last date)
        future_date = current_date + pd.DateOffset(days=180)
        predicted_row = forecast[forecast['ds'] >= future_date].iloc[0]

        predicted_nav = predicted_row['yhat']
        predicted_lower = predicted_row['yhat_lower']
        predicted_upper = predicted_row['yhat_upper']

        # Calculate expected return
        expected_return = calculate_predicted_return(current_nav, predicted_nav)
        expected_return_lower = calculate_predicted_return(current_nav, predicted_lower)
        expected_return_upper = calculate_predicted_return(current_nav, predicted_upper)

        print(
            f"  ✓ Predicted 6M Return: {expected_return:.2f}% (Range: {expected_return_lower:.2f}% to {expected_return_upper:.2f}%)")

        # Create chart
        chart_created = create_prediction_chart(prophet_df, forecast, scheme_name, scheme_code, metrics)

        if chart_created:
            print(f"  ✓ Chart saved")

        # Store results
        results.append({
            'scheme_code': scheme_code,
            'scheme_name': scheme_name,
            'current_nav': current_nav,
            'current_date': current_date,
            'predicted_nav_6m': predicted_nav,
            'predicted_nav_lower': predicted_lower,
            'predicted_nav_upper': predicted_upper,
            'expected_return_6m': expected_return,
            'expected_return_lower': expected_return_lower,
            'expected_return_upper': expected_return_upper,
            'mae': metrics['mae'],
            'rmse': metrics['rmse'],
            'mape': metrics['mape'],
            'r2_score': metrics['r2_score']
        })

        successful += 1
        print()

    return results, successful, failed


def save_results(results):
    """Save prediction results"""

    print("=" * 70)
    print("SAVING RESULTS")
    print("=" * 70)

    # Create DataFrame
    results_df = pd.DataFrame(results)

    # Save detailed results
    output_file = '../results/prediction_results.csv'
    results_df.to_csv(output_file, index=False)
    print(f"✓ Saved detailed results: {output_file}")

    # Create summary statistics
    summary = {
        'Total Funds': len(results_df),
        'Average Expected Return': results_df['expected_return_6m'].mean(),
        'Median Expected Return': results_df['expected_return_6m'].median(),
        'Best Predicted Return': results_df['expected_return_6m'].max(),
        'Worst Predicted Return': results_df['expected_return_6m'].min(),
        'Average MAPE': results_df['mape'].mean(),
        'Average R² Score': results_df['r2_score'].mean()
    }

    # Save summary
    summary_file = '../results/prediction_summary.txt'
    with open(summary_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("PREDICTION SUMMARY STATISTICS\n")
        f.write("=" * 70 + "\n\n")

        for key, value in summary.items():
            f.write(f"{key:30s}: {value:.2f}\n")

        f.write("\n" + "=" * 70 + "\n")
        f.write("TOP 10 PREDICTED PERFORMERS (6-Month Expected Return)\n")
        f.write("=" * 70 + "\n\n")

        top_10 = results_df.nlargest(10, 'expected_return_6m')
        for idx, row in top_10.iterrows():
            f.write(f"{row['scheme_name'][:60]}\n")
            f.write(f"  Expected Return: {row['expected_return_6m']:.2f}% ")
            f.write(f"(Range: {row['expected_return_lower']:.2f}% to {row['expected_return_upper']:.2f}%)\n")
            f.write(f"  Current NAV: {row['current_nav']:.2f} → Predicted: {row['predicted_nav_6m']:.2f}\n")
            f.write(f"  Model Accuracy (MAPE): {row['mape']:.2f}%\n\n")

        f.write("=" * 70 + "\n")
        f.write("BOTTOM 10 PREDICTED PERFORMERS\n")
        f.write("=" * 70 + "\n\n")

        bottom_10 = results_df.nsmallest(10, 'expected_return_6m')
        for idx, row in bottom_10.iterrows():
            f.write(f"{row['scheme_name'][:60]}\n")
            f.write(f"  Expected Return: {row['expected_return_6m']:.2f}% ")
            f.write(f"(Range: {row['expected_return_lower']:.2f}% to {row['expected_return_upper']:.2f}%)\n")
            f.write(f"  Model Accuracy (MAPE): {row['mape']:.2f}%\n\n")

    print(f"✓ Saved summary report: {summary_file}")

    return results_df, summary


def create_summary_visualizations(results_df):
    """Create summary charts"""

    # FIX: Remove any infinite or NaN values
    results_df = results_df.replace([np.inf, -np.inf], np.nan)
    results_df = results_df.dropna(subset=['mape', 'r2_score', 'expected_return_6m'])

    print("\n" + "=" * 70)
    print("CREATING SUMMARY VISUALIZATIONS")
    print("=" * 70)

    # Set style
    sns.set_style("whitegrid")

    # Create figure with subplots
    fig = plt.figure(figsize=(16, 10))

    # Plot 1: Distribution of predicted returns
    ax1 = plt.subplot(2, 3, 1)
    ax1.hist(results_df['expected_return_6m'], bins=20,
             color='steelblue', edgecolor='black', alpha=0.7)
    ax1.axvline(results_df['expected_return_6m'].mean(),
                color='red', linestyle='--', linewidth=2, label='Mean')
    ax1.axvline(results_df['expected_return_6m'].median(),
                color='green', linestyle='--', linewidth=2, label='Median')
    ax1.set_xlabel('Predicted 6-Month Return (%)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Number of Funds', fontsize=11, fontweight='bold')
    ax1.set_title('Distribution of Predicted Returns', fontsize=13, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Top 10 predicted performers
    ax2 = plt.subplot(2, 3, 2)
    top_10 = results_df.nlargest(10, 'expected_return_6m')
    colors = ['green' if x > 0 else 'red' for x in top_10['expected_return_6m']]
    ax2.barh(range(len(top_10)), top_10['expected_return_6m'], color=colors, edgecolor='black')
    ax2.set_yticks(range(len(top_10)))
    ax2.set_yticklabels([name[:30] for name in top_10['scheme_name']], fontsize=8)
    ax2.set_xlabel('Predicted 6M Return (%)', fontsize=11, fontweight='bold')
    ax2.set_title('Top 10 Predicted Performers', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')

    # Plot 3: Bottom 10 predicted performers
    ax3 = plt.subplot(2, 3, 3)
    bottom_10 = results_df.nsmallest(10, 'expected_return_6m')
    colors = ['green' if x > 0 else 'red' for x in bottom_10['expected_return_6m']]
    ax3.barh(range(len(bottom_10)), bottom_10['expected_return_6m'], color=colors, edgecolor='black')
    ax3.set_yticks(range(len(bottom_10)))
    ax3.set_yticklabels([name[:30] for name in bottom_10['scheme_name']], fontsize=8)
    ax3.set_xlabel('Predicted 6M Return (%)', fontsize=11, fontweight='bold')
    ax3.set_title('Bottom 10 Predicted Performers', fontsize=13, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='x')

    # Plot 4: Model accuracy distribution (MAPE)
    ax4 = plt.subplot(2, 3, 4)
    ax4.hist(results_df['mape'], bins=20, color='orange', edgecolor='black', alpha=0.7)
    ax4.axvline(results_df['mape'].mean(), color='red', linestyle='--', linewidth=2, label='Mean')
    ax4.set_xlabel('MAPE (%)', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Number of Funds', fontsize=11, fontweight='bold')
    ax4.set_title('Model Accuracy Distribution (Lower is Better)', fontsize=13, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    # Plot 5: R² Score distribution
    ax5 = plt.subplot(2, 3, 5)
    ax5.hist(results_df['r2_score'], bins=20, color='purple', edgecolor='black', alpha=0.7)
    ax5.axvline(results_df['r2_score'].mean(), color='red', linestyle='--', linewidth=2, label='Mean')
    ax5.set_xlabel('R² Score', fontsize=11, fontweight='bold')
    ax5.set_ylabel('Number of Funds', fontsize=11, fontweight='bold')
    ax5.set_title('Model Fit Distribution (Higher is Better)', fontsize=13, fontweight='bold')
    ax5.legend()
    ax5.grid(True, alpha=0.3)

    # Plot 6: Scatter - Predicted return vs Model accuracy
    ax6 = plt.subplot(2, 3, 6)
    scatter = ax6.scatter(results_df['expected_return_6m'], results_df['mape'],
                          c=results_df['r2_score'], cmap='RdYlGn',
                          s=100, alpha=0.6, edgecolors='black')
    ax6.set_xlabel('Predicted 6M Return (%)', fontsize=11, fontweight='bold')
    ax6.set_ylabel('MAPE (%)', fontsize=11, fontweight='bold')
    ax6.set_title('Return vs Accuracy (Color = R² Score)', fontsize=13, fontweight='bold')
    plt.colorbar(scatter, ax=ax6, label='R² Score')
    ax6.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('../results/prediction_summary_charts.png', dpi=300, bbox_inches='tight')
    print("✓ Saved summary visualization: results/prediction_summary_charts.png")
    plt.close()


def main():
    """Main execution"""

    # Create results directories
    os.makedirs('../results', exist_ok=True)
    os.makedirs('../results/predictions', exist_ok=True)

    # Process all funds
    results, successful, failed = process_all_funds()

    if len(results) == 0:
        print("\n✗ No predictions generated!")
        return

    # Save results
    results_df, summary = save_results(results)

    # Create summary visualizations
    create_summary_visualizations(results_df)

    # Final summary
    print("\n" + "=" * 70)
    print("✓ PREDICTION COMPLETE!")
    print("=" * 70)

    print(f"\nSummary:")
    print(f"   • Total funds processed: {successful + failed}")
    print(f"   • Successful predictions: {successful}")
    print(f"   • Failed: {failed}")
    print(f"   • Average predicted 6M return: {summary['Average Expected Return']:.2f}%")
    print(f"   • Average model accuracy (MAPE): {summary['Average MAPE']:.2f}%")

    print(f"\nOutput files:")
    print(f"   • prediction_results.csv (detailed predictions)")
    print(f"   • prediction_summary.txt (text report)")
    print(f"   • prediction_summary_charts.png (overview charts)")
    print(f"   • predictions/ folder ({successful} individual fund charts)")

if __name__ == "__main__":
    main()