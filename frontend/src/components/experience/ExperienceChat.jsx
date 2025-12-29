import React, { useRef, useEffect, useState } from 'react'
import { RefreshCw, ArrowUp, X, MessageSquare, Volume2, VolumeX } from 'lucide-react'
import { VoiceControls, speakResponse, stopSpeaking } from '../voice/VoiceControls'
import * as cognitiveApi from '../../services/cognitiveApi'

const OPERATOR_ID = 'default'
const AI_NAME = 'HMT Zero'

export const ExperienceChat = ({
    conversation,
    message,
    setMessage,
    interacting,
    sendIntegratedMessage,
    apiKeyConfigured,
    fetchExperientialState,
    endSession
}) => {
    const scrollRef = useRef(null)
    const [ttsEnabled, setTtsEnabled] = useState(false)
    const [operatorName, setOperatorName] = useState('Operator')
    const lastSpokenIndex = useRef(-1)

    // Load operator name from config
    useEffect(() => {
        const savedName = localStorage.getItem('hmt_operator_name')
        if (savedName) setOperatorName(savedName)
    }, [])

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
    }, [conversation])

    // Handle TTS for new AI messages
    useEffect(() => {
        if (ttsEnabled && conversation.length > 0) {
            const lastMsg = conversation[conversation.length - 1]
            const lastIdx = conversation.length - 1
            
            if (lastMsg.role === 'assistant' && lastIdx > lastSpokenIndex.current) {
                // Fetch real cognitive load to adjust voice
                const playTTS = async () => {
                    try {
                        let loadState = 'medium'
                        const loadData = await cognitiveApi.getCognitiveLoad(OPERATOR_ID)
                        if (loadData && loadData.state) {
                            loadState = loadData.state // 'overload', 'high', 'optimal', 'underload'
                        }
                        
                        // Map state to TTS load parameter
                        // high/overload -> 'high' (fast, urgent)
                        // optimal/underload -> 'low' (calm, slower)
                        const ttsLoad = (loadState === 'high' || loadState === 'overload') ? 'high' : 'low'
                        
                        speakResponse(lastMsg.content, ttsLoad)
                        lastSpokenIndex.current = lastIdx
                    } catch (e) {
                        console.error('TTS Load Check Failed:', e)
                        // Fallback
                        speakResponse(lastMsg.content, 'medium')
                        lastSpokenIndex.current = lastIdx
                    }
                }
                playTTS()
            }
        }
    }, [conversation, ttsEnabled])

    const handleVoiceInput = (transcript) => {
        setMessage(transcript)
    }

    return (
        <div className="h-full flex flex-col bg-[#04070d]">
            {/* Minimal Header */}
            <div className="flex-shrink-0 bg-[#060b12] border-b border-[#1f272f] px-4 py-2 flex items-center justify-between">
                <span className="text-[10px] font-medium text-[#484f58] uppercase tracking-[0.2em] font-mono">
                    {AI_NAME} • Session Active
                </span>
                <div className="flex items-center gap-1">
                    <button
                        onClick={() => {
                            if (ttsEnabled) stopSpeaking();
                            setTtsEnabled(!ttsEnabled);
                        }}
                        className={`p-1.5 hover:bg-[#21262d] transition-colors ${ttsEnabled ? 'text-[#d4a62a]' : 'text-[#484f58]'}`}
                        title={ttsEnabled ? "Mute Voice" : "Enable Voice"}
                    >
                        {ttsEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
                    </button>
                    <button
                        onClick={fetchExperientialState}
                        className="p-1.5 hover:bg-[#21262d] text-[#484f58] hover:text-[#8b949e]"
                        title="Refresh"
                    >
                        <RefreshCw className="w-3.5 h-3.5" />
                    </button>
                    <button
                        onClick={endSession}
                        className="p-1.5 hover:bg-[#3d1f1f] text-[#484f58] hover:text-[#ef4444]"
                        title="End Session"
                    >
                        <X className="w-3.5 h-3.5" />
                    </button>
                </div>
            </div>

            {/* Conversation - Clean text flow */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
                {conversation.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-center px-8">
                        <p className="text-[#484f58] text-xs font-mono">Begin conversation with {AI_NAME}</p>
                    </div>
                )}
                {conversation.map((msg, i) => (
                    <div key={i} className="space-y-1">
                        {/* Sender name */}
                        <div className={`text-[10px] uppercase tracking-wider font-mono font-medium ${
                            msg.role === 'user' 
                                ? 'text-[#d4a62a]' 
                                : msg.role === 'error' 
                                    ? 'text-[#ef4444]' 
                                    : 'text-[#8b949e]'
                        }`}>
                            {msg.role === 'user' ? operatorName : msg.role === 'error' ? 'System Error' : AI_NAME}
                        </div>
                        {/* Message content - plain text, no bubble */}
                        <div className={`text-[13px] leading-relaxed font-mono pl-0 ${
                            msg.role === 'user'
                                ? 'text-[#e6edf3]'
                                : msg.role === 'error'
                                    ? 'text-[#ef4444]/80'
                                    : 'text-[#c9d1d9]'
                        }`}>
                            {msg.content}
                        </div>
                    </div>
                ))}
                {interacting && (
                    <div className="space-y-1">
                        <div className="text-[10px] uppercase tracking-wider font-mono font-medium text-[#8b949e]">
                            {AI_NAME}
                        </div>
                        <div className="flex items-center gap-1.5 text-[#484f58]">
                            <span className="w-1 h-1 bg-[#d4a62a] rounded-full animate-pulse"></span>
                            <span className="w-1 h-1 bg-[#d4a62a] rounded-full animate-pulse" style={{animationDelay: '0.15s'}}></span>
                            <span className="w-1 h-1 bg-[#d4a62a] rounded-full animate-pulse" style={{animationDelay: '0.3s'}}></span>
                        </div>
                    </div>
                )}
            </div>

            {/* Input - Clean minimal design */}
            <div className="flex-shrink-0 border-t border-[#1f272f] p-3 bg-[#060b12]">
                {!apiKeyConfigured ? (
                    <div className="text-center py-2">
                        <p className="text-[#484f58] text-[10px] uppercase tracking-wider font-mono">
                            Configure API key to begin
                        </p>
                    </div>
                ) : (
                    <div className="flex items-center gap-2">
                        <VoiceControls 
                            onTranscript={handleVoiceInput}
                            enabled={!interacting}
                        />
                        <div className="flex-1 relative">
                            <input
                                type="text"
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendIntegratedMessage()}
                                placeholder="Message..."
                                className="w-full bg-[#0d1117] border border-[#30363d] px-3 py-2 text-[13px] text-[#e6edf3] placeholder-[#484f58] focus:outline-none focus:border-[#484f58] font-mono"
                                disabled={interacting}
                            />
                        </div>
                        <button
                            onClick={() => sendIntegratedMessage()}
                            disabled={!message.trim() || interacting}
                            className="px-4 py-2 bg-[#d4a62a] disabled:bg-[#30363d] text-[#05070d] disabled:text-[#484f58] text-[11px] font-mono uppercase tracking-wider font-medium transition-colors hover:bg-[#e5b93b]"
                        >
                            Send
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}
