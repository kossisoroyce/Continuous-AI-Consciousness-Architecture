/**
 * RT-DETR Object Detection via ONNX Runtime Web
 * Real-Time Detection Transformer - state-of-the-art accuracy with real-time speed
 */
import * as ort from 'onnxruntime-web'

// COCO class names (80 classes)
const COCO_CLASSES = [
  'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
  'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
  'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
  'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
  'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
  'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
  'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
  'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
  'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator',
  'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]

// Military/tactical class names for future custom models
const TACTICAL_CLASSES = [
  'person', 'vehicle', 'aircraft', 'vessel', 'weapon', 'equipment', 
  'structure', 'barrier', 'drone', 'convoy'
]

class RTDETRDetector {
  constructor() {
    this.session = null
    this.modelLoaded = false
    this.inputSize = 640 // RT-DETR default input size
    this.classes = COCO_CLASSES
  }

  /**
   * Load the RT-DETR ONNX model
   * Falls back to a lighter YOLOv8n model if RT-DETR unavailable
   */
  async load(modelPath = null) {
    if (this.modelLoaded) return true

    try {
      // Configure ONNX Runtime for WASM (more compatible than WebGL)
      ort.env.wasm.wasmPaths = 'https://cdn.jsdelivr.net/npm/onnxruntime-web/dist/'
      
      // Load YOLOv8n from local public folder (exported with ultralytics)
      const modelUrl = modelPath || '/models/yolov8n.onnx'
      
      console.log('Loading YOLOv8n ONNX model from:', modelUrl)
      
      // Use WASM as primary provider (more reliable in browsers)
      this.session = await ort.InferenceSession.create(modelUrl, {
        executionProviders: ['wasm'],
        graphOptimizationLevel: 'all'
      })
      
      this.modelLoaded = true
      console.log('✅ YOLOv8n model loaded successfully')
      console.log('Input names:', this.session.inputNames)
      console.log('Output names:', this.session.outputNames)
      
      return true
    } catch (error) {
      console.error('❌ Failed to load detection model:', error)
      throw error
    }
  }

  /**
   * Preprocess image for model input
   */
  preprocessImage(imageElement, targetSize = 640) {
    const canvas = document.createElement('canvas')
    canvas.width = targetSize
    canvas.height = targetSize
    const ctx = canvas.getContext('2d')
    
    // Get dimensions - handle both video and image elements
    const sourceWidth = imageElement.videoWidth || imageElement.width || imageElement.naturalWidth
    const sourceHeight = imageElement.videoHeight || imageElement.height || imageElement.naturalHeight
    
    if (!sourceWidth || !sourceHeight) {
      throw new Error('Cannot get source dimensions from element')
    }
    
    // Calculate scaling to maintain aspect ratio
    const scale = Math.min(targetSize / sourceWidth, targetSize / sourceHeight)
    const scaledWidth = sourceWidth * scale
    const scaledHeight = sourceHeight * scale
    const offsetX = (targetSize - scaledWidth) / 2
    const offsetY = (targetSize - scaledHeight) / 2
    
    // Fill with gray (letterboxing)
    ctx.fillStyle = '#808080'
    ctx.fillRect(0, 0, targetSize, targetSize)
    
    // Draw scaled image
    ctx.drawImage(imageElement, offsetX, offsetY, scaledWidth, scaledHeight)
    
    // Get image data and normalize
    const imageData = ctx.getImageData(0, 0, targetSize, targetSize)
    const { data } = imageData
    
    // Convert to float32 and normalize to [0, 1]
    const float32Data = new Float32Array(3 * targetSize * targetSize)
    
    for (let i = 0; i < targetSize * targetSize; i++) {
      float32Data[i] = data[i * 4] / 255.0 // R
      float32Data[targetSize * targetSize + i] = data[i * 4 + 1] / 255.0 // G
      float32Data[2 * targetSize * targetSize + i] = data[i * 4 + 2] / 255.0 // B
    }
    
    return {
      tensor: new ort.Tensor('float32', float32Data, [1, 3, targetSize, targetSize]),
      scale,
      offsetX,
      offsetY,
      originalWidth: sourceWidth,
      originalHeight: sourceHeight
    }
  }

  /**
   * Run detection on video element
   */
  async detect(videoElement, confidenceThreshold = 0.5, maxDetections = 20) {
    if (!this.modelLoaded || !this.session) {
      throw new Error('Model not loaded')
    }

    try {
      // Preprocess
      const { tensor, scale, offsetX, offsetY, originalWidth, originalHeight } = 
        this.preprocessImage(videoElement, this.inputSize)
      
      // Run inference
      const inputName = this.session.inputNames[0]
      const feeds = { [inputName]: tensor }
      const results = await this.session.run(feeds)
      
      // Parse output (format depends on model)
      const detections = this.parseOutput(
        results, 
        confidenceThreshold, 
        maxDetections,
        scale,
        offsetX,
        offsetY,
        originalWidth,
        originalHeight
      )
      
      return detections
    } catch (error) {
      console.error('[RTDETR] Detection error:', error)
      return []
    }
  }

  /**
   * Parse model output to detection format
   */
  parseOutput(results, confidenceThreshold, maxDetections, scale, offsetX, offsetY, origW, origH) {
    const detections = []
    
    // Get output tensor (format varies by model)
    const outputName = this.session.outputNames[0]
    const output = results[outputName]
    const data = output.data
    const dims = output.dims
    
    // YOLOv8 output format: [1, 84, 8400] where 84 = 4 bbox + 80 classes
    if (dims.length === 3 && dims[1] === 84) {
      const numBoxes = dims[2]
      const numClasses = 80
      
      for (let i = 0; i < numBoxes && detections.length < maxDetections; i++) {
        // Get class scores
        let maxScore = 0
        let maxClassIdx = 0
        
        for (let c = 0; c < numClasses; c++) {
          const score = data[(4 + c) * numBoxes + i]
          if (score > maxScore) {
            maxScore = score
            maxClassIdx = c
          }
        }
        
        if (maxScore < confidenceThreshold) continue
        
        // Get bbox (center_x, center_y, width, height)
        const cx = data[0 * numBoxes + i]
        const cy = data[1 * numBoxes + i]
        const w = data[2 * numBoxes + i]
        const h = data[3 * numBoxes + i]
        
        // Convert to corner format and scale back to original image
        let x1 = (cx - w / 2 - offsetX) / scale
        let y1 = (cy - h / 2 - offsetY) / scale
        let bw = w / scale
        let bh = h / scale
        
        // Clamp to image bounds
        x1 = Math.max(0, Math.min(x1, origW))
        y1 = Math.max(0, Math.min(y1, origH))
        bw = Math.min(bw, origW - x1)
        bh = Math.min(bh, origH - y1)
        
        detections.push({
          class: this.classes[maxClassIdx] || `class_${maxClassIdx}`,
          confidence: maxScore,
          bbox: [x1, y1, bw, bh],
          classId: maxClassIdx
        })
      }
    }
    // RT-DETR output format: different structure
    else if (dims.length === 3) {
      // Handle RT-DETR specific output
      const numQueries = dims[1]
      const outputSize = dims[2]
      
      for (let i = 0; i < numQueries && detections.length < maxDetections; i++) {
        const baseIdx = i * outputSize
        
        // Assuming format: [x1, y1, x2, y2, conf, class_scores...]
        const x1 = data[baseIdx]
        const y1 = data[baseIdx + 1]
        const x2 = data[baseIdx + 2]
        const y2 = data[baseIdx + 3]
        const conf = data[baseIdx + 4]
        
        if (conf < confidenceThreshold) continue
        
        // Find best class
        let maxScore = 0
        let maxClassIdx = 0
        for (let c = 0; c < Math.min(80, outputSize - 5); c++) {
          const score = data[baseIdx + 5 + c]
          if (score > maxScore) {
            maxScore = score
            maxClassIdx = c
          }
        }
        
        // Scale bbox back to original image coordinates
        const bx1 = (x1 * this.inputSize - offsetX) / scale
        const by1 = (y1 * this.inputSize - offsetY) / scale
        const bx2 = (x2 * this.inputSize - offsetX) / scale
        const by2 = (y2 * this.inputSize - offsetY) / scale
        
        detections.push({
          class: this.classes[maxClassIdx] || `class_${maxClassIdx}`,
          confidence: conf * maxScore,
          bbox: [bx1, by1, bx2 - bx1, by2 - by1],
          classId: maxClassIdx
        })
      }
    }
    
    // Sort by confidence and apply NMS
    detections.sort((a, b) => b.confidence - a.confidence)
    return this.applyNMS(detections, 0.45)
  }

  /**
   * Non-Maximum Suppression to remove overlapping boxes
   */
  applyNMS(detections, iouThreshold = 0.45) {
    const kept = []
    const suppressed = new Set()
    
    for (let i = 0; i < detections.length; i++) {
      if (suppressed.has(i)) continue
      
      kept.push(detections[i])
      
      for (let j = i + 1; j < detections.length; j++) {
        if (suppressed.has(j)) continue
        
        const iou = this.calculateIoU(detections[i].bbox, detections[j].bbox)
        if (iou > iouThreshold) {
          suppressed.add(j)
        }
      }
    }
    
    return kept
  }

  /**
   * Calculate Intersection over Union
   */
  calculateIoU(box1, box2) {
    const [x1, y1, w1, h1] = box1
    const [x2, y2, w2, h2] = box2
    
    const xi1 = Math.max(x1, x2)
    const yi1 = Math.max(y1, y2)
    const xi2 = Math.min(x1 + w1, x2 + w2)
    const yi2 = Math.min(y1 + h1, y2 + h2)
    
    const intersection = Math.max(0, xi2 - xi1) * Math.max(0, yi2 - yi1)
    const union = w1 * h1 + w2 * h2 - intersection
    
    return intersection / union
  }

  /**
   * Dispose of model resources
   */
  dispose() {
    if (this.session) {
      this.session.release()
      this.session = null
      this.modelLoaded = false
    }
  }
}

// Export singleton instance
export const rtdetrDetector = new RTDETRDetector()
export { COCO_CLASSES, TACTICAL_CLASSES }
