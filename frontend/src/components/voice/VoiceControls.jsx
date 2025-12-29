import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Mic, MicOff, Volume2, VolumeX, Activity, Square } from 'lucide-react';

export function VoiceControls({ onTranscript, isSpeaking, onSpeakStart, onSpeakEnd, enabled = true }) {
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(false);
  const [transcript, setTranscript] = useState('');
  const recognitionRef = useRef(null);
  const isListeningRef = useRef(false);

  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListeningRef.current) {
      isListeningRef.current = false;
      recognitionRef.current.stop();
    }
  }, []);

  const startListening = useCallback(() => {
    if (recognitionRef.current && !isListeningRef.current) {
      try {
        isListeningRef.current = true;
        setTranscript('');
        recognitionRef.current.start();
      } catch (e) {
        console.error("Failed to start recognition", e);
        isListeningRef.current = false;
      }
    }
  }, []);

  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      setSupported(true);
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        setListening(true);
        onSpeakStart?.();
      };

      recognition.onend = () => {
        setListening(false);
        isListeningRef.current = false;
        onSpeakEnd?.();
      };

      recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) {
            finalTranscript += result[0].transcript;
          } else {
            interimTranscript += result[0].transcript;
          }
        }
        
        if (finalTranscript) {
          console.log('Voice Command:', finalTranscript);
          onTranscript?.(finalTranscript);
          setTranscript('');
        } else {
          setTranscript(interimTranscript);
        }
      };

      recognition.onerror = (event) => {
        if (event.error !== 'aborted' && event.error !== 'no-speech') {
          console.error('Speech recognition error', event.error);
        }
        setListening(false);
        isListeningRef.current = false;
      };

      recognitionRef.current = recognition;
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  // Update callbacks without recreating recognition
  useEffect(() => {
    if (recognitionRef.current) {
      const recognition = recognitionRef.current;
      recognition.onstart = () => {
        setListening(true);
        onSpeakStart?.();
      };
      recognition.onend = () => {
        setListening(false);
        isListeningRef.current = false;
        onSpeakEnd?.();
      };
    }
  }, [onSpeakStart, onSpeakEnd]);

  const toggleListening = () => {
    if (!supported || !recognitionRef.current) return;
    if (listening) {
      stopListening();
    } else {
      startListening();
    }
  };

  if (!supported) return null;

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={toggleListening}
        disabled={!enabled}
        className={`p-2 transition-all duration-200 border ${
          listening 
            ? 'bg-[#ef4444]/20 text-[#ef4444] border-[#ef4444]/50' 
            : 'bg-[#161b22] text-[#8b949e] border-[#30363d] hover:text-[#d4a62a] hover:border-[#d4a62a]/50'
        } ${!enabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        title={listening ? "Stop Recording" : "Start Recording"}
      >
        {listening ? <Square className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
      </button>
      {listening && transcript && (
        <span className="text-[10px] text-[#8b949e] font-mono italic max-w-[150px] truncate">
          {transcript}...
        </span>
      )}
    </div>
  );
}

// OpenAI TTS - API key should be set via backend proxy or environment
// For direct frontend TTS, set VITE_OPENAI_API_KEY in frontend/.env
const OPENAI_API_KEY = import.meta.env.VITE_OPENAI_API_KEY || '';

// Audio queue for sequential playback
let audioQueue = [];
let isPlaying = false;
let currentAudio = null;

const playNextInQueue = () => {
  if (audioQueue.length === 0) {
    isPlaying = false;
    return;
  }
  
  isPlaying = true;
  const audioUrl = audioQueue.shift();
  currentAudio = new Audio(audioUrl);
  currentAudio.onended = () => {
    URL.revokeObjectURL(audioUrl);
    playNextInQueue();
  };
  currentAudio.onerror = () => {
    URL.revokeObjectURL(audioUrl);
    playNextInQueue();
  };
  currentAudio.play().catch(console.error);
};

// Text-to-Speech Helper using OpenAI TTS
export const speakResponse = async (text, cognitiveLoad = 'medium') => {
  if (!text || text.trim().length === 0) return;

  // Cancel any ongoing speech
  stopSpeaking();

  try {
    // Use OpenAI TTS API with 'onyx' voice (deep, African-sounding)
    const response = await fetch('https://api.openai.com/v1/audio/speech', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'tts-1',
        input: text,
        voice: 'onyx', // Deep, rich voice
        speed: cognitiveLoad === 'high' ? 1.15 : 1.0,
      }),
    });

    if (!response.ok) {
      throw new Error(`TTS API error: ${response.status}`);
    }

    const audioBlob = await response.blob();
    const audioUrl = URL.createObjectURL(audioBlob);
    
    audioQueue.push(audioUrl);
    if (!isPlaying) {
      playNextInQueue();
    }
  } catch (error) {
    console.error('OpenAI TTS failed, falling back to browser TTS:', error);
    // Fallback to browser TTS
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = cognitiveLoad === 'high' ? 1.2 : 1.0;
      window.speechSynthesis.speak(utterance);
    }
  }
};

// Stop all speech
export const stopSpeaking = () => {
  audioQueue = [];
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
  isPlaying = false;
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
};
