import React, { useState, useEffect } from 'react';
import { DollarSign, TrendingDown, Zap, Clock } from 'lucide-react';

export function CostSavingsCalculator() {
  const [currentModel, setCurrentModel] = useState('gpt4');
  const [recommendedModel, setRecommendedModel] = useState('gpt4o');
  const [monthlyRequests, setMonthlyRequests] = useState(1000000);
  const [savings, setSavings] = useState(null);
  const [loading, setLoading] = useState(false);
  const [models, setModels] = useState([]);

  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/models`);
      const data = await response.json();
      setModels(Object.entries(data.models).map(([key, value]) => ({ id: key, ...value })));
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  };

  const calculateSavings = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/calculate-cost-savings?current_model=${currentModel}&recommended_model=${recommendedModel}&monthly_requests=${monthlyRequests}`,
        { method: 'POST' }
      );
      const data = await response.json();
      setSavings(data);
    } catch (error) {
      console.error('Calculation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg p-6 border border-slate-700 w-full">
      <h2 className="text-xl font-bold text-cyan-400 mb-6 flex items-center gap-2">
        <DollarSign className="w-6 h-6" />
        Cost Savings Calculator
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Current Model */}
        <div>
          <label className="text-sm text-slate-300 mb-2 block">Current Model</label>
          <select
            value={currentModel}
            onChange={(e) => setCurrentModel(e.target.value)}
            className="w-full bg-slate-700 border border-slate-600 text-white rounded px-3 py-2 focus:outline-none focus:border-cyan-400"
          >
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>
        </div>

        {/* Recommended Model */}
        <div>
          <label className="text-sm text-slate-300 mb-2 block">Recommended Model</label>
          <select
            value={recommendedModel}
            onChange={(e) => setRecommendedModel(e.target.value)}
            className="w-full bg-slate-700 border border-slate-600 text-white rounded px-3 py-2 focus:outline-none focus:border-cyan-400"
          >
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>
        </div>

        {/* Monthly Requests */}
        <div>
          <label className="text-sm text-slate-300 mb-2 block">Monthly Requests</label>
          <input
            type="number"
            value={monthlyRequests}
            onChange={(e) => setMonthlyRequests(parseInt(e.target.value))}
            className="w-full bg-slate-700 border border-slate-600 text-white rounded px-3 py-2 focus:outline-none focus:border-cyan-400"
          />
        </div>
      </div>

      <button
        onClick={calculateSavings}
        disabled={loading}
        className="w-full bg-cyan-500 hover:bg-cyan-600 text-white font-bold py-2 px-4 rounded mb-6 transition disabled:opacity-50"
      >
        {loading ? 'Calculating...' : 'Calculate Savings'}
      </button>

      {savings && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Savings Card */}
          <div className="bg-slate-700 rounded p-4 border-l-4 border-green-500">
            <div className="flex items-center gap-2 mb-2">
              <TrendingDown className="w-5 h-5 text-green-400" />
              <span className="text-sm text-slate-300">Annual Savings</span>
            </div>
            <div className="text-3xl font-bold text-green-400">
              ${savings.annual_savings_usd.toLocaleString()}
            </div>
            <div className="text-xs text-slate-400 mt-1">
              {savings.savings_percent.toFixed(1)}% reduction
            </div>
          </div>

          {/* Monthly Savings Card */}
          <div className="bg-slate-700 rounded p-4 border-l-4 border-blue-500">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-5 h-5 text-blue-400" />
              <span className="text-sm text-slate-300">Monthly Savings</span>
            </div>
            <div className="text-3xl font-bold text-blue-400">
              ${savings.monthly_savings_usd.toLocaleString()}
            </div>
            <div className="text-xs text-slate-400 mt-1">
              Per {savings.monthly_requests.toLocaleString()} requests
            </div>
          </div>

          {/* Cost Comparison */}
          <div className="bg-slate-700 rounded p-4 col-span-1 md:col-span-2">
            <h3 className="text-sm font-bold text-slate-200 mb-3">Model Comparison</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-slate-400 mb-1">Current: {savings.current_model_name}</div>
                <div className="text-lg font-bold text-slate-200">
                  ${savings.current_monthly_cost.toLocaleString()}
                </div>
                <div className="text-xs text-slate-500">per month</div>
              </div>
              <div>
                <div className="text-xs text-slate-400 mb-1">Recommended: {savings.recommended_model_name}</div>
                <div className="text-lg font-bold text-green-400">
                  ${savings.recommended_monthly_cost.toLocaleString()}
                </div>
                <div className="text-xs text-slate-500">per month</div>
              </div>
            </div>
          </div>

          {/* Payback Period */}
          <div className="bg-slate-700 rounded p-4 col-span-1 md:col-span-2 border-l-4 border-yellow-500">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-5 h-5 text-yellow-400" />
              <span className="text-sm text-slate-300">Payback Period</span>
            </div>
            <div className="text-2xl font-bold text-yellow-400">
              {savings.payback_period_days} days
            </div>
            <div className="text-xs text-slate-400 mt-1">Time to recover switching costs</div>
          </div>

          {/* Model Specs */}
          <div className="bg-slate-700 rounded p-4 col-span-1">
            <h4 className="text-xs font-bold text-slate-300 mb-2">Current Model</h4>
            <ul className="text-xs text-slate-400 space-y-1">
              <li>Latency: {savings.model_specs.current.latency_ms}ms</li>
              <li>Max Tokens: {savings.model_specs.current.max_tokens.toLocaleString()}</li>
              <li>Threshold: {savings.model_specs.current.confidence_threshold}</li>
            </ul>
          </div>

          <div className="bg-slate-700 rounded p-4 col-span-1">
            <h4 className="text-xs font-bold text-slate-300 mb-2">Recommended Model</h4>
            <ul className="text-xs text-slate-400 space-y-1">
              <li>Latency: {savings.model_specs.recommended.latency_ms}ms</li>
              <li>Max Tokens: {savings.model_specs.recommended.max_tokens.toLocaleString()}</li>
              <li>Threshold: {savings.model_specs.recommended.confidence_threshold}</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
