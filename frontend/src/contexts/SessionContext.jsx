import React, { createContext, useContext, useState, useEffect } from 'react';

const SessionContext = createContext();

export const API_BASE = '/api';

export function SessionProvider({ children }) {
  const [sessionId, setSessionId] = useState(() => {
    const stored = localStorage.getItem('nurture_session_id');
    if (stored) return stored;
    const newId = crypto.randomUUID();
    localStorage.setItem('nurture_session_id', newId);
    return newId;
  });
  
  const changeSession = (newId) => {
    setSessionId(newId);
    localStorage.setItem('nurture_session_id', newId);
  };
  
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false);
  const [openaiApiKey, setOpenaiApiKey] = useState(() => {
    return localStorage.getItem('nurture_openai_key') || '';
  });

  // Persist OpenAI key
  useEffect(() => {
    if (openaiApiKey) {
      localStorage.setItem('nurture_openai_key', openaiApiKey);
    }
  }, [openaiApiKey]);

  // Check backend session key status
  useEffect(() => {
    const checkBackendKey = async () => {
      try {
        const res = await fetch(`${API_BASE}/api-key/${sessionId}`);
        if (res.ok) {
          const data = await res.json();
          setApiKeyConfigured(data.configured);
        }
      } catch (err) {
        console.error('Failed to check API key status', err);
      }
    };
    
    checkBackendKey();
    // Poll occasionally to keep sync? Or rely on explicit updates?
    // For now, check once on mount.
  }, [sessionId]);

  const updateOpenAIKey = (key) => {
    setOpenaiApiKey(key);
  };

  const refreshBackendKeyStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api-key/${sessionId}`);
      if (res.ok) {
        const data = await res.json();
        setApiKeyConfigured(data.configured);
      }
    } catch (err) {
      console.error('Failed to refresh API key status', err);
    }
  };

  const value = {
    sessionId,
    changeSession,
    apiKeyConfigured,
    openaiApiKey,
    setOpenaiApiKey: updateOpenAIKey,
    refreshBackendKeyStatus,
    apiBase: API_BASE
  };

  return (
    <SessionContext.Provider value={value}>
      {children}
    </SessionContext.Provider>
  );
}

export const useSession = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};
