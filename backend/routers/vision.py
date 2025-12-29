"""
Vision API Router - Object Detection and Segmentation via Replicate API
Supports YOLO for object detection and SAM for segmentation
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging
import time
from nurture.llm import get_client, LLMClient
import os
import base64
import asyncio
import httpx

logger = logging.getLogger(__name__)
router = APIRouter()

# Rate limiting tracker
_last_request_time = 0
_min_request_interval = 10  # seconds between requests for rate-limited accounts

# Vision Models
DEFAULT_DETECTION_MODEL = "zsxkib/yolov8:1728d8c4a2bbb96dc0e7477112b16a95a52836a571e10c3e8208cbcd50315400"
SAM_MODEL_VERSION = "a8275cba575d7429b69b6628676d3766667252f4772652a715d5f226526cc666" # SAM model version
DEFAULT_VQA_MODEL = "google/gemini-2.0-flash-001" # Good balance of speed and vision capabilities

def get_replicate_key():
    """Get Replicate API key at runtime (after .env is loaded)"""
    return os.getenv("REPLICATE_API_KEY")

class DetectionRequest(BaseModel):
    image: str  # Base64 encoded image
    mode: str = "objects"  # 'objects', 'segmentation', 'both'
    confidence_threshold: float = 0.5
    max_detections: int = 20

class VQARequest(BaseModel):
    image: str # Base64 encoded image
    question: str
    session_id: Optional[str] = None
    model: Optional[str] = DEFAULT_VQA_MODEL

class VQAResponse(BaseModel):
    answer: str
    confidence: float = 1.0 # Placeholder
    processing_time_ms: float

class Detection(BaseModel):
    class_name: str
    confidence: float
    bbox: List[float]  # [x, y, width, height]

class DetectionResponse(BaseModel):
    detections: List[dict]
    segmentation_mask: Optional[str] = None
    processing_time_ms: float

async def run_yolo_detection(image_base64: str, confidence: float, max_det: int) -> List[dict]:
    """Run YOLO object detection via Replicate SDK"""
    global _last_request_time
    
    api_key = get_replicate_key()
    
    if not api_key:
        logger.warning("No REPLICATE_API_KEY found - detection unavailable")
        return []  # Return empty - no mock data
    
    # Rate limiting check
    current_time = time.time()
    time_since_last = current_time - _last_request_time
    if time_since_last < _min_request_interval:
        logger.info(f"Rate limited - waiting {_min_request_interval - time_since_last:.1f}s")
        return []  # Return empty during rate limit
    
    _last_request_time = current_time
    logger.info(f"Running YOLO detection with Replicate SDK (conf={confidence})")
    
    try:
        import replicate
        
        # Prepare image input
        if image_base64.startswith('data:'):
            image_input = image_base64
        else:
            image_input = f"data:image/jpeg;base64,{image_base64.split(',')[-1]}"
        
        # Run prediction using Replicate SDK
        client = replicate.Client(api_token=api_key)
        
        # Use a working YOLO model - this one outputs JSON detections
        output = client.run(
            DEFAULT_DETECTION_MODEL,
            input={
                "image": image_input,
                "conf": confidence,
                "iou": 0.45
            }
        )
        
        logger.info(f"Replicate output type: {type(output)}")
        
        # Parse the output
        parsed = parse_yolo_output(output, confidence)
        logger.info(f"Parsed {len(parsed)} detections")
        return parsed
        
    except replicate.exceptions.ReplicateError as e:
        logger.error(f"Replicate API error: {e}")
        if "rate" in str(e).lower() or "429" in str(e):
            logger.warning("Rate limited by Replicate API")
        return []  # Return empty on API error
    except Exception as e:
        logger.error(f"YOLO detection error: {e}")
        return []  # Return empty on error

async def run_sam_segmentation(image_base64: str) -> Optional[str]:
    """Run SAM segmentation via Replicate API"""
    api_key = get_replicate_key()
    if not api_key:
        return None
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            if image_base64.startswith('data:'):
                image_input = image_base64
            else:
                image_input = f"data:image/jpeg;base64,{image_base64.split(',')[-1]}"
            
            response = await client.post(
                "https://api.replicate.com/v1/predictions",
                headers={
                    "Authorization": f"Token {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "version": SAM_MODEL_VERSION,
                    "input": {
                        "image": image_input
                    }
                }
            )
            
            if response.status_code != 201:
                return None
            
            prediction = response.json()
            prediction_id = prediction.get("id")
            
            # Poll for results
            for _ in range(60):  # Max 60 seconds for segmentation
                await asyncio.sleep(1)
                
                status_response = await client.get(
                    f"https://api.replicate.com/v1/predictions/{prediction_id}",
                    headers={"Authorization": f"Token {api_key}"}
                )
                
                status_data = status_response.json()
                status = status_data.get("status")
                
                if status == "succeeded":
                    output = status_data.get("output")
                    if isinstance(output, str):
                        return output  # Return mask image URL or base64
                    return None
                elif status == "failed":
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"SAM segmentation error: {e}")
            return None

def parse_yolo_output(output: dict, min_confidence: float) -> List[dict]:
    """Parse YOLO output into detection format"""
    detections = []
    
    # Handle different YOLO output formats
    if isinstance(output, list):
        for det in output:
            if isinstance(det, dict):
                conf = det.get("confidence", det.get("score", 0))
                if conf >= min_confidence:
                    detections.append({
                        "class": det.get("class", det.get("label", "object")),
                        "confidence": conf,
                        "bbox": det.get("bbox", det.get("box", [0, 0, 100, 100]))
                    })
    elif isinstance(output, dict):
        # Some models return dict with 'detections' key
        for det in output.get("detections", []):
            conf = det.get("confidence", 0)
            if conf >= min_confidence:
                detections.append({
                    "class": det.get("class", "object"),
                    "confidence": conf,
                    "bbox": det.get("bbox", [0, 0, 100, 100])
                })
    
    return detections

# Mock detection function removed - all data is now real

@router.post("/vision/detect", response_model=DetectionResponse)
async def detect_objects(request: DetectionRequest):
    """
    Run object detection and/or segmentation on an image.
    
    - mode: 'objects' for bounding boxes, 'segmentation' for masks, 'both' for both
    - image: Base64 encoded JPEG/PNG image
    """
    import time
    start_time = time.time()
    
    detections = []
    segmentation_mask = None
    
    try:
        if request.mode in ["objects", "both"]:
            detections = await run_yolo_detection(
                request.image,
                request.confidence_threshold,
                request.max_detections
            )
        
        if request.mode in ["segmentation", "both"]:
            segmentation_mask = await run_sam_segmentation(request.image)
        
        processing_time = (time.time() - start_time) * 1000
        
        return DetectionResponse(
            detections=detections,
            segmentation_mask=segmentation_mask,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vision/analyze", response_model=VQAResponse)
async def analyze_image(request: VQARequest):
    """
    Visual Question Answering: Chat with an image frame.
    Uses OpenRouter vision models (Gemini Flash, GPT-4o, etc).
    """
    import time
    start_time = time.time()
    
    # Get API key - reuse existing config if possible
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        # Check if we have a session client
        if request.session_id:
            client = get_client(request.session_id)
            if client and client.is_configured():
                api_key = client.api_key
    
    if not api_key:
        raise HTTPException(status_code=401, detail="OpenRouter API key required for VQA")
        
    try:
        client = LLMClient(api_key=api_key)
        
        # Prepare multimodal message
        if request.image.startswith('data:'):
            image_url = request.image
        else:
            image_url = f"data:image/jpeg;base64,{request.image}"
            
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": request.question},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            }
        ]
        
        # Use a vision-capable model
        client.model = request.model
        
        answer = client.chat(messages)
        
        processing_time = (time.time() - start_time) * 1000
        
        return VQAResponse(
            answer=answer,
            confidence=0.9,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"VQA error: {e}")
        raise HTTPException(status_code=500, detail=f"Visual analysis failed: {str(e)}")

@router.get("/vision/status")
async def vision_status():
    """Check vision API status and available models"""
    api_key = get_replicate_key()
    has_key = api_key is not None and len(api_key) > 0
    return {
        "replicate_configured": has_key,
        "api_key_preview": f"{api_key[:8]}..." if has_key else None,
        "models": {
            "object_detection": "YOLOv8" if has_key else "Unavailable (no API key)",
            "segmentation": "SAM 2" if has_key else "Not available"
        }
    }

@router.get("/vision/models")
async def list_models():
    """List available vision models"""
    return {
        "object_detection": [
            {"id": "yolov8", "name": "YOLOv8", "description": "Fast object detection, 80 COCO classes"},
        ],
        "segmentation": [
            {"id": "sam2", "name": "SAM 2", "description": "Segment Anything Model 2"},
        ]
    }
