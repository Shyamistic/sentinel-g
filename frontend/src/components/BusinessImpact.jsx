import React from 'react';
import { DollarSign } from 'lucide-react';

export default function BusinessImpact({ incident }) {
  if (!incident || !incident.risk_attribution) return null;

  const risk = incident.risk_attribution;
  const calc = risk.calculation || {};
  const total = calc.projected_24h_revenue_lost || 0;

  return (
    <div className="bg-gradient-to-br from-slate-800/50 to-slate-700/50 border border-slate-700 rounded-lg p-6">
      <div className="flex items-center gap-2 mb-6">
        <DollarSign className="w-5 h-5 text-red-400" />
        <h2 className="text-xl font-bold">Business Impact</h2>
      </div>

      {/* Main impact gauge */}
      <div className="mb-6">
        <div className="text-4xl font-bold text-red-400 mb-2">
          ${(total).toLocaleString()}
        </div>
        <p className="text-gray-400 text-sm mb-4">Revenue at risk (24h estimate)</p>

        {/* Impact bar */}
        <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
          <div
            className="bg-gradient-to-r from-red-500 to-orange-500 h-full transition-all"
            style={{ width: `${Math.min((risk.failure_severity || 0) * 100, 100)}%` }}
          />
        </div>
        <div className="text-xs text-gray-500 mt-2">
          Failure Severity: {((risk.failure_severity || 0) * 100).toFixed(0)}%
        </div>
      </div>

      {/* Breakdown */}
      <div className="space-y-3">
        <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-gray-400">Conversion Loss</span>
            <span className="font-bold text-white">
              ${(calc.conversion_loss || 0).toLocaleString()}
            </span>
          </div>
          <div className="text-xs text-gray-500">63% of total impact</div>
        </div>

        <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-gray-400">Refund Costs</span>
            <span className="font-bold text-white">
              ${(calc.refund_costs || 0).toLocaleString()}
            </span>
          </div>
          <div className="text-xs text-gray-500">24% of total impact</div>
        </div>

        <div className="p-3 bg-slate-700/50 rounded border border-slate-600">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-gray-400">Support Overhead</span>
            <span className="font-bold text-white">
              ${(calc.support_overhead || 0).toLocaleString()}
            </span>
          </div>
          <div className="text-xs text-gray-500">13% of total impact</div>
        </div>
      </div>

      {/* Assumptions */}
      <div className="mt-6 p-3 bg-slate-700/20 border border-slate-600 rounded text-xs text-gray-400">
        <p className="font-semibold mb-1">Calculation</p>
        <p>
          Base Revenue: ${(risk.base_hourly_revenue || 0).toLocaleString()}/hr •
          Hours Undetected: {risk.hours_until_detection || 0}h
        </p>
      </div>
    </div>
  );
}