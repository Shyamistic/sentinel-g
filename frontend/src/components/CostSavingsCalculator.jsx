import React, { useState, useEffect } from 'react';
import { DollarSign, TrendingDown, Zap, Clock } from 'lucide-react';

export function CostSavingsCalculator() {
  // Default to Gemini 1.5 Pro to satisfy Google Hackathon requirements
  const [currentModel, setCurrentModel] = useState('gemini_1_5_pro');
  const [recommendedModel, setRecommendedModel] = useState('gemini_1_5_flash');
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
      if (!response.ok) throw new Error('Failed to fetch models');
      const data = await response.json();
      // Safe conversion of object to array
      if (data && data.models) {
        setModels(Object.entries(data.models).map(([key, value]) => ({ id: key, ...value })));
      }
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  };

  const calculateSavings = async () => {
    setLoading(true);
    try {
      // FIX: Using POST with JSON body instead of Query Params
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/calculate-cost-savings`,
        { 
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            current_model: currentModel,
            recommended_model: recommendedModel,
            monthly_requests: monthlyRequests
          })
        }
      );
      
      if (!response.ok) {
        const err = await response.text();
        throw new Error(`API Error: ${err}`);
      }

      const data = await response.json();
      setSavings(data);
    } catch (error) {
      console.error('Calculation failed:', error);
      alert('Failed to calculate savings. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg p-6 border border-slate-700 w-full shadow-xl">
      <h2 className="text-xl font-bold text-cyan-400 mb-6 flex items-center gap-2">
        <DollarSign className="w-6 h-6" />
        ROI & Cost Savings Calculator
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
          <label className="text-sm text-slate-300 mb-2 block">Target Model</label>
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
            onChange={(e) => setMonthlyRequests(parseInt(e.target.value) || 0)}
            className="w-full bg-slate-700 border border-slate-600 text-white rounded px-3 py-2 focus:outline-none focus:border-cyan-400"
          />
        </div>
      </div>

      <button
        onClick={calculateSavings}
        disabled={loading}
        className="w-full bg-cyan-500 hover:bg-cyan-600 text-white font-bold py-3 px-4 rounded mb-6 transition disabled:opacity-50 shadow-lg shadow-cyan-500/20"
      >
        {loading ? 'Analyzing Cost Efficiency...' : 'Calculate Savings'}
      </button>

      {/* Results Display - Only shows if savings data exists */}
      {savings && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-in fade-in duration-500">
          
          {/* Annual Savings Card */}
          <div className="bg-slate-700/50 rounded p-4 border-l-4 border-green-500">
            <div className="flex items-center gap-2 mb-2">
              <TrendingDown className="w-5 h-5 text-green-400" />
              <span className="text-sm text-slate-300">Projected Annual Savings</span>
            </div>
            <div className="text-3xl font-bold text-green-400">
              ${savings.annual_savings_usd?.toLocaleString() ?? 0}
            </div>
            <div className="text-xs text-slate-400 mt-1">
              {savings.savings_percent}% cost reduction
            </div>
          </div>

          {/* Monthly Savings Card */}
          <div className="bg-slate-700/50 rounded p-4 border-l-4 border-blue-500">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-5 h-5 text-blue-400" />
              <span className="text-sm text-slate-300">Monthly Savings</span>
            </div>
            <div className="text-3xl font-bold text-blue-400">
              ${savings.monthly_savings_usd?.toLocaleString() ?? 0}
            </div>
            <div className="text-xs text-slate-400 mt-1">
              Based on {monthlyRequests.toLocaleString()} requests
            </div>
          </div>

          {/* Model Comparison Table */}
          <div className="bg-slate-700/50 rounded p-4 col-span-1 md:col-span-2">
            <h3 className="text-sm font-bold text-slate-200 mb-3 uppercase tracking-wider">Direct Comparison</h3>
            <div className="grid grid-cols-2 gap-8">
              <div className="border-r border-slate-600 pr-4">
                <div className="text-xs text-slate-400 mb-1">Current: {savings.current_model_name}</div>
                <div className="text-xl font-bold text-slate-200">
                  ${savings.current_monthly_cost?.toLocaleString()}
                </div>
                <div className="text-xs text-slate-500">per month</div>
              </div>
              <div className="pl-4">
                <div className="text-xs text-slate-400 mb-1">Target: {savings.recommended_model_name}</div>
                <div className="text-xl font-bold text-green-400">
                  ${savings.recommended_monthly_cost?.toLocaleString()}
                </div>
                <div className="text-xs text-slate-500">per month</div>
              </div>
            </div>
          </div>

        </div>
      )}
    </div>
  );
}