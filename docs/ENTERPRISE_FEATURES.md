# HMT Platform Enterprise Features

## Overview

This document describes the enterprise-grade features implemented for the HMT (Human-Machine Teaming) platform to meet defense/government contract requirements.

---

## Tier 1: Must-Have (Contract Requirements)

### 1. Immutable Audit Logging System
**Location:** `backend/audit/`

- **Hash-chained events** - Every event includes hash of previous event for tamper detection
- **Event types:** Authentication, AI decisions, operator actions, trust updates, detections
- **SQLite persistence** with integrity verification
- **Export for compliance review**

**API Endpoints:**
- `POST /audit/log` - Log general event
- `POST /audit/log/ai-decision` - Log AI decision with XAI data
- `POST /audit/log/operator-action` - Log operator response
- `GET /audit/events` - Query with filters
- `GET /audit/verify` - Verify chain integrity
- `GET /audit/export` - Export for review

### 2. Role-Based Access Control (RBAC)
**Location:** `backend/auth/rbac.py`

**Predefined Roles:**
| Role | Description | Clearance |
|------|-------------|-----------|
| Operator | Basic HMT interaction | UNCLASSIFIED |
| Senior Operator | Override capabilities | CUI |
| Mission Commander | Full mission control | SECRET |
| Administrator | System administration | TOP SECRET |
| Auditor | Read-only compliance | CUI |

**60+ Fine-grained Permissions** covering:
- Brain management
- AI interaction/override
- Detection/vision
- Trust calibration
- Mission control
- Data classification

**API Endpoints:**
- `POST /auth/login` - Authenticate user
- `GET /auth/users` - List users
- `POST /auth/check-permission` - Verify permission
- `POST /auth/check-clearance` - Verify clearance level

### 3. Data Encryption (At Rest + Transit)
**Location:** `backend/auth/encryption.py`

- **AES-256-GCM** authenticated encryption
- **PBKDF2 key derivation** (100k iterations)
- **Field-level encryption** for sensitive data
- **Associated data binding** prevents tampering

---

## Tier 2: Differentiators

### 4. Multi-Sensor Fusion Framework
**Location:** `backend/sensors/fusion.py`

**Supported Sensors:**
- Camera (RGB/IR)
- Radar
- LiDAR
- GPS/IMU
- Acoustic
- RF Detector
- Drone Telemetry

**Features:**
- Kalman filter-based state estimation
- IoU-based detection matching
- Sensor health monitoring
- Threat level assessment

**API Endpoints:**
- `POST /sensors/register` - Register sensor
- `POST /sensors/data` - Submit sensor data
- `GET /sensors/fused` - Get fused state

### 5. Real-Time Object Tracking
**Location:** `backend/sensors/tracker.py`

- **Persistent track IDs** across frames (OBJ-00001, OBJ-00002...)
- **SORT-inspired algorithm** with IoU matching
- **Velocity estimation** for prediction
- **Track confirmation** (min 3 hits)
- **Lost track handling** (max 15 misses)

**API Endpoints:**
- `POST /tracking/update` - Update with detections
- `GET /tracking/tracks` - Get all tracks
- `GET /tracking/track/{id}` - Get specific track

---

## Tier 3: Competitive Edge

### 6. Adaptive Communication (IQ/Vocabulary Matching)
**Location:** `backend/cognitive/adaptive_comm.py`

**Operator Profiling:**
- Flesch-Kincaid reading level analysis
- Technical term ratio tracking
- Domain familiarity learning (military, aviation, technical)
- Vocabulary richness measurement

**Communication Styles:**
| Style | Target Audience |
|-------|-----------------|
| Technical | 10+ year experts |
| Professional | 3-10 year proficient |
| Conversational | 1-3 year intermediate |
| Simplified | < 1 year novice |

**Features:**
- Automatic vocabulary simplification
- Contextual explanations for unfamiliar terms
- Step-by-step breakdowns for complex instructions
- LLM prompt modifiers for style consistency

**API Endpoints:**
- `POST /cognitive/analyze-message` - Analyze operator message
- `POST /cognitive/adapt-response` - Adapt AI response
- `GET /cognitive/operator-profile/{id}` - Get learned profile
- `GET /cognitive/style-prompt/{id}` - Get LLM modifier

### 7. Cognitive Load Prediction
**Location:** `backend/cognitive/cognitive_load.py`

**Workload Factors:**
- Active detections
- Threat level
- Pending decisions
- Time pressure
- Task complexity
- Information rate
- Interruptions

**States:** Underload → Optimal → Elevated → High → Overload

**Features:**
- 5-minute load prediction
- Overload risk assessment
- Automatic intervention recommendations
- Historical tracking

**API Endpoints:**
- `POST /cognitive/load/update` - Update metrics
- `GET /cognitive/load/{id}` - Get current state
- `GET /cognitive/load/{id}/history` - Get history
- `GET /cognitive/load/{id}/should-intervene` - Check intervention

### 8. Mission Replay & Analysis
**Location:** `backend/cognitive/mission_replay.py`

**Recording Features:**
- Frame-accurate event timeline
- AI decision capture with XAI
- Operator action logging
- Detection history
- Trust/cognitive load metrics

**Replay Features:**
- Time-based event retrieval
- Key moment identification
- Decision deep-analysis
- After-action report generation

**Report Includes:**
- Mission summary statistics
- Override rate analysis
- Trust/load trends
- Lessons learned
- Recommendations

**API Endpoints:**
- `POST /mission/start-recording` - Start recording
- `POST /mission/stop-recording/{id}` - Stop and save
- `POST /mission/record-event` - Log event
- `GET /mission/recordings` - List recordings
- `GET /mission/recording/{id}/report` - After-action report
- `GET /mission/recording/{id}/analyze-decision/{event_id}` - XAI analysis

---

## Frontend: RT-DETR/YOLOv8 Detection
**Location:** `frontend/src/utils/rtdetr.js`

- **ONNX Runtime Web** for browser-based inference
- **YOLOv8n model** (6MB, fast, accurate)
- **WebGL acceleration** with WASM fallback
- **80 COCO classes** with tactical class support planned
- **Non-Maximum Suppression** for clean detections

---

## API Documentation

Access Swagger UI at: `http://localhost:8000/docs`

All new endpoints are organized under these tags:
- `cognitive` - Adaptive communication, load prediction, replay
- `audit` - Logging, querying, integrity
- `auth` - RBAC, users, permissions
- `sensors` - Fusion, tracking

---

## Next Steps for Contract Readiness

1. **MIL-STD-882 Safety Analysis** - Document hazard analysis
2. **NIST Cybersecurity Framework** - Formal compliance documentation
3. **508 Accessibility** - WCAG 2.1 AA compliance
4. **STANAG 4586** - NATO UAV interoperability
5. **Red-team Testing** - Adversarial robustness verification
6. **Air-gapped Deployment** - Offline operation capability
