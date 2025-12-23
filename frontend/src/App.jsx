import React, { useState } from 'react';
import { TrendingUp, Zap, Activity, CheckCircle, AlertTriangle, ShieldAlert } from 'lucide-react';
import MetricsCard from './components/MetricsCard';
import IncidentTimeline from './components/IncidentTimeline';
import BusinessImpact from './components/BusinessImpact';
import RecoveryActions from './components/RecoveryActions';
import EarlyWarnings from './components/EarlyWarnings';
import { CostSavingsCalculator } from './components/CostSavingsCalculator';

const API_URL = import.meta.env.VITE_API_URL || 'https://sentinel-g-api.onrender.com';

export default function App() {
  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState('HEALTHY');
  const [recoveredIncident, setRecoveredIncident] = useState(null);
  const [resolvedIncidents, setResolvedIncidents] = useState([]);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const triggerFailure = async (failureType) => {
    setLoading(true);
    setRecoveredIncident(null);
    try {
      const response = await fetch(`${API_URL}/test-failure?failure_type=${failureType}`, { method: 'POST' });
      if (!response.ok) throw new Error('API Error');
      const data = await response.json();
      setIncident(data);
      setSystemStatus('ALERT');
      showToast(`🔴 ${failureType.toUpperCase()} DETECTED`, 'error');
    } catch (err) {
      showToast(`Failed: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyFix = async (action) => {
    if (!incident) return;
    setLoading(true);
    setSystemStatus('RECOVERING');

    try {
      const url = `${API_URL}/apply-fix?request_id=${incident.request_id}&action=${encodeURIComponent(action.action)}`;
      const response = await fetch(url, { method: 'POST' });
      const data = await response.json();

      if (data.status === 'HEALTHY') {
        showToast(`✓ Fix applied: ${action.action}`, 'success');
        
        // Add to history
        setResolvedIncidents(prev => [{
            action: action.action,
            timestamp: new Date().toLocaleTimeString(),
            executionTime: data.execution_time_sec || 2
        }, ...prev].slice(0, 5));

        setRecoveredIncident({
          confidence_score: data.confidence_recovered || 0.98,
          latency_ms: data.latency_normalized_ms || 1200,
          diversity_score: 0.85,
        });

        setTimeout(() => {
          setIncident(null);
          setRecoveredIncident(null);
          setSystemStatus('HEALTHY');
        }, 4000);
      }
    } catch (err) {
      setSystemStatus('ALERT');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white p-4 md:p-8 font-sans">
      
      {/* Toast Overlay */}
      {toast && (
        <div className={`fixed top-4 left-1/2 transform -translate-x-1/2 px-6 py-3 rounded-full font-bold z-50 shadow-2xl transition-all ${
            toast.type === 'success' ? 'bg-emerald-500 text-white' : 'bg-red-500 text-white'
          }`}>
          {toast.message}
        </div>
      )}

      {/* Header Section */}
      <header className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl md:text-5xl font-extrabold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent tracking-tight">
            SENTINEL-G
          </h1>
          <p className="text-slate-400 mt-1 text-sm md:text-base">Reliability Control Plane & Risk Engine</p>
        </div>
        
        <div className={`px-6 py-2 rounded-full font-bold text-sm tracking-wide border backdrop-blur-md transition-all duration-500 ${
            systemStatus === 'HEALTHY' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/50' :
            systemStatus === 'ALERT' ? 'bg-red-500/10 text-red-400 border-red-500/50 animate-pulse shadow-[0_0_20px_rgba(239,68,68,0.3)]' :
            'bg-amber-500/10 text-amber-400 border-amber-500/50'
          }`}>
          {systemStatus === 'HEALTHY' && '🟢 SYSTEM OPTIMAL'}
          {systemStatus === 'ALERT' && '🔴 CRITICAL FAILURE DETECTED'}
          {systemStatus === 'RECOVERING' && '🟡 EXECUTING RECOVERY...'}
        </div>
      </header>

      {/* Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        <button onClick={() => triggerFailure('hallucination')} disabled={loading}
          className="bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-red-500/50 text-white py-3 rounded-xl font-medium transition-all shadow-lg hover:shadow-red-500/10">
          Trigger Hallucination
        </button>
        <button onClick={() => triggerFailure('latency')} disabled={loading}
          className="bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-orange-500/50 text-white py-3 rounded-xl font-medium transition-all shadow-lg hover:shadow-orange-500/10">
          Trigger Latency Spike
        </button>
        <button onClick={() => triggerFailure('cost')} disabled={loading}
          className="bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-yellow-500/50 text-white py-3 rounded-xl font-medium transition-all shadow-lg hover:shadow-yellow-500/10">
          Trigger Cost Surge
        </button>
        {/* NEW BUTTON */}
        <button onClick={() => triggerFailure('injection')} disabled={loading}
          className="bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-purple-500/50 text-white py-3 rounded-xl font-medium transition-all shadow-lg hover:shadow-purple-500/10 flex items-center justify-center gap-2">
          <ShieldAlert size={18} /> Sim Security Attack
        </button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <MetricsCard 
          title="Confidence" 
          value={recoveredIncident?.confidence_score?.toFixed(2) ?? incident?.classification?.confidence?.toFixed(2) ?? '0.99'} 
          trend={incident ? 'down' : 'stable'} 
          threshold="0.70" 
          icon={<Activity size={20}/>} 
        />
        <MetricsCard 
          title="Latency" 
          value={recoveredIncident?.latency_ms ?? incident?.classification?.latency_ms ?? 142} 
          unit="ms" 
          trend={incident ? 'up' : 'stable'} 
          threshold="2000ms" 
          icon={<Zap size={20}/>} 
        />
        <MetricsCard 
          title="Requests/Min" 
          value="4.2k" 
          trend="up" 
          threshold="baseline" 
          icon={<TrendingUp size={20}/>} 
        />
        {/* New "Golden Ratio" Visual */}
        <div className="bg-slate-800/50 border border-slate-700 p-4 rounded-xl flex flex-col justify-between">
            <div className="flex justify-between items-start mb-2">
                <span className="text-slate-400 text-xs uppercase tracking-wider">Health Score</span>
                <span className="text-emerald-400"><CheckCircle size={20} /></span>
            </div>
            <div className="text-3xl font-bold text-white">98.4</div>
            <div className="text-xs text-slate-500 mt-1">Golden Ratio (Q/Cost)</div>
        </div>
      </div>

      <div className="mb-8"><CostSavingsCalculator /></div>

      {/* Main Content Area */}
      {incident && !recoveredIncident && (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
           {/* Alerts */}
           <div className="mb-6"><EarlyWarnings incident={incident} /></div>

           <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
             <div className="lg:col-span-2 bg-slate-800/50 rounded-xl border border-slate-700 p-1">
               <IncidentTimeline incident={incident} />
             </div>
             <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-1">
               <BusinessImpact incident={incident} />
             </div>
           </div>

           <RecoveryActions incident={incident} onApply={handleApplyFix} />
        </div>
      )}

      {/* Mobile-Friendly Resolved History */}
      {resolvedIncidents.length > 0 && (
        <div className="mt-12 pt-8 border-t border-slate-800">
          <h3 className="text-slate-400 text-sm font-bold uppercase tracking-wider mb-4 flex items-center gap-2">
            <CheckCircle size={16} /> Recent Automated Recoveries
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {resolvedIncidents.map((r, i) => (
              <div key={i} className="bg-emerald-900/10 border border-emerald-500/20 p-3 rounded-lg flex justify-between items-center">
                <div>
                  <div className="text-emerald-400 font-medium text-sm">{r.action}</div>
                  <div className="text-slate-500 text-xs">Auto-executed in {r.executionTime}s</div>
                </div>
                <div className="text-slate-600 text-xs font-mono">{r.timestamp}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <footer className="mt-12 text-center text-slate-600 text-xs py-4">
        SENTINEL-G TITAN ENGINE | Powered by Google Vertex AI & Datadog
      </footer>
    </div>
  );
}