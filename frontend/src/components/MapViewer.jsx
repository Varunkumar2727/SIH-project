import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getImageUrl } from '../services/api';
import { Crosshair } from 'lucide-react';

export default function MapViewer({ 
  rawImageUrl, 
  imageMeta,
  results, 
  layers, 
  opacity,
  isCalibrating,
  calibrationLine,
  setCalibrationLine,
  gcps = [],
  selectedGcpId,
  setSelectedGcpId,
  isAddingGcp,
  setPendingGcpPoint
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const layerGroupRef = useRef(null);
  const imageOverlayRef = useRef(null);
  const inspectMarkerRef = useRef(null);
  const gcpLayerRef = useRef(null);

  const [inspectedCoord, setInspectedCoord] = useState(null);
  const [hoverCoord, setHoverCoord] = useState(null);

  const width = results?.dimensions?.width || results?.image_dimensions?.width || imageMeta?.width || 800;
  const height = results?.dimensions?.height || results?.image_dimensions?.height || imageMeta?.height || 600;

  // Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

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

    map.fitBounds(bounds);

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [width, height]);

  // Handle Map Interactions (Click for GCP, Calibration, or Coordinate Inspection)
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    const onMapClick = async (e) => {
      // 1. If Adding GCP mode is active: capture pixel and open GCP dialog
      if (isAddingGcp && setPendingGcpPoint) {
        const px = Math.round(e.latlng.lng);
        const py = Math.round(height - e.latlng.lat);
        if (px >= 0 && px <= width && py >= 0 && py <= height) {
          setPendingGcpPoint({ x: px, y: py });
        }
        return;
      }

      // 2. If Calibrating, delegate to calibration line drawing
      if (isCalibrating) {
        if (calibrationLine.length >= 2) return;
        const newPoint = { lat: e.latlng.lat, lng: e.latlng.lng, x: e.latlng.lng, y: height - e.latlng.lat };
        setCalibrationLine(prev => [...prev, newPoint]);
        return;
      }

      // 3. Otherwise, handle coordinate inspection
      const px = Math.round(e.latlng.lng);
      const py = Math.round(height - e.latlng.lat);

      if (px < 0 || px > width || py < 0 || py > height) return;

      // Update map inspection marker
      if (inspectMarkerRef.current) {
        map.removeLayer(inspectMarkerRef.current);
      }
      const marker = L.circleMarker([e.latlng.lat, e.latlng.lng], {
        radius: 6,
        color: '#38BDF8',
        fillColor: '#0284C7',
        fillOpacity: 0.9,
        weight: 2
      }).addTo(map);
      inspectMarkerRef.current = marker;

      // Query coordinate API
      const imgId = imageMeta?.image_id || results?.image_id;
      if (imgId) {
        try {
          const res = await fetch(`/api/coordinates/${imgId}?x=${px}&y=${py}`);
          const data = await res.json();
          setInspectedCoord(data);
        } catch (err) {
          console.error("Failed to fetch coordinates:", err);
        }
      } else {
        setInspectedCoord({
          pixel: { x: px, y: py },
          georeferenced: false,
          coordinates: "Not available"
        });
      }
    };

    const onMouseMove = (e) => {
      const px = Math.round(e.latlng.lng);
      const py = Math.round(height - e.latlng.lat);
      if (px >= 0 && px <= width && py >= 0 && py <= height) {
        setHoverCoord({ x: px, y: py });
      } else {
        setHoverCoord(null);
      }
    };

    map.on('click', onMapClick);
    map.on('mousemove', onMouseMove);

    return () => {
      map.off('click', onMapClick);
      map.off('mousemove', onMouseMove);
    };
  }, [isAddingGcp, isCalibrating, calibrationLine, height, width, imageMeta, results, setPendingGcpPoint, setCalibrationLine]);

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
      
      calibrationLine.forEach(pt => {
        L.circleMarker([pt.lat, pt.lng], { color: '#10B981', radius: 4, fillOpacity: 1, fillColor: '#FFF' }).addTo(layerGroup);
      });
    }
  }, [calibrationLine, isCalibrating]);

  // Update Ground Control Points (GCP) Layer
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (gcpLayerRef.current) {
      map.removeLayer(gcpLayerRef.current);
      gcpLayerRef.current = null;
    }

    if (gcps && gcps.length > 0) {
      const gcpGroup = L.layerGroup().addTo(map);
      gcpLayerRef.current = gcpGroup;

      gcps.forEach(gcp => {
        const lat = height - gcp.image_y;
        const lng = gcp.image_x;
        const isSelected = selectedGcpId === gcp.id;

        // Visual Target Circle Marker
        const marker = L.circleMarker([lat, lng], {
          radius: isSelected ? 8 : 6,
          color: isSelected ? '#F59E0B' : '#06B6D4',
          fillColor: isSelected ? '#F59E0B' : '#0891B2',
          fillOpacity: 0.9,
          weight: isSelected ? 3 : 2
        }).addTo(gcpGroup);

        // Marker label divIcon anchored above
        const labelIcon = L.divIcon({
          className: 'gcp-label-icon',
          html: `<div style="
            background: ${isSelected ? '#F59E0B' : '#0F172A'};
            color: ${isSelected ? '#000' : '#38BDF8'};
            border: 1px solid ${isSelected ? '#FFF' : 'rgba(56, 189, 248, 0.4)'};
            font-size: 10px;
            font-weight: 800;
            padding: 1px 5px;
            border-radius: 4px;
            white-space: nowrap;
            box-shadow: 0 2px 6px rgba(0,0,0,0.5);
            font-family: monospace;
          ">${gcp.name}</div>`,
          iconSize: [44, 16],
          iconAnchor: [22, 22]
        });
        L.marker([lat, lng], { icon: labelIcon, interactive: false }).addTo(gcpGroup);

        marker.bindTooltip(`
          <div style="font-family: monospace; font-size: 11px;">
            <strong style="color: #38BDF8;">${gcp.name}</strong><br/>
            Pixel: (${Math.round(gcp.image_x)}, ${Math.round(gcp.image_y)})<br/>
            World: ${gcp.coordinate_type === 'geographic'
              ? `${gcp.latitude?.toFixed(5)}, ${gcp.longitude?.toFixed(5)}`
              : `${Math.round(gcp.world_x)}, ${Math.round(gcp.world_y)}`}<br/>
            CRS: ${gcp.crs}
          </div>
        `);

        marker.on('click', (ev) => {
          L.DomEvent.stopPropagation(ev);
          if (setSelectedGcpId) setSelectedGcpId(gcp.id);
        });
      });
    }
  }, [gcps, selectedGcpId, height, setSelectedGcpId]);

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

    const toLeafletCoords = (pts) => pts.map(pt => [height - pt[1], pt[0]]);

    // 2. Render Open Land Layer
    if (layers?.open_land && results.features.open_land) {
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
    if (layers?.vegetation && results.features.vegetation) {
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
    if (layers?.roads && results.features.roads) {
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
    if (layers?.buildings && results.features.buildings) {
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
    if (layers?.parcels && results.parcels) {
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
    <div style={{
      position: 'relative',
      width: '100%',
      height: '100%',
      minHeight: '520px',
      cursor: isAddingGcp ? 'crosshair' : 'default'
    }}>
      <div
        ref={mapContainerRef}
        style={{
          width: '100%',
          height: '100%',
          minHeight: '520px',
          borderRadius: '10px',
          overflow: 'hidden'
        }}
      />
      
      {/* Interactive Coordinate Readout Widget */}
      <div style={{
        position: 'absolute',
        top: '16px',
        right: '16px',
        zIndex: 1000,
        background: 'rgba(15, 23, 42, 0.90)',
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(255, 255, 255, 0.12)',
        borderRadius: '10px',
        padding: '12px 16px',
        minWidth: '220px',
        maxWidth: '270px',
        fontSize: '11px',
        color: '#E2E8F0',
        fontFamily: 'var(--font-mono, monospace)',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.55)',
        pointerEvents: 'auto'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '8px',
          paddingBottom: '6px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)'
        }}>
          <span style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontWeight: '800',
            fontSize: '10px',
            letterSpacing: '0.06em',
            color: '#38BDF8',
            textTransform: 'uppercase'
          }}>
            <Crosshair size={13} color="#38BDF8" /> Coordinate Readout
          </span>
          <span style={{ fontSize: '9px', color: '#64748B' }}>Click to inspect</span>
        </div>

        {inspectedCoord ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', lineHeight: '1.5' }}>
            <div>
              <span style={{ color: '#94A3B8' }}>Pixel: </span>
              <strong>X {inspectedCoord.pixel?.x}, Y {inspectedCoord.pixel?.y}</strong>
            </div>

            {inspectedCoord.georeferenced ? (
              <>
                <div>
                  <span style={{ color: '#94A3B8' }}>{inspectedCoord.native?.label_x || 'Easting'}: </span>
                  <strong style={{ color: '#34D399' }}>{inspectedCoord.native?.x?.toLocaleString()}</strong>
                </div>
                <div>
                  <span style={{ color: '#94A3B8' }}>{inspectedCoord.native?.label_y || 'Northing'}: </span>
                  <strong style={{ color: '#34D399' }}>{inspectedCoord.native?.y?.toLocaleString()}</strong>
                </div>
                <div>
                  <span style={{ color: '#94A3B8' }}>Lat: </span>
                  <strong style={{ color: '#38BDF8' }}>{inspectedCoord.wgs84?.lat?.toFixed(6)}</strong>
                </div>
                <div>
                  <span style={{ color: '#94A3B8' }}>Lon: </span>
                  <strong style={{ color: '#38BDF8' }}>{inspectedCoord.wgs84?.lon?.toFixed(6)}</strong>
                </div>
                {inspectedCoord.method === 'gcp' && (
                  <div style={{ fontSize: '10px', color: '#06B6D4' }}>
                    Source: GCP Affine {inspectedCoord.rmse ? `(RMSE: ${inspectedCoord.rmse.toFixed(2)}m)` : ''}
                  </div>
                )}
              </>
            ) : (
              <div>
                <span style={{ color: '#94A3B8' }}>Coordinates: </span>
                <strong style={{ color: '#F59E0B' }}>Not available</strong>
              </div>
            )}
          </div>
        ) : hoverCoord ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', lineHeight: '1.5' }}>
            <div>
              <span style={{ color: '#94A3B8' }}>Cursor Pixel: </span>
              <strong>X {hoverCoord.x}, Y {hoverCoord.y}</strong>
            </div>
            <div style={{ fontSize: '10px', color: '#64748B', fontStyle: 'italic' }}>
              Click point to calculate world coordinates
            </div>
          </div>
        ) : (
          <div style={{ fontSize: '10.5px', color: '#64748B', fontStyle: 'italic', lineHeight: '1.4' }}>
            Click anywhere on map to inspect coordinates
          </div>
        )}
      </div>

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
        color: '#E2E8F0',
        flexWrap: 'wrap'
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
        {gcps.length > 0 && (
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#38BDF8', border: '1px solid #FFF' }} /> Control Points ({gcps.length})
          </span>
        )}
      </div>
    </div>
  );
}
