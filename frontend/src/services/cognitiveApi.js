/**
 * Cognitive Systems API Client
 * Connects to backend cognitive endpoints for real data
 */

const API_BASE = 'http://localhost:8000'

// ============== Adaptive Communication ==============

export async function analyzeOperatorMessage(operatorId, message) {
  const response = await fetch(`${API_BASE}/cognitive/analyze-message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ operator_id: operatorId, message })
  })
  if (!response.ok) throw new Error('Failed to analyze message')
  return response.json()
}

export async function adaptAIResponse(operatorId, response, overrideStyle = null) {
  const res = await fetch(`${API_BASE}/cognitive/adapt-response`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      operator_id: operatorId, 
      response,
      override_style: overrideStyle
    })
  })
  if (!res.ok) throw new Error('Failed to adapt response')
  return res.json()
}

export async function getOperatorProfile(operatorId) {
  const response = await fetch(`${API_BASE}/cognitive/operator-profile/${operatorId}`)
  if (!response.ok) throw new Error('Failed to get operator profile')
  return response.json()
}

export async function getStylePrompt(operatorId) {
  const response = await fetch(`${API_BASE}/cognitive/style-prompt/${operatorId}`)
  if (!response.ok) throw new Error('Failed to get style prompt')
  return response.json()
}

// ============== Cognitive Load ==============

export async function updateCognitiveLoad(operatorId, metrics) {
  const response = await fetch(`${API_BASE}/cognitive/load/update`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ operator_id: operatorId, metrics })
  })
  if (!response.ok) throw new Error('Failed to update cognitive load')
  return response.json()
}

export async function getCognitiveLoad(operatorId) {
  const response = await fetch(`${API_BASE}/cognitive/load/${operatorId}`)
  if (!response.ok) throw new Error('Failed to get cognitive load')
  return response.json()
}

export async function getCognitiveLoadHistory(operatorId, minutes = 30) {
  const response = await fetch(`${API_BASE}/cognitive/load/${operatorId}/history?minutes=${minutes}`)
  if (!response.ok) throw new Error('Failed to get cognitive load history')
  return response.json()
}

export async function shouldIntervene(operatorId) {
  const response = await fetch(`${API_BASE}/cognitive/load/${operatorId}/should-intervene`)
  if (!response.ok) throw new Error('Failed to check intervention')
  return response.json()
}

// ============== Mission Recording ==============

export async function startMissionRecording(name, description = '', operatorId = null, brainId = null) {
  const response = await fetch(`${API_BASE}/mission/start-recording`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description, operator_id: operatorId, brain_id: brainId })
  })
  if (!response.ok) throw new Error('Failed to start recording')
  return response.json()
}

export async function stopMissionRecording(recordingId) {
  const response = await fetch(`${API_BASE}/mission/stop-recording/${recordingId}`, {
    method: 'POST'
  })
  if (!response.ok) throw new Error('Failed to stop recording')
  return response.json()
}

export async function recordMissionEvent(recordingId, eventType, data, options = {}) {
  const response = await fetch(`${API_BASE}/mission/record-event`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      recording_id: recordingId,
      event_type: eventType,
      data,
      operator_id: options.operatorId,
      brain_id: options.brainId,
      ai_confidence: options.aiConfidence,
      ai_reasoning: options.aiReasoning
    })
  })
  if (!response.ok) throw new Error('Failed to record event')
  return response.json()
}

export async function listMissionRecordings() {
  const response = await fetch(`${API_BASE}/mission/recordings`)
  if (!response.ok) throw new Error('Failed to list recordings')
  return response.json()
}

export async function getMissionRecording(recordingId) {
  const response = await fetch(`${API_BASE}/mission/recording/${recordingId}`)
  if (!response.ok) throw new Error('Failed to get recording')
  return response.json()
}

export async function getAfterActionReport(recordingId) {
  const response = await fetch(`${API_BASE}/mission/recording/${recordingId}/report`)
  if (!response.ok) throw new Error('Failed to get report')
  return response.json()
}

// ============== Vision ==============

export async function detectObjects(image, mode = 'objects', confidence = 0.5) {
  const response = await fetch(`${API_BASE}/vision/detect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      image,
      mode,
      confidence_threshold: confidence
    })
  })
  if (!response.ok) throw new Error('Failed to detect objects')
  return response.json()
}

export async function analyzeImage(image, question, sessionId = null) {
  const response = await fetch(`${API_BASE}/vision/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      image,
      question,
      session_id: sessionId
    })
  })
  if (!response.ok) throw new Error('Visual analysis failed')
  return response.json()
}

// ============== Tracking ==============

export async function updateTracking(detections) {
  const response = await fetch(`${API_BASE}/tracking/update`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ detections })
  })
  if (!response.ok) throw new Error('Failed to update tracking')
  return response.json()
}

export async function getTracks() {
  const response = await fetch(`${API_BASE}/tracking/tracks`)
  if (!response.ok) throw new Error('Failed to get tracks')
  return response.json()
}

export async function getTrack(trackId) {
  const response = await fetch(`${API_BASE}/tracking/track/${trackId}`)
  if (!response.ok) throw new Error('Failed to get track')
  return response.json()
}

// ============== Audit ==============

export async function logAuditEvent(eventType, action, details = {}, options = {}) {
  const response = await fetch(`${API_BASE}/audit/log`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      event_type: eventType,
      action,
      details,
      session_id: options.sessionId,
      user_id: options.userId,
      brain_id: options.brainId,
      ai_confidence: options.aiConfidence,
      ai_reasoning: options.aiReasoning
    })
  })
  if (!response.ok) throw new Error('Failed to log event')
  return response.json()
}

export async function logAIDecision(action, recommendation, confidence, reasoning, options = {}) {
  const response = await fetch(`${API_BASE}/audit/log/ai-decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      action,
      recommendation,
      confidence,
      reasoning,
      session_id: options.sessionId,
      brain_id: options.brainId,
      details: options.details || {}
    })
  })
  if (!response.ok) throw new Error('Failed to log AI decision')
  return response.json()
}

export async function getAuditEvents(filters = {}) {
  const params = new URLSearchParams()
  if (filters.eventType) params.append('event_type', filters.eventType)
  if (filters.sessionId) params.append('session_id', filters.sessionId)
  if (filters.limit) params.append('limit', filters.limit)
  
  const response = await fetch(`${API_BASE}/audit/events?${params}`)
  if (!response.ok) throw new Error('Failed to get audit events')
  return response.json()
}

export async function getSessions(limit = 20, offset = 0) {
  const response = await fetch(`${API_BASE}/audit/sessions?limit=${limit}&offset=${offset}`)
  if (!response.ok) throw new Error('Failed to list sessions')
  return response.json()
}

export async function verifyAuditIntegrity(sessionId = null) {
  const url = sessionId 
    ? `${API_BASE}/audit/verify?session_id=${sessionId}`
    : `${API_BASE}/audit/verify`
  const response = await fetch(url)
  if (!response.ok) throw new Error('Failed to verify integrity')
  return response.json()
}
