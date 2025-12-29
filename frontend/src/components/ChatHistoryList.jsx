import React, { useState, useEffect } from 'react'
import { Clock, MessageSquare, ChevronRight, Loader } from 'lucide-react'
import { getSessions } from '../services/cognitiveApi'

export function ChatHistoryList({ currentSessionId, onSelectSession, onReplaySession }) {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    try {
      setLoading(true)
      const data = await getSessions(20, 0) // Limit 20 for sidebar
      setSessions(data.sessions || [])
    } catch (err) {
      setError('Failed to load history')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading && sessions.length === 0) {
    return (
      <div className="p-4 text-center">
        <Loader className="w-4 h-4 text-[#d4a62a] animate-spin mx-auto" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 text-center text-[#ef4444] text-[10px]">
        {error}
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-[#0a0c0f]">
      <div className="p-2 border-b border-[#30363d] flex justify-between items-center">
        <span className="text-[10px] text-[#8b949e] uppercase tracking-wider">Recent Sessions</span>
        <button onClick={fetchHistory} className="text-[#d4a62a] hover:text-[#e6edf3]">
          <Clock className="w-3 h-3" />
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        {sessions.length === 0 ? (
          <div className="p-4 text-center text-[#484f58] text-[10px] italic">
            No history available
          </div>
        ) : (
          <div className="divide-y divide-[#30363d]">
            {sessions.map(session => (
              <div 
                key={session.session_id}
                className={`w-full p-3 hover:bg-[#161b22] transition-colors group flex items-start gap-2 ${
                  currentSessionId === session.session_id ? 'bg-[#161b22] border-l-2 border-[#d4a62a]' : ''
                }`}
              >
                <div 
                  className="flex-1 cursor-pointer"
                  onClick={() => onSelectSession(session.session_id)}
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className={`text-[11px] font-mono truncate max-w-[140px] ${
                      currentSessionId === session.session_id ? 'text-[#d4a62a]' : 'text-[#e6edf3]'
                    }`}>
                      {session.title || 'Untitled Session'}
                    </span>
                    <span className="text-[9px] text-[#484f58]">
                      {new Date(session.start_time).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-[9px] text-[#8b949e]">
                    <MessageSquare className="w-3 h-3" />
                    <span>{session.event_count} events</span>
                  </div>
                </div>
                
                {onReplaySession && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onReplaySession(session.session_id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1.5 text-[#d4a62a] hover:bg-[#21262d] rounded transition-all"
                    title="Replay Mission"
                  >
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
