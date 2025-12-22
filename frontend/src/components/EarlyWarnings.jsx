import React from 'react';
import { AlertCircle, Zap, TrendingUp } from 'lucide-react';

export default function EarlyWarnings({ incident }) {
  if (!incident) return null;

  const classification = incident.classification || {};
  const signals = [];

  // Check each signal
  if (classification.confidence < 0.70) {
    signals.push({
      name: 'Confidence Drift',
      value: classification.confidence,
      status: 'TRIGGERED',
      color: 'red',
      icon: <AlertCircle className="w-5 h-5" />,
    });
  } else {
    signals.push({
      name: 'Confidence Drift',
      value: classification.confidence,
      status: 'MONITORING',
      color: 'green',
      icon: <AlertCircle className="w-5 h-5" />,
    });
  }

  if (classification.latency_ms > 2340) {
    signals.push({
      name: 'Latency Spike',
      value: classification.latency_ms,
      status: 'TRIGGERED',
      color: 'red',
      icon: <TrendingUp className="w-5 h-5" />,
    });
  } else {
    signals.push({
      name: 'Latency Spike',
      value: classification.latency_ms,
      status: 'MONITORING',
      color: 'green',
      icon: <TrendingUp className="w-5 h-5" />,
    });
  }

  if (classification.diversity_score < 0.50) {
    signals.push({
      name: 'Diversity Collapse',
      value: classification.diversity_score,
      status: 'TRIGGERED',
      color: 'red',
      icon: <Zap className="w-5 h-5" />,
    });
  } else {
    signals.push({
      name: 'Diversity Collapse',
      value: classification.diversity_score,
      status: 'MONITORING',
      color: 'green',
      icon: <Zap className="w-5 h-5" />,
    });
  }

  return (
    <div className="mb-8 p-6 bg-gradient-to-r from-red-900/20 to-orange-900/20 border border-red-500/30 rounded-lg">
      <h2 className="text-lg font-bold text-red-400 mb-4">⚠️ Early Warning Signals</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {signals.map((signal, idx) => (
          <div
            key={idx}
            className={`p-4 rounded-lg border ${
              signal.status === 'TRIGGERED'
                ? 'bg-red-900/30 border-red-500/50'
                : 'bg-green-900/20 border-green-500/30'
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <div className={signal.status === 'TRIGGERED' ? 'text-red-400' : 'text-green-400'}>
                {signal.icon}
              </div>
              <h3 className="font-semibold">{signal.name}</h3>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">
                {signal.value}
              </span>
              <span
                className={`text-xs font-bold px-2 py-1 rounded ${
                  signal.status === 'TRIGGERED'
                    ? 'bg-red-500/30 text-red-300'
                    : 'bg-green-500/30 text-green-300'
                }`}
              >
                {signal.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}