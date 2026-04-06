import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { getModelComparison, getAllClusters, getAllAnomalies } from '../services/api';
import MetricCard from '../components/MetricCard';
import LoadingSpinner from '../components/LoadingSpinner';

const ANOMALY_COLORS = {
  'Normal': '#10b981',
  'Performance Issue': '#f59e0b',
  'Risk Issue': '#f97316',
  'High Priority': '#ef4444',
};

const CLUSTER_COLORS = ['#10b981', '#22d3ee', '#f59e0b', '#f97316', '#ef4444'];

const Analytics = () => {
  const [modelStats, setModelStats] = useState(null);
  const [clusters, setClusters] = useState(null);
  const [anomalies, setAnomalies] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [modelRes, clusterRes, anomalyRes] = await Promise.allSettled([
          getModelComparison(),
          getAllClusters(),
          getAllAnomalies(),
        ]);
        if (modelRes.status === 'fulfilled') setModelStats(modelRes.value.data);
        if (clusterRes.status === 'fulfilled') setClusters(clusterRes.value.data);
        if (anomalyRes.status === 'fulfilled') setAnomalies(anomalyRes.value.data);
      } catch (err) {
        console.error('Error loading analytics:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  if (loading) return <LoadingSpinner message="Loading analytics dashboard..." />;

  // Prepare chart data
  const modelComparisonData = modelStats ? [
    { name: 'Avg MAPE (%)', Prophet: modelStats.prophet.avg_mape, LSTM: modelStats.lstm.avg_mape },
    { name: 'Avg R²', Prophet: modelStats.prophet.avg_r2 * 100, LSTM: modelStats.lstm.avg_r2 * 100 },
    { name: 'Win Rate (%)', Prophet: modelStats.prophet.win_rate, LSTM: modelStats.lstm.win_rate },
  ] : [];

  const anomalyPieData = anomalies
    ? Object.entries(anomalies.anomaly_distribution).map(([name, value]) => ({
        name,
        value,
        color: ANOMALY_COLORS[name] || '#6b7280',
      }))
    : [];

  const CustomBarTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass-card p-3 text-sm">
          <p className="text-gray-400 mb-2 font-medium">{label}</p>
          {payload.map((p, i) => (
            <p key={i} style={{ color: p.color }} className="font-semibold">
              {p.name}: {p.value?.toFixed(3)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const CustomPieTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="glass-card p-3 text-sm">
          <p className="text-white font-semibold">{payload[0].name}</p>
          <p className="text-gray-400">{payload[0].value} funds</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="min-h-screen bg-[#0f1117]">
      {/* Page Header */}
      <div className="bg-gradient-to-br from-[#151829] to-[#0f1117] border-b border-white/5">
        <div className="container mx-auto px-4 py-10">
          <h1 className="text-4xl font-bold gradient-text mb-2">Analytics Dashboard</h1>
          <p className="text-gray-400">ML model performance, risk clusters, and anomaly insights</p>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 space-y-10">

        {/* =============== MODEL SHOWDOWN =============== */}
        {modelStats && (
          <section>
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <span className="text-2xl">⚔️</span> Model Showdown: Prophet vs LSTM
            </h2>

            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <MetricCard
                label="Prophet Win Rate"
                value={`${modelStats.prophet.win_rate.toFixed(1)}%`}
                sub={`${modelStats.prophet.wins} wins`}
                icon="📈"
                color="blue"
              />
              <MetricCard
                label="LSTM Win Rate"
                value={`${modelStats.lstm.win_rate.toFixed(1)}%`}
                sub={`${modelStats.lstm.wins} wins`}
                icon="🧠"
                color="purple"
              />
              <MetricCard
                label="Prophet Avg MAPE"
                value={`${modelStats.prophet.avg_mape.toFixed(3)}%`}
                sub="Mean Absolute % Error"
                icon="🎯"
                color="cyan"
              />
              <MetricCard
                label="LSTM Avg MAPE"
                value={`${modelStats.lstm.avg_mape.toFixed(3)}%`}
                sub="Mean Absolute % Error"
                icon="🎯"
                color="orange"
              />
            </div>

            {/* Bar Chart */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Performance Comparison</h3>
              <div className="h-[320px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={modelComparisonData} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" stroke="#6b7280" tick={{ fill: '#9ca3af', fontSize: 12 }} />
                    <YAxis stroke="#6b7280" tick={{ fill: '#9ca3af', fontSize: 12 }} />
                    <Tooltip content={<CustomBarTooltip />} />
                    <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 13 }} />
                    <Bar dataKey="Prophet" fill="#3b82f6" radius={[6, 6, 0, 0]} />
                    <Bar dataKey="LSTM" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <p className="text-xs text-gray-500 mt-3 text-center">
                Compared across {modelStats.total_funds} mutual funds
              </p>
            </div>
          </section>
        )}

        {/* =============== RISK CLUSTERS =============== */}
        {clusters && (
          <section>
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <span className="text-2xl">🎯</span> Risk Clusters (K-Means)
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {clusters.clusters.map((cluster, idx) => (
                <div key={cluster.cluster_id} className="glass-card p-5 relative overflow-hidden">
                  {/* Color bar */}
                  <div
                    className="absolute top-0 left-0 right-0 h-1"
                    style={{ background: CLUSTER_COLORS[idx % CLUSTER_COLORS.length] }}
                  ></div>

                  <div className="flex items-center justify-between mb-3">
                    <span
                      className="text-xs font-bold px-2 py-1 rounded-full"
                      style={{
                        background: `${CLUSTER_COLORS[idx % CLUSTER_COLORS.length]}20`,
                        color: CLUSTER_COLORS[idx % CLUSTER_COLORS.length],
                      }}
                    >
                      Cluster {cluster.cluster_id}
                    </span>
                    <span className="text-xs text-gray-400">{cluster.fund_count} funds</span>
                  </div>

                  <h3 className="text-sm font-semibold text-white mb-3">{cluster.risk_category}</h3>

                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Avg Volatility</span>
                      <span className="text-orange-400 font-medium">{cluster.avg_volatility.toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Avg Return</span>
                      <span className={`font-medium ${cluster.avg_return >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {cluster.avg_return.toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Avg Sharpe</span>
                      <span className="text-purple-400 font-medium">{cluster.avg_sharpe.toFixed(3)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Max Drawdown</span>
                      <span className="text-red-400 font-medium">{cluster.avg_max_drawdown.toFixed(2)}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* =============== ANOMALY DETECTION =============== */}
        {anomalies && (
          <section>
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <span className="text-2xl">⚠️</span> Anomaly Detection
            </h2>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Pie Chart */}
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Distribution Overview</h3>

                <div className="flex flex-col md:flex-row items-center gap-6">
                  <div className="h-[280px] w-full md:w-1/2">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={anomalyPieData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          paddingAngle={3}
                          dataKey="value"
                          stroke="none"
                        >
                          {anomalyPieData.map((entry, index) => (
                            <Cell key={index} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip content={<CustomPieTooltip />} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Legend */}
                  <div className="space-y-3 w-full md:w-1/2">
                    {anomalyPieData.map((entry) => (
                      <div key={entry.name} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full" style={{ background: entry.color }}></div>
                          <span className="text-sm text-gray-300">{entry.name}</span>
                        </div>
                        <span className="text-sm font-semibold text-white">{entry.value}</span>
                      </div>
                    ))}
                    <div className="pt-2 border-t border-white/10 flex justify-between">
                      <span className="text-sm text-gray-400">Total</span>
                      <span className="text-sm font-bold text-white">{anomalies.total_funds}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Anomaly Summary</h3>

                <div className="grid grid-cols-2 gap-4 mb-6">
                  <MetricCard
                    label="Total Funds"
                    value={anomalies.total_funds}
                    icon="📋"
                    color="blue"
                  />
                  <MetricCard
                    label="Flagged Funds"
                    value={anomalies.flagged_count}
                    icon="🚩"
                    color="red"
                  />
                </div>

                <div className="text-sm text-gray-400 mb-3">
                  Flag Rate: <span className="text-white font-semibold">{((anomalies.flagged_count / anomalies.total_funds) * 100).toFixed(1)}%</span> of funds have anomalies
                </div>

                {/* Quick category breakdown */}
                <div className="space-y-2">
                  {anomalyPieData.filter(e => e.name !== 'Normal').map((entry) => (
                    <div key={entry.name} className="flex items-center gap-3">
                      <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${(entry.value / anomalies.total_funds) * 100}%`,
                            background: entry.color,
                          }}
                        ></div>
                      </div>
                      <span className="text-xs text-gray-400 w-28 text-right">{entry.name}</span>
                      <span className="text-xs font-medium text-white w-8 text-right">{entry.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Flagged Funds Table */}
            {anomalies.flagged_funds && anomalies.flagged_funds.length > 0 && (
              <div className="glass-card p-6 mt-6 overflow-x-auto">
                <h3 className="text-lg font-semibold text-white mb-4">
                  🚩 Flagged Funds ({anomalies.flagged_count})
                </h3>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/10 text-left">
                      <th className="py-3 px-4 text-gray-400 font-medium">Scheme Code</th>
                      <th className="py-3 px-4 text-gray-400 font-medium">Fund Name</th>
                      <th className="py-3 px-4 text-gray-400 font-medium">Category</th>
                      <th className="py-3 px-4 text-gray-400 font-medium">Anomaly Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {anomalies.flagged_funds.slice(0, 20).map((fund, idx) => (
                      <tr
                        key={fund.scheme_code || idx}
                        className="border-b border-white/5 hover:bg-white/[0.02] transition-colors"
                      >
                        <td className="py-3 px-4 text-blue-400 font-mono text-xs">{fund.scheme_code}</td>
                        <td className="py-3 px-4 text-white max-w-xs truncate">{fund.scheme_name}</td>
                        <td className="py-3 px-4">
                          <span
                            className="inline-block px-2 py-1 rounded-full text-xs font-semibold"
                            style={{
                              background: `${ANOMALY_COLORS[fund.anomaly_category] || '#6b7280'}20`,
                              color: ANOMALY_COLORS[fund.anomaly_category] || '#6b7280',
                            }}
                          >
                            {fund.anomaly_category}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-gray-300 font-medium">
                          {fund.anomaly_score?.toFixed(3) || 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {anomalies.flagged_count > 20 && (
                  <p className="text-xs text-gray-500 mt-3 text-center">
                    Showing 20 of {anomalies.flagged_count} flagged funds
                  </p>
                )}
              </div>
            )}
          </section>
        )}
      </div>

      {/* Footer */}
      <div className="bg-[#0a0c14] border-t border-white/5 py-6 mt-8">
        <div className="container mx-auto px-4 text-center">
          <p className="text-xs text-gray-500">
            © 2025 IntelliMF — Intelligent Mutual Fund Analysis | Powered by Machine Learning
          </p>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
