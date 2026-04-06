import React from 'react';
import { useNavigate } from 'react-router-dom';

const FundCard = ({ fund }) => {
  const navigate = useNavigate();

  const getRiskStyle = (category) => {
    const styles = {
      'Very Low Risk': { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20' },
      'Low Risk': { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/20' },
      'Moderate Risk': { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/20' },
      'High Risk': { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20' },
      'Very High Risk': { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20' },
    };
    return styles[category] || { bg: 'bg-gray-500/10', text: 'text-gray-400', border: 'border-gray-500/20' };
  };

  const getAnomalyStyle = (category) => {
    const styles = {
      'Normal': { color: 'text-emerald-400', icon: '✓' },
      'Performance Issue': { color: 'text-yellow-400', icon: '⚠' },
      'Risk Issue': { color: 'text-orange-400', icon: '⚠' },
      'High Priority': { color: 'text-red-400', icon: '🚨' },
    };
    return styles[category] || { color: 'text-gray-400', icon: '•' };
  };

  const risk = getRiskStyle(fund.risk_category);
  const anomaly = getAnomalyStyle(fund.anomaly_category);

  return (
    <div
      className="glass-card p-5 cursor-pointer group"
      onClick={() => navigate(`/fund/${fund.scheme_code}`)}
    >
      {/* Fund Name */}
      <h3 className="text-base font-semibold text-white mb-3 line-clamp-2 h-12 group-hover:text-blue-400 transition-colors">
        {fund.scheme_name}
      </h3>

      {/* Badges */}
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold border ${risk.bg} ${risk.text} ${risk.border}`}>
          {fund.risk_category}
        </span>
        <span className={`inline-flex items-center gap-1 text-xs font-medium ${anomaly.color}`}>
          {anomaly.icon} {fund.anomaly_category}
        </span>
      </div>

      {/* Metrics */}
      <div className="space-y-2.5 mb-4">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-400">Predicted Return</span>
          <span className={`text-sm font-bold ${fund.recommended_return >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {fund.recommended_return?.toFixed(2)}%
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-400">Model</span>
          <span className="text-sm font-medium text-blue-400">{fund.recommended_model}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-400">Current NAV</span>
          <span className="text-sm font-medium text-white">₹{fund.latest_nav?.toFixed(2)}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-400">Volatility</span>
          <span className="text-sm font-medium text-orange-400">{fund.volatility?.toFixed(2)}%</span>
        </div>
      </div>

      {/* View Details */}
      <div className="pt-3 border-t border-white/5">
        <div className="text-center text-sm text-blue-400 font-medium group-hover:text-blue-300 transition-colors flex items-center justify-center gap-1">
          View Details
          <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>
      </div>
    </div>
  );
};

export default FundCard;