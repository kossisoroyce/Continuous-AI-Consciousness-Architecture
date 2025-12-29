import React from 'react'
import { cn } from '../../lib/utils'

export const CONDITIONS = [
    { id: 'raw', name: 'Control A: Raw Model', description: 'No system prompt' },
    { id: 'static_prompt', name: 'Control B: Static Prompt', description: 'Best-case prompt engineering' },
    { id: 'nurture', name: 'Experimental: Nurture Layer', description: 'Dynamic character formation' }
]

export const ConditionSelector = ({
    selectedCondition,
    setSelectedCondition,
    instanceId,
    results,
    allPromptsCount,
    isRunning
}) => {
    return (
        <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-300">Select Condition to Run</h4>
            <div className="grid grid-cols-1 gap-2">
                {CONDITIONS.map(cond => (
                    <button
                        key={cond.id}
                        onClick={() => setSelectedCondition(cond.id)}
                        disabled={isRunning || (cond.id === 'nurture' && !instanceId)}
                        className={cn(
                            "p-3 rounded-lg border text-left transition-colors",
                            selectedCondition === cond.id
                                ? 'border-purple-500 bg-purple-900/30'
                                : 'border-slate-700 bg-slate-800/50 hover:border-slate-600',
                            (cond.id === 'nurture' && !instanceId) && 'opacity-50'
                        )}
                    >
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="text-sm font-medium text-slate-200">{cond.name}</div>
                                <div className="text-xs text-slate-500">{cond.description}</div>
                            </div>
                            <div className="text-xs text-slate-500">
                                {results?.[cond.id]?.length || 0}/{allPromptsCount}
                            </div>
                        </div>
                    </button>
                ))}
            </div>
            {selectedCondition === 'nurture' && !instanceId && (
                <p className="text-xs text-amber-400">Create an instance first to run Nurture Layer condition</p>
            )}
        </div>
    )
}
