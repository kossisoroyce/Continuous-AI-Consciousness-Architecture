import React, { useState } from 'react';
import { MessageSquare, BarChart3, Activity, Shield, Download, Users, Plus, Zap, Brain, Settings, Target } from 'lucide-react';
import { useSession } from './contexts/SessionContext';
import { useInstance } from './contexts/InstanceContext';
import { SessionProvider } from './contexts/SessionContext';
import { InstanceProvider } from './contexts/InstanceContext';

// Components
import InteractionPanel from './components/InteractionPanel';
import MetricsPanel from './components/MetricsPanel';
import HistoryPanel from './components/HistoryPanel';
import ExperientialPanel from './components/ExperientialPanel';
import { HMTPanel } from './components/hmt/HMTPanel';
import { WorkloadIndicator } from './components/hmt/WorkloadIndicator';
import { TrustDashboard } from './components/hmt/TrustDashboard';

// HMT Header Component
function HMTHeader({ instanceId, instances, selectInstance, createInstance }) {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <header className="bg-slate-900 border-b border-slate-800 h-14 flex items-center justify-between px-6 z-50 relative flex-shrink-0">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg">
            <Users className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight leading-none">HMT Research Platform</h1>
            <p className="text-[10px] text-slate-500 font-medium">Human-Machine Teaming • Electric Sheep Africa</p>
          </div>
        </div>

        {/* AI Partner Selector */}
        <div className="relative ml-4">
          <button 
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition-all text-sm"
          >
            <Brain className="w-4 h-4 text-purple-400" />
            <span className="text-slate-300 font-mono text-xs">
              {instanceId ? instanceId.slice(0, 12) : "Select AI Partner"}
            </span>
          </button>

          {isOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
              <div className="absolute top-full left-0 mt-2 w-64 bg-slate-800 rounded-lg border border-slate-700 shadow-xl z-20 py-1">
                <div className="max-h-48 overflow-y-auto">
                  {instances.map(id => (
                    <button
                      key={id}
                      onClick={() => { selectInstance(id); setIsOpen(false); }}
                      className={`w-full text-left px-3 py-2 text-xs font-mono hover:bg-slate-700 ${
                        instanceId === id ? 'text-cyan-400 bg-slate-700/50' : 'text-slate-300'
                      }`}
                    >
                      {id}
                    </button>
                  ))}
                  {instances.length === 0 && (
                    <div className="px-3 py-2 text-xs text-slate-500">No AI partners created</div>
                  )}
                </div>
                <div className="border-t border-slate-700 p-2">
                  <button
                    onClick={() => { createInstance(); setIsOpen(false); }}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold rounded"
                  >
                    <Plus className="w-3 h-3" /> New AI Partner
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="px-3 py-1 bg-slate-800 rounded-full border border-slate-700">
          <span className="flex items-center gap-2 text-xs text-slate-400">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Online
          </span>
        </div>
      </div>
    </header>
  );
}

function MainLayout() {
  const { 
    selectedInstanceId, 
    instanceState, 
    createInstance, 
    instances,
    selectInstance,
    updateInstanceState, 
    error,
    setError
  } = useInstance();
  
  const { 
    sessionId, 
    apiBase, 
    apiKeyConfigured, 
    refreshBackendKeyStatus,
    openrouterApiKey 
  } = useSession();

  const [activeTab, setActiveTab] = useState('collaborate');
  const [analysisTab, setAnalysisTab] = useState('trust');

  const handleInteraction = (response) => {
    if (response && response.state && response.state.instance_id) {
      updateInstanceState(response.state);
    }
  };

  const exportData = async () => {
    if (!selectedInstanceId) return;
    try {
      const res = await fetch(`${apiBase}/hmt/state/${selectedInstanceId}/default`);
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `hmt-data-${selectedInstanceId}-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to export data');
    }
  };

  return (
    <div className="h-screen bg-slate-950 flex flex-col overflow-hidden">
      <HMTHeader 
        instanceId={selectedInstanceId}
        instances={instances}
        selectInstance={selectInstance}
        createInstance={createInstance}
      />

      <main className="flex-1 flex flex-col overflow-hidden min-h-0">
        {selectedInstanceId && instanceState ? (
          <>
            {/* Primary Navigation - HMT Focused */}
            <div className="bg-slate-900 border-b border-slate-800 px-6 flex-shrink-0">
              <div className="flex justify-between items-center h-11">
                <div className="flex gap-1 h-full">
                  {[
                    { id: 'collaborate', icon: MessageSquare, label: 'Collaborate' },
                    { id: 'analyze', icon: BarChart3, label: 'Analyze' },
                    { id: 'configure', icon: Settings, label: 'Configure' },
                  ].map(tab => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center gap-2 px-4 h-full text-sm font-medium transition-colors border-b-2 ${
                        activeTab === tab.id
                          ? 'text-cyan-400 border-cyan-500'
                          : 'text-slate-400 border-transparent hover:text-slate-200'
                      }`}
                    >
                      <tab.icon className="w-4 h-4" />
                      {tab.label}
                    </button>
                  ))}
                </div>

                <div className="flex items-center gap-4">
                  {/* Live HMT Status */}
                  <WorkloadIndicator instanceId={selectedInstanceId} apiBase={apiBase} compact />
                  
                  <button
                    onClick={exportData}
                    className="p-1.5 text-slate-400 hover:text-cyan-400 transition-colors"
                    title="Export HMT Data"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-hidden min-h-0">
              {/* COLLABORATE - Main interaction with HMT sidebar */}
              {activeTab === 'collaborate' && (
                <div className="h-full flex">
                  {/* Chat Area */}
                  <div className="flex-1 min-w-0">
                    <ExperientialPanel
                      instanceId={selectedInstanceId}
                      sessionId={sessionId}
                      apiKeyConfigured={apiKeyConfigured}
                      openrouterApiKey={openrouterApiKey}
                    />
                  </div>
                  
                  {/* HMT Metrics Sidebar */}
                  <div className="w-80 border-l border-slate-800 bg-slate-900 flex-shrink-0 overflow-y-auto">
                    <HMTPanel
                      instanceId={selectedInstanceId}
                      operatorId="default"
                      apiBase={apiBase}
                    />
                  </div>
                </div>
              )}

              {/* ANALYZE - Deep HMT Analytics */}
              {activeTab === 'analyze' && (
                <div className="h-full flex flex-col">
                  <div className="bg-slate-900 border-b border-slate-800 px-6 py-2 flex-shrink-0">
                    <div className="flex gap-2">
                      {[
                        { id: 'trust', icon: Shield, label: 'Trust Calibration' },
                        { id: 'workload', icon: Activity, label: 'Workload History' },
                        { id: 'mental', icon: Brain, label: 'Mental Models' },
                        { id: 'metrics', icon: BarChart3, label: 'AI Metrics' },
                      ].map(tab => (
                        <button
                          key={tab.id}
                          onClick={() => setAnalysisTab(tab.id)}
                          className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                            analysisTab === tab.id
                              ? 'bg-cyan-900/30 text-cyan-300 ring-1 ring-cyan-500/50'
                              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                          }`}
                        >
                          <tab.icon className="w-3 h-3" />
                          {tab.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="flex-1 overflow-y-auto p-6">
                    {analysisTab === 'trust' && (
                      <div className="max-w-4xl mx-auto">
                        <h2 className="text-lg font-bold text-white mb-4">Trust Calibration Analysis</h2>
                        <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                          <TrustDashboard
                            instanceId={selectedInstanceId}
                            operatorId="default"
                            apiBase={apiBase}
                          />
                        </div>
                      </div>
                    )}
                    {analysisTab === 'metrics' && (
                      <div className="max-w-4xl mx-auto">
                        <h2 className="text-lg font-bold text-white mb-4">AI Partner Metrics</h2>
                        <MetricsPanel instanceState={instanceState} />
                      </div>
                    )}
                    {(analysisTab === 'workload' || analysisTab === 'mental') && (
                      <div className="max-w-4xl mx-auto">
                        <div className="bg-slate-900 rounded-xl border border-slate-800">
                          <HMTPanel
                            instanceId={selectedInstanceId}
                            operatorId="default"
                            apiBase={apiBase}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* CONFIGURE - Settings and Debug */}
              {activeTab === 'configure' && (
                <div className="h-full overflow-y-auto p-6">
                  <div className="max-w-2xl mx-auto space-y-6">
                    <h2 className="text-lg font-bold text-white">Configuration</h2>
                    
                    <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                      <InteractionPanel
                        instanceId={selectedInstanceId}
                        instanceState={instanceState}
                        onInteraction={handleInteraction}
                        apiBase={apiBase}
                        sessionId={sessionId}
                        apiKeyConfigured={apiKeyConfigured}
                        onApiKeyChange={refreshBackendKeyStatus}
                      />
                    </div>

                    <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
                      <h3 className="text-sm font-bold text-slate-300 mb-3">Session History</h3>
                      <HistoryPanel instanceId={selectedInstanceId} apiBase={apiBase} />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          /* HMT-Focused Welcome Screen */
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center max-w-2xl px-6">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center mx-auto mb-8 shadow-2xl">
                <Users className="w-10 h-10 text-white" />
              </div>
              <h2 className="text-3xl font-bold text-white mb-4">
                Human-Machine Teaming Research
              </h2>
              <p className="text-slate-400 mb-10 leading-relaxed text-lg">
                Build calibrated trust between human operators and AI systems.
                Measure, adapt, and optimize collaboration in real-time.
              </p>

              {/* HMT Capabilities */}
              <div className="grid grid-cols-3 gap-4 mb-10 text-left">
                <div className="bg-slate-900/80 rounded-xl p-5 border border-slate-800">
                  <Shield className="w-6 h-6 text-purple-400 mb-3" />
                  <h3 className="text-sm font-bold text-white mb-2">Trust Calibration</h3>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Track if AI confidence predicts actual correctness. Identify overtrust and undertrust risks.
                  </p>
                </div>
                <div className="bg-slate-900/80 rounded-xl p-5 border border-slate-800">
                  <Activity className="w-6 h-6 text-cyan-400 mb-3" />
                  <h3 className="text-sm font-bold text-white mb-2">Workload Adaptation</h3>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    AI detects operator cognitive load and adjusts response verbosity automatically.
                  </p>
                </div>
                <div className="bg-slate-900/80 rounded-xl p-5 border border-slate-800">
                  <Brain className="w-6 h-6 text-amber-400 mb-3" />
                  <h3 className="text-sm font-bold text-white mb-2">Mental Model Tracking</h3>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Detect when operator's beliefs about AI diverge from reality. Auto-repair misalignments.
                  </p>
                </div>
              </div>

              {/* Research Applications */}
              <div className="bg-slate-900/50 rounded-xl p-4 mb-8 border border-slate-800">
                <p className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-2">Research Applications</p>
                <div className="flex justify-center gap-3 flex-wrap">
                  {['DARPA Programs', 'ONR Human-AI Teaming', 'AFRL Autonomy', 'Defense R&D'].map(app => (
                    <span key={app} className="px-3 py-1 bg-slate-800 rounded-full text-xs text-slate-400">
                      {app}
                    </span>
                  ))}
                </div>
              </div>

              <button
                onClick={createInstance}
                className="inline-flex items-center gap-3 bg-cyan-600 hover:bg-cyan-500 text-white py-4 px-10 rounded-xl transition-all font-medium text-lg shadow-xl shadow-cyan-900/30"
              >
                <Plus className="w-5 h-5" />
                Initialize AI Partner
              </button>
              <p className="text-slate-600 text-xs mt-4">Creates an AI instance with HMT instrumentation</p>
            </div>
          </div>
        )}
      </main>

      {/* Error Toast */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-red-500/90 backdrop-blur text-white px-4 py-3 rounded-lg shadow-xl border border-red-400 z-50 flex items-center gap-3">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="opacity-80 hover:opacity-100">×</button>
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
