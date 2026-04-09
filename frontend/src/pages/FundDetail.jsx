import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getFundByCode, getPredictions, getHistoricalNav } from '../services/api';
import MetricCard from '../components/MetricCard';
import LoadingSpinner from '../components/LoadingSpinner';

const FundDetail = () => {
  const { schemeCode } = useParams();
  const navigate = useNavigate();
  const [fund, setFund] = useState(null);
  const [predictions, setPredictions] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [fundRes, predRes, histRes] = await Promise.allSettled([
          getFundByCode(schemeCode),
          getPredictions(schemeCode),
          getHistoricalNav(schemeCode),
        ]);

        if (fundRes.status === 'fulfilled') setFund(fundRes.value.data);
        else setError('Fund not found');

        if (predRes.status === 'fulfilled') setPredictions(predRes.value.data);
        if (histRes.status === 'fulfilled') setHistoricalData(histRes.value.data.data || []);
      } catch (err) {
        setError('Failed to load fund details');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [schemeCode]);

  const getRiskBadge = (category) => {
    const map = {
      'Very Low Risk': 'badge-low-risk',
      'Low Risk': 'badge-low-risk',
      'Moderate Risk': 'badge-moderate-risk',
      'High Risk': 'badge-high-risk',
      'Very High Risk': 'badge-high-risk',
    };
    return map[category] || 'badge-moderate-risk';
  };

  const getAnomalyStyle = (category) => {
    const map = {
      'Normal': { color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/20', icon: '✓', label: 'Normal' },
      'Performance Issue': { color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20', icon: '⚠', label: 'Performance Issue' },
      'Risk Issue': { color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/20', icon: '⚠', label: 'Risk Issue' },
      'High Priority': { color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/20', icon: '🚨', label: 'High Priority' },
    };
    return map[category] || map['Normal'];
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass-card p-3 text-sm">
          <p className="text-gray-400 mb-1">{label}</p>
          <p className="text-blue-400 font-semibold">NAV: ₹{payload[0].value?.toFixed(2)}</p>
        </div>
      );
    }
    return null;
  };

  if (loading) return <LoadingSpinner message="Loading fund details..." />;

  if (error || !fund) {
    return (
      <div className="min-h-screen bg-[#0f1117] flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">😕</div>
          <h2 className="text-2xl font-bold text-white mb-2">Fund Not Found</h2>
          <p className="text-gray-400 mb-6">{error || 'The requested fund could not be loaded.'}</p>
          <button
            onClick={() => navigate('/explorer')}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-lg transition-colors"
          >
            Back to Explorer
          </button>
        </div>
      </div>
    );
  }

  const anomaly = getAnomalyStyle(fund.anomaly_category);

  return (
    <div className="min-h-screen bg-[#0f1117]">
      {/* Hero Header */}
      <div className="bg-gradient-to-br from-[#151829] to-[#0f1117] border-b border-white/5">
        <div className="container mx-auto px-4 py-10">
          {/* Back Button */}
          <button
            onClick={() => navigate('/explorer')}
            className="flex items-center text-gray-400 hover:text-white transition-colors mb-6 group"
          >
            <svg className="w-5 h-5 mr-2 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Explorer
          </button>

          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3 flex-wrap">
                <span className={getRiskBadge(fund.risk_category)}>{fund.risk_category}</span>
                <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold border ${anomaly.bg} ${anomaly.color}`}>
                  {anomaly.icon} {anomaly.label}
                </span>
              </div>
              <h1 className="text-3xl lg:text-4xl font-bold text-white mb-2">{fund.scheme_name}</h1>
              <p className="text-gray-400 text-sm">Scheme Code: {fund.scheme_code}</p>
            </div>

            {/* Quick Stats */}
            <div className="flex gap-6 items-center">
              <div className="text-center">
                <div className="text-sm text-gray-400 mb-1">Current NAV</div>
                <div className="text-2xl font-bold text-white">
                  {fund.latest_nav !== null && fund.latest_nav !== undefined ? `₹${fund.latest_nav.toFixed(2)}` : 'N/A'}
                </div>
              </div>
              <div className="w-px h-12 bg-white/10"></div>
              <div className="text-center">
                <div className="text-sm text-gray-400 mb-1">Predicted Return</div>
                <div className={`text-2xl font-bold ${fund.recommended_return >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {fund.recommended_return !== null && fund.recommended_return !== undefined ? `${fund.recommended_return.toFixed(2)}%` : 'N/A'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 space-y-8">
        {/* Key Metrics Grid */}
        <div>
          <h2 className="text-xl font-bold text-white mb-4">Key Metrics</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <MetricCard label="Latest NAV" value={fund.latest_nav !== null && fund.latest_nav !== undefined ? `₹${fund.latest_nav.toFixed(2)}` : 'N/A'}  color="blue" />
            <MetricCard label="Volatility" value={fund.volatility !== null && fund.volatility !== undefined ? `${fund.volatility.toFixed(2)}%` : 'N/A'}  color="orange" />
            <MetricCard label="Sharpe Ratio" value={fund.sharpe_ratio !== null && fund.sharpe_ratio !== undefined ? fund.sharpe_ratio.toFixed(3) : 'N/A'}  color="purple" />
            <MetricCard label="Max Drawdown" value={fund.max_drawdown !== null && fund.max_drawdown !== undefined ? `${fund.max_drawdown.toFixed(2)}%` : 'N/A'}  color="red" />
            <MetricCard label="1Y Return" value={fund.return_1y !== null && fund.return_1y !== undefined ? `${fund.return_1y.toFixed(2)}%` : 'N/A'}  color="green" trend={fund.return_1y} />
            <MetricCard label="Cluster" value={fund.cluster !== null ? `#${fund.cluster}` : 'N/A'} color="cyan" />
          </div>
        </div>

        {/* Historical NAV Chart */}
        {historicalData.length > 0 && (
          <div className="glass-card p-6">
            <h2 className="text-xl font-bold text-white mb-6">Historical NAV (Last 2 Years)</h2>
            <div className="h-[350px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={historicalData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                  <defs>
                    <linearGradient id="navGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis
                    dataKey="date"
                    stroke="#4b5563"
                    tick={{ fill: '#6b7280', fontSize: 11 }}
                    tickFormatter={(d) => {
                      const date = new Date(d);
                      return date.toLocaleDateString('en-IN', { month: 'short', year: '2-digit' });
                    }}
                    interval="preserveStartEnd"
                    minTickGap={50}
                  />
                  <YAxis
                    stroke="#4b5563"
                    tick={{ fill: '#6b7280', fontSize: 11 }}
                    domain={['auto', 'auto']}
                    tickFormatter={(v) => `₹${v.toFixed(0)}`}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="nav"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    fill="url(#navGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Prediction Panel */}
        {predictions && (
          <div>
            <h2 className="text-xl font-bold text-white mb-4">ML Predictions (6-Month Outlook)</h2>

            {/* Ensemble Recommendation Banner */}
            <div className="glass-card p-5 mb-4 border-l-4 border-l-blue-500">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <div className="text-xs text-blue-400 font-semibold uppercase tracking-wider mb-1">
                    Recommended Model
                  </div>
                  <div className="text-lg font-bold text-white">{predictions.recommended_model}</div>
                  <div className="text-sm text-gray-400 mt-1">
                    MAPE: {predictions.recommended_mape !== null && predictions.recommended_mape !== undefined ? `${predictions.recommended_mape.toFixed(3)}%` : 'N/A'}
                  </div>
                </div>
                <div className="text-center md:text-right">
                  <div className="text-sm text-gray-400">Expected Return</div>
                  <div className={`text-3xl font-bold ${predictions.recommended_return >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {predictions.recommended_return !== null && predictions.recommended_return !== undefined ? `${predictions.recommended_return.toFixed(2)}%` : 'N/A'}
                  </div>
                </div>
              </div>
            </div>

            {/* Model Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Prophet Card */}
              {predictions.prophet && (
                <div className={`glass-card p-5 ${predictions.recommended_model === 'Prophet' ? 'ring-1 ring-blue-500/40' : ''}`}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                      Prophet
                    </h3>
                    {predictions.recommended_model === 'Prophet' && (
                      <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded-full font-medium">Best Model</span>
                    )}
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Predicted Return</span>
                      <span className={`font-semibold ${predictions.prophet.predicted_return_6m >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {predictions.prophet.predicted_return_6m !== null && predictions.prophet.predicted_return_6m !== undefined ? `${predictions.prophet.predicted_return_6m.toFixed(2)}%` : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Predicted NAV</span>
                      <span className="text-white font-medium">
                        {predictions.prophet.predicted_nav_6m !== null && predictions.prophet.predicted_nav_6m !== undefined ? `₹${predictions.prophet.predicted_nav_6m.toFixed(2)}` : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Confidence Range</span>
                      <span className="text-gray-300 text-xs">
                        {predictions.prophet.confidence_lower !== null ? `${predictions.prophet.confidence_lower.toFixed(2)}%` : 'N/A'} — {predictions.prophet.confidence_upper !== null ? `${predictions.prophet.confidence_upper.toFixed(2)}%` : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">MAPE</span>
                      <span className="text-yellow-400 font-medium">{predictions.prophet.mape !== null ? `${predictions.prophet.mape.toFixed(3)}%` : 'N/A'}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">R² Score</span>
                      <span className="text-purple-400 font-medium">{predictions.prophet.r2_score !== null ? predictions.prophet.r2_score.toFixed(4) : 'N/A'}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* LSTM Card */}
              {predictions.lstm && (
                <div className={`glass-card p-5 ${predictions.recommended_model === 'LSTM' ? 'ring-1 ring-purple-500/40' : ''}`}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full bg-purple-500"></span>
                      LSTM
                    </h3>
                    {predictions.recommended_model === 'LSTM' && (
                      <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded-full font-medium">Best Model</span>
                    )}
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Predicted Return</span>
                      <span className={`font-semibold ${predictions.lstm.predicted_return_6m >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {predictions.lstm.predicted_return_6m !== null && predictions.lstm.predicted_return_6m !== undefined ? `${predictions.lstm.predicted_return_6m.toFixed(2)}%` : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Predicted NAV</span>
                      <span className="text-white font-medium">
                        {predictions.lstm.predicted_nav_6m !== null && predictions.lstm.predicted_nav_6m !== undefined ? `₹${predictions.lstm.predicted_nav_6m.toFixed(2)}` : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Confidence Range</span>
                      <span className="text-gray-300 text-xs">
                        {predictions.lstm.confidence_lower !== null ? `${predictions.lstm.confidence_lower.toFixed(2)}%` : 'N/A'} — {predictions.lstm.confidence_upper !== null ? `${predictions.lstm.confidence_upper.toFixed(2)}%` : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">MAPE</span>
                      <span className="text-yellow-400 font-medium">{predictions.lstm.mape !== null ? `${predictions.lstm.mape.toFixed(3)}%` : 'N/A'}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">R² Score</span>
                      <span className="text-purple-400 font-medium">{predictions.lstm.r2_score !== null ? predictions.lstm.r2_score.toFixed(4) : 'N/A'}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Ensemble Values */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
              <MetricCard
                label="Simple Ensemble"
                value={predictions.ensemble_simple !== null ? `${predictions.ensemble_simple.toFixed(2)}%` : 'N/A'}
                sub="Equal weight average"
                color="cyan"
              />
              <MetricCard
                label="Weighted Ensemble"
                value={predictions.ensemble_weighted !== null ? `${predictions.ensemble_weighted.toFixed(2)}%` : 'N/A'}
                sub="Accuracy-weighted average"
                color="purple"
              />
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-[#0a0c14] border-t border-white/5 py-6 mt-8">
        <div className="container mx-auto px-4 text-center">
          <p className="text-xs text-gray-500">
            Predictions are for educational purposes only. Not investment advice.
          </p>
        </div>
      </div>
    </div>
  );
};

export default FundDetail;
