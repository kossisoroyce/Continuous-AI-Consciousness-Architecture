import React, { useState, useEffect } from 'react';
import { 
  MessageSquare, Shield, Activity, Brain, Users, Plus, Download, 
  AlertTriangle, CheckCircle, Clock, Database, RefreshCw, Cpu,
  Radio, Target, Crosshair, Zap, Eye, ChevronRight
} from 'lucide-react';
import { useSession } from './contexts/SessionContext';
import { useInstance } from './contexts/InstanceContext';
import { SessionProvider } from './contexts/SessionContext';
import { InstanceProvider } from './contexts/InstanceContext';
import './styles/military.css';

// Components
import ExperientialPanel from './components/ExperientialPanel';
import { HMTPanel } from './components/hmt/HMTPanel';

// ========== TACTICAL UI COMPONENTS ==========

function TacticalHeader({ brainId, brains, onSelectBrain, onCreateBrain, status }) {
  const [showBrainList, setShowBrainList] = useState(false);
  
  return (
    <header className="h-12 bg-[#0d1117] border-b border-[#30363d] flex items-center justify-between px-4 font-mono relative z-50">
      {/* Left: System ID */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 border border-[#d4a62a] flex items-center justify-center relative">
            <Users className="w-4 h-4 text-[#d4a62a]" />
            <div className="absolute -top-px -left-px w-2 h-2 border-t border-l border-[#d4a62a]" />
            <div className="absolute -bottom-px -right-px w-2 h-2 border-b border-r border-[#d4a62a]" />
          </div>
          <div>
            <div className="text-[10px] text-[#8b949e] uppercase tracking-[0.2em]">HMT RESEARCH</div>
            <div className="text-xs text-[#d4a62a] font-bold tracking-wider">ELECTRIC SHEEP AFRICA</div>
          </div>
        </div>

        {/* Brain Selector */}
        <div className="relative">
          <button 
            onClick={() => setShowBrainList(!showBrainList)}
            className="flex items-center gap-2 px-3 py-1.5 bg-[#161b22] border border-[#30363d] hover:border-[#d4a62a] transition-colors"
          >
            <Brain className="w-3.5 h-3.5 text-[#22d3ee]" />
            <span className="text-[11px] text-[#e6edf3] uppercase tracking-wider">
              {brainId ? `BRAIN-${brainId.slice(0, 8)}` : 'NO BRAIN LOADED'}
            </span>
            <ChevronRight className={`w-3 h-3 text-[#8b949e] transition-transform ${showBrainList ? 'rotate-90' : ''}`} />
          </button>

          {showBrainList && (
            <>
              <div className="fixed inset-0" onClick={() => setShowBrainList(false)} />
              <div className="absolute top-full left-0 mt-1 w-72 bg-[#161b22] border border-[#30363d] z-50">
                <div className="p-2 border-b border-[#30363d]">
                  <div className="text-[9px] text-[#d4a62a] uppercase tracking-[0.2em]">Available Brains</div>
                </div>
                <div className="max-h-48 overflow-y-auto">
                  {brains.map(id => (
                    <button
                      key={id}
                      onClick={() => { onSelectBrain(id); setShowBrainList(false); }}
                      className={`w-full text-left px-3 py-2 text-[11px] font-mono hover:bg-[#21262d] flex items-center gap-2 ${
                        brainId === id ? 'text-[#22d3ee] bg-[#21262d]' : 'text-[#8b949e]'
                      }`}
                    >
                      <Database className="w-3 h-3" />
                      {id}
                    </button>
                  ))}
                  {brains.length === 0 && (
                    <div className="px-3 py-4 text-[10px] text-[#484f58] text-center uppercase">No brains initialized</div>
                  )}
                </div>
                <div className="p-2 border-t border-[#30363d]">
                  <button
                    onClick={() => { onCreateBrain(); setShowBrainList(false); }}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-[#d4a62a] hover:bg-[#b8942a] text-[#0a0c0f] text-[10px] font-bold uppercase tracking-wider"
                  >
                    <Plus className="w-3 h-3" /> Initialize New Brain
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Center: Time */}
      <div className="absolute left-1/2 -translate-x-1/2 text-center">
        <SystemClock />
      </div>

      {/* Right: Status */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1 bg-[#161b22] border border-[#30363d]">
          <div className={`w-2 h-2 rounded-full ${status === 'online' ? 'bg-[#10b981] animate-pulse' : 'bg-[#ef4444]'}`} />
          <span className="text-[10px] text-[#8b949e] uppercase tracking-wider">{status}</span>
        </div>
        <div className="text-[10px] text-[#484f58] uppercase">
          <span className="text-[#8b949e]">SYS</span> v0.2.0
        </div>
      </div>
    </header>
  );
}

function SystemClock() {
  const [time, setTime] = useState(new Date());
  
  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);
  
  return (
    <div className="font-mono">
      <div className="text-lg text-[#d4a62a] font-bold tracking-[0.15em]">
        {time.toLocaleTimeString('en-US', { hour12: false })}
      </div>
      <div className="text-[9px] text-[#484f58] uppercase tracking-[0.3em]">
        {time.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' }).toUpperCase()}
      </div>
    </div>
  );
}

function MetricCard({ label, value, unit, color = 'amber', trend }) {
  const colors = {
    amber: 'text-[#d4a62a] border-[#8b6914]',
    cyan: 'text-[#22d3ee] border-[#0891b2]',
    green: 'text-[#10b981] border-[#047857]',
    red: 'text-[#ef4444] border-[#991b1b]'
  };
  
  return (
    <div className="bg-[#0d1117] border border-[#30363d] p-3 relative">
      <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-[#d4a62a]" />
      <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-[#d4a62a]" />
      
      <div className="text-[9px] text-[#484f58] uppercase tracking-[0.2em] mb-1">{label}</div>
      <div className={`text-xl font-bold font-mono ${colors[color]}`}>
        {value}
        {unit && <span className="text-xs ml-1 opacity-60">{unit}</span>}
      </div>
      {trend !== undefined && (
        <div className={`text-[9px] mt-1 ${trend >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
          {trend >= 0 ? '▲' : '▼'} {Math.abs(trend).toFixed(1)}%
        </div>
      )}
    </div>
  );
}

function TacticalProgress({ label, value, max = 100, color = 'amber' }) {
  const pct = (value / max) * 100;
  const barColors = {
    amber: 'bg-gradient-to-r from-[#8b6914] to-[#d4a62a]',
    cyan: 'bg-gradient-to-r from-[#0891b2] to-[#22d3ee]',
    green: 'bg-gradient-to-r from-[#047857] to-[#10b981]',
    red: 'bg-gradient-to-r from-[#991b1b] to-[#ef4444]'
  };
  
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[9px] uppercase tracking-wider">
        <span className="text-[#8b949e]">{label}</span>
        <span className="text-[#e6edf3] font-mono">{value.toFixed(0)}{max === 100 ? '%' : `/${max}`}</span>
      </div>
      <div className="h-1 bg-[#0a0c0f] border border-[#30363d]">
        <div className={`h-full ${barColors[color]} transition-all duration-300`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function BrainStatusPanel({ brain, apiBase }) {
  if (!brain) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Cpu className="w-12 h-12 text-[#30363d] mx-auto mb-4" />
          <div className="text-[#484f58] text-sm uppercase tracking-wider">No Brain Selected</div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="h-full flex flex-col bg-[#0a0c0f] overflow-hidden">
      {/* Header */}
      <div className="p-3 border-b border-[#30363d] bg-[#0d1117]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-[#d4a62a]" />
            <span className="text-[10px] text-[#d4a62a] uppercase tracking-[0.2em] font-bold">Brain Status</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 rounded-full bg-[#10b981] animate-pulse" />
            <span className="text-[9px] text-[#10b981] uppercase">Active</span>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="p-3 space-y-3 flex-1 overflow-y-auto">
        <div className="grid grid-cols-2 gap-2">
          <MetricCard label="Stability" value={(brain.stability * 100).toFixed(0)} unit="%" color="cyan" />
          <MetricCard label="Plasticity" value={(brain.plasticity * 100).toFixed(0)} unit="%" color="amber" />
        </div>

        <div className="bg-[#0d1117] border border-[#30363d] p-3">
          <div className="text-[9px] text-[#d4a62a] uppercase tracking-[0.2em] mb-3">Trust Metrics</div>
          <div className="space-y-2">
            <TacticalProgress label="Calibration" value={brain.trust_calibration * 100} color="cyan" />
            <TacticalProgress label="Overtrust Risk" value={brain.overtrust_risk * 100} color="red" />
            <TacticalProgress label="Undertrust Risk" value={brain.undertrust_risk * 100} color="amber" />
          </div>
        </div>

        <div className="bg-[#0d1117] border border-[#30363d] p-3">
          <div className="text-[9px] text-[#d4a62a] uppercase tracking-[0.2em] mb-2">System Info</div>
          <div className="space-y-1 text-[10px] font-mono">
            <div className="flex justify-between">
              <span className="text-[#484f58]">PHASE</span>
              <span className="text-[#e6edf3] uppercase">{brain.phase}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#484f58]">INTERACTIONS</span>
              <span className="text-[#22d3ee]">{brain.interaction_count}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#484f58]">BRAIN ID</span>
              <span className="text-[#8b949e]">{brain.id?.slice(0, 12)}...</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function TacticalChatPanel({ instanceId, sessionId, apiKeyConfigured, openaiApiKey }) {
  return (
    <div className="h-full flex flex-col bg-[#0a0c0f]">
      {/* Header */}
      <div className="p-3 border-b border-[#30363d] bg-[#0d1117] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Radio className="w-4 h-4 text-[#22d3ee]" />
          <span className="text-[10px] text-[#22d3ee] uppercase tracking-[0.2em] font-bold">Operator Interface</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="text-[9px] text-[#484f58] uppercase">SESSION</div>
          <div className="text-[10px] text-[#8b949e] font-mono">{sessionId?.slice(0, 8) || '---'}</div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-hidden">
        <ExperientialPanel
          instanceId={instanceId}
          sessionId={sessionId}
          apiKeyConfigured={apiKeyConfigured}
          openaiApiKey={openaiApiKey}
        />
      </div>
    </div>
  );
}

function HMTMetricsPanel({ instanceId, apiBase }) {
  return (
    <div className="h-full flex flex-col bg-[#0a0c0f]">
      {/* Header */}
      <div className="p-3 border-b border-[#30363d] bg-[#0d1117] flex items-center gap-2">
        <Eye className="w-4 h-4 text-[#d4a62a]" />
        <span className="text-[10px] text-[#d4a62a] uppercase tracking-[0.2em] font-bold">HMT Analytics</span>
      </div>

      {/* HMT Panel */}
      <div className="flex-1 overflow-hidden">
        <HMTPanel
          instanceId={instanceId}
          operatorId="default"
          apiBase={apiBase}
        />
      </div>
    </div>
  );
}

// ========== MAIN LAYOUT ==========

function MainLayout() {
  const { 
    selectedInstanceId, 
    instanceState, 
    createInstance, 
    instances,
    selectInstance,
    error,
    setError
  } = useInstance();
  
  const { 
    sessionId, 
    apiBase, 
    apiKeyConfigured, 
    openaiApiKey 
  } = useSession();

  return (
    <div className="h-screen w-screen bg-[#0a0c0f] flex flex-col overflow-hidden font-sans">
      <TacticalHeader 
        brainId={selectedInstanceId}
        brains={instances}
        onSelectBrain={selectInstance}
        onCreateBrain={createInstance}
        status={selectedInstanceId ? 'online' : 'standby'}
      />

      <main className="flex-1 flex overflow-hidden min-h-0">
        {selectedInstanceId && instanceState ? (
          <>
            {/* Left Panel: Brain Status (fixed width) */}
            <div className="w-64 border-r border-[#30363d] flex-shrink-0">
              <BrainStatusPanel brain={instanceState} apiBase={apiBase} />
            </div>

            {/* Center: Operator Interface (flexible) */}
            <div className="flex-1 min-w-0 border-r border-[#30363d]">
              <TacticalChatPanel
                instanceId={selectedInstanceId}
                sessionId={sessionId}
                apiKeyConfigured={apiKeyConfigured}
                openaiApiKey={openaiApiKey}
              />
            </div>

            {/* Right Panel: HMT Analytics (fixed width) */}
            <div className="w-80 flex-shrink-0">
              <HMTMetricsPanel instanceId={selectedInstanceId} apiBase={apiBase} />
            </div>
          </>
        ) : (
          /* Welcome Screen */
          <div className="flex-1 flex items-center justify-center relative">
            {/* Grid overlay */}
            <div className="absolute inset-0 opacity-20" style={{
              backgroundImage: `
                linear-gradient(rgba(212, 166, 42, 0.1) 1px, transparent 1px),
                linear-gradient(90deg, rgba(212, 166, 42, 0.1) 1px, transparent 1px)
              `,
              backgroundSize: '50px 50px'
            }} />

            <div className="text-center max-w-3xl px-8 relative z-10">
              {/* Logo */}
              <div className="w-24 h-24 border-2 border-[#d4a62a] flex items-center justify-center mx-auto mb-8 relative">
                <Users className="w-12 h-12 text-[#d4a62a]" />
                <div className="absolute -top-1 -left-1 w-4 h-4 border-t-2 border-l-2 border-[#d4a62a]" />
                <div className="absolute -top-1 -right-1 w-4 h-4 border-t-2 border-r-2 border-[#d4a62a]" />
                <div className="absolute -bottom-1 -left-1 w-4 h-4 border-b-2 border-l-2 border-[#d4a62a]" />
                <div className="absolute -bottom-1 -right-1 w-4 h-4 border-b-2 border-r-2 border-[#d4a62a]" />
              </div>

              <h1 className="text-3xl font-bold text-[#e6edf3] tracking-[0.1em] uppercase mb-2">
                Human-Machine Teaming
              </h1>
              <p className="text-[#d4a62a] text-sm uppercase tracking-[0.3em] mb-8">
                Research Platform
              </p>

              <p className="text-[#8b949e] mb-12 max-w-xl mx-auto leading-relaxed">
                Initialize an AI brain to begin operator-AI collaboration research.
                All brain states are persisted with automatic backup and recovery.
              </p>

              {/* Capabilities */}
              <div className="grid grid-cols-3 gap-4 mb-12">
                {[
                  { icon: Shield, label: 'Trust Calibration', desc: 'Measure confidence vs accuracy' },
                  { icon: Activity, label: 'Workload Tracking', desc: 'Adaptive response verbosity' },
                  { icon: Brain, label: 'Mental Models', desc: 'Belief alignment detection' }
                ].map(({ icon: Icon, label, desc }) => (
                  <div key={label} className="bg-[#0d1117] border border-[#30363d] p-4 relative">
                    <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-[#d4a62a]" />
                    <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-[#d4a62a]" />
                    <Icon className="w-6 h-6 text-[#d4a62a] mb-3 mx-auto" />
                    <div className="text-[11px] text-[#e6edf3] uppercase tracking-wider font-bold mb-1">{label}</div>
                    <div className="text-[10px] text-[#484f58]">{desc}</div>
                  </div>
                ))}
              </div>

              <button
                onClick={createInstance}
                className="inline-flex items-center gap-3 bg-[#d4a62a] hover:bg-[#b8942a] text-[#0a0c0f] py-4 px-10 font-bold text-sm uppercase tracking-[0.15em] transition-colors"
              >
                <Zap className="w-5 h-5" />
                Initialize Brain
              </button>

              <div className="mt-6 text-[10px] text-[#484f58] uppercase tracking-wider">
                Brain data persisted to SQLite with WAL journaling
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Error Toast */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-[#991b1b] border border-[#ef4444] text-white px-4 py-3 z-50 flex items-center gap-3 font-mono text-sm">
          <AlertTriangle className="w-4 h-4" />
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-white/60 hover:text-white ml-2">×</button>
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <SessionProvider>
      <InstanceProvider>
        <MainLayout />
      </InstanceProvider>
    </SessionProvider>
  );
}

export default App;
