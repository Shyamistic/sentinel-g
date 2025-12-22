import React from 'react';
import { Activity } from 'lucide-react';

export default function MetricsCard({ title, value, unit, trend, threshold, icon }) {
  const isCritical = trend === 'down' || trend === 'up';
  
  return (
    <div className="bg-gradient-to-br from-slate-800/50 to-slate-700/50 border border-slate-700 rounded-lg p-6 hover:border-teal-500/30 transition">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-gray-400 text-sm font-semibold">{title}</h3>
        <div className="text-teal-400">{icon}</div>
      </div>
      
      <div className="flex items-baseline gap-2 mb-3">
        <span className={`text-3xl font-bold ${
          isCritical ? 'text-red-400' : 'text-teal-400'
        }`}>
          {typeof value === 'number' ? value.toLocaleString() : value}
        </span>
        {unit && <span className="text-gray-500 text-sm">{unit}</span>}
      </div>
      
      <div className="flex items-center justify-between text-xs">
        <span className={`font-semibold ${
          trend === 'up' ? 'text-red-400' : 
          trend === 'down' ? 'text-yellow-400' : 
          'text-green-400'
        }`}>
          {trend === 'up' ? '↑ Rising' : 
           trend === 'down' ? '↓ Declining' : 
           '→ Stable'}
        </span>
        <span className="text-gray-500">Threshold: {threshold}</span>
      </div>
    </div>
  );
}