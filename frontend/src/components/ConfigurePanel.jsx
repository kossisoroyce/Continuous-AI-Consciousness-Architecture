import React, { useState, useEffect } from 'react'
import { Settings, User, Brain, X, Save, RotateCcw } from 'lucide-react'

export function ConfigurePanel({ isOpen, onClose, apiBase, instanceId }) {
  const [operatorName, setOperatorName] = useState('')
  const [experientialConfig, setExperientialConfig] = useState({
    selfStimulationInterval: 30,
    memoryConsolidation: true,
    thoughtGateSensitivity: 0.5
  })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    // Load saved settings from localStorage
    const savedName = localStorage.getItem('hmt_operator_name')
    if (savedName) setOperatorName(savedName)

    const savedConfig = localStorage.getItem('hmt_experiential_config')
    if (savedConfig) {
      try {
        setExperientialConfig(JSON.parse(savedConfig))
      } catch (e) {
        console.error('Failed to parse experiential config', e)
      }
    }
  }, [isOpen])

  const handleSave = async () => {
    setSaving(true)
    
    // Save to localStorage
    localStorage.setItem('hmt_operator_name', operatorName)
    localStorage.setItem('hmt_experiential_config', JSON.stringify(experientialConfig))

    // Optionally send to backend if instance exists
    if (instanceId && apiBase) {
      try {
        await fetch(`${apiBase}/experience/config/${instanceId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            operator_name: operatorName,
            ...experientialConfig
          })
        })
      } catch (err) {
        console.error('Failed to save config to backend', err)
      }
    }

    setSaving(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleReset = () => {
    setOperatorName('')
    setExperientialConfig({
      selfStimulationInterval: 30,
      memoryConsolidation: true,
      thoughtGateSensitivity: 0.5
    })
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-[#0a0c0f] border border-[#30363d] w-full max-w-md mx-4 overflow-hidden">
        {/* Corner brackets */}
        <div className="absolute top-0 left-0 w-4 h-4 border-t border-l border-[#6b7280]" />
        <div className="absolute top-0 right-0 w-4 h-4 border-t border-r border-[#6b7280]" />
        <div className="absolute bottom-0 left-0 w-4 h-4 border-b border-l border-[#6b7280]" />
        <div className="absolute bottom-0 right-0 w-4 h-4 border-b border-r border-[#6b7280]" />

        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#30363d] bg-[#0d1117]">
          <div className="flex items-center gap-2">
            <Settings className="w-4 h-4 text-[#9ca3af]" />
            <span className="text-[11px] font-bold text-[#9ca3af] uppercase tracking-[0.15em] font-mono">
              Configure
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-[#21262d] text-[#8b949e] hover:text-[#e6edf3] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-6">
          
          {/* Operator Settings */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 mb-2">
              <User className="w-3.5 h-3.5 text-[#9ca3af]" />
              <span className="text-[10px] font-bold text-[#9ca3af] uppercase tracking-wider font-mono">
                Operator Settings
              </span>
            </div>
            
            <div className="bg-[#0d1117] border border-[#30363d] p-3">
              <label className="block text-[9px] text-[#484f58] uppercase tracking-wider font-mono mb-1">
                Preferred Name
              </label>
              <input
                type="text"
                value={operatorName}
                onChange={(e) => setOperatorName(e.target.value)}
                placeholder="Enter your name..."
                className="w-full bg-[#0a0c0f] border border-[#30363d] px-3 py-2 text-[11px] text-[#e6edf3] font-mono placeholder-[#484f58] focus:outline-none focus:border-[#6b7280]"
              />
              <p className="text-[8px] text-[#484f58] mt-1 font-mono">
                AI will use this name when addressing you
              </p>
            </div>
          </div>

          {/* Experiential Layer Settings */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 mb-2">
              <Brain className="w-3.5 h-3.5 text-[#9ca3af]" />
              <span className="text-[10px] font-bold text-[#9ca3af] uppercase tracking-wider font-mono">
                Experiential Layer
              </span>
            </div>

            {/* Self-Stimulation Interval */}
            <div className="bg-[#0d1117] border border-[#30363d] p-3">
              <div className="flex justify-between items-center mb-2">
                <label className="text-[9px] text-[#484f58] uppercase tracking-wider font-mono">
                  Self-Stimulation Interval
                </label>
                <span className="text-[10px] text-[#e6edf3] font-mono">
                  {experientialConfig.selfStimulationInterval}s
                </span>
              </div>
              <div className="relative w-full h-1 bg-[#30363d]">
                <div 
                  className="absolute h-full bg-[#6b7280]" 
                  style={{ width: `${((experientialConfig.selfStimulationInterval - 10) / 110) * 100}%` }}
                />
                <input
                  type="range"
                  min="10"
                  max="120"
                  step="5"
                  value={experientialConfig.selfStimulationInterval}
                  onChange={(e) => setExperientialConfig(prev => ({
                    ...prev,
                    selfStimulationInterval: parseInt(e.target.value)
                  }))}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div 
                  className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-[#9ca3af] border border-[#6b7280]"
                  style={{ left: `calc(${((experientialConfig.selfStimulationInterval - 10) / 110) * 100}% - 6px)` }}
                />
              </div>
              <p className="text-[8px] text-[#484f58] mt-1 font-mono">
                How often AI generates internal thoughts
              </p>
            </div>

            {/* Memory Consolidation */}
            <div className="bg-[#0d1117] border border-[#30363d] p-3">
              <div className="flex justify-between items-center">
                <div>
                  <label className="text-[9px] text-[#484f58] uppercase tracking-wider font-mono block">
                    Memory Consolidation
                  </label>
                  <p className="text-[8px] text-[#484f58] mt-0.5 font-mono">
                    Background memory processing
                  </p>
                </div>
                <button
                  onClick={() => setExperientialConfig(prev => ({
                    ...prev,
                    memoryConsolidation: !prev.memoryConsolidation
                  }))}
                  className={`w-10 h-5 flex items-center px-0.5 transition-colors ${
                    experientialConfig.memoryConsolidation 
                      ? 'bg-[#6b7280] justify-end' 
                      : 'bg-[#30363d] justify-start'
                  }`}
                >
                  <div className="w-4 h-4 bg-[#e6edf3]" />
                </button>
              </div>
            </div>

            {/* Thought Gate Sensitivity */}
            <div className="bg-[#0d1117] border border-[#30363d] p-3">
              <div className="flex justify-between items-center mb-2">
                <label className="text-[9px] text-[#484f58] uppercase tracking-wider font-mono">
                  Thought Gate Sensitivity
                </label>
                <span className="text-[10px] text-[#e6edf3] font-mono">
                  {(experientialConfig.thoughtGateSensitivity * 100).toFixed(0)}%
                </span>
              </div>
              <div className="relative w-full h-1 bg-[#30363d]">
                <div 
                  className="absolute h-full bg-[#6b7280]" 
                  style={{ width: `${experientialConfig.thoughtGateSensitivity * 100}%` }}
                />
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={experientialConfig.thoughtGateSensitivity * 100}
                  onChange={(e) => setExperientialConfig(prev => ({
                    ...prev,
                    thoughtGateSensitivity: parseInt(e.target.value) / 100
                  }))}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div 
                  className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-[#9ca3af] border border-[#6b7280]"
                  style={{ left: `calc(${experientialConfig.thoughtGateSensitivity * 100}% - 6px)` }}
                />
              </div>
              <p className="text-[8px] text-[#484f58] mt-1 font-mono">
                Filter threshold for spontaneous thoughts
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-[#30363d] bg-[#0d1117]">
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-1.5 text-[9px] font-mono uppercase tracking-wider text-[#8b949e] hover:text-[#e6edf3] border border-[#30363d] hover:border-[#484f58] transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            Reset
          </button>
          
          <button
            onClick={handleSave}
            disabled={saving}
            className={`flex items-center gap-1.5 px-4 py-1.5 text-[9px] font-mono uppercase tracking-wider transition-colors ${
              saved 
                ? 'bg-[#6b7280] text-[#0a0c0f]' 
                : 'bg-[#9ca3af] hover:bg-[#d1d5db] text-[#0a0c0f]'
            }`}
          >
            <Save className="w-3 h-3" />
            {saving ? 'Saving...' : saved ? 'Saved!' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}
