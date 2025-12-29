import React, { useState, useEffect } from 'react'
import { Brain, AlertTriangle, CheckCircle, RefreshCw, Eye } from 'lucide-react'

export function MentalModelView({ instanceId, operatorId, apiBase }) {
  const [projection, setProjection] = useState(null)
  const [alignment, setAlignment] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (instanceId && operatorId) {
      fetchData()
    }
  }, [instanceId, operatorId])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [projRes, alertsRes] = await Promise.all([
        fetch(`${apiBase}/hmt/mental-model/projection/${instanceId}/${operatorId}`),
        fetch(`${apiBase}/hmt/mental-model/alerts/${instanceId}/${operatorId}`)
      ])
      
      if (projRes.ok) {
        setProjection(await projRes.json())
      }
      if (alertsRes.ok) {
        const data = await alertsRes.json()
        setAlerts(data.alerts || [])
      }
    } catch (err) {
      console.error('Failed to fetch mental model:', err)
    } finally {
      setLoading(false)
    }
  }

  const clearAlerts = async () => {
    try {
      await fetch(`${apiBase}/hmt/mental-model/clear-alerts/${instanceId}?operator_id=${operatorId}`, {
        method: 'POST'
      })
      setAlerts([])
    } catch (err) {
      console.error('Failed to clear alerts:', err)
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-[#2d1010] border-[#ef4444]/30 text-[#ef4444]'
      case 'high': return 'bg-[#2d1a10] border-[#f97316]/30 text-[#f97316]'
      case 'medium': return 'bg-[#2d2310] border-[#d4a62a]/30 text-[#d4a62a]'
      default: return 'bg-[#0d1117] border-[#30363d] text-[#484f58]'
    }
  }

  return (
    <div className="p-3 space-y-2 bg-[#050810]">

      {/* What Operator Believes */}
      {projection && (
        <div className="space-y-2">
          <div className="text-[9px] text-[#d4a62a] uppercase tracking-wider font-mono">Operator's Perceived AI State</div>
          
          {/* Known Facts */}
          <div className="bg-[#0d1117] border border-[#30363d] p-2">
            <div className="flex items-center gap-1 text-[9px] text-[#8b949e] mb-1 font-mono">
              <Eye className="w-3 h-3" />
              <span className="uppercase tracking-wider">AI Knowledge ({Object.keys(projection.known_facts || {}).length})</span>
            </div>
            <div className="space-y-1">
              {Object.values(projection.known_facts || {}).slice(0, 3).map((belief, i) => (
                <div key={i} className="bg-[#0a0c0f] border border-[#30363d] px-2 py-1 text-[9px] text-[#8b949e] font-mono">
                  {belief.content?.substring(0, 50)}...
                  <span className="text-[#d4a62a] ml-1">({(belief.confidence * 100).toFixed(0)}%)</span>
                </div>
              ))}
              {Object.keys(projection.known_facts || {}).length === 0 && (
                <p className="text-[9px] text-[#484f58] font-mono">No beliefs tracked</p>
              )}
            </div>
          </div>

          {/* Trust Level */}
          <div className="bg-[#0d1117] border border-[#30363d] p-2">
            <div className="flex justify-between items-center text-[9px] font-mono">
              <span className="text-[#484f58] uppercase tracking-wider">Perceived Trust</span>
              <span className="text-[#e6edf3]">
                {projection.perceived_trust_level != null 
                  ? `${(projection.perceived_trust_level * 100).toFixed(0)}%` 
                  : '—'}
              </span>
            </div>
            <div className="h-1 bg-[#0a0c0f] border border-[#30363d] mt-1 overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-[#8b6914] to-[#d4a62a] transition-all"
                style={{ width: `${(projection.perceived_trust_level || 0) * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Misalignment Alerts */}
      {alerts.length > 0 && (
        <div className="border-t border-[#30363d] pt-2">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-1 text-[9px] text-[#d4a62a] font-mono">
              <AlertTriangle className="w-3 h-3" />
              <span className="uppercase tracking-wider font-bold">Misalignments ({alerts.length})</span>
            </div>
            <button
              onClick={clearAlerts}
              className="text-[8px] text-[#484f58] hover:text-[#8b949e] font-mono uppercase"
            >
              Clear
            </button>
          </div>
          
          <div className="space-y-1">
            {alerts.slice(0, 2).map((alert, i) => (
              <div key={i} className={`border p-2 ${getSeverityColor(alert.severity)}`}>
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-3 h-3 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="text-[9px] font-bold font-mono uppercase">{alert.type.replace('_', ' ')}</div>
                    <p className="text-[8px] opacity-80 font-mono">{alert.description?.substring(0, 60)}...</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Good Alignment Indicator */}
      {alerts.length === 0 && projection && (
        <div className="bg-[#2d2310] border border-[#d4a62a]/30 text-[#d4a62a] text-[9px] p-2 flex items-center gap-2 font-mono">
          <CheckCircle className="w-3 h-3" />
          <span className="uppercase tracking-wider">Models Aligned</span>
        </div>
      )}
    </div>
  )
}
