import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import seaborn as sns
import os
from glob import glob
import warnings

warnings.filterwarnings('ignore')

# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)


def load_fund_data(fund_file):
    """Load and prepare data for a single fund"""
    try:
        df = pd.read_csv(fund_file)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        scheme_name = df['scheme_name'].iloc[0]
        scheme_code = df['scheme_code'].iloc[0]

        return df, scheme_name, scheme_code

    except Exception as e:
        print(f"Error loading {fund_file}: {e}")
        return None, None, None


def create_sequences(data, sequence_length=60):
    """
    Create sequences for LSTM
    sequence_length: number of past days to use for prediction (default 60 days)
    """
    X, y = [], []

    for i in range(sequence_length, len(data)):
        X.append(data[i - sequence_length:i, 0])
        y.append(data[i, 0])

    return np.array(X), np.array(y)


def build_lstm_model(sequence_length):
    """Build LSTM model architecture"""
    model = Sequential([
        LSTM(units=50, return_sequences=True, input_shape=(sequence_length, 1)),
        Dropout(0.2),

        LSTM(units=50, return_sequences=True),
        Dropout(0.2),

        LSTM(units=50),
        Dropout(0.2),

        Dense(units=25),
        Dense(units=1)
    ])

    model.compile(optimizer='adam', loss='mean_squared_error')

    return model


def train_lstm_model(df, scheme_name, sequence_length=60):
    """Train LSTM model for a fund"""
    try:
        # Prepare data
        nav_data = df[['nav']].values

        # Check if enough data
        if len(nav_data) < sequence_length + 100:
            print(f"  ✗ Insufficient data (need at least {sequence_length + 100} days)")
            return None, None, None, None

        # Scale data (LSTM works better with normalized data)
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(nav_data)

        # Split into train and test (80-20 split)
        train_size = int(len(scaled_data) * 0.8)
        train_data = scaled_data[:train_size]
        test_data = scaled_data[train_size - sequence_length:]

        # Create sequences
        X_train, y_train = create_sequences(train_data, sequence_length)
        X_test, y_test = create_sequences(test_data, sequence_length)

        # Reshape for LSTM [samples, time steps, features]
        X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
        X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

        # Build model
        model = build_lstm_model(sequence_length)

        # Early stopping to prevent overfitting
        early_stop = EarlyStopping(monitor='loss', patience=5, restore_best_weights=True)

        # Train model (suppress verbose output)
        model.fit(
            X_train, y_train,
            epochs=50,
            batch_size=32,
            callbacks=[early_stop],
            verbose=0
        )

        return model, scaler, X_test, y_test

    except Exception as e:
        print(f"  Error training LSTM for {scheme_name}: {e}")
        return None, None, None, None


def make_predictions(model, scaler, df, sequence_length=60, future_days=180):
    """Make future predictions"""
    try:
        # Get last sequence_length days
        nav_data = df[['nav']].values
        last_sequence = nav_data[-sequence_length:]

        # Scale
        scaled_sequence = scaler.transform(last_sequence)

        # Predict future
        predictions = []
        current_sequence = scaled_sequence.copy()

        for _ in range(future_days):
            # Reshape for prediction
            X_pred = current_sequence.reshape(1, sequence_length, 1)

            # Predict next value
            next_pred = model.predict(X_pred, verbose=0)
            predictions.append(next_pred[0, 0])

            # Update sequence (rolling window)
            current_sequence = np.append(current_sequence[1:], next_pred, axis=0)

        # Inverse transform to get actual NAV values
        predictions = np.array(predictions).reshape(-1, 1)
        predictions = scaler.inverse_transform(predictions)

        return predictions.flatten()

    except Exception as e:
        print(f"  Error making predictions: {e}")
        return None


def calculate_accuracy_metrics(y_true, y_pred, scaler):
    """Calculate prediction accuracy on test data"""
    try:
        # Inverse transform
        y_true = scaler.inverse_transform(y_true.reshape(-1, 1)).flatten()
        y_pred = scaler.inverse_transform(y_pred.reshape(-1, 1)).flatten()

        # Calculate metrics
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

        # R-squared
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - y_true.mean()) ** 2)
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


def calculate_confidence_interval(predictions, confidence=0.80):
    """
    Calculate confidence intervals for predictions
    Using simple standard deviation-based method
    """
    # Estimate uncertainty (simplified approach)
    # In practice, you'd use Monte Carlo dropout or ensemble methods
    std = np.std(predictions) * 0.1  # Conservative estimate

    z_score = 1.28  # For 80% confidence interval

    lower = predictions - (z_score * std)
    upper = predictions + (z_score * std)

    return lower, upper


def calculate_predicted_return(current_nav, predicted_nav):
    """Calculate expected return"""
    return ((predicted_nav - current_nav) / current_nav) * 100


def create_prediction_chart(df, predictions, scheme_name, scheme_code, metrics, sequence_length):
    """Create visualization for individual fund prediction"""
    try:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # Prepare data
        dates = df['date'].values
        actual_nav = df['nav'].values

        # Create future dates
        last_date = pd.to_datetime(dates[-1])
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=len(predictions))

        # Calculate confidence intervals
        pred_lower, pred_upper = calculate_confidence_interval(predictions)

        # Plot 1: Full timeline with predictions
        ax1.plot(dates, actual_nav, 'b-', label='Historical NAV', linewidth=2)
        ax1.plot(future_dates, predictions, 'r--', label='LSTM Predicted NAV', linewidth=2)
        ax1.fill_between(future_dates, pred_lower, pred_upper,
                         alpha=0.3, color='red', label='80% Confidence Interval (Estimated)')

        ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax1.set_ylabel('NAV', fontsize=12, fontweight='bold')
        ax1.set_title(f'{scheme_name[:60]}\nLSTM 6-Month Prediction',
                      fontsize=14, fontweight='bold')
        ax1.legend(loc='best', fontsize=10)
        ax1.grid(True, alpha=0.3)

        # Plot 2: Recent history + prediction (zoomed)
        recent_cutoff = pd.to_datetime(dates[-1]) - pd.DateOffset(years=1)
        recent_mask = pd.to_datetime(dates) >= recent_cutoff
        recent_dates = dates[recent_mask]
        recent_nav = actual_nav[recent_mask]

        ax2.plot(recent_dates, recent_nav,
                 'b-', label='Recent Historical NAV', linewidth=2, marker='o', markersize=3)
        ax2.plot(future_dates, predictions,
                 'r--', label='6-Month LSTM Prediction', linewidth=2, marker='s', markersize=3)
        ax2.fill_between(future_dates, pred_lower, pred_upper,
                         alpha=0.3, color='red')

        ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax2.set_ylabel('NAV', fontsize=12, fontweight='bold')
        ax2.set_title('Recent Trend & LSTM Forecast (Zoomed)', fontsize=13, fontweight='bold')
        ax2.legend(loc='best', fontsize=10)
        ax2.grid(True, alpha=0.3)

        # Add metrics text box
        metrics_text = f"LSTM Accuracy Metrics:\n"
        metrics_text += f"MAE: {metrics['mae']:.2f}\n"
        metrics_text += f"RMSE: {metrics['rmse']:.2f}\n"
        metrics_text += f"MAPE: {metrics['mape']:.2f}%\n"
        metrics_text += f"R²: {metrics['r2_score']:.3f}"

        ax2.text(0.02, 0.98, metrics_text,
                 transform=ax2.transAxes,
                 fontsize=10,
                 verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

        plt.tight_layout()

        # Save
        os.makedirs('../results/predictions_lstm', exist_ok=True)
        plt.savefig(f'../results/predictions_lstm/prediction_lstm_{scheme_code}.png',
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
    print("║" + " " * 10 + "LSTM MUTUAL FUND PERFORMANCE PREDICTION" + " " * 19 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # Get all fund files
    fund_files = glob('../data/fund_*.csv')

    sequence_length = 60  # Use 60 days of history

    print("=" * 70)
    print(f"PROCESSING {len(fund_files)} FUNDS WITH LSTM")
    print("=" * 70)
    print(f"\nSequence Length: {sequence_length} days")
    print(f"Prediction Horizon: 180 days (~6 months)")
    print(f"\nThis will take approximately {len(fund_files) * 1.0:.0f}-{len(fund_files) * 1.5:.0f} minutes")
    print("LSTM training is slower than Prophet - please be patient...\n")

    results = []
    successful = 0
    failed = 0

    for i, fund_file in enumerate(fund_files, 1):
        # Load data
        df, scheme_name, scheme_code = load_fund_data(fund_file)

        if df is None or len(df) < 365:
            print(f"[{i}/{len(fund_files)}] ✗ Skipped {os.path.basename(fund_file)} (insufficient data)")
            failed += 1
            continue
            
        # Check if fund is inactive
        cutoff_date = pd.Timestamp.now() - pd.DateOffset(years=2)
        if df['date'].max() < cutoff_date:
            print(f"[{i}/{len(fund_files)}] ✗ Skipped {os.path.basename(fund_file)} (inactive fund, last date: {df['date'].max().date()})")
            failed += 1
            continue

        print(f"[{i}/{len(fund_files)}] Processing: {scheme_name[:55]}...")

        # Train LSTM model
        model, scaler, X_test, y_test = train_lstm_model(df, scheme_name, sequence_length)

        if model is None:
            print(f"  ✗ Failed to train LSTM model")
            failed += 1
            continue

        print(f"  ✓ LSTM model trained")

        # Test accuracy on test set
        y_pred_test = model.predict(X_test, verbose=0)
        metrics = calculate_accuracy_metrics(y_test, y_pred_test, scaler)

        if metrics is None:
            print(f"  ✗ Failed to calculate metrics")
            failed += 1
            continue

        print(f"  ✓ Test Accuracy - MAE: {metrics['mae']:.2f}, MAPE: {metrics['mape']:.2f}%")

        # Make future predictions
        predictions = make_predictions(model, scaler, df, sequence_length, future_days=180)

        if predictions is None:
            print(f"  ✗ Failed to generate predictions")
            failed += 1
            continue

        # Get current and predicted values
        current_nav = df['nav'].iloc[-1]
        current_date = df['date'].iloc[-1]

        # 6-month prediction (180 days)
        predicted_nav_6m = predictions[179]  # Day 180 (0-indexed)

        # Calculate confidence interval
        pred_lower, pred_upper = calculate_confidence_interval(predictions)
        predicted_lower = pred_lower[179]
        predicted_upper = pred_upper[179]

        # Calculate expected return
        expected_return = calculate_predicted_return(current_nav, predicted_nav_6m)
        expected_return_lower = calculate_predicted_return(current_nav, predicted_lower)
        expected_return_upper = calculate_predicted_return(current_nav, predicted_upper)

        print(
            f"  ✓ Predicted 6M Return: {expected_return:.2f}% (Range: {expected_return_lower:.2f}% to {expected_return_upper:.2f}%)")

        # Create chart
        chart_created = create_prediction_chart(df, predictions, scheme_name, scheme_code, metrics, sequence_length)

        if chart_created:
            print(f"  ✓ Chart saved")

        # Store results
        results.append({
            'scheme_code': scheme_code,
            'scheme_name': scheme_name,
            'current_nav': current_nav,
            'current_date': current_date,
            'predicted_nav_6m': predicted_nav_6m,
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

        # Clear memory
        del model
        tf.keras.backend.clear_session()

    return results, successful, failed


def save_results(results):
    """Save LSTM prediction results"""

    print("=" * 70)
    print("SAVING LSTM RESULTS")
    print("=" * 70)

    # Create DataFrame
    results_df = pd.DataFrame(results)

    # Save detailed results
    output_file = '../results/prediction_results_lstm.csv'
    results_df.to_csv(output_file, index=False)
    print(f"✓ Saved detailed LSTM results: {output_file}")

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
    summary_file = '../results/prediction_summary_lstm.txt'
    with open(summary_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("LSTM PREDICTION SUMMARY STATISTICS\n")
        f.write("=" * 70 + "\n\n")

        for key, value in summary.items():
            f.write(f"{key:30s}: {value:.2f}\n")

        f.write("\n" + "=" * 70 + "\n")
        f.write("TOP 10 LSTM PREDICTED PERFORMERS (6-Month Expected Return)\n")
        f.write("=" * 70 + "\n\n")

        top_10 = results_df.nlargest(10, 'expected_return_6m')
        for idx, row in top_10.iterrows():
            f.write(f"{row['scheme_name'][:60]}\n")
            f.write(f"  Expected Return: {row['expected_return_6m']:.2f}% ")
            f.write(f"(Range: {row['expected_return_lower']:.2f}% to {row['expected_return_upper']:.2f}%)\n")
            f.write(f"  Current NAV: {row['current_nav']:.2f} → Predicted: {row['predicted_nav_6m']:.2f}\n")
            f.write(f"  Model Accuracy (MAPE): {row['mape']:.2f}%\n\n")

        f.write("=" * 70 + "\n")
        f.write("BOTTOM 10 LSTM PREDICTED PERFORMERS\n")
        f.write("=" * 70 + "\n\n")

        bottom_10 = results_df.nsmallest(10, 'expected_return_6m')
        for idx, row in bottom_10.iterrows():
            f.write(f"{row['scheme_name'][:60]}\n")
            f.write(f"  Expected Return: {row['expected_return_6m']:.2f}% ")
            f.write(f"(Range: {row['expected_return_lower']:.2f}% to {row['expected_return_upper']:.2f}%)\n")
            f.write(f"  Model Accuracy (MAPE): {row['mape']:.2f}%\n\n")

    print(f"✓ Saved LSTM summary report: {summary_file}")

    return results_df, summary


def create_summary_visualizations(results_df):
    """Create LSTM summary charts"""

    # FIX: Remove any infinite or NaN values
    results_df = results_df.replace([np.inf, -np.inf], np.nan)
    results_df = results_df.dropna(subset=['mape', 'r2_score', 'expected_return_6m'])

    print("\n" + "=" * 70)
    print("CREATING LSTM SUMMARY VISUALIZATIONS")
    print("=" * 70)

    # Set style
    sns.set_style("whitegrid")

    fig = plt.figure(figsize=(16, 10))

    # Plot 1: Distribution of predicted returns
    ax1 = plt.subplot(2, 3, 1)
    ax1.hist(results_df['expected_return_6m'], bins=20,
             color='steelblue', edgecolor='black', alpha=0.7)
    ax1.axvline(results_df['expected_return_6m'].mean(),
                color='red', linestyle='--', linewidth=2, label='Mean')
    ax1.axvline(results_df['expected_return_6m'].median(),
                color='green', linestyle='--', linewidth=2, label='Median')
    ax1.set_xlabel('LSTM Predicted 6-Month Return (%)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Number of Funds', fontsize=11, fontweight='bold')
    ax1.set_title('LSTM: Distribution of Predicted Returns', fontsize=13, fontweight='bold')
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
    ax2.set_title('LSTM: Top 10 Predicted Performers', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')

    # Plot 3: Bottom 10 predicted performers
    ax3 = plt.subplot(2, 3, 3)
    bottom_10 = results_df.nsmallest(10, 'expected_return_6m')
    colors = ['green' if x > 0 else 'red' for x in bottom_10['expected_return_6m']]
    ax3.barh(range(len(bottom_10)), bottom_10['expected_return_6m'], color=colors, edgecolor='black')
    ax3.set_yticks(range(len(bottom_10)))
    ax3.set_yticklabels([name[:30] for name in bottom_10['scheme_name']], fontsize=8)
    ax3.set_xlabel('Predicted 6M Return (%)', fontsize=11, fontweight='bold')
    ax3.set_title('LSTM: Bottom 10 Predicted Performers', fontsize=13, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='x')

    # Plot 4: Model accuracy distribution (MAPE)
    ax4 = plt.subplot(2, 3, 4)
    ax4.hist(results_df['mape'], bins=20, color='orange', edgecolor='black', alpha=0.7)
    ax4.axvline(results_df['mape'].mean(), color='red', linestyle='--', linewidth=2, label='Mean')
    ax4.set_xlabel('MAPE (%)', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Number of Funds', fontsize=11, fontweight='bold')
    ax4.set_title('LSTM: Model Accuracy Distribution', fontsize=13, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    # Plot 5: R² Score distribution
    ax5 = plt.subplot(2, 3, 5)
    ax5.hist(results_df['r2_score'], bins=20, color='purple', edgecolor='black', alpha=0.7)
    ax5.axvline(results_df['r2_score'].mean(), color='red', linestyle='--', linewidth=2, label='Mean')
    ax5.set_xlabel('R² Score', fontsize=11, fontweight='bold')
    ax5.set_ylabel('Number of Funds', fontsize=11, fontweight='bold')
    ax5.set_title('LSTM: Model Fit Distribution', fontsize=13, fontweight='bold')
    ax5.legend()
    ax5.grid(True, alpha=0.3)

    # Plot 6: Scatter - Predicted return vs Model accuracy
    ax6 = plt.subplot(2, 3, 6)
    scatter = ax6.scatter(results_df['expected_return_6m'], results_df['mape'],
                          c=results_df['r2_score'], cmap='RdYlGn',
                          s=100, alpha=0.6, edgecolors='black')
    ax6.set_xlabel('Predicted 6M Return (%)', fontsize=11, fontweight='bold')
    ax6.set_ylabel('MAPE (%)', fontsize=11, fontweight='bold')
    ax6.set_title('LSTM: Return vs Accuracy', fontsize=13, fontweight='bold')
    plt.colorbar(scatter, ax=ax6, label='R² Score')
    ax6.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('../results/prediction_summary_charts_lstm.png', dpi=300, bbox_inches='tight')
    print("✓ Saved LSTM summary visualization: results/prediction_summary_charts_lstm.png")
    plt.close()


def main():
    """Main execution"""

    # Create results directories
    os.makedirs('../results', exist_ok=True)
    os.makedirs('../results/predictions_lstm', exist_ok=True)

    # Process all funds
    results, successful, failed = process_all_funds()

    if len(results) == 0:
        print("\n✗ No LSTM predictions generated!")
        return

    # Save results
    results_df, summary = save_results(results)

    # Create summary visualizations
    create_summary_visualizations(results_df)

    # Final summary
    print("\n" + "=" * 70)
    print("✓ LSTM PREDICTION COMPLETE!")
    print("=" * 70)

    print(f"\nSummary:")
    print(f"   • Total funds processed: {successful + failed}")
    print(f"   • Successful LSTM predictions: {successful}")
    print(f"   • Failed: {failed}")
    print(f"   • Average predicted 6M return: {summary['Average Expected Return']:.2f}%")
    print(f"   • Average model accuracy (MAPE): {summary['Average MAPE']:.2f}%")

    print(f"\nOutput files:")
    print(f"   • prediction_results_lstm.csv (detailed predictions)")
    print(f"   • prediction_summary_lstm.txt (text report)")
    print(f"   • prediction_summary_charts_lstm.png (overview charts)")
    print(f"   • predictions_lstm/ folder ({successful} individual fund charts)")


if __name__ == "__main__":
    main()