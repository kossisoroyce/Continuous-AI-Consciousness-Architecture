import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Circle } from 'react-leaflet';
import { Search, Map as MapIcon, Crosshair, Navigation, Cpu } from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useSensor } from '../../contexts/SensorContext';

// Fix Leaflet default icon issue in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom Icons
const droneIcon = new L.DivIcon({
  className: 'custom-drone-icon',
  html: `<div style="background-color: #d4a62a; width: 16px; height: 16px; border-radius: 50%; border: 2px solid #0a0c0f; box-shadow: 0 0 10px #d4a62a;"></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8]
});

const detectionIcon = new L.DivIcon({
  className: 'custom-detection-icon',
  html: `<div style="background-color: #ef4444; width: 12px; height: 12px; transform: rotate(45deg); border: 1px solid #0a0c0f;"></div>`,
  iconSize: [12, 12],
  iconAnchor: [6, 6]
});

// Component to handle map movement
function MapController({ center, zoom, tracking }) {
  const map = useMap();
  useEffect(() => {
    if (center && tracking) {
      map.flyTo(center, zoom, {
        duration: 1.0,
        easeLinearity: 0.25
      });
    }
  }, [center, zoom, tracking, map]);
  return null;
}

export function GISMapPanel({ apiBase, replayTelemetry, replayDetections }) {
  const sensorData = useSensor();
  
  // Use replay data if provided, otherwise use live sensor data
  const telemetry = replayTelemetry || sensorData.telemetry;
  const sensorDetections = replayDetections || sensorData.sensorDetections;
  
  const [query, setQuery] = useState('');
  const [center, setCenter] = useState([51.505, -0.09]); 
  const [zoom, setZoom] = useState(13);
  const [markers, setMarkers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [trackingDrone, setTrackingDrone] = useState(true);

  // Sync map center with drone telemetry if tracking is enabled
  useEffect(() => {
    if (trackingDrone && telemetry) {
      setCenter([telemetry.latitude, telemetry.longitude]);
    }
  }, [telemetry, trackingDrone]);

  // Search location using Nominatim (OpenStreetMap)
  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setTrackingDrone(false); // Disable drone tracking when searching

    try {
      const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`);
      const data = await response.json();

      if (data && data.length > 0) {
        const result = data[0];
        const lat = parseFloat(result.lat);
        const lon = parseFloat(result.lon);
        
        const newLocation = [lat, lon];
        setCenter(newLocation);
        setZoom(16);
        
        // Add marker
        setMarkers(prev => [...prev, {
          position: newLocation,
          title: result.display_name,
          type: 'search'
        }]);
      } else {
        setError('Location not found');
      }
    } catch (err) {
      setError('Search failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLocateMe = () => {
    setTrackingDrone(false);
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          const newLocation = [latitude, longitude];
          setCenter(newLocation);
          setZoom(16);
          setMarkers(prev => [...prev, {
            position: newLocation,
            title: 'Current Location',
            type: 'user'
          }]);
        },
        () => setError('Geolocation failed')
      );
    } else {
      setError('Geolocation not supported');
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#050810] relative">
      {/* Header / Search Bar Overlay */}
      <div className="absolute top-4 left-4 right-4 z-[1000] flex gap-2">
        <form onSubmit={handleSearch} className="flex-1 flex gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter coordinates or location..."
              className="w-full bg-[#0d1117]/90 border border-[#30363d] text-[#e6edf3] px-4 py-2 pl-10 text-xs font-mono backdrop-blur-sm focus:border-[#d4a62a] focus:outline-none rounded-sm shadow-lg"
            />
            <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-[#8b949e]" />
          </div>
          <button 
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-[#d4a62a]/90 text-[#0a0c0f] text-xs font-bold uppercase tracking-wider hover:bg-[#b8942a] backdrop-blur-sm shadow-lg rounded-sm flex items-center gap-2"
          >
            {loading ? 'Scanning...' : 'Navigate'}
          </button>
        </form>
        <button 
          onClick={() => setTrackingDrone(!trackingDrone)}
          className={`px-3 py-2 border border-[#30363d] backdrop-blur-sm shadow-lg rounded-sm transition-colors ${
            trackingDrone ? 'bg-[#d4a62a]/90 text-[#0a0c0f]' : 'bg-[#161b22]/90 text-[#d4a62a]'
          }`}
          title="Track Drone"
        >
          <Cpu className="w-4 h-4" />
        </button>
        <button 
          onClick={handleLocateMe}
          className="px-3 py-2 bg-[#161b22]/90 border border-[#30363d] text-[#d4a62a] hover:bg-[#21262d] backdrop-blur-sm shadow-lg rounded-sm"
          title="Locate Me"
        >
          <Crosshair className="w-4 h-4" />
        </button>
      </div>

      {/* Map Container */}
      <div className="flex-1 z-0">
        <MapContainer 
          center={center} 
          zoom={zoom} 
          style={{ height: '100%', width: '100%', background: '#050810' }}
          zoomControl={false}
        >
          {/* Dark Mode Tiles */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />
          
          <MapController center={center} zoom={zoom} tracking={trackingDrone} />
          
          {/* User/Search Markers */}
          {markers.map((marker, idx) => (
            <Marker key={idx} position={marker.position}>
              <Popup className="font-mono text-xs">
                <div className="text-[#0a0c0f] font-bold">{marker.title}</div>
                <div className="text-[10px] text-gray-600">
                  {marker.position[0].toFixed(6)}, {marker.position[1].toFixed(6)}
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Drone Marker */}
          {telemetry && (
            <>
              <Marker 
                position={[telemetry.latitude, telemetry.longitude]} 
                icon={droneIcon}
                zIndexOffset={1000}
              >
                <Popup className="font-mono text-xs">
                  <div className="text-[#0a0c0f] font-bold">DRONE-1</div>
                  <div className="text-[10px] text-gray-600">
                    ALT: {telemetry.altitude}m<br/>
                    HDG: {telemetry.heading}°
                  </div>
                </Popup>
              </Marker>
              <Circle 
                center={[telemetry.latitude, telemetry.longitude]}
                radius={telemetry.altitude * 1.5} // Approximate FOV footprint
                pathOptions={{ color: '#d4a62a', fillColor: '#d4a62a', fillOpacity: 0.1, weight: 1, dashArray: '5, 5' }}
              />
            </>
          )}

          {/* Sensor Detections */}
          {sensorDetections.map((det) => (
            <Marker 
              key={det.id} 
              position={[det.location.lat, det.location.lon]} 
              icon={detectionIcon}
            >
              <Popup className="font-mono text-xs">
                <div className="text-[#0a0c0f] font-bold">{det.class.toUpperCase()}</div>
                <div className="text-[10px] text-gray-600">
                  CONF: {(det.confidence * 100).toFixed(0)}%
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {/* Status Footer */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-[#0d1117]/90 border border-[#30363d] p-2 backdrop-blur-sm rounded-sm">
        <div className="flex items-center gap-3 text-[10px] font-mono">
          <div className="flex items-center gap-1 text-[#d4a62a]">
            <Navigation className="w-3 h-3" />
            <span>GIS SYSTEM ACTIVE</span>
          </div>
          <div className="text-[#8b949e]">
            LAT: {center[0].toFixed(4)} LON: {center[1].toFixed(4)}
          </div>
          {error && <span className="text-[#ef4444]">{error}</span>}
        </div>
      </div>
    </div>
  );
}
