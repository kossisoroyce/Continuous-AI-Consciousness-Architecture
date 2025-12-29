import React from 'react'
import { MessageSquare, Zap, Brain, Lightbulb, Radio } from 'lucide-react'

export const ExperienceSplash = ({
    startSession,
    loading,
    instanceId
}) => {
    return (
        <div className="h-full flex items-center justify-center p-8 bg-[#050810]">
            <div className="text-center max-w-lg">
                {/* Tactical Logo */}
                <div className="w-16 h-16 border-2 border-[#d4a62a] flex items-center justify-center mx-auto mb-6 relative">
                    <Radio className="w-7 h-7 text-[#d4a62a]" />
                    <div className="absolute -top-1 -left-1 w-3 h-3 border-t-2 border-l-2 border-[#d4a62a]" />
                    <div className="absolute -top-1 -right-1 w-3 h-3 border-t-2 border-r-2 border-[#d4a62a]" />
                    <div className="absolute -bottom-1 -left-1 w-3 h-3 border-b-2 border-l-2 border-[#d4a62a]" />
                    <div className="absolute -bottom-1 -right-1 w-3 h-3 border-b-2 border-r-2 border-[#d4a62a]" />
                </div>
                
                <h2 className="text-xl font-bold text-[#e6edf3] mb-2 uppercase tracking-[0.15em] font-mono">
                    Initialize Comms Link
                </h2>
                <p className="text-[#8b949e] mb-8 leading-relaxed text-sm">
                    Establish operator-AI communication channel. All interactions are logged and analyzed.
                </p>

                {/* Capability Cards */}
                <div className="grid grid-cols-3 gap-3 mb-8 text-left">
                    <div className="bg-[#0d1117] p-4 border border-[#30363d] relative">
                        <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-[#d4a62a]" />
                        <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-[#d4a62a]" />
                        <MessageSquare className="w-5 h-5 text-[#d4a62a] mb-2" />
                        <h3 className="text-[10px] font-bold text-[#e6edf3] mb-1 uppercase tracking-wider font-mono">Comms</h3>
                        <p className="text-[10px] text-[#8b949e] leading-snug">Bidirectional operator exchange</p>
                    </div>
                    <div className="bg-[#0d1117] p-4 border border-[#30363d] relative">
                        <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-[#d4a62a]" />
                        <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-[#d4a62a]" />
                        <Lightbulb className="w-5 h-5 text-[#d4a62a] mb-2" />
                        <h3 className="text-[10px] font-bold text-[#e6edf3] mb-1 uppercase tracking-wider font-mono">Intel</h3>
                        <p className="text-[10px] text-[#8b949e] leading-snug">Facts, queries, commitments</p>
                    </div>
                    <div className="bg-[#0d1117] p-4 border border-[#30363d] relative">
                        <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-[#d4a62a]" />
                        <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-[#d4a62a]" />
                        <Brain className="w-5 h-5 text-[#d4a62a] mb-2" />
                        <h3 className="text-[10px] font-bold text-[#e6edf3] mb-1 uppercase tracking-wider font-mono">Cognition</h3>
                        <p className="text-[10px] text-[#8b949e] leading-snug">Real-time internal processing</p>
                    </div>
                </div>

                <button
                    onClick={startSession}
                    disabled={loading || !instanceId}
                    className="inline-flex items-center gap-2 bg-[#d4a62a] hover:bg-[#b8942a] disabled:bg-[#30363d] disabled:text-[#484f58] text-[#0a0c0f] py-3 px-8 transition-all font-bold text-sm uppercase tracking-wider font-mono"
                >
                    {loading ? (
                        <span className="animate-pulse">Initializing...</span>
                    ) : (
                        <>Establish Link</>
                    )}
                </button>
                {!instanceId && (
                    <p className="text-[#d4a62a] text-[10px] mt-4 uppercase tracking-wider font-mono">
                        ↑ Select brain from header first
                    </p>
                )}
            </div>
        </div>
    )
}
