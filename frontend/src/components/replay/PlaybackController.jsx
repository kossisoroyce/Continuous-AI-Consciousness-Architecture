import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipBack, SkipForward, Clock, Rewind } from 'lucide-react';
import { getAuditEvents } from '../../services/cognitiveApi';

export function PlaybackController({ sessionId, onPlaybackUpdate, onExit }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0); // Offset in ms from start
  const [duration, setDuration] = useState(0);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  
  const startTimeRef = useRef(0);
  const requestRef = useRef();
  const lastTickRef = useRef();

  // Load session data
  useEffect(() => {
    async function loadSession() {
      if (!sessionId) return;
      
      setLoading(true);
      try {
        // Fetch all events for the session
        // In a real app, we might need pagination or sparse loading
        const data = await getAuditEvents({ sessionId, limit: 1000 });
        
        if (data.events && data.events.length > 0) {
          // Sort by timestamp ascending
          const sortedEvents = [...data.events].sort((a, b) => 
            new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
          );
          
          setEvents(sortedEvents);
          
          const start = new Date(sortedEvents[0].timestamp).getTime();
          const end = new Date(sortedEvents[sortedEvents.length - 1].timestamp).getTime();
          
          startTimeRef.current = start;
          setDuration(end - start + 5000); // Add 5s buffer
          setCurrentTime(0);
          
          // Initial update
          updateParent(0, sortedEvents, start);
        }
      } catch (err) {
        console.error("Failed to load replay data:", err);
      } finally {
        setLoading(false);
      }
    }
    
    loadSession();
  }, [sessionId]);

  // Playback loop
  useEffect(() => {
    if (isPlaying) {
      lastTickRef.current = Date.now();
      requestRef.current = requestAnimationFrame(animate);
    } else {
      cancelAnimationFrame(requestRef.current);
    }
    return () => cancelAnimationFrame(requestRef.current);
  }, [isPlaying, duration]);

  const animate = () => {
    const now = Date.now();
    const delta = now - lastTickRef.current;
    lastTickRef.current = now;
    
    setCurrentTime(prev => {
      const nextTime = prev + delta * playbackSpeed;
      if (nextTime >= duration) {
        setIsPlaying(false);
        return duration;
      }
      return nextTime;
    });
    
    requestRef.current = requestAnimationFrame(animate);
  };

  // Sync with parent when time changes
  useEffect(() => {
    if (events.length > 0) {
      updateParent(currentTime, events, startTimeRef.current);
    }
  }, [currentTime, events]);

  const updateParent = (offset, allEvents, startTs) => {
    const currentAbsTime = startTs + offset;
    
    // Find events that have happened up to this point
    const pastEvents = allEvents.filter(e => 
      new Date(e.timestamp).getTime() <= currentAbsTime
    );
    
    // Derive state from events
    let lastTelemetry = null;
    let lastDetections = [];
    const conversation = []; // Reconstruct conversation
    
    pastEvents.forEach(e => {
      // Telemetry
      if (e.event_type === 'detection.track' && e.action === 'telemetry_update') {
        lastTelemetry = e.details;
      }
      
      // Detections
      if (e.event_type === 'detection.new' && e.action === 'objects_detected') {
        if (e.details && e.details.objects) {
          // Map back to format expected by GISMapPanel
          lastDetections = e.details.objects.map(obj => ({
            ...obj,
            id: obj.id || `replay_${Math.random()}`, // Ensure ID exists
            location: obj.location || { lat: 0, lon: 0 } // Fallback
          }));
        }
      }
      
      // Chat reconstruction
      if (e.event_type === 'operator.command' && e.action === 'chat_input') {
        conversation.push({ role: 'user', content: e.details.message });
      }
      if (e.event_type === 'ai.recommendation' && e.action === 'chat_response') {
        conversation.push({ role: 'assistant', content: e.details.recommendation });
      }
      
      // VQA Reconstruction
      if (e.event_type === 'ai.recommendation' && e.action === 'visual_analysis') {
        // We can show this in conversation or special overlay. For now, inject as assistant message about vision.
        conversation.push({ 
          role: 'assistant', 
          content: `[VISUAL INTELLIGENCE REPORT]\n${e.details.recommendation}`,
          isVisualReport: true 
        });
      }
    });
    
    const latestState = {
      timestamp: currentAbsTime,
      events: pastEvents,
      telemetry: lastTelemetry,
      detections: lastDetections,
      conversation: conversation
    };
    
    onPlaybackUpdate(latestState);
  };

  const handleSeek = (e) => {
    const newTime = parseInt(e.target.value);
    setCurrentTime(newTime);
  };

  const formatTime = (ms) => {
    const seconds = Math.floor(ms / 1000);
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return <div className="p-4 text-[#d4a62a] font-mono text-xs">LOADING MISSION DATA...</div>;
  }

  if (events.length === 0) {
    return <div className="p-4 text-[#8b949e] font-mono text-xs">NO MISSION DATA FOUND</div>;
  }

  return (
    <div className="bg-[#0d1117] border-t border-[#30363d] p-2 flex flex-col gap-2">
      {/* Timeline Scrubber */}
      <div className="flex items-center gap-3">
        <span className="text-[10px] font-mono text-[#d4a62a] w-10 text-right">
          {formatTime(currentTime)}
        </span>
        <input
          type="range"
          min="0"
          max={duration}
          value={currentTime}
          onChange={handleSeek}
          className="flex-1 h-1 bg-[#30363d] rounded-lg appearance-none cursor-pointer accent-[#d4a62a]"
        />
        <span className="text-[10px] font-mono text-[#8b949e] w-10">
          {formatTime(duration)}
        </span>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between px-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="p-1.5 bg-[#d4a62a] text-[#0a0c0f] rounded hover:bg-[#b8942a] transition-colors"
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          
          <button
            onClick={() => setCurrentTime(0)}
            className="p-1.5 text-[#8b949e] hover:text-[#e6edf3]"
            title="Reset"
          >
            <Rewind className="w-4 h-4" />
          </button>

          <div className="h-4 w-px bg-[#30363d] mx-1" />
          
          <div className="flex gap-1">
            {[1, 2, 5].map(speed => (
              <button
                key={speed}
                onClick={() => setPlaybackSpeed(speed)}
                className={`px-1.5 py-0.5 text-[9px] font-mono border ${
                  playbackSpeed === speed 
                    ? 'text-[#d4a62a] border-[#d4a62a]' 
                    : 'text-[#8b949e] border-[#30363d] hover:border-[#8b949e]'
                }`}
              >
                {speed}x
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="px-2 py-0.5 bg-[#161b22] border border-[#30363d] text-[10px] font-mono text-[#e6edf3]">
            {new Date(startTimeRef.current + currentTime).toLocaleString()}
          </div>
          <button
            onClick={onExit}
            className="px-3 py-1 bg-[#3d1f1f] text-[#ef4444] text-[10px] font-mono uppercase tracking-wider hover:bg-[#4d2525] border border-[#ef4444]/30"
          >
            Exit Debrief
          </button>
        </div>
      </div>
    </div>
  );
}
