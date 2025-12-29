import React from 'react'

export const ExperimentProgress = ({
    isRunning,
    selectedConditionName,
    currentPromptIndex,
    totalPrompts,
    currentPromptText
}) => {
    if (!isRunning) return null

    return (
        <div className="bg-slate-800 rounded-lg p-4">
            <div className="flex justify-between text-sm text-slate-400 mb-2">
                <span>Running: {selectedConditionName}</span>
                <span>{currentPromptIndex + 1}/{totalPrompts}</span>
            </div>
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                    className="h-full bg-purple-500 transition-all duration-300"
                    style={{ width: `${((currentPromptIndex + 1) / totalPrompts) * 100}%` }}
                />
            </div>
            <div className="text-xs text-slate-500 mt-2 truncate">
                "{currentPromptText}"
            </div>
        </div>
    )
}
