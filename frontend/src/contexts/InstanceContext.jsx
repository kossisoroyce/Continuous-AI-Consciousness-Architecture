import React, { createContext, useContext, useState, useEffect } from 'react';
import { useSession } from './SessionContext';

const InstanceContext = createContext();

export function InstanceProvider({ children }) {
  const { apiBase } = useSession();
  const [instances, setInstances] = useState([]);
  const [selectedInstanceId, setSelectedInstanceId] = useState(null);
  const [instanceState, setInstanceState] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Initial fetch
  useEffect(() => {
    fetchInstances();
  }, [apiBase]);

  // Fetch state when selection changes
  useEffect(() => {
    if (selectedInstanceId) {
      fetchInstanceState(selectedInstanceId);
    } else {
      setInstanceState(null);
    }
  }, [selectedInstanceId, apiBase]);

  const fetchInstances = async () => {
    try {
      const res = await fetch(`${apiBase}/instances`);
      const data = await res.json();
      setInstances(data);
      
      // Auto-select first if none selected
      if (data.length > 0 && !selectedInstanceId) {
        // Try to restore from localStorage?
        const stored = localStorage.getItem('nurture_selected_instance');
        if (stored && data.includes(stored)) {
          setSelectedInstanceId(stored);
        } else {
          setSelectedInstanceId(data[0]);
        }
      }
    } catch (err) {
      setError('Failed to fetch instances');
      console.error(err);
    }
  };

  const fetchInstanceState = async (id) => {
    if (!id) return;
    try {
      setLoading(true);
      const res = await fetch(`${apiBase}/instances/${id}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      
      // Only update if still selected
      if (id === selectedInstanceId) {
        setInstanceState(data);
      }
    } catch (err) {
      console.error('Failed to fetch instance state:', err);
      setError('Failed to fetch instance state');
    } finally {
      setLoading(false);
    }
  };

  const selectInstance = (id) => {
    setSelectedInstanceId(id);
    localStorage.setItem('nurture_selected_instance', id);
  };

  const createInstance = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${apiBase}/instances`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();
      setInstances(prev => [...prev, data.instance_id]);
      selectInstance(data.instance_id);
      setInstanceState(data);
    } catch (err) {
      setError('Failed to create instance');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const deleteInstance = async (id) => {
    if (!confirm('Are you sure you want to delete this instance?')) return;
    try {
      await fetch(`${apiBase}/instances/${id}`, { method: 'DELETE' });
      const newInstances = instances.filter(i => i !== id);
      setInstances(newInstances);
      
      if (selectedInstanceId === id) {
        const next = newInstances[0] || null;
        selectInstance(next);
      }
    } catch (err) {
      setError('Failed to delete instance');
    }
  };

  const refreshInstanceState = async () => {
    if (selectedInstanceId) {
      await fetchInstanceState(selectedInstanceId);
    }
  };

  const updateInstanceState = (newState) => {
    if (newState && newState.instance_id === selectedInstanceId) {
      setInstanceState(newState);
    }
  };

  const value = {
    instances,
    selectedInstanceId,
    instanceState,
    loading,
    error,
    selectInstance,
    createInstance,
    deleteInstance,
    refreshInstanceState,
    updateInstanceState,
    setError
  };

  return (
    <InstanceContext.Provider value={value}>
      {children}
    </InstanceContext.Provider>
  );
}

export const useInstance = () => {
  const context = useContext(InstanceContext);
  if (!context) {
    throw new Error('useInstance must be used within an InstanceProvider');
  }
  return context;
};
