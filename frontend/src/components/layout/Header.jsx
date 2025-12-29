import React, { useState } from 'react';
import { Brain, ChevronDown, Plus, Trash2, Check } from 'lucide-react';
import { useInstance } from '../../contexts/InstanceContext';

export function Header() {
  const { instances, selectedInstanceId, selectInstance, createInstance, deleteInstance } = useInstance();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <header className="bg-slate-900 border-b border-slate-800 h-16 flex items-center justify-between px-6 z-50 relative">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center shadow-lg shadow-purple-900/20">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight leading-none">Nurture Layer</h1>
            <p className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Electric Sheep Africa</p>
          </div>
        </div>

        {/* Instance Selector */}
        <div className="relative">
          <button 
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center gap-3 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-md border border-slate-700 transition-all min-w-[200px]"
          >
            <div className="flex flex-col items-start overflow-hidden">
              <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Current Instance</span>
              <span className="text-sm font-mono text-purple-300 truncate w-full text-left">
                {selectedInstanceId || "Select Instance"}
              </span>
            </div>
            <ChevronDown className={`w-4 h-4 text-slate-500 ml-auto transition-transform ${isOpen ? 'rotate-180' : ''}`} />
          </button>

          {/* Dropdown Menu */}
          {isOpen && (
            <>
              <div 
                className="fixed inset-0 z-10"
                onClick={() => setIsOpen(false)}
              />
              <div className="absolute top-full left-0 mt-2 w-72 bg-slate-800 rounded-lg border border-slate-700 shadow-xl z-20 py-1 max-h-[80vh] flex flex-col">
                <div className="overflow-y-auto max-h-[60vh] custom-scrollbar">
                  {instances.map(id => (
                    <div 
                      key={id}
                      className="group flex items-center justify-between px-3 py-2 hover:bg-slate-700/50 cursor-pointer"
                      onClick={() => {
                        selectInstance(id);
                        setIsOpen(false);
                      }}
                    >
                      <div className="flex items-center gap-2 overflow-hidden">
                        {selectedInstanceId === id && <Check className="w-3 h-3 text-purple-400 flex-shrink-0" />}
                        <span className={`text-sm font-mono truncate ${selectedInstanceId === id ? 'text-purple-300' : 'text-slate-300'}`}>
                          {id}
                        </span>
                      </div>
                      <button
                        onClick={(e) => { e.stopPropagation(); deleteInstance(id); }}
                        className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-900/30 rounded text-slate-500 hover:text-red-400 transition-all"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                  {instances.length === 0 && (
                    <div className="px-4 py-3 text-center text-xs text-slate-500">
                      No instances found
                    </div>
                  )}
                </div>
                <div className="border-t border-slate-700 p-2 bg-slate-800/50">
                  <button
                    onClick={() => {
                      createInstance();
                      setIsOpen(false);
                    }}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold uppercase tracking-wider rounded transition-colors"
                  >
                    <Plus className="w-3 h-3" />
                    New Instance
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="px-3 py-1 bg-slate-800 rounded-full border border-slate-700">
          <span className="flex items-center gap-2 text-xs text-slate-400">
            <span className="w-2 h-2 rounded-full bg-[#d4a62a] shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
            System Online
          </span>
        </div>
      </div>
    </header>
  );
}
