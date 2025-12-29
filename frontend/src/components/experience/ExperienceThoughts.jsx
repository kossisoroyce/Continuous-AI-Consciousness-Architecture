import React, { useEffect, useRef } from 'react'

export function ExperienceThoughts({ thoughts }) {
    const scrollRef = useRef(null)

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
    }, [thoughts])

    if (!thoughts || thoughts.length === 0) {
        return (
            <div className="h-full flex flex-col items-center justify-center p-6 text-center">
                <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center mb-3">
                    <span className="text-lg">💭</span>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">
                    When you stop chatting, the AI will start thinking aloud here
                </p>
            </div>
        )
    }

    return (
        <div ref={scrollRef} className="h-full overflow-y-auto p-3 space-y-2">
            {thoughts.map((t, i) => (
                <div key={i} className="bg-slate-800/50 rounded-lg p-3 border-l-2 border-purple-500/50">
                    <p className="text-xs text-slate-300 leading-relaxed italic">
                        "{t.thought}"
                    </p>
                    <div className="flex items-center justify-between mt-2">
                        <span className="text-[10px] text-purple-400/70 uppercase font-medium">{t.type}</span>
                        <span className="text-[10px] text-slate-600">
                            {new Date(t.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                    </div>
                </div>
            ))}
        </div>
    )
}
