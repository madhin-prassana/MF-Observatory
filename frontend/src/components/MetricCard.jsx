import React from 'react';

const MetricCard = ({ label, value, sub, icon, color = 'blue', trend }) => {
  const colorMap = {
    blue: 'from-blue-500/20 to-blue-600/5 border-blue-500/20',
    purple: 'from-purple-500/20 to-purple-600/5 border-purple-500/20',
    green: 'from-emerald-500/20 to-emerald-600/5 border-emerald-500/20',
    red: 'from-red-500/20 to-red-600/5 border-red-500/20',
    orange: 'from-orange-500/20 to-orange-600/5 border-orange-500/20',
    cyan: 'from-cyan-500/20 to-cyan-600/5 border-cyan-500/20',
  };

  const textColorMap = {
    blue: 'text-blue-400',
    purple: 'text-purple-400',
    green: 'text-emerald-400',
    red: 'text-red-400',
    orange: 'text-orange-400',
    cyan: 'text-cyan-400',
  };

  return (
    <div className={`bg-gradient-to-br ${colorMap[color]} border rounded-xl p-5 transition-all duration-300 hover:scale-[1.02]`}>
      <div className="flex items-start justify-between mb-3">
        <span className="text-gray-400 text-sm font-medium">{label}</span>
        {icon && <span className="text-xl">{icon}</span>}
      </div>
      <div className={`text-2xl font-bold ${textColorMap[color]} mb-1`}>
        {value}
      </div>
      {sub && <div className="text-xs text-gray-500">{sub}</div>}
      {trend !== undefined && (
        <div className={`text-xs mt-2 font-medium ${trend >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(2)}%
        </div>
      )}
    </div>
  );
};

export default MetricCard;
