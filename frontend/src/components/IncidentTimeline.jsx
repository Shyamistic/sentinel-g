import React from 'react';
import { Clock } from 'lucide-react';

export default function IncidentTimeline({ incident }) {
  if (!incident || !incident.failure_lineage) return null;

  const lineage = incident.failure_lineage;

  return (
    <div className="bg-gradient-to-br from-slate-800/50 to-slate-700/50 border border-slate-700 rounded-lg p-6">
      <div className="flex items-center gap-2 mb-6">
        <Clock className="w-5 h-5 text-teal-400" />
        <h2 className="text-xl font-bold">Failure Lineage Timeline</h2>
      </div>

      <div className="space-y-4">
        {lineage.map((event, idx) => (
          <div key={idx} className="relative">
            {/* Timeline line */}
            {idx < lineage.length - 1 && (
              <div className="absolute left-6 top-12 w-1 h-8 bg-gradient-to-b from-teal-500/50 to-red-500/50" />
            )}

            {/* Event */}
            <div className="flex gap-4">
              {/* Timeline dot */}
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0 ${
                  idx === lineage.length - 1
                    ? 'bg-red-500/30 border-2 border-red-500 text-red-400'
                    : 'bg-slate-700 border-2 border-teal-500/50 text-teal-400'
                }`}
              >
                {event.time_marker}
              </div>

              {/* Event content */}
              <div className="flex-1 pt-2">
                <h3 className="font-semibold text-white mb-1">{event.signal}</h3>
                <p className="text-sm text-gray-400 mb-2">{event.description}</p>
                <div className="flex gap-4 text-xs text-gray-500">
                  <span>Value: {event.value.toFixed(2)}</span>
                  <span>{new Date(event.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 bg-red-900/20 border border-red-500/30 rounded text-sm text-red-300">
        <p className="font-semibold mb-1">📊 Insight</p>
        <p>
          System showed early warning signs at t-12m. Could have alerted at t-6m with
          proactive monitoring.
        </p>
      </div>
    </div>
  );
}