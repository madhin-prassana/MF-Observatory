import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getFundStats } from '../services/api';

const Home = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await getFundStats();
        setStats(response.data);
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  return (
    <div className="min-h-screen bg-[#0f1117]">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Ambient glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-gradient-radial from-blue-500/10 via-purple-500/5 to-transparent rounded-full blur-3xl pointer-events-none"></div>

        <div className="container mx-auto px-4 pt-20 pb-16 relative">
          <div className="text-center mb-16 max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-4 py-1.5 text-sm text-gray-400 mb-6">
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
              Powered by Machine Learning
            </div>
            <h1 className="text-5xl lg:text-6xl font-extrabold text-white mb-5 leading-tight">
              Intelligent Mutual Fund
              <span className="block gradient-text">Analysis Platform</span>
            </h1>
            <p className="text-lg text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed">
              Make smarter investment decisions with ML-powered predictions, risk clustering, and anomaly detection across hundreds of mutual funds.
            </p>
            <div className="flex justify-center gap-4 flex-wrap">
              <button
                onClick={() => navigate('/explorer')}
                className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600 text-white font-semibold py-3 px-8 rounded-xl shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 transition-all duration-300 hover:-translate-y-0.5"
              >
                Explore Funds
              </button>
              <button
                onClick={() => navigate('/analytics')}
                className="bg-white/5 hover:bg-white/10 text-white font-semibold py-3 px-8 rounded-xl border border-white/10 hover:border-white/20 transition-all duration-300 hover:-translate-y-0.5"
              >
                View Analytics
              </button>
            </div>
          </div>

          {/* Stats Cards */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              {[1, 2, 3].map((i) => (
                <div key={i} className="glass-card p-8">
                  <div className="skeleton h-12 w-24 mx-auto mb-3"></div>
                  <div className="skeleton h-4 w-32 mx-auto"></div>
                </div>
              ))}
            </div>
          ) : stats ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              <div className="glass-card p-8 text-center">
                <div className="text-5xl font-bold text-blue-400 mb-2">{stats.total_funds}</div>
                <div className="text-gray-400 font-medium">Funds Analyzed</div>
              </div>
              <div className="glass-card p-8 text-center">
                <div className="text-5xl font-bold text-purple-400 mb-2">3</div>
                <div className="text-gray-400 font-medium">ML Models Used</div>
                <div className="text-xs text-gray-500 mt-2">Clustering · Anomaly · Prediction</div>
              </div>
              <div className="glass-card p-8 text-center">
                <div className={`text-5xl font-bold mb-2 ${stats.avg_predicted_return >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {stats.avg_predicted_return?.toFixed(1)}%
                </div>
                <div className="text-gray-400 font-medium">Avg Predicted Return</div>
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {/* Features Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="glass-card p-10">
          <h2 className="text-3xl font-bold text-white mb-10 text-center">
            What Makes <span className="gradient-text">IntelliMF</span> Different
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            <div className="text-center group">
              <div className="w-16 h-16 mx-auto mb-5 bg-gradient-to-br from-emerald-500/20 to-emerald-500/5 rounded-2xl flex items-center justify-center text-3xl group-hover:scale-110 transition-transform">
                📊
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">Risk Clustering</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Automatically categorize funds into 5 risk levels using K-Means clustering based on actual behavior, not just labels.
              </p>
            </div>
            <div className="text-center group">
              <div className="w-16 h-16 mx-auto mb-5 bg-gradient-to-br from-blue-500/20 to-blue-500/5 rounded-2xl flex items-center justify-center text-3xl group-hover:scale-110 transition-transform">
                🔮
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">Performance Prediction</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Forecast 6-month returns using Prophet and LSTM models with confidence intervals. Choose the best model for each fund.
              </p>
            </div>
            <div className="text-center group">
              <div className="w-16 h-16 mx-auto mb-5 bg-gradient-to-br from-red-500/20 to-red-500/5 rounded-2xl flex items-center justify-center text-3xl group-hover:scale-110 transition-transform">
                ⚠️
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">Anomaly Detection</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Early warning system identifies unusual patterns, volatility spikes, and potential red flags before they become obvious.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Top Performer */}
      {stats && stats.top_performer && (
        <div className="container mx-auto px-4 pb-16">
          <div className="glass-card p-8 text-center relative overflow-hidden">
            {/* Background glow */}
            <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/5 via-transparent to-emerald-500/5 pointer-events-none"></div>
            <div className="relative">
              <div className="text-3xl mb-3">🏆</div>
              <h2 className="text-2xl font-bold text-white mb-3">Top Predicted Performer</h2>
              <p className="text-gray-300 mb-2 text-lg">{stats.top_performer.name}</p>
              <p className="text-4xl font-bold text-emerald-400 mb-4">
                {stats.top_performer.return?.toFixed(2)}%
                <span className="text-lg text-gray-400 font-normal ml-2">Expected Return</span>
              </p>
              <button
                onClick={() => navigate('/explorer')}
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-2.5 px-6 rounded-xl transition-all duration-200 hover:-translate-y-0.5 shadow-lg shadow-emerald-500/20"
              >
                Explore All Funds
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="bg-[#0a0c14] border-t border-white/5 py-8">
        <div className="container mx-auto px-4 text-center">
          <p className="text-sm text-gray-500">
            © 2025 IntelliMF — Intelligent Mutual Fund Analysis | Powered by Machine Learning
          </p>
          <p className="text-xs text-gray-600 mt-2">
            Disclaimer: Predictions are for educational purposes only. Not investment advice.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Home;