import React, { useState, useEffect } from 'react'
import { Play, Square, FastForward, CheckCircle, Download } from 'lucide-react'
import { getAllExperientialPrompts } from '../../testProtocolExperiential'

export const ExperienceAutomatedRunner = ({
    instanceId,
    sessionId,
    apiKeyConfigured,
    onInteract,
    isInteracting,
    compact = false
}) => {
    const [isRunning, setIsRunning] = useState(false)
    const [currentPromptIndex, setCurrentPromptIndex] = useState(0)
    const [results, setResults] = useState([])
    const [autoMode, setAutoMode] = useState(false)

    const allPrompts = getAllExperientialPrompts()
    const currentPromptData = allPrompts[currentPromptIndex]

    // Effect to drive the automation
    useEffect(() => {
        let timer
        if (isRunning && autoMode && !isInteracting && currentPromptIndex < allPrompts.length) {
            // Small delay before sending next prompt to make it readable
            timer = setTimeout(() => {
                executeStep()
            }, 2000)
        } else if (isRunning && autoMode && currentPromptIndex >= allPrompts.length) {
            setIsRunning(false)
            setAutoMode(false)
        }
        return () => clearTimeout(timer)
    }, [isRunning, autoMode, isInteracting, currentPromptIndex])

    const executeStep = async () => {
        if (currentPromptIndex >= allPrompts.length) return Promise.resolve()

        const promptData = allPrompts[currentPromptIndex]

        // Trigger interaction in parent
        const startTime = Date.now()
        try {
            // We pass a callback or promise-based interaction?
            // Ideally onInteract returns a promise that resolves when done
            const responseData = await onInteract(promptData.prompt)

            // Record result
            setResults(prev => [...prev, {
                ...promptData,
                response: responseData?.response,
                timestamp: new Date().toISOString(),
                latency: Date.now() - startTime
            }])

            setCurrentPromptIndex(prev => prev + 1)
        } catch (err) {
            console.error("Test execution failed at step", currentPromptIndex, err)
            setIsRunning(false)
        }
    }

    const startAuto = () => {
        setIsRunning(true)
        setAutoMode(true)
        // If we finished before, reset
        if (currentPromptIndex >= allPrompts.length) {
            setCurrentPromptIndex(0)
            setResults([])
        }
    }

    const stopAuto = () => {
        setIsRunning(false)
        setAutoMode(false)
    }

    const stepForward = () => {
        // If we finished before, reset
        if (currentPromptIndex >= allPrompts.length) {
            setCurrentPromptIndex(0)
            setResults([])
        }
        setIsRunning(true) // Mark as running so we know we are active
        executeStep()
    }

    const exportResults = () => {
        const exportData = {
            experiment: "Experiential Layer Validation",
            timestamp: new Date().toISOString(),
            total_prompts: allPrompts.length,
            results: results
        }

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `experiential-test-${new Date().toISOString().split('T')[0]}.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
    }

    if (!sessionId) return null

    const progress = (currentPromptIndex / allPrompts.length) * 100

    // Compact mode for sidebar
    if (compact) {
        return (
            <div className="flex items-center gap-2">
                <span className="text-[10px] text-slate-500 uppercase font-bold">Test</span>
                {!autoMode ? (
                    <button
                        onClick={startAuto}
                        disabled={isInteracting || !apiKeyConfigured}
                        className="flex-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-300 text-[10px] py-1.5 px-2 rounded flex items-center justify-center gap-1"
                    >
                        <Play className="w-2.5 h-2.5" />
                        Auto
                    </button>
                ) : (
                    <button
                        onClick={stopAuto}
                        className="flex-1 bg-amber-600/20 text-amber-400 text-[10px] py-1.5 px-2 rounded flex items-center justify-center gap-1"
                    >
                        <Square className="w-2.5 h-2.5" />
                        Stop
                    </button>
                )}
                <span className="text-[10px] text-slate-600">{currentPromptIndex}/{allPrompts.length}</span>
            </div>
        )
    }

    return (
        <div className="bg-slate-800 border-b border-slate-700 p-4">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-[#d4a62a] flex items-center gap-2">
                    <FastForward className="w-4 h-4" />
                    Automated Validation Protocol
                </h3>
                <div className="text-xs text-slate-400">
                    {currentPromptIndex} / {allPrompts.length} steps
                </div>
            </div>

            {isRunning && (
                <div className="mb-4">
                    <div className="flex justify-between text-xs text-slate-500 mb-1">
                        <span>Current: {currentPromptData?.experimentName}</span>
                        <span>Prompt {currentPromptData?.promptIndex}/{currentPromptData?.totalInExperiment}</span>
                    </div>
                    <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-[#d4a62a] transition-all duration-300"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                    <div className="mt-2 p-2 bg-slate-900/50 rounded text-xs text-slate-300 font-mono truncate">
                        {currentPromptData?.prompt}
                    </div>
                </div>
            )}

            <div className="flex gap-2">
                {!autoMode ? (
                    <button
                        onClick={startAuto}
                        disabled={isInteracting || !apiKeyConfigured}
                        className="flex-1 bg-[#d4a62a] hover:bg-[#b8942a] disabled:bg-slate-700 disabled:text-slate-500 text-white text-xs font-medium py-2 px-3 rounded flex items-center justify-center gap-2"
                    >
                        <Play className="w-3 h-3" />
                        Run All
                    </button>
                ) : (
                    <button
                        onClick={stopAuto}
                        className="flex-1 bg-amber-600 hover:bg-amber-700 text-white text-xs font-medium py-2 px-3 rounded flex items-center justify-center gap-2"
                    >
                        <Square className="w-3 h-3" />
                        Stop
                    </button>
                )}

                <button
                    onClick={stepForward}
                    disabled={autoMode || isInteracting || !apiKeyConfigured}
                    className="flex-1 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white text-xs font-medium py-2 px-3 rounded flex items-center justify-center gap-2"
                >
                    <FastForward className="w-3 h-3" />
                    Step
                </button>

                {results.length > 0 && (
                    <button
                        onClick={exportResults}
                        className="bg-[#d4a62a] hover:bg-[#b8942a] text-white p-2 rounded"
                        title="Export Results"
                    >
                        <Download className="w-4 h-4" />
                    </button>
                )}
            </div>

            {currentPromptIndex >= allPrompts.length && (
                <div className="mt-2 text-xs text-[#d4a62a] flex items-center justify-center gap-1">
                    <CheckCircle className="w-3 h-3" /> Protocol Complete
                </div>
            )}
        </div>
    )
}
