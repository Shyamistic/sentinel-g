import React, { useState } from 'react';
import { Play, CheckCircle } from 'lucide-react';

export default function RecoveryActions({ incident, onApply }) {
  const [selectedIdx, setSelectedIdx] = useState(null);
  const [isExecuting, setIsExecuting] = useState(false);

  if (!incident || !incident.recovery_options) return null;

  const options = incident.recovery_options;

  const handleApply = (option) => {
    setSelectedIdx(options.indexOf(option));
    setIsExecuting(true);
    onApply(option);
    setTimeout(() => setIsExecuting(false), 2000);
  };

  return (
    <div className="bg-gradient-to-br from-slate-800/50 to-slate-700/50 border border-slate-700 rounded-lg p-6">
      <h2 className="text-xl font-bold mb-6">Recovery Actions</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {options.map((option, idx) => (
          <div
            key={idx}
            className={`p-6 rounded-lg border-2 transition ${
              selectedIdx === idx
                ? 'border-green-500 bg-green-900/20'
                : 'border-slate-600 bg-slate-700/30 hover:border-teal-500/50'
            }`}
          >
            {/* Rank badge */}
            <div className="flex items-center justify-between mb-4">
              <span className="inline-block bg-teal-500/30 text-teal-400 px-3 py-1 rounded text-sm font-bold">
                #{option.rank}
              </span>
              {selectedIdx === idx && (
                <CheckCircle className="w-5 h-5 text-green-400" />
              )}
            </div>

            {/* Action name */}
            <h3 className="font-bold text-white mb-3 text-sm">{option.action}</h3>

            {/* Metrics */}
            <div className="space-y-2 mb-4 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Success Rate</span>
                <span className="font-bold text-teal-400">
                  {(option.success_rate * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Execution Time</span>
                <span className="font-bold text-teal-400">
                  {option.execution_time_min} min
                </span>
              </div>
            </div>

            {/* Success rate bar */}
            <div className="w-full bg-slate-700 rounded-full h-2 mb-4 overflow-hidden">
              <div
                className="bg-gradient-to-r from-teal-500 to-cyan-500 h-full"
                style={{ width: `${option.success_rate * 100}%` }}
              />
            </div>

            {/* Apply button */}
            <button
              onClick={() => handleApply(option)}
              disabled={isExecuting}
              className={`w-full py-2 rounded-lg font-bold text-sm flex items-center justify-center gap-2 transition ${
                selectedIdx === idx
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white'
              }`}
            >
              <Play className="w-4 h-4" />
              {selectedIdx === idx ? 'Applied' : 'Apply Fix'}
            </button>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 bg-slate-700/20 border border-slate-600 rounded text-sm text-gray-400">
        <p className="font-semibold text-white mb-2">How to Use</p>
        <p>
          Click "Apply Fix" on any recovery option. The system will execute the fix and 
          update metrics in real-time. You'll see confidence recover and latency normalize.
        </p>
      </div>
    </div>
  );
}