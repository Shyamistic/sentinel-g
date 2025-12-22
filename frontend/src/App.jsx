import React, { useState } from 'react';
import { TrendingUp, Zap, Activity, CheckCircle } from 'lucide-react';
import MetricsCard from './components/MetricsCard';
import IncidentTimeline from './components/IncidentTimeline';
import BusinessImpact from './components/BusinessImpact';
import RecoveryActions from './components/RecoveryActions';
import EarlyWarnings from './components/EarlyWarnings';

// Get API URL from environment variable or use Render backend
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
      const url = `${API_URL}/test-failure?failure_type=${failureType}`;
      console.log('Triggering failure at:', url);
      
      const response = await fetch(url, { method: 'POST' });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Incident received:', data);
      
      // Backend returns incident directly
      setIncident(data);
      setSystemStatus('ALERT');
      showToast(`🔴 ${failureType.toUpperCase()} failure detected`, 'error');

      // Auto-recover after 8 seconds for demo
      setTimeout(() => setSystemStatus('RECOVERING'), 5000);
      setTimeout(() => setSystemStatus('HEALTHY'), 8000);
    } catch (err) {
      console.error('Error triggering failure:', err);
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
      console.log('Applying fix at:', url);
      
      const response = await fetch(url, { method: 'POST' });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Recovery response:', data);

      // Backend returns status directly
      if (data.status === 'HEALTHY') {
        showToast(`✓ Fix applied: ${action.action}`, 'success');
        
        // Store the resolved incident
        setResolvedIncidents([
          {
            action: action.action,
            timestamp: new Date().toLocaleTimeString(),
            executionTime: data.execution_time_sec,
            confidenceRecovered: data.confidence_recovered,
            latencyNormalized: data.latency_normalized_ms,
          },
          ...resolvedIncidents,
        ].slice(0, 5));

        // Show recovered state
        setRecoveredIncident({
          confidence_score: data.confidence_recovered,
          latency_ms: data.latency_normalized_ms,
          diversity_score: 0.85,
        });

        // After 3 seconds, clear incident and return to healthy
        setTimeout(() => {
          setIncident(null);
          setRecoveredIncident(null);
          setSystemStatus('HEALTHY');
        }, 3000);
      } else {
        showToast('Failed to apply fix', 'error');
        setSystemStatus('ALERT');
      }
    } catch (err) {
      console.error('Error applying fix:', err);
      showToast(`Error: ${err.message}`, 'error');
      setSystemStatus('ALERT');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-8">
      {/* Toast notification */}
      {toast && (
        <div
          className={`fixed top-4 right-4 px-6 py-3 rounded-lg font-bold z-50 transition ${
            toast.type === 'success'
              ? 'bg-green-500/20 text-green-400 border border-green-500'
              : 'bg-red-500/20 text-red-400 border border-red-500'
          }`}
        >
          {toast.message}
        </div>
      )}

      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-teal-400 to-cyan-400 bg-clip-text text-transparent">
              SENTINEL-G
            </h1>
            <p className="text-gray-400 mt-2">
              LLM Reliability & Business Impact Detection
            </p>
          </div>
          <div
            className={`px-6 py-3 rounded-lg font-bold text-lg border ${
              systemStatus === 'HEALTHY'
                ? 'bg-green-500/20 text-green-400 border-green-500'
                : systemStatus === 'ALERT'
                ? 'bg-red-500/20 text-red-400 border-red-500 animate-pulse'
                : 'bg-yellow-500/20 text-yellow-400 border-yellow-500'
            }`}
          >
            {systemStatus === 'HEALTHY' && '🟢 HEALTHY'}
            {systemStatus === 'ALERT' && '🔴 ALERT – FAILURE DETECTED'}
            {systemStatus === 'RECOVERING' && '🟡 RECOVERING'}
          </div>
        </div>
      </div>

      {/* Resolved incidents log (top right, compact) */}
      {resolvedIncidents.length > 0 && (
        <div className="fixed top-24 right-8 bg-gradient-to-br from-green-900/30 to-green-800/30 border border-green-500/30 rounded-lg p-4 w-80 max-h-40 overflow-y-auto z-40">
          <div className="flex items-center mb-2">
            <CheckCircle className="w-4 h-4 text-green-400 mr-2" />
            <h3 className="text-sm font-bold text-green-400">Resolved Incidents</h3>
          </div>
          <div className="space-y-2">
            {resolvedIncidents.map((r, idx) => (
              <div key={idx} className="text-xs text-green-300 bg-green-900/20 p-2 rounded">
                <p className="font-semibold truncate">{r.action}</p>
                <p className="text-green-400/70">{r.timestamp} • {r.executionTime}s</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Control panel */}
      <div className="mb-8 flex flex-wrap gap-4">
        <button
          onClick={() => triggerFailure('hallucination')}
          disabled={loading}
          className="bg-red-600 hover:bg-red-700 disabled:opacity-50 px-6 py-2 rounded-lg font-bold transition"
        >
          Trigger Hallucination
        </button>
        <button
          onClick={() => triggerFailure('latency')}
          disabled={loading}
          className="bg-orange-600 hover:bg-orange-700 disabled:opacity-50 px-6 py-2 rounded-lg font-bold transition"
        >
          Trigger Latency Spike
        </button>
        <button
          onClick={() => triggerFailure('cost')}
          disabled={loading}
          className="bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 px-6 py-2 rounded-lg font-bold transition"
        >
          Trigger Cost Anomaly
        </button>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricsCard
          title="Confidence Score"
          value={
            recoveredIncident?.confidence_score?.toFixed(2) ??
            incident?.classification?.confidence?.toFixed(2) ?? 
            '0.81'
          }
          unit=""
          trend={incident ? 'down' : 'stable'}
          threshold="0.70"
          icon={<Activity className="w-6 h-6" />}
        />
        <MetricsCard
          title="Latency"
          value={
            recoveredIncident?.latency_ms ??
            incident?.classification?.latency_ms ?? 
            1704
          }
          unit="ms"
          trend={incident ? 'up' : 'stable'}
          threshold="2340ms"
          icon={<TrendingUp className="w-6 h-6" />}
        />
        <MetricsCard
          title="Diversity Score"
          value={
            recoveredIncident?.diversity_score?.toFixed(2) ??
            incident?.classification?.diversity_score?.toFixed(2) ?? 
            '0.70'
          }
          unit=""
          trend="stable"
          threshold="0.50"
          icon={<Zap className="w-6 h-6" />}
        />
        <MetricsCard
          title="Requests"
          value="50k"
          unit="/day"
          trend={incident ? 'up' : 'stable'}
          threshold="baseline"
          icon={<TrendingUp className="w-6 h-6" />}
        />
      </div>

      {/* Recovered incident badge */}
      {recoveredIncident && (
        <div className="mb-8 p-4 bg-gradient-to-r from-green-600/20 to-emerald-600/20 border border-green-500/30 rounded-lg">
          <div className="flex items-center">
            <CheckCircle className="w-6 h-6 text-green-400 mr-3" />
            <div>
              <p className="text-green-400 font-bold">✓ Recovery Successful</p>
              <p className="text-green-300 text-sm">System returned to healthy state</p>
            </div>
          </div>
        </div>
      )}

      {/* Early warnings */}
      {incident && !recoveredIncident && <EarlyWarnings incident={incident} />}

      {/* Timeline + business impact */}
      {incident && !recoveredIncident && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          <div className="lg:col-span-2">
            <IncidentTimeline incident={incident} />
          </div>
          <div>
            <BusinessImpact incident={incident} />
          </div>
        </div>
      )}

      {/* Recovery actions */}
      {incident && !recoveredIncident && (
        <RecoveryActions incident={incident} onApply={handleApplyFix} />
      )}

      {/* Footer */}
      <div className="mt-12 pt-8 border-t border-gray-700 text-center text-gray-500 text-sm">
        <p>SENTINEL-G v1.0.0 | Real-time LLM Reliability Detection</p>
        <p className="mt-2">
          Use the controls above to simulate failures and apply fixes.
        </p>
      </div>
    </div>
  );
}
