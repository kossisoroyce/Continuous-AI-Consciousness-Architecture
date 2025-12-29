import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { logAuditEvent } from '../services/cognitiveApi';
import { useSession } from './SessionContext';
import { useInstance } from './InstanceContext';

const SensorContext = createContext();

export function SensorProvider({ children }) {
  const { sessionId } = useSession();
  const { selectedInstanceId } = useInstance();
  
  // Drone Telemetry (simulated for now, would come from MAVLink in prod)
  const [telemetry, setTelemetry] = useState({
    latitude: 51.505, // Default London
    longitude: -0.09,
    altitude: 50, // meters
    heading: 0,   // degrees (0 = North)
    speed: 0      // m/s
  });

  // Current detections from the vision system
  const [sensorDetections, setSensorDetections] = useState([]);
  
  // History of detections for trails
  const [detectionHistory, setDetectionHistory] = useState([]);

  // Connection State
  const [connectionUrl, setConnectionUrl] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);

  // Refs for logging throttling
  const lastTelemetryLogRef = useRef(0);

  // Connect to MAVLink Bridge
  useEffect(() => {
    if (!connectionUrl) return;

    try {
      const ws = new WebSocket(connectionUrl);
      
      ws.onopen = () => {
        console.log('MAVLink Bridge Connected');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Expecting generic telemetry format or MAVLink JSON
          // { lat, lon, alt, heading, ground_speed }
          if (data.lat || data.latitude) {
            setTelemetry(prev => ({
              ...prev,
              latitude: data.lat || data.latitude || prev.latitude,
              longitude: data.lon || data.longitude || prev.longitude,
              altitude: data.alt || data.altitude || prev.altitude,
              heading: data.hdg || data.heading || prev.heading,
              speed: data.ground_speed || data.speed || prev.speed
            }));
          }
        } catch (e) {
          console.warn('Invalid MAVLink data:', event.data);
        }
      };

      ws.onclose = () => {
        console.log('MAVLink Bridge Disconnected');
        setIsConnected(false);
      };

      socketRef.current = ws;

      return () => {
        ws.close();
      };
    } catch (e) {
      console.error('Failed to connect to MAVLink bridge:', e);
    }
  }, [connectionUrl]);

  // Update telemetry (Simulation fallback if not connected)
  useEffect(() => {
    if (isConnected) return; // Disable simulation when connected

    const interval = setInterval(() => {
      setTelemetry(prev => {
        // Simulate a slow circular orbit
        const time = Date.now() / 10000;
        const radius = 0.002; // ~200m
        const newTelemetry = {
          ...prev,
          latitude: 51.505 + Math.sin(time) * radius,
          longitude: -0.09 + Math.cos(time) * radius * 1.5, // 1.5 for aspect ratio correction
          heading: (prev.heading + 1) % 360
        };
        
        // Log telemetry to audit every 5 seconds for replay
        const now = Date.now();
        if (now - lastTelemetryLogRef.current > 5000 && sessionId && selectedInstanceId) {
          logAuditEvent(
            'detection.track', // Using generic track event for telemetry
            'telemetry_update',
            newTelemetry,
            { sessionId, brainId: selectedInstanceId }
          ).catch(e => console.warn("Failed to log telemetry", e));
          lastTelemetryLogRef.current = now;
        }
        
        return newTelemetry;
      });
    }, 100); // 10Hz update

    return () => clearInterval(interval);
  }, [sessionId, selectedInstanceId]);

  // Function to broadcast new detections from the vision system
  const broadcastDetections = (detections, source = 'drone_1') => {
    // Transform detections to include geospatial coordinates
    // In a real system, we'd use FOV, altitude, and heading to project pixels to lat/lon
    // Here we'll do a simple projection based on the drone's position
    
    const timestamp = Date.now();
    
    const geoDetections = detections.map(det => {
      // Simple offset simulation based on bounding box center
      // Center of screen is drone position.
      // x-axis is longitude, y-axis is latitude (simplified)
      const [x, y, w, h] = det.bbox;
      const screenCenterX = 640 / 2; // Assuming 640x640 input
      const screenCenterY = 640 / 2;
      
      // Calculate offset meters (approx) based on altitude
      // at 50m altitude, typical FOV covers ~50x50m
      const metersPerPixel = (telemetry.altitude * 1.0) / 640;
      
      const offsetX = (x + w/2 - screenCenterX) * metersPerPixel;
      const offsetY = (y + h/2 - screenCenterY) * metersPerPixel;
      
      // Convert meters to lat/lon degrees (very rough approx)
      // 1 deg lat ~= 111km, 1 deg lon ~= 111km * cos(lat)
      const dLat = -offsetY / 111111; // -y is North (up) in pixel coords usually, but y goes down in canvas
      // Actually in canvas y=0 is top. So +y is South. 
      // If heading is 0 (North), +y (down screen) is South (lower lat). So dLat should be negative. Correct.
      const dLon = offsetX / (111111 * Math.cos(telemetry.latitude * Math.PI / 180));
      
      return {
        ...det,
        id: det.id || `${source}_${timestamp}_${Math.random().toString(36).substr(2, 5)}`,
        source,
        timestamp,
        location: {
          lat: telemetry.latitude + dLat,
          lon: telemetry.longitude + dLon
        }
      };
    });

    setSensorDetections(geoDetections);
    
    // Add to history (limit to 100 items)
    setDetectionHistory(prev => [...geoDetections, ...prev].slice(0, 100));
    
    // Log significant detections to audit
    if (sessionId && selectedInstanceId) {
        logAuditEvent(
            'detection.new',
            'objects_detected',
            { 
              count: geoDetections.length, 
              objects: geoDetections.map(d => ({
                class: d.class,
                confidence: d.confidence,
                location: d.location,
                bbox: d.bbox
              }))
            },
            { sessionId, brainId: selectedInstanceId }
        ).catch(e => console.warn("Failed to log detections", e));
    }
  };

  const value = {
    telemetry,
    setTelemetry,
    sensorDetections,
    detectionHistory,
    broadcastDetections,
    setConnectionUrl,
    isConnected
  };

  return (
    <SensorContext.Provider value={value}>
      {children}
    </SensorContext.Provider>
  );
}

export function useSensor() {
  const context = useContext(SensorContext);
  if (!context) {
    throw new Error('useSensor must be used within a SensorProvider');
  }
  return context;
}
