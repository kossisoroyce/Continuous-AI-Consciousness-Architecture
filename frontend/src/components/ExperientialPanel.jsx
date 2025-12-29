import React, { useState, useEffect } from 'react'
import { ExperienceSplash } from './experience/ExperienceSplash'
import { ExperienceChat } from './experience/ExperienceChat'
import { ExperienceInspector } from './experience/ExperienceInspector'
import { ExperienceAutomatedRunner } from './experience/ExperienceAutomatedRunner'
import { ExperienceThoughts } from './experience/ExperienceThoughts'
import { useSession } from '../contexts/SessionContext'
import * as cognitiveApi from '../services/cognitiveApi'

const PULSE_VERSION = 3 // Cache bust
const OPERATOR_ID = 'default' // TODO: Get from auth context

function ExperientialPanel({ instanceId, sessionId, replayConversation }) {
  const { 
    apiBase, 
    apiKeyConfigured, 
    openaiApiKey 
  } = useSession()

  const [experientialState, setExperientialState] = useState(null)
  const [facts, setFacts] = useState([])
  const [questions, setQuestions] = useState([])
  const [commitments, setCommitments] = useState([])
  const [thoughts, setThoughts] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [sessionActive, setSessionActive] = useState(false)

  // Integrated interaction state
  const [message, setMessage] = useState('')
  const [conversation, setConversation] = useState([])
  const [interacting, setInteracting] = useState(false)
  const [lastActivity, setLastActivity] = useState(Date.now())

  // Override conversation if replay data is provided
  const activeConversation = replayConversation || conversation

  useEffect(() => {
    if (sessionActive) {
      fetchExperientialState()
    }
  }, [sessionId, sessionActive])

  // Pulse Heartbeat: Trigger self-stimulation when idle
  useEffect(() => {
    if (!sessionActive || !apiKeyConfigured) return

    const interval = setInterval(async () => {
      // Basic idle check for pulse
      const idleTime = Date.now() - lastActivity
      if (idleTime > 10000) { // Check after 10s idle (human attention span)
        console.log('[PULSE v2] Triggering self-stimulation...', { instanceId, sessionId })
        try {
          const res = await fetch(`${apiBase}/experience/pulse`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              instance_id: instanceId,
              session_id: sessionId,
              openai_api_key: openaiApiKey || null,
              model_name: 'mistralai/mistral-7b-instruct:free'
            })
          })
          if (res.ok) {
            const data = await res.json()
            if (data.triggered) {
              console.log('Self-stimulation triggered:', data.result?.type)
              await fetchExperientialState() // Refresh to see new thoughts
            }
          }
        } catch (err) {
          console.error('Pulse failed:', err)
        }
      }
    }, 5000) // Poll every 5s to catch 10s idle threshold

    return () => clearInterval(interval)
  }, [sessionActive, lastActivity, instanceId, sessionId, apiKeyConfigured, openaiApiKey, apiBase])

  const startSession = async () => {
    try {
      setLoading(true)
      const res = await fetch(`${apiBase}/experience/session?instance_id=${instanceId}&session_id=${sessionId}`, {
        method: 'POST'
      })
      if (!res.ok) throw new Error('Failed to start session')
      setSessionActive(true)
      
      // Start mission recording (non-blocking)
      cognitiveApi.startMissionRecording(
        `Session-${sessionId?.slice(0, 8)}`,
        'HMT interaction session',
        OPERATOR_ID,
        instanceId
      ).catch(() => {})
      
      await fetchExperientialState()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const endSession = async () => {
    try {
      setLoading(true)
      const res = await fetch(`${apiBase}/experience/session/${sessionId}`, {
        method: 'DELETE'
      })
      const data = await res.json()
      setSessionActive(false)
      setExperientialState(null)
      setFacts([])
      setQuestions([])
      setCommitments([])
      setConversation([])
      return data
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchExperientialState = async () => {
    try {
      const [stateRes, factsRes, questionsRes, commitmentsRes] = await Promise.all([
        fetch(`${apiBase}/experience/session/${sessionId}`),
        fetch(`${apiBase}/experience/facts/${sessionId}`),
        fetch(`${apiBase}/experience/questions/${sessionId}`),
        fetch(`${apiBase}/experience/commitments/${sessionId}`)
      ])

      if (stateRes.ok) {
        const data = await stateRes.json()
        setExperientialState(data)
        setThoughts(data.internal_thoughts || [])
      }
      if (factsRes.ok) {
        const factsData = await factsRes.json()
        setFacts(factsData.facts || [])
      }
      if (questionsRes.ok) {
        const questionsData = await questionsRes.json()
        setQuestions(questionsData.questions || [])
      }
      if (commitmentsRes.ok) {
        const commitmentsData = await commitmentsRes.json()
        setCommitments(commitmentsData.commitments || [])
      }
    } catch (err) {
      console.error('Failed to fetch experiential state:', err)
    }
  }

  const sendIntegratedMessage = async (text = null) => {
    // Determine message content
    const content = text || message

    if (!content.trim() || !apiKeyConfigured) return

    // Clear input if using manual input
    if (!text) setMessage('')

    setLastActivity(Date.now())
    setConversation(prev => [...prev, { role: 'user', content: content.trim() }])
    setInteracting(true)

    try {
      // Log operator input to audit
      cognitiveApi.logAuditEvent(
        'operator.command', 
        'chat_input', 
        { message: content.trim() },
        { sessionId, brainId: instanceId }
      ).catch(() => {})

      // Analyze operator message for adaptive communication (non-blocking)
      cognitiveApi.analyzeOperatorMessage(OPERATOR_ID, content.trim()).catch(() => {})
      
      // Update cognitive load metrics based on activity
      cognitiveApi.updateCognitiveLoad(OPERATOR_ID, {
        active_detections: 0.3,
        decision_pending: 0.2,
        information_rate: 0.4,
        task_complexity: 0.3
      }).catch(() => {})

      const res = await fetch(`${apiBase}/integrated/interact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          instance_id: instanceId,
          session_id: sessionId,
          user_input: content.trim(),
          openai_api_key: openaiApiKey,
          model_name: 'mistralai/mistral-7b-instruct:free'
        })
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Request failed')
      }

      const data = await res.json()
      
      // Log AI decision to audit (non-blocking)
      cognitiveApi.logAIDecision(
        'chat_response',
        data.response || 'Response generated',
        0.85,
        'Generated based on operator query',
        { sessionId, brainId: instanceId }
      ).catch(() => {})

      setConversation(prev => [...prev, { role: 'assistant', content: data.response }])
      setExperientialState(data.experiential_state)

      // Refresh working memory
      await fetchExperientialState()

      return data // Return data for automated runner
    } catch (err) {
      setError(err.message)
      setConversation(prev => [...prev, { role: 'error', content: err.message }])
      throw err
    } finally {
      setInteracting(false)
    }
  }

  if (!sessionActive) {
    return (
      <ExperienceSplash
        startSession={startSession}
        loading={loading}
        instanceId={instanceId}
      />
    )
  }

  return (
    <div className="h-full flex overflow-hidden">
      <div className="flex-1 flex flex-col min-w-0">
        <ExperienceChat
          conversation={activeConversation}
          message={message}
          setMessage={setMessage}
          interacting={interacting}
          sendIntegratedMessage={() => sendIntegratedMessage()}
          apiKeyConfigured={apiKeyConfigured}
          fetchExperientialState={fetchExperientialState}
          endSession={endSession}
        />
      </div>

      {/* Error Toast */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-[#991b1b] border border-[#ef4444] text-white px-4 py-2 z-50 font-mono text-sm">
          {error}
          <button onClick={() => setError(null)} className="ml-4 font-bold">×</button>
        </div>
      )}
    </div>
  )
}

export default ExperientialPanel
