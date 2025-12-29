import React, { useState, useEffect } from 'react'
import { Beaker } from 'lucide-react'
import { getAllPrompts } from '../testProtocol'
import { ModelProviderSelector } from './control/ModelProviderSelector'
import { ConditionSelector, CONDITIONS } from './control/ConditionSelector'
import { ExperimentProgress } from './control/ExperimentProgress'
import { ExperimentActions } from './control/ExperimentActions'
import { ResultsSummary } from './control/ResultsSummary'
import { useSession } from '../contexts/SessionContext'

export const ControlExperiment = ({ instanceId, onNurtureInteraction }) => {
  const { 
    apiBase, 
    sessionId, 
    apiKeyConfigured, 
    openaiApiKey,
    setOpenaiApiKey
  } = useSession()

  const [selectedCondition, setSelectedCondition] = useState('raw')
  const [selectedProvider, setSelectedProvider] = useState('openrouter')
  const [ollamaStatus, setOllamaStatus] = useState({ available: false, models: [] })
  const [selectedModel, setSelectedModel] = useState('mistralai/mistral-7b-instruct:free')
  const [isRunning, setIsRunning] = useState(false)
  const [results, setResults] = useState({ raw: [], static_prompt: [], nurture: [] })
  const [currentPromptIndex, setCurrentPromptIndex] = useState(0)
  const [conversationHistory, setConversationHistory] = useState({ raw: [], static_prompt: [] })

  // Check Ollama status on mount
  useEffect(() => {
    checkOllamaStatus()
  }, [])

  const checkOllamaStatus = async () => {
    try {
      const res = await fetch(`${apiBase}/ollama/status`)
      const data = await res.json()
      setOllamaStatus(data)
      if (data.models?.length > 0) {
        // Prefer mistral if available
        const mistral = data.models.find(m => m.includes('mistral'))
        if (mistral) {
          setSelectedModel(mistral || data.models[0])
        }
      }
    } catch (err) {
      setOllamaStatus({ available: false, models: [] })
    }
  }

  const allPrompts = getAllPrompts()

  const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms))

  const runSingleCondition = async (condition) => {
    setIsRunning(true)
    const conditionResults = []
    const history = []

    for (let i = 0; i < allPrompts.length; i++) {
      setCurrentPromptIndex(i)
      const promptData = allPrompts[i]

      try {
        let response, data

        if (condition === 'nurture') {
          // Use the Nurture Layer endpoint
          const res = await fetch(`${apiBase}/interact`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              instance_id: instanceId,
              user_input: promptData.prompt,
              session_id: sessionId
            })
          })
          if (!res.ok) {
            throw new Error(`HTTP ${res.status}: ${res.statusText}`)
          }
          data = await res.json()
          response = data.response

          // Only call callback if we have valid data
          if (onNurtureInteraction && data && data.state) {
            onNurtureInteraction(data)
          }
        } else {
          // Use control endpoint
          const res = await fetch(`${apiBase}/control/interact`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              user_input: promptData.prompt,
              session_id: sessionId,
              condition: condition,
              conversation_history: history,
              model_provider: selectedProvider,
              model_name: selectedModel,
              openai_api_key: selectedProvider === 'openrouter' ? openaiApiKey : null
            })
          })
          if (!res.ok) {
            throw new Error(`HTTP ${res.status}: ${res.statusText}`)
          }
          data = await res.json()
          response = data.response

          // Update history for next request
          history.push({ role: 'user', content: promptData.prompt })
          history.push({ role: 'assistant', content: response })
        }

        conditionResults.push({
          ...promptData,
          response: response,
          condition: condition,
          metadata: condition === 'nurture' ? data.metadata : null
        })

        // Delay between requests
        if (i < allPrompts.length - 1) {
          await delay(1500)
        }

      } catch (err) {
        console.error(`Error at prompt ${i}:`, err)
        conditionResults.push({
          ...promptData,
          response: `ERROR: ${err.message}`,
          condition: condition,
          error: true
        })
      }
    }

    setResults(prev => ({ ...prev, [condition]: conditionResults }))
    setIsRunning(false)
    setCurrentPromptIndex(0)

    return conditionResults
  }

  const exportResults = () => {
    // Build plotting-friendly trajectory data
    const buildTrajectory = (conditionResults, conditionName) => {
      return {
        condition: conditionName,
        interaction_numbers: conditionResults.map((_, i) => i + 1),
        experiments: conditionResults.map(r => r.experimentName),
        prompts: conditionResults.map(r => r.prompt),
        responses: conditionResults.map(r => r.response),
        response_lengths: conditionResults.map(r => r.response?.length || 0),
        // Nurture-specific metrics (null for control conditions)
        significance_scores: conditionResults.map(r => r.metadata?.significance_score || null),
        was_evaluated: conditionResults.map(r => r.metadata?.was_evaluated || null),
        delta_magnitudes: conditionResults.map(r => r.metadata?.delta_magnitude || null),
      }
    }

    const modelName = selectedProvider === 'openrouter' ? `openrouter/${selectedModel}` :
      selectedProvider === 'ollama' ? `ollama/${selectedModel}` : 'openai/gpt-4o'

    const exportData = {
      export_version: '2.1',
      exported_at: new Date().toISOString(),
      experiment_type: 'control_comparison',
      model_provider: selectedProvider,
      model_name: modelName,
      total_prompts: allPrompts.length,

      // Summary stats
      summary: {
        raw: { total: results.raw.length, complete: results.raw.length === allPrompts.length, model: modelName },
        static_prompt: { total: results.static_prompt.length, complete: results.static_prompt.length === allPrompts.length, model: modelName },
        nurture: {
          total: results.nurture.length,
          complete: results.nurture.length === allPrompts.length,
          evaluated_count: results.nurture.filter(r => r.metadata?.was_evaluated).length,
          avg_significance: results.nurture.length > 0
            ? results.nurture.reduce((sum, r) => sum + (r.metadata?.significance_score || 0), 0) / results.nurture.length
            : 0
        }
      },

      // Plotting-friendly trajectories
      trajectories: {
        raw: buildTrajectory(results.raw, 'Control A: Raw GPT-4o'),
        static_prompt: buildTrajectory(results.static_prompt, 'Control B: Static Prompt'),
        nurture: buildTrajectory(results.nurture, 'Experimental: Nurture Layer')
      },

      // Full results for detailed analysis
      conditions: {
        raw: {
          name: 'Control A: Raw GPT-4o',
          description: 'No system prompt',
          results: results.raw
        },
        static_prompt: {
          name: 'Control B: Static Prompt',
          description: 'Best-case prompt engineering',
          results: results.static_prompt
        },
        nurture: {
          name: 'Experimental: Nurture Layer',
          description: 'Dynamic character formation',
          results: results.nurture
        }
      }
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `control-experiment-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const resetResults = () => {
    setResults({ raw: [], static_prompt: [], nurture: [] })
    setConversationHistory({ raw: [], static_prompt: [] })
  }

  const totalResults = results.raw.length + results.static_prompt.length + results.nurture.length
  const hasResults = totalResults > 0

  return (
    <div className="p-6 space-y-6 overflow-y-auto max-h-full">
      <div className="bg-purple-900/20 border border-purple-600/50 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <Beaker className="w-5 h-5 text-purple-400" />
          <h3 className="text-sm font-semibold text-purple-400">Control Experiment Mode</h3>
        </div>
        <p className="text-sm text-slate-400">
          Run the same test protocol across three conditions to scientifically compare
          Nurture Layer against baseline approaches.
        </p>
      </div>

      <ModelProviderSelector
        selectedProvider={selectedProvider}
        setSelectedProvider={setSelectedProvider}
        selectedModel={selectedModel}
        setSelectedModel={setSelectedModel}
        openaiApiKey={openaiApiKey}
        setOpenaiApiKey={setOpenaiApiKey}
        ollamaStatus={ollamaStatus}
        checkOllamaStatus={checkOllamaStatus}
        isRunning={isRunning}
      />

      <ConditionSelector
        selectedCondition={selectedCondition}
        setSelectedCondition={setSelectedCondition}
        instanceId={instanceId}
        results={results}
        allPromptsCount={allPrompts.length}
        isRunning={isRunning}
      />

      <ExperimentProgress
        isRunning={isRunning}
        selectedConditionName={CONDITIONS.find(c => c.id === selectedCondition)?.name}
        currentPromptIndex={currentPromptIndex}
        totalPrompts={allPrompts.length}
        currentPromptText={allPrompts[currentPromptIndex]?.prompt}
      />

      <ExperimentActions
        runExperiment={() => runSingleCondition(selectedCondition)}
        exportResults={exportResults}
        resetResults={resetResults}
        isRunning={isRunning}
        selectedCondition={selectedCondition}
        selectedConditionName={CONDITIONS.find(c => c.id === selectedCondition)?.name}
        selectedProvider={selectedProvider}
        selectedModel={selectedModel}
        instanceId={instanceId}
        apiKeyConfigured={apiKeyConfigured}
        openaiApiKey={openaiApiKey}
        ollamaStatus={ollamaStatus}
        hasResults={hasResults}
      />

      <ResultsSummary
        results={results}
        allPromptsLength={allPrompts.length}
      />

      {/* Instructions */}
      <div className="text-xs text-slate-500 space-y-1">
        <p><strong>Recommended protocol:</strong></p>
        <ol className="list-decimal list-inside space-y-1 ml-2">
          <li>Run Control A (Raw GPT-4o)</li>
          <li>Run Control B (Static Prompt)</li>
          <li>Create fresh instance, then run Nurture Layer</li>
          <li>Export all results for comparison</li>
        </ol>
      </div>
    </div>
  )
}

// export default ControlExperiment

