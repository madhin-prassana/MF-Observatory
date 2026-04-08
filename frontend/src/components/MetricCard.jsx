import React from 'react';

const MetricCard = ({ label, value, sub, icon, color = 'cyan', trend }) => {
  const textColorMap = {
    blue: 'text-glacial-blue',
    purple: 'text-electric-cyan',
    green: 'text-arctic-emerald',
    red: 'text-critical-red',
    orange: 'text-warning-amber',
    cyan: 'text-electric-cyan',
  };

  return (
    <div className={`bg-glacial-base border border-permafrost rounded-sm p-5 transition-all duration-300 hover:border-electric-cyan/30 hover:shadow-[0_0_15px_rgba(76,215,246,0.05)] cursor-default`}>
      <div className="flex items-start justify-between mb-3">
        <span className="text-gray-400 text-xs tracking-wider uppercase font-bold">{label}</span>
        {icon && <span className="text-xl drop-shadow-sm">{icon}</span>}
      </div>
      <div className={`text-2xl font-bold tracking-tight ${textColorMap[color]} mb-1`}>
        {value}
      </div>
      {sub && <div className="text-xs text-glacial-blue/50 font-medium">{sub}</div>}
      {trend !== undefined && (
        <div className={`text-xs mt-2 font-bold ${trend >= 0 ? 'text-arctic-emerald' : 'text-critical-red'}`}>
          {trend >= 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(2)}%
        </div>
      )}
    </div>
  );
};

export default MetricCard;
