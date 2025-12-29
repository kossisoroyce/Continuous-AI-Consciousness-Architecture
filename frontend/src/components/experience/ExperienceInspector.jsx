import React from 'react'

export const ExperienceInspector = ({
    experientialState,
    facts,
    questions,
    commitments
}) => {
    const totalItems = facts.length + questions.length + commitments.length

    if (totalItems === 0 && !experientialState) {
        return (
            <div className="h-full flex flex-col items-center justify-center p-6 text-center">
                <p className="text-xs text-slate-500">Start chatting to build working memory</p>
            </div>
        )
    }

    return (
        <div className="p-3 space-y-3">
            {/* Compact Stats Row */}
            {experientialState && (
                <div className="flex gap-2 text-[10px]">
                    <div className="flex-1 bg-slate-800/50 rounded px-2 py-1.5">
                        <span className="text-slate-500">Turns</span>
                        <span className="text-white ml-1 font-medium">{experientialState.interaction_count || 0}</span>
                    </div>
                    <div className="flex-1 bg-slate-800/50 rounded px-2 py-1.5">
                        <span className="text-slate-500">Mood</span>
                        <span className="text-white ml-1 font-medium">{experientialState.emotion_summary || 'neutral'}</span>
                    </div>
                </div>
            )}

            {/* Facts */}
            {facts.length > 0 && (
                <div>
                    <div className="text-[10px] font-bold text-[#d4a62a]/70 uppercase mb-1.5">Facts ({facts.length})</div>
                    <div className="space-y-1">
                        {facts.slice(0, 3).map((fact, i) => (
                            <div key={i} className="bg-slate-800/30 rounded px-2 py-1.5 text-[11px] text-slate-400 leading-snug">
                                {fact.content}
                            </div>
                        ))}
                        {facts.length > 3 && <p className="text-[10px] text-slate-600">+{facts.length - 3} more</p>}
                    </div>
                </div>
            )}

            {/* Questions */}
            {questions.length > 0 && (
                <div>
                    <div className="text-[10px] font-bold text-amber-400/70 uppercase mb-1.5">Questions ({questions.filter(q => !q.resolved).length})</div>
                    <div className="space-y-1">
                        {questions.filter(q => !q.resolved).slice(0, 2).map((q, i) => (
                            <div key={i} className="bg-slate-800/30 rounded px-2 py-1.5 text-[11px] text-slate-400 leading-snug">
                                {q.question}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Commitments */}
            {commitments.length > 0 && (
                <div>
                    <div className="text-[10px] font-bold text-purple-400/70 uppercase mb-1.5">Commitments ({commitments.filter(c => !c.fulfilled).length})</div>
                    <div className="space-y-1">
                        {commitments.filter(c => !c.fulfilled).slice(0, 2).map((c, i) => (
                            <div key={i} className="bg-slate-800/30 rounded px-2 py-1.5 text-[11px] text-slate-400 leading-snug">
                                {c.promise}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
