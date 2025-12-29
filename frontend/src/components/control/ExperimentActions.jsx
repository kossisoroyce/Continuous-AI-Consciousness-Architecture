import React from 'react'
import { Play, Download, RefreshCw } from 'lucide-react'

export const ExperimentActions = ({
    runExperiment,
    exportResults,
    resetResults,
    isRunning,
    selectedCondition,
    selectedConditionName,
    selectedProvider,
    selectedModel,
    instanceId,
    apiKeyConfigured,
    openaiApiKey,
    ollamaStatus,
    hasResults
}) => {
    const isRunnable = !(
        isRunning ||
        (selectedCondition === 'nurture' && !instanceId) ||
        (selectedCondition !== 'nurture' && selectedProvider === 'openai' && !apiKeyConfigured) ||
        (selectedCondition !== 'nurture' && selectedProvider === 'openrouter' && !openaiApiKey) ||
        (selectedCondition !== 'nurture' && selectedProvider === 'ollama' && !ollamaStatus.available)
    )

    const modelDisplay = selectedCondition !== 'nurture'
        ? ` (${selectedProvider === 'openrouter' ? selectedModel : selectedProvider === 'ollama' ? selectedModel : 'GPT-4o'})`
        : ''

    return (
        <div className="flex gap-2">
            <button
                onClick={runExperiment}
                disabled={!isRunnable}
                className="flex-1 flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 disabled:text-slate-500 text-white py-2.5 px-4 rounded-lg transition-colors font-medium"
            >
                <Play className="w-4 h-4" />
                Run {selectedConditionName?.split(':')[0]}
                {modelDisplay}
            </button>

            {hasResults && (
                <>
                    <button
                        onClick={exportResults}
                        className="flex items-center gap-2 px-4 py-2.5 bg-[#d4a62a] hover:bg-[#b8942a] text-white rounded-lg transition-colors"
                    >
                        <Download className="w-4 h-4" />
                    </button>
                    <button
                        onClick={resetResults}
                        className="flex items-center gap-2 px-4 py-2.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors"
                    >
                        <RefreshCw className="w-4 h-4" />
                    </button>
                </>
            )}
        </div>
    )
}
