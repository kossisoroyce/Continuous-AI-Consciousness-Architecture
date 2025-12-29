import React from 'react'
import { CONDITIONS } from './ConditionSelector'

export const ResultsSummary = ({
    results,
    allPromptsLength
}) => {
    const totalResults = results.raw.length + results.static_prompt.length + results.nurture.length
    if (totalResults === 0) return null

    const allComplete = results.raw.length === allPromptsLength &&
        results.static_prompt.length === allPromptsLength &&
        results.nurture.length === allPromptsLength

    return (
        <div className="bg-slate-800 rounded-lg p-4">
            <h4 className="text-sm font-medium text-slate-300 mb-3">Results Summary</h4>
            <div className="grid grid-cols-3 gap-4 text-center text-sm">
                {CONDITIONS.map(cond => (
                    <div key={cond.id} className="bg-slate-700/50 rounded p-3">
                        <div className="text-xs text-slate-500 mb-1">{cond.name.split(':')[0]}</div>
                        <div className={`text-lg font-semibold ${results[cond.id].length === allPromptsLength ? 'text-[#d4a62a]' : 'text-slate-400'
                            }`}>
                            {results[cond.id].length}/{allPromptsLength}
                        </div>
                    </div>
                ))}
            </div>

            {allComplete && (
                <div className="mt-4 p-3 bg-[#2d2310] border border-[#d4a62a]/30 rounded text-sm text-[#d4a62a] text-center">
                    ✓ All conditions complete! Export results for analysis.
                </div>
            )}
        </div>
    )
}
