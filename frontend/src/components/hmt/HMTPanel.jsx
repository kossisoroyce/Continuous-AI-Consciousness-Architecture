import React, { useState } from 'react'
import { Users, Shield, Activity, Brain, ChevronDown, ChevronUp, Settings } from 'lucide-react'
import { TrustDashboard } from './TrustDashboard'
import { WorkloadIndicator } from './WorkloadIndicator'
import { MentalModelView } from './MentalModelView'

export function HMTPanel({ instanceId, operatorId = 'default', apiBase, onOpenConfig }) {
  const [collapsed, setCollapsed] = useState({
    trust: false,
    workload: false,
    mental: false
  })

  const toggleSection = (section) => {
    setCollapsed(prev => ({ ...prev, [section]: !prev[section] }))
  }

  return (
    <div className="h-full flex flex-col bg-[#050810] overflow-hidden">
      {/* Content - No scroll */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Trust Calibration Section */}
        <div className="border-b border-[#30363d]">
          <button
            onClick={() => toggleSection('trust')}
            className="w-full flex items-center justify-between px-4 py-2 hover:bg-[#21262d]"
          >
            <div className="flex items-center gap-2">
              <Shield className="w-3.5 h-3.5 text-[#d4a62a]" />
              <span className="text-[10px] font-medium text-[#e6edf3] uppercase tracking-wider font-mono">Trust Calibration</span>
            </div>
            {collapsed.trust ? (
              <ChevronDown className="w-3.5 h-3.5 text-[#484f58]" />
            ) : (
              <ChevronUp className="w-3.5 h-3.5 text-[#484f58]" />
            )}
          </button>
          {!collapsed.trust && (
            <TrustDashboard
              instanceId={instanceId}
              operatorId={operatorId}
              apiBase={apiBase}
            />
          )}
        </div>

        {/* Workload Section */}
        <div className="border-b border-[#30363d]">
          <button
            onClick={() => toggleSection('workload')}
            className="w-full flex items-center justify-between px-4 py-2 hover:bg-[#21262d]"
          >
            <div className="flex items-center gap-2">
              <Activity className="w-3.5 h-3.5 text-[#8b949e]" />
              <span className="text-[10px] font-medium text-[#e6edf3] uppercase tracking-wider font-mono">Operator Workload</span>
            </div>
            {collapsed.workload ? (
              <ChevronDown className="w-3.5 h-3.5 text-[#484f58]" />
            ) : (
              <ChevronUp className="w-3.5 h-3.5 text-[#484f58]" />
            )}
          </button>
          {!collapsed.workload && (
            <WorkloadIndicator
              instanceId={instanceId}
              apiBase={apiBase}
            />
          )}
        </div>

        {/* Mental Model Section */}
        <div className="border-b border-[#30363d]">
          <button
            onClick={() => toggleSection('mental')}
            className="w-full flex items-center justify-between px-4 py-2 hover:bg-[#21262d]"
          >
            <div className="flex items-center gap-2">
              <Brain className="w-3.5 h-3.5 text-[#d4a62a]" />
              <span className="text-[10px] font-medium text-[#e6edf3] uppercase tracking-wider font-mono">Mental Model</span>
            </div>
            {collapsed.mental ? (
              <ChevronDown className="w-3.5 h-3.5 text-[#484f58]" />
            ) : (
              <ChevronUp className="w-3.5 h-3.5 text-[#484f58]" />
            )}
          </button>
          {!collapsed.mental && (
            <MentalModelView
              instanceId={instanceId}
              operatorId={operatorId}
              apiBase={apiBase}
            />
          )}
        </div>

      </div>

      {/* Configure Link - Fixed at bottom */}
      <div className="flex-shrink-0 border-t border-[#30363d] bg-[#0d1117]">
        <button
          onClick={onOpenConfig}
          className="w-full flex items-center gap-2 px-4 py-2 hover:bg-[#21262d] text-[#8b949e] hover:text-[#d4a62a] transition-colors"
        >
          <Settings className="w-3.5 h-3.5" />
          <span className="text-[10px] font-medium uppercase tracking-wider font-mono">Configure</span>
        </button>
      </div>
    </div>
  )
}

// Compact version for sidebar/header display
export function HMTCompactStatus({ instanceId, apiBase }) {
  return (
    <div className="flex items-center gap-2">
      <WorkloadIndicator instanceId={instanceId} apiBase={apiBase} compact />
    </div>
  )
}
