import React from 'react'
import { Server, RefreshCw } from 'lucide-react'
import { cn } from '../../lib/utils'

export const MODEL_PROVIDERS = [
    { id: 'openai', name: 'OpenAI GPT-4o', description: 'Requires API key' },
    { id: 'openrouter', name: 'OpenRouter', description: 'Mistral 7B via API - fast' },
    { id: 'ollama', name: 'Ollama (Local)', description: 'Local models - slow' }
]

export const OPENROUTER_MODELS = [
    { id: 'mistralai/mistral-7b-instruct:free', name: 'Mistral 7B Instruct (FREE)', description: 'Free tier - recommended' },
    { id: 'mistral-7b', name: 'Mistral 7B Instruct', description: 'Fast, malleable' },
    { id: 'mistral-small', name: 'Mistral Small', description: 'Better quality' },
    { id: 'llama-3-8b', name: 'Llama 3 8B', description: 'Meta model' },
]

export const ModelProviderSelector = ({
    selectedProvider,
    setSelectedProvider,
    selectedModel,
    setSelectedModel,
    openaiApiKey,
    setOpenaiApiKey,
    ollamaStatus,
    checkOllamaStatus,
    isRunning
}) => {
    return (
        <div className="space-y-3">
            <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-slate-300">Model Provider</h4>
                <button
                    onClick={checkOllamaStatus}
                    className="text-xs text-slate-500 hover:text-slate-300 flex items-center gap-1"
                >
                    <RefreshCw className="w-3 h-3" />
                    Refresh
                </button>
            </div>
            <div className="grid grid-cols-3 gap-2">
                {MODEL_PROVIDERS.map(provider => (
                    <button
                        key={provider.id}
                        onClick={() => setSelectedProvider(provider.id)}
                        disabled={isRunning || (provider.id === 'ollama' && !ollamaStatus.available)}
                        className={cn(
                            "p-3 rounded-lg border text-left transition-colors",
                            selectedProvider === provider.id
                                ? 'border-cyan-500 bg-cyan-900/30'
                                : 'border-slate-700 bg-slate-800/50 hover:border-slate-600',
                            (provider.id === 'ollama' && !ollamaStatus.available) && 'opacity-50'
                        )}
                    >
                        <div className="flex items-center gap-2">
                            <Server className={cn(
                                "w-4 h-4",
                                provider.id === 'ollama' ? 'text-orange-400' :
                                    provider.id === 'openrouter' ? 'text-purple-400' : 'text-green-400'
                            )} />
                            <div>
                                <div className="text-sm font-medium text-slate-200">{provider.name}</div>
                                <div className="text-xs text-slate-500">{provider.description}</div>
                            </div>
                        </div>
                    </button>
                ))}
            </div>

            {/* OpenRouter Config */}
            {selectedProvider === 'openrouter' && (
                <div className="space-y-2">
                    <input
                        type="password"
                        placeholder="OpenRouter API Key"
                        value={openaiApiKey}
                        onChange={(e) => setOpenaiApiKey(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-slate-200 placeholder-slate-500"
                    />
                    <select
                        value={selectedModel}
                        onChange={(e) => setSelectedModel(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-slate-200"
                    >
                        {OPENROUTER_MODELS.map(model => (
                            <option key={model.id} value={model.id}>{model.name} - {model.description}</option>
                        ))}
                    </select>
                    {!openaiApiKey && (
                        <p className="text-xs text-amber-400">
                            Get API key from <a href="https://openrouter.ai/keys" target="_blank" rel="noopener" className="underline">openrouter.ai/keys</a>
                        </p>
                    )}
                </div>
            )}

            {/* Ollama Config */}
            {selectedProvider === 'ollama' && ollamaStatus.available && ollamaStatus.models.length > 0 && (
                <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-slate-200"
                >
                    {ollamaStatus.models.map(model => (
                        <option key={model} value={model}>{model}</option>
                    ))}
                </select>
            )}
            {selectedProvider === 'ollama' && !ollamaStatus.available && (
                <p className="text-xs text-amber-400">
                    Ollama not detected. Run: <code className="bg-slate-800 px-1 rounded">ollama serve</code> then <code className="bg-slate-800 px-1 rounded">ollama pull mistral</code>
                </p>
            )}
        </div>
    )
}
