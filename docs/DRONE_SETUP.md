# Drone Integration Setup

This guide explains how to connect a physical drone to the HMT Zero platform for live video streaming and telemetry tracking (GIS).

## Architecture Overview

The platform uses standard protocols to ensure compatibility with most PX4/ArduPilot drones (DJI, Autel, custom builds).

1.  **Telemetry (GIS Tracking)**: Uses **MAVLink** via a WebSocket bridge.
2.  **Video Feed (Visual Intelligence)**: Uses **RTSP** or **WebRTC** converted for browser playback.

### Connection Diagram

```mermaid
[Physical Drone] 
      |
      | (Radio/Telemetry 433/915MHz)
      v
[Ground Control Station (Mission Planner/QGC)]
      |
      | (MAVLink Forwarding)
      v
[MAVLink Router / Bridge] ----(WebSocket ws://)----> [HMT Zero Frontend]
      |                                                 (SensorContext)
      |
[RTSP Video Server] ---------(HTTP/WebRTC)---------> [HMT Zero Frontend]
                                                      (DroneFeedPanel)
```

## Step 1: Telemetry Setup (MAVLink)

To get the drone moving on the GIS Map, you need to bridge the MAVLink serial data to a WebSocket that the browser can read.

### Option A: Using MAVROS (ROS Users)
Run `rosbridge_server` to expose topics over WebSocket.

### Option B: Using mavlink-router (Recommended)
1.  Install `mavlink-router` on your ground station.
2.  Configure it to route serial data to a TCP/WebSocket port.
    ```ini
    [UdpEndpoint websockets]
    Mode = Server
    Address = 0.0.0.0
    Port = 5760
    ```

### Option C: Python Bridge (Simple)
We provide a simple Python script to bridge Serial -> WebSocket.
Run `python scripts/mavlink_bridge.py --device /dev/ttyUSB0` (Coming soon).

**In HMT Zero UI:**
1.  Go to **Drone** view.
2.  Open **Settings** (Gear icon).
3.  Enter the WebSocket URL: `ws://localhost:5760` (or your ground station IP).

## Step 2: Video Stream Setup

Browsers cannot natively play raw RTSP streams. You need a low-latency gateway.

### Recommended: MediaMTX (formerly rtsp-simple-server)
1.  Download and run [MediaMTX](https://github.com/bluenviron/mediamtx).
2.  Push your drone video to it:
    ```bash
    ffmpeg -i rtsp://drone-ip:554/stream -c copy -f rtsp rtsp://localhost:8554/live
    ```
3.  MediaMTX automatically provides a WebRTC stream at `http://localhost:8889/live`.

**In HMT Zero UI:**
1.  Go to **Drone** view.
2.  Open **Settings**.
3.  Enter the Stream URL: `http://localhost:8889/live` (WebRTC) or `http://localhost:8888/live` (HLS).

## Step 3: Visual Intelligence (VQA)

Once the video is live:
1.  Click the **Brain Icon** ("Analyze Scene") in the Drone Feed control bar.
2.  The system captures the current frame from the HTML5 Video element.
3.  It sends the frame to the AI Agent (backend).
4.  The AI analyzes the scene for threats/targets and logs the result to the Mission Audit.

## Troubleshooting

-   **CORS Errors**: Ensure your video server allows CORS (MediaMTX does by default).
-   **Latency**: Use WebRTC for <500ms latency. HLS/Dash can have 3-5s latency which is bad for tracking.
-   **No Telemetry**: Check if your Ground Control Station is "hogging" the COM port. Use MAVLink forwarding in Mission Planner (Ctrl+F > Mavlink Mirror).
