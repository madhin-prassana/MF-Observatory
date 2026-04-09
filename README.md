# Vantage . - Mutual Fund Analysis Platform

Vantage . is a full-stack machine learning platform designed to analyze mutual funds, perform risk-based clustering, detect performance anomalies, and predict future returns using a hybrid ensemble of LSTM and Prophet models.

## Features

*   **Risk Clustering:** Categorizes funds into five distinct risk levels using K-Means clustering based on market behavior patterns, including volatility, drawdowns, and Sharpe ratios.
*   **Performance Prediction:** Utilizes a hybrid forecasting approach comparing Facebook Prophet and LSTM models. The system selects the optimal model per fund to predict six-month expected returns and Net Asset Values (NAV) with high-confidence intervals.
*   **Anomaly Detection:** Systematically scans historical NAV records to identify statistical irregularities, sudden performance drops, or high-risk volatility spikes using Z-score analysis.
*   **Modern Analytics Dashboard:** A high-performance interface built with React and Tailwind CSS, featuring interactive financial visualizations and ML model performance metrics.

## Technical Stack

### Frontend Development
*   **Framework:** React.js (v19)
*   **Styling:** Tailwind CSS (v3)
*   **Data Visualization:** Recharts
*   **Routing:** React Router (v7)
*   **API Integration:** Axios
*   **Runtime Environment:** Node.js (Frontend build pipeline and development server)

### Backend Engineering
*   **Framework:** FastAPI (Python)
*   **Server:** Uvicorn (ASGI)
*   **Architecture:** RESTful API with modular routing and CORS middleware configuration

### Machine Learning and Data Science
*   **Deep Learning Modeling:** LSTM (Long Short-Term Memory) networks implemented via TensorFlow/Keras for complex time-series forecasting.
*   **Time-Series Analysis:** Facebook Prophet for robust trend identification and seasonal forecasting.
*   **Unsupervised Learning:** Scikit-learn (K-Means Clustering) for risk assessment and fund categorization.
*   **Data Manipulation:** Pandas and NumPy for advanced feature engineering and metrics calculation.
*   **Statistical Analysis:** Z-score based Anomaly Detection for performance risk monitoring.

### Infrastructure and Tools
*   **Version Control:** Git
*   **Environment Management:** Python Virtual Environments (venv)
*   **Package Management:** npm (JavaScript) and pip (Python)
*   **Data Storage:** CSV-based local data architecture

## Execution Instructions

To run the platform, both the Python backend and the React frontend must be operational in parallel.

### 1. Backend Server Initialization
Navigate to the project root and start the FastAPI server:

```bash
# Activate the Python virtual environment
source .venv/bin/activate

# Start the FastAPI server on port 8000
uvicorn backend.main:app --reload --port 8000
```

### 2. Frontend Application Initialization
Open a separate terminal window and start the React development server:

```bash
# Navigate to the frontend directory
cd frontend

# Initialize the application
npm start
```

The dashboard will be accessible via browser at `http://localhost:3000`.

## Project Structure

```text
MutualFunds_ML/
├── backend/            # FastAPI application logic and routers
├── frontend/           # React application and UI components
├── scripts/            # Machine Learning training and data processing scripts
├── data/               # Raw and processed datasets
├── results/            # Model outputs and visualization results
└── README.md           # Project documentation
```
