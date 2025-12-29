import React from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { useInstance } from '../../contexts/InstanceContext';

export function Sidebar() {
  const { 
    instances, 
    selectedInstanceId, 
    selectInstance, 
    createInstance, 
    deleteInstance 
  } = useInstance();

  return (
    <aside className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
      <div className="p-4 border-b border-slate-700">
        <button
          onClick={createInstance}
          className="w-full flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700 text-white py-2 px-4 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Instance
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-2">
        {instances.map(id => (
          <div
            key={id}
            className={`flex items-center justify-between p-3 rounded-lg cursor-pointer mb-1 ${
              selectedInstanceId === id 
                ? 'bg-purple-600/20 border border-purple-500/50' 
                : 'hover:bg-slate-700'
            }`}
            onClick={() => selectInstance(id)}
          >
            <span className="text-sm font-mono text-slate-300 truncate">
              {id.substring(0, 8)}...
            </span>
            <button
              onClick={(e) => { e.stopPropagation(); deleteInstance(id); }}
              className="p-1 hover:bg-slate-600 rounded"
            >
              <Trash2 className="w-4 h-4 text-slate-400 hover:text-red-400" />
            </button>
          </div>
        ))}
        {instances.length === 0 && (
          <p className="text-center text-slate-500 text-sm py-8">
            No instances yet.<br />Create one to begin.
          </p>
        )}
      </div>
    </aside>
  );
}
