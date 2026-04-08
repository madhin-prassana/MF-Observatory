import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { getFundStats } from '../services/api';

const Home = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

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
    <div className="min-h-screen bg-deep-space">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Ambient glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-gradient-radial from-glacial-blue/10 via-electric-cyan/5 to-transparent rounded-full blur-3xl pointer-events-none"></div>

        <div className="container mx-auto px-4 pt-20 pb-16 relative">
          <div className="text-center mb-16 max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 border border-white/5 bg-arctic-sheet rounded-sm px-4 py-1.5 text-xs font-bold tracking-[0.1em] text-gray-400 mb-6 uppercase shadow-sm">
              <span className="w-2 h-2 bg-arctic-emerald rounded-full animate-pulse-slow shadow-[0_0_8px_#00E6A1]"></span>
              {stats ? `Last Pipeline Sync: ${stats.last_sync}` : 'Initializing Telemetry...'}
            </div>
            <h1 className="text-5xl lg:text-7xl font-extrabold text-white mb-6 tracking-tighter leading-tight drop-shadow-sm">
              Predictive Mutual Fund
              <span className="block text-electric-cyan">Intelligence Platform</span>
            </h1>
            <p className="text-lg text-glacial-blue/70 mb-10 max-w-2xl mx-auto leading-relaxed">
              A quantitative research environment leveraging machine learning to forecast NAV trajectories, categorize risk profiles, and detect performance anomalies across the Indian mutual fund landscape.
            </p>

            {/* Search Bar */}
            <div className="max-w-2xl mx-auto mb-12 relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-electric-cyan/20 to-glacial-blue/20 rounded-lg blur opacity-25 group-hover:opacity-50 transition duration-1000"></div>
              <form 
                onSubmit={(e) => {
                  e.preventDefault();
                  if (searchQuery.trim()) navigate(`/explorer?search=${searchQuery}`);
                }}
                className="relative flex items-center bg-glacial-base border border-permafrost rounded-lg overflow-hidden p-1 shadow-2xl"
              >
                <div className="pl-4 text-gray-500">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <input
                  type="text"
                  placeholder="Search by Fund Name or Scheme Code (e.g. 102640)..."
                  className="w-full bg-transparent border-none text-white px-4 py-4 focus:ring-0 text-sm font-medium placeholder-gray-600"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                <button
                  type="submit"
                  className="bg-glacial-blue text-deep-space px-8 py-3 rounded-md font-bold text-xs uppercase tracking-widest hover:bg-white transition-colors"
                >
                  Analyze
                </button>
              </form>
            </div>

            <div className="flex justify-center gap-4 flex-wrap">
              <button
                onClick={() => navigate('/explorer')}
                className="ghost-btn text-xs tracking-widest uppercase font-bold"
              >
                Browse All Funds
              </button>
              <button
                onClick={() => navigate('/analytics')}
                className="ghost-btn text-xs tracking-widest uppercase font-bold"
              >
                Global Analytics
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
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 max-w-6xl mx-auto">
              <div className="glass-card p-6 text-center border-permafrost">
                <div className="text-4xl font-extrabold text-white mb-1 tracking-tight">{stats.total_funds.toLocaleString()}</div>
                <div className="text-xs font-bold text-gray-500 uppercase tracking-widest">Funds Analyzed</div>
              </div>
              <div className="glass-card p-6 text-center border-permafrost">
                <div className="text-4xl font-extrabold text-glacial-blue mb-1 tracking-tight">{stats.total_forecasts.toLocaleString()}</div>
                <div className="text-xs font-bold text-gray-500 uppercase tracking-widest">Forecasts Generated</div>
              </div>
              <div className="glass-card p-6 text-center border-permafrost">
                <div className={`text-4xl font-extrabold mb-1 tracking-tight ${stats.avg_predicted_return >= 0 ? 'text-arctic-emerald' : 'text-critical-red'}`}>
                  {stats.avg_predicted_return?.toFixed(1)}%
                </div>
                <div className="text-xs font-bold text-gray-500 uppercase tracking-widest">Avg Predicted Return</div>
              </div>
              <div className="glass-card p-6 text-center border-permafrost">
                <div className="text-4xl font-extrabold text-warning-amber mb-1 tracking-tight">{stats.anomaly_rate?.toFixed(1)}%</div>
                <div className="text-xs font-bold text-gray-500 uppercase tracking-widest">Anomaly Detection Rate</div>
              </div>
            </div>
          ) : null}

          {/* Risk Spectrum Preview */}
          {stats && stats.risk_distribution && (
            <div className="max-w-4xl mx-auto mt-12 pb-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-500">Risk Spectrum Distribution</span>
                <span className="text-[10px] font-bold text-electric-cyan uppercase tracking-widest">Market Wide Analysis</span>
              </div>
              <div className="h-1.5 w-full flex rounded-full overflow-hidden bg-white/5 border border-white/5">
                {Object.entries(stats.risk_distribution).map(([category, count], idx) => {
                  const colors = ['#00E6A1', '#4CD7F6', '#FFB340', '#f97316', '#FF5C5C'];
                  const percent = (count / stats.total_funds) * 100;
                  return (
                    <div 
                      key={category}
                      style={{ width: `${percent}%`, backgroundColor: colors[idx % colors.length] }}
                      className="h-full transition-all duration-500 hover:opacity-80 cursor-help"
                      title={`${category}: ${count} funds (${percent.toFixed(1)}%)`}
                    />
                  );
                })}
              </div>
              <div className="flex justify-between mt-3 flex-wrap gap-4">
                {Object.entries(stats.risk_distribution).map(([category, count], idx) => {
                  const colors = ['bg-[#00E6A1]', 'bg-[#4CD7F6]', 'bg-[#FFB340]', 'bg-[#f97316]', 'bg-[#FF5C5C]'];
                  return (
                    <div key={category} className="flex items-center gap-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${colors[idx % colors.length]}`}></div>
                      <span className="text-[9px] font-bold text-gray-500 uppercase tracking-tighter">{category}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Features Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="glass-card p-10">
          <h2 className="text-3xl font-bold text-white mb-10 text-center">
            Features of <span className="gradient-text">Vantage .</span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            <div className="text-center group">

              <h3 className="text-xl font-semibold text-white mb-3">Risk Clustering</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Automatically categorize funds into 5 risk levels using K-Means clustering based on actual behavior, not just labels.
              </p>
            </div>
            <div className="text-center group">

              <h3 className="text-xl font-semibold text-white mb-3">Performance Prediction</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Forecast 6-month returns using Prophet and LSTM models with confidence intervals. Choose the best model for each fund.
              </p>
            </div>
            <div className="text-center group">

              <h3 className="text-xl font-semibold text-white mb-3">Anomaly Detection</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Early warning system identifies unusual patterns, volatility spikes, and potential red flags before they become obvious.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Top Performers Leaderboard */}
      {stats && stats.top_performers && (
        <div className="container mx-auto px-4 pb-16">
          <div className="glass-card overflow-hidden border-permafrost">
            <div className="bg-arctic-sheet px-8 py-6 border-b border-permafrost flex items-center justify-between">
              <div>
                <h2 className="text-xl font-extrabold text-white tracking-tight uppercase">Top Predicted Performers</h2>
                <p className="text-xs text-gray-500 font-bold tracking-widest mt-1 uppercase">6-Month Trajectory Consensus</p>
              </div>
              <Link to="/explorer" className="text-electric-cyan text-xs font-bold uppercase tracking-widest hover:text-white transition-colors">
                View All Targets →
              </Link>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 border-b border-permafrost">
                    <th className="px-8 py-4">Ranking</th>
                    <th className="px-8 py-4">Mutual Fund Entity</th>
                    <th className="px-8 py-4">Risk Profile</th>
                    <th className="px-8 py-4 text-right">Expected Trajectory</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-permafrost/50">
                  {stats.top_performers.map((fund, idx) => (
                    <tr 
                      key={fund.scheme_code} 
                      className="hover:bg-white/[0.02] transition-colors cursor-pointer group"
                      onClick={() => navigate(`/fund/${fund.scheme_code}`)}
                    >
                      <td className="px-8 py-5">
                        <span className={`text-lg font-black ${idx === 0 ? 'text-warning-amber' : 'text-gray-600'}`}>
                          0{idx + 1}
                        </span>
                      </td>
                      <td className="px-8 py-5">
                        <div className="text-sm font-bold text-white group-hover:text-electric-cyan transition-colors">{fund.name}</div>
                        <div className="text-[10px] font-mono text-gray-600 mt-0.5">{fund.scheme_code}</div>
                      </td>
                      <td className="px-8 py-5">
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-sm bg-white/5 border border-white/5 text-glacial-blue uppercase tracking-tighter">
                          {fund.risk}
                        </span>
                      </td>
                      <td className="px-8 py-5 text-right">
                        <span className="text-lg font-black text-arctic-emerald">
                          +{fund.return.toFixed(2)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="bg-[#0C1324] border-t border-permafrost py-8 mt-10">
        <div className="container mx-auto px-4 text-center">
          <p className="text-xs font-bold tracking-widest uppercase text-gray-500">
            © 2025 Vantage . — Clinical Precision Analysis | Frozen Core Architecture
          </p>
          <p className="text-xs text-permafrost mt-3">
            Environment: ARCTIC_SHELF_2. Data Ingress: NOMINAL. Results for research and diagnostics only.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Home;