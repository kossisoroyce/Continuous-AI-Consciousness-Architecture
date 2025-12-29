import React, { useState, useEffect } from 'react'
import { Shield, TrendingUp, TrendingDown, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'

export function TrustDashboard({ instanceId, operatorId, apiBase }) {
  const [trustState, setTrustState] = useState(null)
  const [pending, setPending] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (instanceId && operatorId) {
      fetchTrustMetrics()
      fetchPending()
    }
  }, [instanceId, operatorId])

  const fetchTrustMetrics = async () => {
    try {
      const res = await fetch(`${apiBase}/hmt/trust/metrics/${instanceId}/${operatorId}`)
      if (res.ok) {
        const data = await res.json()
        setTrustState(data)
      }
    } catch (err) {
      console.error('Failed to fetch trust metrics:', err)
    }
  }

  const fetchPending = async () => {
    try {
      const res = await fetch(`${apiBase}/hmt/trust/pending/${instanceId}/${operatorId}`)
      if (res.ok) {
        const data = await res.json()
        setPending(data.pending || [])
      }
    } catch (err) {
      console.error('Failed to fetch pending:', err)
    }
  }

  const recordOutcome = async (recId, wasCorrect) => {
    setLoading(true)
    try {
      await fetch(`${apiBase}/hmt/trust/outcome`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          instance_id: instanceId,
          recommendation_id: recId,
          was_correct: wasCorrect
        })
      })
      await fetchTrustMetrics()
      await fetchPending()
    } catch (err) {
      console.error('Failed to record outcome:', err)
    } finally {
      setLoading(false)
    }
  }

  // Handle no data or insufficient data
  const hasData = trustState && trustState.total_recommendations > 0
  const calibration = hasData ? trustState.calibration_score : 0.5
  const accuracy = hasData ? trustState.overall_accuracy : 0
  const overtrust = hasData ? trustState.overtrust_risk : 0
  const undertrust = hasData ? trustState.undertrust_risk : 0
  const acceptance = hasData ? trustState.acceptance_rate : 0
  const totalRecs = trustState?.total_recommendations || 0

  if (!trustState) {
    return (
      <div className="p-4 text-center text-[#484f58] text-sm font-mono">
        <Shield className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p className="text-[10px] uppercase tracking-wider">No trust data yet</p>
      </div>
    )
  }

  const calibrationColor = !hasData ? 'text-[#484f58]' :
    calibration > 0.7 ? 'text-[#d4a62a]' :
    calibration > 0.5 ? 'text-[#d4a62a]' : 'text-[#ef4444]'

  return (
    <div className="p-3 space-y-3 bg-[#050810]">

      {/* Key Metrics */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-[#0d1117] border border-[#30363d] p-2 relative">
          <div className="absolute top-0 left-0 w-1.5 h-1.5 border-t border-l border-[#d4a62a]" />
          <div className="text-[9px] text-[#484f58] uppercase tracking-wider font-mono mb-1">Calibration</div>
          <div className={`text-lg font-bold font-mono ${calibrationColor}`}>
            {hasData ? `${(calibration * 100).toFixed(0)}%` : '—'}
          </div>
          <div className="text-[9px] text-[#484f58]">{hasData ? 'confidence ↔ accuracy' : 'awaiting data'}</div>
        </div>

        <div className="bg-[#0d1117] border border-[#30363d] p-2 relative">
          <div className="absolute top-0 left-0 w-1.5 h-1.5 border-t border-l border-[#d4a62a]" />
          <div className="text-[9px] text-[#484f58] uppercase tracking-wider font-mono mb-1">Accuracy</div>
          <div className={`text-lg font-bold font-mono ${hasData ? 'text-[#d4a62a]' : 'text-[#484f58]'}`}>
            {hasData ? `${(accuracy * 100).toFixed(0)}%` : '—'}
          </div>
          <div className="text-[9px] text-[#484f58]">{totalRecs} recs</div>
        </div>
      </div>

      {/* Risk Indicators */}
      <div className="flex gap-2">
        <div className={`flex-1 px-2 py-1.5 text-[9px] font-mono border ${
          hasData && overtrust > 0.3 ? 'bg-[#3d1f1f] border-[#ef4444]/30 text-[#ef4444]' : 'bg-[#0d1117] border-[#30363d] text-[#484f58]'
        }`}>
          <TrendingUp className="w-3 h-3 inline mr-1" />
          Overtrust: {hasData ? `${(overtrust * 100).toFixed(0)}%` : '—'}
        </div>
        <div className={`flex-1 px-2 py-1.5 text-[9px] font-mono border ${
          hasData && undertrust > 0.3 ? 'bg-[#3d2f1f] border-[#d4a62a]/30 text-[#d4a62a]' : 'bg-[#0d1117] border-[#30363d] text-[#484f58]'
        }`}>
          <TrendingDown className="w-3 h-3 inline mr-1" />
          Undertrust: {hasData ? `${(undertrust * 100).toFixed(0)}%` : '—'}
        </div>
      </div>

      {/* Acceptance Rate */}
      <div className="bg-[#0d1117] border border-[#30363d] p-2">
        <div className="flex justify-between items-center text-[9px] font-mono">
          <span className="text-[#484f58] uppercase tracking-wider">Acceptance Rate</span>
          <span className="text-[#e6edf3] font-medium">{hasData ? `${(acceptance * 100).toFixed(0)}%` : '—'}</span>
        </div>
        <div className="h-1 bg-[#0a0c0f] border border-[#30363d] mt-1 overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-[#8b6914] to-[#d4a62a] transition-all"
            style={{ width: `${hasData ? acceptance * 100 : 0}%` }}
          />
        </div>
      </div>

      {/* Confidence Adjustment */}
      {hasData && trustState.recommended_confidence_adjustment !== 0 && (
        <div className={`text-[10px] p-2 rounded ${
          trustState.recommended_confidence_adjustment > 0 
            ? 'bg-[#2d2310] text-[#d4a62a]' 
            : 'bg-amber-900/20 text-amber-400'
        }`}>
          <AlertTriangle className="w-3 h-3 inline mr-1" />
          Recommended: {trustState.recommended_confidence_adjustment > 0 ? 'Increase' : 'Decrease'} AI confidence by{' '}
          {Math.abs(trustState.recommended_confidence_adjustment * 100).toFixed(0)}%
        </div>
      )}

      {/* Pending Recommendations */}
      {pending.length > 0 && (
        <div className="border-t border-slate-800 pt-3">
          <div className="text-[10px] text-slate-500 uppercase mb-2">Pending Feedback ({pending.length})</div>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {pending.slice(0, 3).map(rec => (
              <div key={rec.id} className="bg-slate-800/30 rounded p-2">
                <p className="text-[11px] text-slate-300 mb-2 line-clamp-2">{rec.recommendation}</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => recordOutcome(rec.id, true)}
                    disabled={loading}
                    className="flex-1 flex items-center justify-center gap-1 bg-[#2d2310] hover:bg-[#3d3320] text-[#d4a62a] text-[10px] py-1"
                  >
                    <CheckCircle className="w-3 h-3" /> Correct
                  </button>
                  <button
                    onClick={() => recordOutcome(rec.id, false)}
                    disabled={loading}
                    className="flex-1 flex items-center justify-center gap-1 bg-red-600/20 hover:bg-red-600/30 text-red-400 text-[10px] py-1 rounded"
                  >
                    <XCircle className="w-3 h-3" /> Incorrect
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
