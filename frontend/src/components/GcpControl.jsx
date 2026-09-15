import React, { useState } from 'react';
import { 
  Crosshair, 
  MapPin, 
  Plus, 
  Trash2, 
  Calculator, 
  CheckCircle2, 
  AlertTriangle, 
  RotateCcw,
  Check
} from 'lucide-react';
import axios from 'axios';

export default function GcpControl({
  imageId,
  imageMeta,
  gcps = [],
  setGcps,
  gcpTransformation,
  setGcpTransformation,
  isAddingGcp,
  setIsAddingGcp,
  pendingGcpPoint,
  setPendingGcpPoint,
  activeGeoref,
  setActiveGeoref,
  selectedGcpId,
  setSelectedGcpId,
  onRefreshResults
}) {
  // GCP Form Dialog State
  const [editingGcp, setEditingGcp] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    coordinate_type: 'projected',
    world_x: '',
    world_y: '',
    latitude: '',
    longitude: '',
    elevation: '',
    crs: imageMeta?.crs && !imageMeta.crs.includes('not georeferenced') ? imageMeta.crs : 'EPSG:32643',
    source: 'Field Survey',
    description: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // When a pending point is selected by clicking on map, open form
  React.useEffect(() => {
    if (pendingGcpPoint) {
      const nextIndex = gcps.length + 1;
      setFormData({
        name: `GCP-${nextIndex < 10 ? '0' : ''}${nextIndex}`,
        coordinate_type: 'projected',
        world_x: '',
        world_y: '',
        latitude: '',
        longitude: '',
        elevation: '',
        crs: imageMeta?.crs && !imageMeta.crs.includes('not georeferenced') ? imageMeta.crs : 'EPSG:32643',
        source: 'Field Survey',
        description: ''
      });
      setErrorMsg(null);
    }
  }, [pendingGcpPoint, gcps.length, imageMeta]);

  const handleSaveGcp = async (e) => {
    e.preventDefault();
    if (!imageId) return;

    const imgX = pendingGcpPoint ? pendingGcpPoint.x : editingGcp?.image_x;
    const imgY = pendingGcpPoint ? pendingGcpPoint.y : editingGcp?.image_y;

    if (imgX === undefined || imgY === undefined) {
      setErrorMsg("Image position is required.");
      return;
    }

    const payload = {
      id: editingGcp?.id,
      name: formData.name || `GCP-${gcps.length + 1}`,
      image_x: imgX,
      image_y: imgY,
      coordinate_type: formData.coordinate_type,
      crs: formData.crs || 'EPSG:32643',
      description: formData.description || '',
      source: formData.source || 'Field Survey',
      elevation: formData.elevation ? parseFloat(formData.elevation) : null
    };

    if (formData.coordinate_type === 'geographic') {
      if (!formData.latitude || !formData.longitude) {
        setErrorMsg("Latitude and longitude are required for geographic GCP.");
        return;
      }
      payload.latitude = parseFloat(formData.latitude);
      payload.longitude = parseFloat(formData.longitude);
      payload.world_x = payload.longitude;
      payload.world_y = payload.latitude;
    } else {
      if (!formData.world_x || !formData.world_y) {
        setErrorMsg("Easting (X) and Northing (Y) are required for projected GCP.");
        return;
      }
      payload.world_x = parseFloat(formData.world_x);
      payload.world_y = parseFloat(formData.world_y);
    }

    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const res = await axios.post(`/api/gcps/${imageId}`, payload);
      const savedGcp = res.data.gcp;

      setGcps(prev => {
        const existingIdx = prev.findIndex(g => g.id === savedGcp.id);
        if (existingIdx >= 0) {
          const updated = [...prev];
          updated[existingIdx] = savedGcp;
          return updated;
        }
        return [...prev, savedGcp];
      });

      // Clear dialog
      setPendingGcpPoint(null);
      setEditingGcp(null);
      setIsAddingGcp(false);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message;
      setErrorMsg(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteGcp = async (gcpId) => {
    if (!imageId) return;
    try {
      await axios.delete(`/api/gcps/${imageId}/${gcpId}`);
      setGcps(prev => prev.filter(g => g.id !== gcpId));
      if (selectedGcpId === gcpId) setSelectedGcpId(null);

      // If dropped below 3, reset transformation
      if (gcps.length - 1 < 3) {
        setGcpTransformation(null);
        if (activeGeoref === 'gcp') {
          setActiveGeoref(null);
          if (onRefreshResults) onRefreshResults();
        }
      }
    } catch (err) {
      console.error("Failed to delete GCP:", err);
    }
  };

  const handleCalculateTransform = async () => {
    if (!imageId || gcps.length < 3) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const res = await axios.post(`/api/gcps/${imageId}/calculate`, {
        target_crs: imageMeta?.crs && !imageMeta.crs.includes('not georeferenced') ? imageMeta.crs : undefined
      });
      setGcpTransformation(res.data);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message;
      setErrorMsg(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApplyGcpGeoref = async () => {
    if (!imageId || !gcpTransformation) return;
    setIsSubmitting(true);
    try {
      await axios.post(`/api/gcps/${imageId}/apply`);
      setActiveGeoref('gcp');
      if (onRefreshResults) onRefreshResults('geographic');
    } catch (err) {
      console.error("Failed to apply GCP georeferencing:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetGeoref = async () => {
    if (!imageId) return;
    setIsSubmitting(true);
    try {
      await axios.post(`/api/gcps/${imageId}/reset`);
      setActiveGeoref(imageMeta?.is_georeferenced ? 'geotiff' : 'pixels');
      if (onRefreshResults) onRefreshResults(imageMeta?.is_georeferenced ? 'geographic' : 'pixels');
    } catch (err) {
      console.error("Failed to reset georeferencing:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const count = gcps.length;
  let statusBadge = {
    text: `GCPs: ${count} / 3 min`,
    subtext: 'Not enough control points',
    color: '#F59E0B',
    bg: 'rgba(245, 158, 11, 0.15)',
    border: 'rgba(245, 158, 11, 0.3)'
  };
  if (count === 3) {
    statusBadge = {
      text: `GCPs: 3`,
      subtext: 'Minimum points available',
      color: '#38BDF8',
      bg: 'rgba(56, 189, 248, 0.15)',
      border: 'rgba(56, 189, 248, 0.3)'
    };
  } else if (count >= 4) {
    statusBadge = {
      text: `GCPs: ${count}`,
      subtext: 'Ready for georeferencing',
      color: '#10B981',
      bg: 'rgba(16, 185, 129, 0.15)',
      border: 'rgba(16, 185, 129, 0.3)'
    };
  }

  const isFormOpen = Boolean(pendingGcpPoint || editingGcp);

  return (
    <div className="glass-panel" style={{ padding: '20px', marginBottom: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ background: 'rgba(6, 182, 212, 0.15)', padding: '6px', borderRadius: '8px', color: '#06B6D4' }}>
            <Crosshair size={16} />
          </div>
          <div>
            <h4 style={{ fontSize: '14px', fontWeight: '800', color: '#F8FAFC' }}>
              Survey Control Points (GCP)
            </h4>
            <span style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>
              2D Affine Georeferencing
            </span>
          </div>
        </div>

        {/* Count Status Badge */}
        <span style={{
          fontSize: '10px',
          fontWeight: '700',
          color: statusBadge.color,
          background: statusBadge.bg,
          border: `1px solid ${statusBadge.border}`,
          padding: '3px 8px',
          borderRadius: '6px'
        }}>
          {statusBadge.text}
        </span>
      </div>

      {/* Subtext Status */}
      <div style={{ fontSize: '11px', color: statusBadge.color, marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
        {count >= 3 ? <CheckCircle2 size={13} /> : <AlertTriangle size={13} />}
        <span>{statusBadge.subtext}</span>
      </div>

      {/* Active Georeferencing Status Callout */}
      {activeGeoref === 'gcp' ? (
        <div style={{
          padding: '10px 12px',
          background: 'rgba(16, 185, 129, 0.12)',
          border: '1px solid rgba(16, 185, 129, 0.35)',
          borderRadius: '8px',
          marginBottom: '14px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div>
            <div style={{ fontSize: '11px', fontWeight: '700', color: '#34D399', display: 'flex', alignItems: 'center', gap: '5px' }}>
              <Check size={13} /> Active: GCP Affine Transformation
            </div>
            <div style={{ fontSize: '10px', color: '#94A3B8' }}>
              RMSE: {gcpTransformation?.rmse ? `${gcpTransformation.rmse.toFixed(3)} m` : 'Calculated'} | CRS: {gcpTransformation?.crs}
            </div>
          </div>
          <button
            onClick={handleResetGeoref}
            className="btn-secondary"
            style={{ padding: '4px 8px', fontSize: '10.5px' }}
            title="Reset to native GeoTIFF or manual calibration"
          >
            <RotateCcw size={12} /> Reset
          </button>
        </div>
      ) : (
        <div style={{
          padding: '8px 12px',
          background: 'rgba(0, 0, 0, 0.25)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          borderRadius: '8px',
          marginBottom: '14px',
          fontSize: '11px',
          color: '#94A3B8'
        }}>
          Current Georef: <strong style={{ color: '#F1F5F9' }}>
            {imageMeta?.is_georeferenced ? 'GeoTIFF Native CRS' : 'Manual Calibration / Pixel'}
          </strong>
        </div>
      )}

      {/* Action Toolbar */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        <button
          onClick={() => {
            setIsAddingGcp(!isAddingGcp);
            setPendingGcpPoint(null);
            setEditingGcp(null);
          }}
          className={isAddingGcp ? "btn-primary" : "btn-secondary"}
          style={{ flex: 1, justifyContent: 'center', padding: '8px 12px', fontSize: '12px' }}
        >
          <Plus size={14} />
          {isAddingGcp ? 'Click Map Point...' : 'Add GCP'}
        </button>

        <button
          onClick={handleCalculateTransform}
          disabled={count < 3 || isSubmitting}
          className="btn-primary"
          style={{
            flex: 1,
            justifyContent: 'center',
            padding: '8px 12px',
            fontSize: '12px',
            opacity: count < 3 ? 0.45 : 1,
            cursor: count < 3 ? 'not-allowed' : 'pointer'
          }}
        >
          <Calculator size={14} /> Calculate
        </button>
      </div>

      {/* Guide Banner when user is in Add GCP mode */}
      {isAddingGcp && !pendingGcpPoint && (
        <div style={{
          padding: '10px 14px',
          background: 'rgba(6, 182, 212, 0.15)',
          border: '1px dashed rgba(6, 182, 212, 0.4)',
          borderRadius: '8px',
          marginBottom: '14px',
          fontSize: '11px',
          color: '#67E8F9',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <MapPin size={14} />
          <span>Click on the aerial map to pinpoint the Ground Control Point location.</span>
        </div>
      )}

      {/* Add / Edit GCP Form Dialog */}
      {isFormOpen && (
        <div style={{
          background: 'rgba(15, 23, 42, 0.95)',
          border: '1px solid rgba(6, 182, 212, 0.4)',
          borderRadius: '10px',
          padding: '14px',
          marginBottom: '16px',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span style={{ fontSize: '12px', fontWeight: '800', color: '#38BDF8' }}>
              {editingGcp ? `Edit ${editingGcp.name}` : `New Survey Point: ${formData.name}`}
            </span>
            <span style={{ fontSize: '10px', color: '#94A3B8', fontFamily: 'monospace' }}>
              Pixel: ({pendingGcpPoint?.x ?? editingGcp?.image_x}, {pendingGcpPoint?.y ?? editingGcp?.image_y})
            </span>
          </div>

          {errorMsg && (
            <div style={{ padding: '6px 10px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '6px', color: '#FCA5A5', fontSize: '11px', marginBottom: '10px' }}>
              {errorMsg}
            </div>
          )}

          <form onSubmit={handleSaveGcp} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {/* Coordinate Format Switcher */}
            <div style={{ display: 'flex', gap: '6px', marginBottom: '4px' }}>
              <button
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, coordinate_type: 'projected' }))}
                style={{
                  flex: 1,
                  padding: '5px',
                  borderRadius: '6px',
                  fontSize: '11px',
                  fontWeight: '600',
                  border: 'none',
                  background: formData.coordinate_type === 'projected' ? 'rgba(6, 182, 212, 0.25)' : 'rgba(255,255,255,0.05)',
                  color: formData.coordinate_type === 'projected' ? '#38BDF8' : '#94A3B8',
                  cursor: 'pointer'
                }}
              >
                Projected (Easting/Northing)
              </button>
              <button
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, coordinate_type: 'geographic', crs: 'EPSG:4326' }))}
                style={{
                  flex: 1,
                  padding: '5px',
                  borderRadius: '6px',
                  fontSize: '11px',
                  fontWeight: '600',
                  border: 'none',
                  background: formData.coordinate_type === 'geographic' ? 'rgba(6, 182, 212, 0.25)' : 'rgba(255,255,255,0.05)',
                  color: formData.coordinate_type === 'geographic' ? '#38BDF8' : '#94A3B8',
                  cursor: 'pointer'
                }}
              >
                Geographic (Lat/Lon)
              </button>
            </div>

            {/* Coordinate Inputs */}
            {formData.coordinate_type === 'projected' ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <div>
                  <label style={{ fontSize: '10px', color: '#94A3B8', display: 'block', marginBottom: '2px' }}>Easting (X, meters)</label>
                  <input
                    type="number"
                    step="any"
                    required
                    placeholder="e.g. 500120.45"
                    value={formData.world_x}
                    onChange={(e) => setFormData(prev => ({ ...prev, world_x: e.target.value }))}
                    style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: '#FFF', padding: '6px 8px', borderRadius: '6px', fontSize: '11px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '10px', color: '#94A3B8', display: 'block', marginBottom: '2px' }}>Northing (Y, meters)</label>
                  <input
                    type="number"
                    step="any"
                    required
                    placeholder="e.g. 1450320.10"
                    value={formData.world_y}
                    onChange={(e) => setFormData(prev => ({ ...prev, world_y: e.target.value }))}
                    style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: '#FFF', padding: '6px 8px', borderRadius: '6px', fontSize: '11px' }}
                  />
                </div>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <div>
                  <label style={{ fontSize: '10px', color: '#94A3B8', display: 'block', marginBottom: '2px' }}>Latitude (°N)</label>
                  <input
                    type="number"
                    step="any"
                    required
                    placeholder="e.g. 13.123456"
                    value={formData.latitude}
                    onChange={(e) => setFormData(prev => ({ ...prev, latitude: e.target.value }))}
                    style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: '#FFF', padding: '6px 8px', borderRadius: '6px', fontSize: '11px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '10px', color: '#94A3B8', display: 'block', marginBottom: '2px' }}>Longitude (°E)</label>
                  <input
                    type="number"
                    step="any"
                    required
                    placeholder="e.g. 77.123456"
                    value={formData.longitude}
                    onChange={(e) => setFormData(prev => ({ ...prev, longitude: e.target.value }))}
                    style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: '#FFF', padding: '6px 8px', borderRadius: '6px', fontSize: '11px' }}
                  />
                </div>
              </div>
            )}

            {/* CRS and Elevation */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ fontSize: '10px', color: '#94A3B8', display: 'block', marginBottom: '2px' }}>CRS</label>
                <input
                  type="text"
                  required
                  value={formData.crs}
                  onChange={(e) => setFormData(prev => ({ ...prev, crs: e.target.value }))}
                  placeholder="e.g. EPSG:32643"
                  style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: '#FFF', padding: '6px 8px', borderRadius: '6px', fontSize: '11px' }}
                />
              </div>
              <div>
                <label style={{ fontSize: '10px', color: '#94A3B8', display: 'block', marginBottom: '2px' }}>Elevation (m)</label>
                <input
                  type="number"
                  step="any"
                  placeholder="Optional"
                  value={formData.elevation}
                  onChange={(e) => setFormData(prev => ({ ...prev, elevation: e.target.value }))}
                  style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: '#FFF', padding: '6px 8px', borderRadius: '6px', fontSize: '11px' }}
                />
              </div>
            </div>

            {/* Buttons */}
            <div style={{ display: 'flex', gap: '8px', marginTop: '6px' }}>
              <button
                type="submit"
                disabled={isSubmitting}
                className="btn-primary"
                style={{ flex: 1, padding: '7px', fontSize: '11.5px', justifyContent: 'center' }}
              >
                Save Control Point
              </button>
              <button
                type="button"
                onClick={() => {
                  setPendingGcpPoint(null);
                  setEditingGcp(null);
                  setIsAddingGcp(false);
                }}
                className="btn-secondary"
                style={{ padding: '7px 12px', fontSize: '11.5px' }}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Transformation Quality & Error Statistics Panel */}
      {gcpTransformation && (
        <div style={{
          background: 'rgba(15, 23, 42, 0.85)',
          border: '1px solid rgba(6, 182, 212, 0.3)',
          borderRadius: '10px',
          padding: '12px 14px',
          marginBottom: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', fontWeight: '800', color: '#38BDF8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Survey Control Quality
            </span>
            <span style={{
              fontSize: '10px',
              fontWeight: '700',
              color: gcpTransformation.rmse <= 1.0 ? '#10B981' : '#F59E0B',
              background: gcpTransformation.rmse <= 1.0 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
              padding: '2px 6px',
              borderRadius: '4px'
            }}>
              RMSE: {gcpTransformation.rmse?.toFixed(3)} m
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', fontSize: '10.5px', fontFamily: 'monospace' }}>
            <div>
              <span style={{ color: '#94A3B8', display: 'block', fontSize: '9.5px' }}>Model</span>
              <strong>2D Affine</strong>
            </div>
            <div>
              <span style={{ color: '#94A3B8', display: 'block', fontSize: '9.5px' }}>Max Error</span>
              <strong>{gcpTransformation.max_error?.toFixed(3)} m</strong>
            </div>
            <div>
              <span style={{ color: '#94A3B8', display: 'block', fontSize: '9.5px' }}>Points</span>
              <strong>{gcpTransformation.gcp_count} GCPs</strong>
            </div>
          </div>

          {/* Spatial Distribution Status */}
          <div style={{
            fontSize: '10.5px',
            color: gcpTransformation.distribution?.is_clustered ? '#F59E0B' : '#34D399',
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            background: 'rgba(0,0,0,0.2)',
            padding: '6px 8px',
            borderRadius: '6px'
          }}>
            {gcpTransformation.distribution?.is_clustered ? (
              <AlertTriangle size={13} color="#F59E0B" />
            ) : (
              <CheckCircle2 size={13} color="#34D399" />
            )}
            <span>{gcpTransformation.distribution?.message}</span>
          </div>

          {/* High Error Warning */}
          {gcpTransformation.rmse > 2.0 && (
            <div style={{ fontSize: '10.5px', color: '#F87171', background: 'rgba(239, 68, 68, 0.1)', padding: '6px 8px', borderRadius: '6px' }}>
              ⚠ High transformation error. Check GCP survey coordinates and image placements.
            </div>
          )}

          {/* Apply GCP Georeferencing Button */}
          {activeGeoref !== 'gcp' && (
            <button
              onClick={handleApplyGcpGeoref}
              className="btn-primary"
              style={{
                width: '100%',
                justifyContent: 'center',
                padding: '8px',
                fontSize: '11.5px',
                marginTop: '4px'
              }}
            >
              <Check size={14} /> Apply GCP Georeferencing
            </button>
          )}
        </div>
      )}

      {/* GCP Management Table */}
      {gcps.length > 0 ? (
        <div style={{ overflowX: 'auto' }}>
          <table style={{
            width: '100%',
            fontSize: '10.5px',
            borderCollapse: 'collapse',
            textAlign: 'left',
            fontFamily: 'monospace'
          }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#94A3B8' }}>
                <th style={{ padding: '6px 4px' }}>Name</th>
                <th style={{ padding: '6px 4px' }}>Pixel (X, Y)</th>
                <th style={{ padding: '6px 4px' }}>World Coords</th>
                <th style={{ padding: '6px 4px' }}>Error</th>
                <th style={{ padding: '6px 4px', textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {gcps.map((gcp) => {
                const residual = gcpTransformation?.residuals?.[gcp.id];
                const isSelected = selectedGcpId === gcp.id;
                return (
                  <tr
                    key={gcp.id}
                    onClick={() => setSelectedGcpId(isSelected ? null : gcp.id)}
                    style={{
                      borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                      cursor: 'pointer',
                      background: isSelected ? 'rgba(6, 182, 212, 0.18)' : 'transparent',
                      transition: 'background 0.15s ease'
                    }}
                  >
                    <td style={{ padding: '6px 4px', fontWeight: '700', color: '#38BDF8' }}>
                      {gcp.name}
                    </td>
                    <td style={{ padding: '6px 4px', color: '#CBD5E1' }}>
                      {Math.round(gcp.image_x)}, {Math.round(gcp.image_y)}
                    </td>
                    <td style={{ padding: '6px 4px', color: '#CBD5E1' }}>
                      {gcp.coordinate_type === 'geographic'
                        ? `${gcp.latitude?.toFixed(4)}, ${gcp.longitude?.toFixed(4)}`
                        : `${Math.round(gcp.world_x)}, ${Math.round(gcp.world_y)}`}
                    </td>
                    <td style={{ padding: '6px 4px', color: residual !== undefined ? (residual <= 1.0 ? '#34D399' : '#F59E0B') : '#64748B' }}>
                      {residual !== undefined ? `${residual.toFixed(2)}m` : '—'}
                    </td>
                    <td style={{ padding: '6px 4px', textAlign: 'right' }}>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteGcp(gcp.id);
                        }}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: '#EF4444',
                          cursor: 'pointer',
                          padding: '2px 4px'
                        }}
                        title="Delete GCP"
                      >
                        <Trash2 size={13} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div style={{
          padding: '16px',
          textAlign: 'center',
          color: '#64748B',
          fontSize: '11px',
          background: 'rgba(0,0,0,0.15)',
          borderRadius: '8px'
        }}>
          No Ground Control Points added yet. Click <strong>Add GCP</strong> and pinpoint control locations on the aerial map.
        </div>
      )}
    </div>
  );
}
