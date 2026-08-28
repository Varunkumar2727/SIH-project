import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getImageUrl } from '../services/api';

export default function MapViewer({ 
  rawImageUrl, 
  results, 
  layers, 
  opacity,
  isCalibrating,
  calibrationLine,
  setCalibrationLine
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const layerGroupRef = useRef(null);
  const imageOverlayRef = useRef(null);

  const width = results?.dimensions?.width || 800;
  const height = results?.dimensions?.height || 600;

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Clean up existing map instance
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    // Initialize Leaflet map with Simple CRS (pixel coordinates)
    const bounds = [[0, 0], [height, width]];
    const map = L.map(mapContainerRef.current, {
      crs: L.CRS.Simple,
      minZoom: -2,
      maxZoom: 3,
      zoomSnap: 0.25,
      attributionControl: false
    });

    mapInstanceRef.current = map;
    layerGroupRef.current = L.layerGroup().addTo(map);

    // Fit map bounds
    map.fitBounds(bounds);

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [width, height]);

  // Handle Calibration Drawing
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    const onClick = (e) => {
      if (!isCalibrating) return;
      if (calibrationLine.length >= 2) return;
      
      const newPoint = { lat: e.latlng.lat, lng: e.latlng.lng, x: e.latlng.lng, y: height - e.latlng.lat };
      setCalibrationLine(prev => [...prev, newPoint]);
    };

    map.on('click', onClick);
    return () => { map.off('click', onClick); };
  }, [isCalibrating, calibrationLine, height, setCalibrationLine]);

  // Update Calibration Line Layer
  const calibrationLayerRef = useRef(null);
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (calibrationLayerRef.current) {
      map.removeLayer(calibrationLayerRef.current);
      calibrationLayerRef.current = null;
    }

    if (calibrationLine.length > 0 && isCalibrating) {
      const layerGroup = L.layerGroup().addTo(map);
      calibrationLayerRef.current = layerGroup;

      const latlngs = calibrationLine.map(pt => [pt.lat, pt.lng]);
      
      if (latlngs.length > 1) {
        L.polyline(latlngs, { color: '#10B981', weight: 4, dashArray: '5, 10' }).addTo(layerGroup);
      }
      
      // Add markers
      calibrationLine.forEach(pt => {
        L.circleMarker([pt.lat, pt.lng], { color: '#10B981', radius: 4, fillOpacity: 1, fillColor: '#FFF' }).addTo(layerGroup);
      });
    }
  }, [calibrationLine, isCalibrating]);

  // Update Image Overlay (Base Aerial Image)
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !rawImageUrl) return;

    const imageUrl = getImageUrl(rawImageUrl);
    const bounds = [[0, 0], [height, width]];

    if (imageOverlayRef.current) {
      map.removeLayer(imageOverlayRef.current);
    }
    
    const overlay = L.imageOverlay(imageUrl, bounds).addTo(map);
    imageOverlayRef.current = overlay;

  }, [rawImageUrl, width, height]);

  // Update Polygon Layers
  useEffect(() => {
    const map = mapInstanceRef.current;
    const layerGroup = layerGroupRef.current;
    if (!map || !layerGroup) return;

    layerGroup.clearLayers();

    if (!results || !results.features) return;

    // Helper to flip [x, y] pixel coords to Leaflet [y, x] (lat, lng in Simple CRS)
    const toLeafletCoords = (pts) => pts.map(pt => [height - pt[1], pt[0]]);

    // 2. Render Open Land Layer
    if (layers.open_land && results.features.open_land) {
      results.features.open_land.forEach(land => {
        const polyCoords = toLeafletCoords(land.polygon);
        L.polygon(polyCoords, {
          color: '#F59E0B',
          fillColor: '#F59E0B',
          fillOpacity: opacity * 0.4,
          weight: 2
        }).bindTooltip(`<div style="white-space: pre-line;"><b>Open Land</b><br/>Area: ${land.formatted_area || land.area_px + ' px²'}</div>`).addTo(layerGroup);
      });
    }

    // 3. Render Vegetation Layer
    if (layers.vegetation && results.features.vegetation) {
      results.features.vegetation.forEach(veg => {
        const polyCoords = toLeafletCoords(veg.polygon);
        L.polygon(polyCoords, {
          color: '#10B981',
          fillColor: '#10B981',
          fillOpacity: opacity * 0.45,
          weight: 2
        }).bindTooltip(`<div style="white-space: pre-line;"><b>Vegetation</b><br/>Area: ${veg.formatted_area || veg.area_px + ' px²'}</div>`).addTo(layerGroup);
      });
    }

    // 4. Render Roads Layer
    if (layers.roads && results.features.roads) {
      results.features.roads.forEach(road => {
        const polyCoords = toLeafletCoords(road.polygon);
        L.polygon(polyCoords, {
          color: '#06B6D4',
          fillColor: '#06B6D4',
          fillOpacity: opacity * 0.5,
          weight: 2
        }).bindTooltip(`<div style="white-space: pre-line;"><b>Road Infrastructure</b><br/>Area: ${road.formatted_area || road.area_px + ' px²'}</div>`).addTo(layerGroup);
      });
    }

    // 5. Render Buildings Layer
    if (layers.buildings && results.features.buildings) {
      results.features.buildings.forEach(bld => {
        const polyCoords = toLeafletCoords(bld.polygon);
        L.polygon(polyCoords, {
          color: '#EF4444',
          fillColor: '#EF4444',
          fillOpacity: opacity * 0.55,
          weight: 2.5
        }).bindTooltip(`
          <div style="font-family: sans-serif; font-size: 12px; white-space: pre-line;">
            <b style="color: #EF4444;">Building Structure</b><br/>
            ID: ${bld.id}<br/>
            Confidence: ${(bld.confidence * 100).toFixed(0)}%<br/>
            Area: ${bld.formatted_area || bld.area_px + ' px²'}
          </div>
        `).addTo(layerGroup);
      });
    }

    // 6. Render AI Proposed Parcels Layer
    if (layers.parcels && results.parcels) {
      results.parcels.forEach(parcel => {
        const polyCoords = toLeafletCoords(parcel.polygon);
        L.polygon(polyCoords, {
          color: '#8B5CF6',
          fillColor: 'transparent',
          weight: 2.5,
          dashArray: '6, 6'
        }).bindTooltip(`
          <div style="font-family: sans-serif; font-size: 12px; white-space: pre-line;">
            <b style="color: #8B5CF6;">Proposed Parcel (${parcel.parcel_id})</b><br/>
            Status: <span style="color: #F59E0B;">Requires Verification</span><br/>
            Area: ${parcel.formatted_area || parcel.area_px + ' px²'}
          </div>
        `).addTo(layerGroup);
      });
    }

  }, [results, layers, opacity, width, height]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', minHeight: '480px' }}>
      <div
        ref={mapContainerRef}
        style={{
          width: '100%',
          height: '100%',
          minHeight: '480px',
          borderRadius: '10px',
          overflow: 'hidden'
        }}
      />
      
      {/* Map Legend */}
      <div style={{
        position: 'absolute',
        bottom: '16px',
        left: '16px',
        zIndex: 1000,
        background: 'rgba(15, 23, 42, 0.85)',
        backdropFilter: 'blur(8px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '8px',
        padding: '8px 12px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        fontSize: '11px',
        color: '#E2E8F0'
      }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#EF4444' }} /> Buildings
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#06B6D4' }} /> Roads
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10B981' }} /> Vegetation
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#8B5CF6' }} /> Proposed Parcels
        </span>
      </div>
    </div>
  );
}
