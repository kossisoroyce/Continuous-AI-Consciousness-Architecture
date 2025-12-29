import React, { useState, useEffect } from 'react'
import { Activity, Zap, Coffee, AlertCircle, AlertTriangle } from 'lucide-react'

export function WorkloadIndicator({ instanceId, apiBase, operatorId = 'default', compact = false }) {
  const [workload, setWorkload] = useState(null)
  const [cognitiveLoad, setCognitiveLoad] = useState(null)
  const [responseConfig, setResponseConfig] = useState(null)

  useEffect(() => {
    if (instanceId) {
      fetchWorkload()
      const interval = setInterval(fetchWorkload, 5000) // Update every 5s
      return () => clearInterval(interval)
    }
  }, [instanceId, operatorId])

  const fetchWorkload = async () => {
    try {
      // Fetch from both HMT workload and new cognitive load APIs
      const [workloadRes, configRes, cogLoadRes] = await Promise.all([
        fetch(`${apiBase}/hmt/workload/estimate/${instanceId}`).catch(() => null),
        fetch(`${apiBase}/hmt/workload/config/${instanceId}`).catch(() => null),
        fetch(`${apiBase}/cognitive/load/${operatorId}`).catch(() => null)
      ])
      
      if (workloadRes?.ok) {
        setWorkload(await workloadRes.json())
      }
      if (configRes?.ok) {
        setResponseConfig(await configRes.json())
      }
      if (cogLoadRes?.ok) {
        setCognitiveLoad(await cogLoadRes.json())
      }
    } catch (err) {
      console.error('Failed to fetch workload:', err)
    }
  }

  if (!workload) {
    return null
  }

  const level = workload.level
  const mode = workload.interaction_mode

  const getModeConfig = () => {
    if (mode === 'proactive') {
      return {
        icon: Zap,
        color: 'text-[#d4a62a]',
        bg: 'bg-[#2d2310] border border-[#d4a62a]/30',
        label: 'Proactive',
        description: 'Full assistance available'
      }
    } else if (mode === 'responsive') {
      return {
        icon: Activity,
        color: 'text-[#d4a62a]',
        bg: 'bg-[#2d2310] border border-[#d4a62a]/30',
        label: 'Responsive',
        description: 'Answering when asked'
      }
    } else {
      return {
        icon: Coffee,
        color: 'text-[#ef4444]',
        bg: 'bg-[#2d1010] border border-[#ef4444]/30',
        label: 'Minimal',
        description: 'Brief responses only'
      }
    }
  }

  const config = getModeConfig()
  const Icon = config.icon

  if (compact) {
    return (
      <div className={`flex items-center gap-1.5 px-2 py-1 ${config.bg}`}>
        <Icon className={`w-3 h-3 ${config.color}`} />
        <span className={`text-[10px] font-medium font-mono uppercase tracking-wider ${config.color}`}>{config.label}</span>
      </div>
    )
  }

  return (
    <div className="p-3 space-y-2 bg-[#050810]">
      {/* Mode Indicator */}
      <div className={`${config.bg} p-2`}>
        <div className="flex items-center gap-2 mb-1">
          <Icon className={`w-4 h-4 ${config.color}`} />
          <span className={`text-[10px] font-bold font-mono uppercase tracking-wider ${config.color}`}>{config.label} Mode</span>
        </div>
        <p className="text-[9px] text-[#484f58] font-mono">{config.description}</p>
      </div>

      {/* Workload Bar */}
      <div className="bg-[#0d1117] border border-[#30363d] p-2">
        <div className="flex justify-between text-[9px] font-mono mb-1">
          <span className="text-[#484f58] uppercase tracking-wider">Cognitive Load</span>
          <span className="text-[#e6edf3]">{level > 0 ? `${(level * 100).toFixed(0)}%` : 'baseline'}</span>
        </div>
        <div className="h-1 bg-[#0a0c0f] border border-[#30363d] overflow-hidden">
          <div 
            className={`h-full transition-all ${
              level < 0.3 ? 'bg-[#d4a62a]' :
              level < 0.7 ? 'bg-[#d4a62a]' : 'bg-[#ef4444]'
            }`}
            style={{ width: `${level * 100}%` }}
          />
        </div>
      </div>

      {/* Component Scores */}
      <div className="grid grid-cols-2 gap-1 text-[9px] font-mono">
        <div className="bg-[#0d1117] border border-[#30363d] px-2 py-1">
          <span className="text-[#484f58]">Latency</span>
          <span className="text-[#8b949e] ml-1">{workload.latency_score > 0 ? `${(workload.latency_score * 100).toFixed(0)}%` : '—'}</span>
        </div>
        <div className="bg-[#0d1117] border border-[#30363d] px-2 py-1">
          <span className="text-[#484f58]">Brevity</span>
          <span className="text-[#8b949e] ml-1">{workload.brevity_score > 0 ? `${(workload.brevity_score * 100).toFixed(0)}%` : '—'}</span>
        </div>
        <div className="bg-[#0d1117] border border-[#30363d] px-2 py-1">
          <span className="text-[#484f58]">Errors</span>
          <span className="text-[#8b949e] ml-1">{workload.error_score > 0 ? `${(workload.error_score * 100).toFixed(0)}%` : '—'}</span>
        </div>
        <div className="bg-[#0d1117] border border-[#30363d] px-2 py-1">
          <span className="text-[#484f58]">Fatigue</span>
          <span className="text-[#8b949e] ml-1">{workload.fatigue_score > 0 ? `${(workload.fatigue_score * 100).toFixed(0)}%` : '—'}</span>
        </div>
      </div>

      {/* Cognitive Load Prediction (from new API) */}
      {cognitiveLoad && cognitiveLoad.state !== 'unknown' && (
        <div className="bg-[#0d1117] border border-[#30363d] p-2">
          <div className="flex justify-between items-center text-[9px] font-mono mb-1">
            <span className="text-[#484f58] uppercase tracking-wider">Predicted Load</span>
            <span className={`px-1.5 py-0.5 text-[8px] uppercase ${
              cognitiveLoad.state === 'overload' ? 'bg-[#2d1010] text-[#ef4444]' :
              cognitiveLoad.state === 'high' ? 'bg-[#2d2010] text-[#f59e0b]' :
              cognitiveLoad.state === 'optimal' ? 'bg-[#102d10] text-[#10b981]' :
              'bg-[#2d2310] text-[#d4a62a]'
            }`}>
              {cognitiveLoad.state}
            </span>
          </div>
          {cognitiveLoad.overload_risk > 0.5 && (
            <div className="flex items-center gap-1 text-[9px] text-[#ef4444] font-mono mt-1">
              <AlertTriangle className="w-3 h-3" />
              <span>Overload risk: {(cognitiveLoad.overload_risk * 100).toFixed(0)}%</span>
            </div>
          )}
          {cognitiveLoad.recommendations?.length > 0 && (
            <div className="mt-2 text-[8px] text-[#8b949e] font-mono">
              {cognitiveLoad.recommendations[0]}
            </div>
          )}
        </div>
      )}

      {/* Response Config */}
      {responseConfig && (
        <div className="border-t border-[#30363d] pt-2">
          <div className="text-[9px] text-[#d4a62a] uppercase tracking-wider font-mono mb-1">AI Response Adaptation</div>
          <div className="flex flex-wrap gap-1">
            <span className={`px-1.5 py-0.5 text-[8px] font-mono uppercase ${
              responseConfig.include_explanation ? 'bg-[#2d2310] border border-[#d4a62a]/30 text-[#d4a62a]' : 'bg-[#0d1117] border border-[#30363d] text-[#484f58]'
            }`}>
              Explanations
            </span>
            <span className={`px-1.5 py-0.5 text-[8px] font-mono uppercase ${
              responseConfig.include_proactive_info ? 'bg-[#2d2310] border border-[#d4a62a]/30 text-[#d4a62a]' : 'bg-[#0d1117] border border-[#30363d] text-[#484f58]'
            }`}>
              Proactive
            </span>
            <span className={`px-1.5 py-0.5 text-[8px] font-mono uppercase ${
              responseConfig.ask_clarifying_questions ? 'bg-[#2d2310] border border-[#d4a62a]/30 text-[#d4a62a]' : 'bg-[#0d1117] border border-[#30363d] text-[#484f58]'
            }`}>
              Clarify
            </span>
          </div>
          <div className="mt-1 text-[8px] text-[#484f58] font-mono">
            Max: {responseConfig.max_length} chars
          </div>
        </div>
      )}
    </div>
  )
}
