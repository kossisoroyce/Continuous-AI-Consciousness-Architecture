import React, { useRef, useState, useEffect, useCallback } from 'react'
import { 
  Camera, CameraOff, Play, Pause, Settings, Target, 
  Box, Layers, RefreshCw, Download, Maximize2, AlertTriangle,
  Crosshair, Eye, Cpu, Activity, Brain, MessageSquare
} from 'lucide-react'
import { rtdetrDetector } from '../../utils/rtdetr'
import { useSensor } from '../../contexts/SensorContext'
import { analyzeImage } from '../../services/cognitiveApi'

export function DroneFeedPanel({ apiBase, instanceId }) {
  const { broadcastDetections, telemetry } = useSensor()
  const videoRef = useRef(null)
  const canvasRef = useRef(null)

  const streamRef = useRef(null)
  const animationRef = useRef(null)
  
  const [isStreaming, setIsStreaming] = useState(false)
  const [isDetecting, setIsDetecting] = useState(false)
  const [detectionMode, setDetectionMode] = useState('objects') // 'objects', 'segmentation', 'both'
  const [detections, setDetections] = useState([])
  const [segmentationMask, setSegmentationMask] = useState(null)
  const [fps, setFps] = useState(0)
  const [error, setError] = useState(null)
  const [modelStatus, setModelStatus] = useState('idle') // 'idle', 'loading', 'ready', 'processing'
  const [modelName, setModelName] = useState('RT-DETR') // Current model name
  const [showSettings, setShowSettings] = useState(false)
  
  // Drone Connection State
  const [connectionConfig, setConnectionConfig] = useState({
    mavlinkUrl: 'ws://localhost:5760',
    streamUrl: 'http://localhost:8889/live', // Default to WebRTC/HLS
    useExternalStream: false,
    isConnected: false
  })

  // VQA State
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [showAnalysis, setShowAnalysis] = useState(false)

  const [settings, setSettings] = useState({
    confidenceThreshold: 0.5,
    maxDetections: 20,
    showLabels: true,
    showConfidence: true,
    boxColor: '#d4a62a',
    segmentationOpacity: 0.4
  })

  const lastFrameTime = useRef(Date.now())
  const frameCount = useRef(0)

  // Load RT-DETR / YOLOv8 model via ONNX Runtime
  const loadModel = useCallback(async () => {
    if (rtdetrDetector.modelLoaded) {
      setModelStatus('ready')
      return
    }
    
    setModelStatus('loading')
    setError(null)
    
    try {
      console.log('Loading RT-DETR/YOLOv8 model...')
      await rtdetrDetector.load()
      setModelStatus('ready')
      setModelName('YOLOv8n-ONNX')
      console.log('Detection model loaded!')
    } catch (err) {
      console.error('Failed to load model:', err)
      setError(`Failed to load ML model: ${err.message}`)
      setModelStatus('idle')
    }
  }, [])

  // Analyze current frame with VQA
  const handleAnalyzeFrame = async () => {
    if (!videoRef.current || isAnalyzing) return
    
    setIsAnalyzing(true)
    setAnalysisResult(null)
    setShowAnalysis(true)
    
    try {
      // Capture high-quality frame
      const frame = captureFrame()
      if (!frame) throw new Error("Could not capture frame")
      
      // Call VQA API
      const result = await analyzeImage(
        frame,
        "Analyze this tactical scene. Identify potential threats, assets, and significant activity.",
        instanceId
      )
      
      setAnalysisResult(result.answer)
      
      // Log VQA result to audit
      logAIDecision(
        'visual_analysis',
        result.answer,
        result.confidence || 0.9,
        'Visual Question Answering on Sensor Feed',
        { 
          sessionId: 'current', // Ideally pass session ID prop or get from context
          brainId: instanceId,
          details: { question: "Analyze this tactical scene..." } 
        }
      ).catch(console.error)
      
    } catch (err) {
      console.error('Analysis failed:', err)
      setAnalysisResult(`Analysis failed: ${err.message}`)
    } finally {
      setIsAnalyzing(false)
    }
  }

  // Run detection on current video frame using RT-DETR/ONNX
  const runLocalDetection = useCallback(async () => {
    if (!rtdetrDetector.modelLoaded) {
      console.log('[Detection] Model not loaded yet')
      return []
    }
    if (!videoRef.current) {
      console.log('[Detection] No video ref')
      return []
    }
    if (!videoRef.current.videoWidth || !videoRef.current.videoHeight) {
      console.log('[Detection] Video not ready (no dimensions)')
      return []
    }
    if (modelStatus === 'processing') return []
    
    setModelStatus('processing')
    
    try {
      const detections = await rtdetrDetector.detect(
        videoRef.current,
        settings.confidenceThreshold,
        settings.maxDetections
      )
      
      if (detections.length > 0) {
        console.log(`[Detection] Found ${detections.length} objects:`, detections.map(d => d.class))
      }
      
      setModelStatus('ready')
      return detections
    } catch (err) {
      console.error('[Detection] Error:', err)
      setModelStatus('ready')
      return []
    }
  }, [settings.maxDetections, settings.confidenceThreshold, modelStatus])

  // Toggle Drone Connection
  const toggleConnection = () => {
    if (connectionConfig.useExternalStream) {
      // Disconnect
      setConnectionConfig(prev => ({ ...prev, useExternalStream: false }))
      setConnectionUrl(null)
      stopStream()
    } else {
      // Connect
      setConnectionConfig(prev => ({ ...prev, useExternalStream: true }))
      setConnectionUrl(connectionConfig.mavlinkUrl)
      // Auto-start stream if URL is provided
      if (connectionConfig.streamUrl) {
        startStream(true) // Pass true for external
      }
    }
  }

  // Start stream (Webcam or External)
  const startStream = async (forceExternal = false) => {
    try {
      setError(null)
      
      const useExternal = forceExternal || connectionConfig.useExternalStream
      
      if (useExternal && connectionConfig.streamUrl) {
        // External Stream (HLS/HTTP/WebRTC)
        if (videoRef.current) {
          // For simple MJPEG or direct browser-supported streams
          videoRef.current.src = connectionConfig.streamUrl
          videoRef.current.crossOrigin = "anonymous" // Needed for canvas processing
          // If HLS, we'd need hls.js here. For now assume browser supported (MJPEG/WebRTC/MP4)
          // or user uses MediaMTX WebRTC view which is an iframe, but we need raw video for detection.
          // Detection on external video requires CORS support on the video server!
          
          await videoRef.current.play().catch(e => {
            throw new Error(`Stream play failed: ${e.message}. Check CORS headers on video server.`)
          })
          
          setIsStreaming(true)
        }
      } else {
        // Webcam
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { 
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: 'environment'
          }
        })
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          streamRef.current = stream
          setIsStreaming(true)
        }
      }
    } catch (err) {
      setError(`Stream error: ${err.message}`)
      console.error('Failed to start stream:', err)
      setIsStreaming(false)
    }
  }

  // Stop webcam stream
  const stopStream = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    setIsStreaming(false)
    setIsDetecting(false)
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current)
    }
  }

  // Capture frame as base64
  const captureFrame = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return null
    
    const video = videoRef.current
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    ctx.drawImage(video, 0, 0)
    
    return canvas.toDataURL('image/jpeg', 0.8)
  }, [])

  // Run object detection via backend
  const runDetection = useCallback(async (frameData) => {
    if (modelStatus === 'processing') return
    
    setModelStatus('processing')
    
    try {
      const response = await fetch(`${apiBase}/vision/detect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image: frameData,
          mode: detectionMode,
          confidence_threshold: settings.confidenceThreshold,
          max_detections: settings.maxDetections
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        setDetections(data.detections || [])
        if (data.segmentation_mask) {
          setSegmentationMask(data.segmentation_mask)
        }
      }
    } catch (err) {
      console.error('Detection failed:', err)
    } finally {
      setModelStatus('ready')
    }
  }, [apiBase, detectionMode, settings, modelStatus])

  // Draw annotations on canvas
  const drawAnnotations = useCallback(() => {
    if (!canvasRef.current || !videoRef.current) return
    
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const video = videoRef.current
    
    canvas.width = video.videoWidth || 1280
    canvas.height = video.videoHeight || 720
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    // Draw segmentation mask if available
    if (segmentationMask && (detectionMode === 'segmentation' || detectionMode === 'both')) {
      ctx.globalAlpha = settings.segmentationOpacity
      // Segmentation mask would be drawn here from base64 or pixel data
      ctx.globalAlpha = 1
    }
    
    // Draw bounding boxes
    if (detectionMode === 'objects' || detectionMode === 'both') {
      detections.forEach((det, i) => {
        const [x, y, width, height] = det.bbox
        
        // Box
        ctx.strokeStyle = settings.boxColor
        ctx.lineWidth = 2
        ctx.strokeRect(x, y, width, height)
        
        // Corner brackets
        const bracketSize = 12
        ctx.lineWidth = 3
        
        // Top-left
        ctx.beginPath()
        ctx.moveTo(x, y + bracketSize)
        ctx.lineTo(x, y)
        ctx.lineTo(x + bracketSize, y)
        ctx.stroke()
        
        // Top-right
        ctx.beginPath()
        ctx.moveTo(x + width - bracketSize, y)
        ctx.lineTo(x + width, y)
        ctx.lineTo(x + width, y + bracketSize)
        ctx.stroke()
        
        // Bottom-left
        ctx.beginPath()
        ctx.moveTo(x, y + height - bracketSize)
        ctx.lineTo(x, y + height)
        ctx.lineTo(x + bracketSize, y + height)
        ctx.stroke()
        
        // Bottom-right
        ctx.beginPath()
        ctx.moveTo(x + width - bracketSize, y + height)
        ctx.lineTo(x + width, y + height)
        ctx.lineTo(x + width, y + height - bracketSize)
        ctx.stroke()
        
        // Label background
        if (settings.showLabels) {
          const label = settings.showConfidence 
            ? `${det.class} ${(det.confidence * 100).toFixed(0)}%`
            : det.class
          
          ctx.font = '12px monospace'
          const textWidth = ctx.measureText(label).width
          
          ctx.fillStyle = 'rgba(10, 12, 15, 0.85)'
          ctx.fillRect(x, y - 20, textWidth + 8, 18)
          
          ctx.fillStyle = settings.boxColor
          ctx.fillText(label, x + 4, y - 6)
        }
      })
    }
    
    // Crosshair in center
    const cx = canvas.width / 2
    const cy = canvas.height / 2
    ctx.strokeStyle = 'rgba(212, 166, 42, 0.3)'
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(cx - 30, cy)
    ctx.lineTo(cx + 30, cy)
    ctx.moveTo(cx, cy - 30)
    ctx.lineTo(cx, cy + 30)
    ctx.stroke()
    
  }, [detections, segmentationMask, detectionMode, settings])

  // Load model when detection is enabled
  useEffect(() => {
    if (isDetecting && !rtdetrDetector.modelLoaded) {
      loadModel()
    }
  }, [isDetecting, loadModel])

  // Detection loop using RT-DETR/ONNX (client-side)
  useEffect(() => {
    if (!isDetecting || !isStreaming) return
    if (!rtdetrDetector.modelLoaded && modelStatus !== 'loading') {
      loadModel()
      return
    }
    
    let lastDetectionTime = 0
    const detectionInterval = 200 // Run detection every 200ms for smoother tracking
    
    const loop = async (timestamp) => {
      // Calculate FPS
      frameCount.current++
      if (timestamp - lastFrameTime.current >= 1000) {
        setFps(frameCount.current)
        frameCount.current = 0
        lastFrameTime.current = timestamp
      }
      
      // Run local ONNX detection at interval
      if (timestamp - lastDetectionTime >= detectionInterval && rtdetrDetector.modelLoaded) {
        const newDetections = await runLocalDetection()
        setDetections(newDetections)
        // Broadcast to sensor fusion network (GIS)
        if (newDetections.length > 0) {
          broadcastDetections(newDetections)
        }
        lastDetectionTime = timestamp
      }
      
      // Draw annotations
      drawAnnotations()
      
      animationRef.current = requestAnimationFrame(loop)
    }
    
    animationRef.current = requestAnimationFrame(loop)
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [isDetecting, isStreaming, modelStatus, loadModel, runLocalDetection, drawAnnotations, detections.length])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopStream()
    }
  }, [])

  // Screenshot
  const takeScreenshot = () => {
    const frame = captureFrame()
    if (frame) {
      const link = document.createElement('a')
      link.download = `drone-capture-${Date.now()}.jpg`
      link.href = frame
      link.click()
    }
  }

  return (
    <div className="h-full flex flex-col bg-[#050810]">
      {/* Header */}
      <div className="flex-shrink-0 bg-[#0d1117] border-b border-[#30363d] px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Camera className="w-4 h-4 text-[#d4a62a]" />
          <span className="text-[10px] font-bold text-[#d4a62a] uppercase tracking-[0.15em] font-mono">
            Drone Feed Monitor
          </span>
          {isStreaming && (
            <span className="flex items-center gap-1.5 px-2 py-0.5 bg-[#2d2310] border border-[#d4a62a]/30 text-[#d4a62a] text-[9px] font-mono">
              <span className="w-1.5 h-1.5 bg-[#d4a62a] rounded-full animate-pulse" />
              LIVE
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {/* FPS Counter */}
          {isStreaming && (
            <span className="text-[9px] text-[#8b949e] font-mono">
              {fps} FPS
            </span>
          )}
          
          {/* Model Status */}
          <div className={`flex items-center gap-1 px-2 py-0.5 text-[9px] font-mono ${
            modelStatus === 'processing' ? 'text-[#d4a62a]' :
            modelStatus === 'ready' ? 'text-[#8b949e]' : 'text-[#484f58]'
          }`}>
            <Cpu className="w-3 h-3" />
            {modelStatus.toUpperCase()}
          </div>
          
          {/* Settings */}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={`p-1.5 hover:bg-[#21262d] transition-colors ${
              showSettings ? 'text-[#d4a62a]' : 'text-[#8b949e]'
            }`}
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Video Container */}
        <div className="flex-1 relative bg-black">
          {/* Video Element */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="absolute inset-0 w-full h-full object-contain"
            style={{ display: isStreaming ? 'block' : 'none' }}
          />
          
          {/* Canvas Overlay */}
          <canvas
            ref={canvasRef}
            className="absolute inset-0 w-full h-full object-contain pointer-events-none"
            style={{ display: isStreaming ? 'block' : 'none' }}
          />
          
          {/* No Stream Placeholder */}
          {!isStreaming && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <CameraOff className="w-16 h-16 text-[#30363d] mx-auto mb-4" />
                <p className="text-[#484f58] text-sm font-mono uppercase tracking-wider mb-4">
                  No Feed Active
                </p>
                <button
                  onClick={startStream}
                  className="inline-flex items-center gap-2 bg-[#d4a62a] hover:bg-[#b8942a] text-[#0a0c0f] px-6 py-2 font-bold text-sm uppercase tracking-wider font-mono transition-colors"
                >
                  <Camera className="w-4 h-4" />
                  Start Feed
                </button>
              </div>
            </div>
          )}
          
          {/* Error Display */}
          {error && (
            <div className="absolute top-4 left-4 right-4 bg-[#3d1f1f] border border-[#ef4444]/30 text-[#ef4444] px-4 py-2 text-sm font-mono flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              {error}
            </div>
          )}
          
          {/* Detection Stats Overlay */}
          {isStreaming && isDetecting && detections.length > 0 && (
            <div className="absolute top-4 left-4 bg-[#0a0c0f]/90 border border-[#30363d] px-3 py-2">
              <div className="text-[9px] text-[#d4a62a] uppercase tracking-wider font-mono mb-1">
                Detections
              </div>
              <div className="text-lg font-bold text-[#e6edf3] font-mono">
                {detections.length}
              </div>
              <div className="text-[9px] text-[#8b949e] font-mono">
                objects tracked
              </div>
            </div>
          )}
          
          {/* VQA Analysis Overlay */}
          {showAnalysis && (
            <div className="absolute inset-0 bg-black/80 flex items-center justify-center p-8 z-20 backdrop-blur-sm">
              <div className="bg-[#0d1117] border border-[#30363d] w-full max-w-2xl max-h-full flex flex-col shadow-2xl">
                <div className="flex items-center justify-between p-4 border-b border-[#30363d] bg-[#161b22]">
                  <div className="flex items-center gap-2 text-[#d4a62a]">
                    <Brain className="w-5 h-5" />
                    <span className="text-sm font-bold font-mono uppercase tracking-wider">Visual Intelligence</span>
                  </div>
                  <button 
                    onClick={() => setShowAnalysis(false)}
                    className="text-[#8b949e] hover:text-[#e6edf3]"
                  >
                    ×
                  </button>
                </div>
                
                <div className="p-6 overflow-y-auto font-mono text-sm leading-relaxed text-[#e6edf3]">
                  {isAnalyzing ? (
                    <div className="flex flex-col items-center justify-center py-12 gap-4">
                      <div className="w-8 h-8 border-2 border-[#d4a62a] border-t-transparent rounded-full animate-spin" />
                      <div className="text-[#8b949e] animate-pulse">ANALYZING TACTICAL SCENE...</div>
                    </div>
                  ) : (
                    <div className="whitespace-pre-wrap">
                      {analysisResult}
                    </div>
                  )}
                </div>
                
                <div className="p-4 border-t border-[#30363d] bg-[#161b22] flex justify-end">
                  <button
                    onClick={() => setShowAnalysis(false)}
                    className="px-4 py-2 bg-[#21262d] hover:bg-[#30363d] text-[#e6edf3] text-xs font-bold uppercase tracking-wider border border-[#30363d]"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Telemetry Overlay */}
          {isStreaming && (
            <div className="absolute bottom-4 left-4 right-4 flex justify-between items-end">
              <div className="bg-[#0a0c0f]/90 border border-[#30363d] px-3 py-2">
                <div className="grid grid-cols-3 gap-4 text-[9px] font-mono">
                  <div>
                    <span className="text-[#484f58]">ALT</span>
                    <span className="text-[#e6edf3] ml-2">120m</span>
                  </div>
                  <div>
                    <span className="text-[#484f58]">SPD</span>
                    <span className="text-[#e6edf3] ml-2">15m/s</span>
                  </div>
                  <div>
                    <span className="text-[#484f58]">HDG</span>
                    <span className="text-[#e6edf3] ml-2">045°</span>
                  </div>
                </div>
              </div>
              
              <div className="bg-[#0a0c0f]/90 border border-[#30363d] px-3 py-2">
                <div className="text-[9px] font-mono text-[#8b949e]">
                  {new Date().toLocaleTimeString()}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="w-64 border-l border-[#30363d] bg-[#0d1117] overflow-y-auto">
            <div className="p-4 space-y-4">
              {/* Detection Settings Header */}
              <div className="text-[10px] text-[#d4a62a] uppercase tracking-wider font-mono mb-3">
                Drone Connection
              </div>

              {/* Connection Inputs */}
              <div className="space-y-2 mb-4 pb-4 border-b border-[#30363d]">
                <div>
                  <label className="block text-[9px] text-[#484f58] uppercase tracking-wider font-mono mb-1">
                    MAVLink Bridge URL
                  </label>
                  <input 
                    type="text" 
                    value={connectionConfig.mavlinkUrl}
                    onChange={(e) => setConnectionConfig(c => ({ ...c, mavlinkUrl: e.target.value }))}
                    className="w-full bg-[#161b22] border border-[#30363d] text-[#e6edf3] text-[10px] px-2 py-1 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[9px] text-[#484f58] uppercase tracking-wider font-mono mb-1">
                    Video Stream URL (RTSP/WebRTC)
                  </label>
                  <input 
                    type="text" 
                    value={connectionConfig.streamUrl}
                    onChange={(e) => setConnectionConfig(c => ({ ...c, streamUrl: e.target.value }))}
                    className="w-full bg-[#161b22] border border-[#30363d] text-[#e6edf3] text-[10px] px-2 py-1 font-mono"
                  />
                </div>
                <button 
                  className={`w-full py-1.5 text-[10px] font-bold uppercase tracking-wider ${
                    connectionConfig.isConnected 
                      ? 'bg-[#2d2310] text-[#d4a62a] border border-[#d4a62a]/30' 
                      : 'bg-[#21262d] text-[#8b949e] border border-[#30363d] hover:text-[#e6edf3]'
                  }`}
                  onClick={() => setConnectionConfig(c => ({ ...c, isConnected: !c.isConnected }))}
                >
                  {connectionConfig.isConnected ? 'Connected' : 'Connect Drone'}
                </button>
              </div>

              <div className="text-[10px] text-[#d4a62a] uppercase tracking-wider font-mono mb-3">
                Detection Settings
              </div>
              
              {/* Detection Mode */}
              <div>
                <label className="block text-[9px] text-[#484f58] uppercase tracking-wider font-mono mb-2">
                  Mode
                </label>
                <div className="flex gap-1">
                  {['objects', 'segmentation', 'both'].map(mode => (
                    <button
                      key={mode}
                      onClick={() => setDetectionMode(mode)}
                      className={`flex-1 py-1.5 text-[9px] font-mono uppercase transition-colors ${
                        detectionMode === mode
                          ? 'bg-[#d4a62a] text-[#0a0c0f]'
                          : 'bg-[#21262d] text-[#8b949e] hover:bg-[#30363d]'
                      }`}
                    >
                      {mode === 'objects' ? <Box className="w-3 h-3 mx-auto" /> :
                       mode === 'segmentation' ? <Layers className="w-3 h-3 mx-auto" /> :
                       <Eye className="w-3 h-3 mx-auto" />}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Confidence Threshold */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-[9px] text-[#484f58] uppercase tracking-wider font-mono">
                    Confidence
                  </label>
                  <span className="text-[10px] text-[#e6edf3] font-mono">
                    {(settings.confidenceThreshold * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="relative h-1 bg-[#30363d]">
                  <div 
                    className="absolute h-full bg-[#d4a62a]"
                    style={{ width: `${settings.confidenceThreshold * 100}%` }}
                  />
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={settings.confidenceThreshold * 100}
                    onChange={(e) => setSettings(s => ({
                      ...s,
                      confidenceThreshold: parseInt(e.target.value) / 100
                    }))}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                </div>
              </div>
              
              {/* Max Detections */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-[9px] text-[#484f58] uppercase tracking-wider font-mono">
                    Max Objects
                  </label>
                  <span className="text-[10px] text-[#e6edf3] font-mono">
                    {settings.maxDetections}
                  </span>
                </div>
                <div className="relative h-1 bg-[#30363d]">
                  <div 
                    className="absolute h-full bg-[#d4a62a]"
                    style={{ width: `${(settings.maxDetections / 50) * 100}%` }}
                  />
                  <input
                    type="range"
                    min="1"
                    max="50"
                    value={settings.maxDetections}
                    onChange={(e) => setSettings(s => ({
                      ...s,
                      maxDetections: parseInt(e.target.value)
                    }))}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                </div>
              </div>
              
              {/* Toggles */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[9px] text-[#484f58] uppercase tracking-wider font-mono">
                    Show Labels
                  </span>
                  <button
                    onClick={() => setSettings(s => ({ ...s, showLabels: !s.showLabels }))}
                    className={`w-8 h-4 flex items-center px-0.5 transition-colors ${
                      settings.showLabels ? 'bg-[#d4a62a] justify-end' : 'bg-[#30363d] justify-start'
                    }`}
                  >
                    <div className="w-3 h-3 bg-[#e6edf3]" />
                  </button>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-[9px] text-[#484f58] uppercase tracking-wider font-mono">
                    Show Confidence
                  </span>
                  <button
                    onClick={() => setSettings(s => ({ ...s, showConfidence: !s.showConfidence }))}
                    className={`w-8 h-4 flex items-center px-0.5 transition-colors ${
                      settings.showConfidence ? 'bg-[#d4a62a] justify-end' : 'bg-[#30363d] justify-start'
                    }`}
                  >
                    <div className="w-3 h-3 bg-[#e6edf3]" />
                  </button>
                </div>
              </div>
              
              {/* Segmentation Opacity */}
              {(detectionMode === 'segmentation' || detectionMode === 'both') && (
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-[9px] text-[#484f58] uppercase tracking-wider font-mono">
                      Mask Opacity
                    </label>
                    <span className="text-[10px] text-[#e6edf3] font-mono">
                      {(settings.segmentationOpacity * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="relative h-1 bg-[#30363d]">
                    <div 
                      className="absolute h-full bg-[#d4a62a]"
                      style={{ width: `${settings.segmentationOpacity * 100}%` }}
                    />
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={settings.segmentationOpacity * 100}
                      onChange={(e) => setSettings(s => ({
                        ...s,
                        segmentationOpacity: parseInt(e.target.value) / 100
                      }))}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Control Bar */}
      <div className="flex-shrink-0 bg-[#0d1117] border-t border-[#30363d] px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {/* Stream Control */}
          {isStreaming ? (
            <button
              onClick={stopStream}
              className="flex items-center gap-2 px-3 py-1.5 bg-[#3d1f1f] border border-[#ef4444]/30 text-[#ef4444] text-[10px] font-mono uppercase tracking-wider hover:bg-[#4d2525] transition-colors"
            >
              <CameraOff className="w-3.5 h-3.5" />
              Stop Feed
            </button>
          ) : (
            <button
              onClick={startStream}
              className="flex items-center gap-2 px-3 py-1.5 bg-[#2d2310] border border-[#d4a62a]/30 text-[#d4a62a] text-[10px] font-mono uppercase tracking-wider hover:bg-[#3d3320] transition-colors"
            >
              <Camera className="w-3.5 h-3.5" />
              Start Feed
            </button>
          )}
          
          {/* Detection Control */}
          {isStreaming && (
            <button
              onClick={() => setIsDetecting(!isDetecting)}
              className={`flex items-center gap-2 px-3 py-1.5 text-[10px] font-mono uppercase tracking-wider transition-colors ${
                isDetecting
                  ? 'bg-[#d4a62a] text-[#0a0c0f]'
                  : 'bg-[#21262d] text-[#8b949e] hover:bg-[#30363d]'
              }`}
            >
              {isDetecting ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
              {isDetecting ? 'Stop Detection' : 'Start Detection'}
            </button>
          )}

          {/* Analyze Frame - Visual Intelligence */}
          {isStreaming && (
            <button
              onClick={handleAnalyzeFrame}
              disabled={isAnalyzing}
              className="flex items-center gap-2 px-3 py-1.5 bg-[#161b22] border border-[#30363d] text-[#22d3ee] text-[10px] font-mono uppercase tracking-wider hover:bg-[#21262d] transition-colors disabled:opacity-50"
              title="Ask AI to analyze the current frame"
            >
              <Brain className="w-3.5 h-3.5" />
              {isAnalyzing ? 'Analyzing...' : 'Analyze Scene'}
            </button>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {/* Screenshot */}
          {isStreaming && (
            <button
              onClick={takeScreenshot}
              className="p-1.5 hover:bg-[#21262d] text-[#8b949e] hover:text-[#e6edf3] transition-colors"
              title="Take Screenshot"
            >
              <Download className="w-4 h-4" />
            </button>
          )}
          
          {/* Fullscreen */}
          <button
            className="p-1.5 hover:bg-[#21262d] text-[#8b949e] hover:text-[#e6edf3] transition-colors"
            title="Fullscreen"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}

export default DroneFeedPanel
