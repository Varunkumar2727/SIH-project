import React, { useState } from 'react';
import { Ruler, AlertTriangle, Compass, Monitor, PenTool } from 'lucide-react';
import axios from 'axios';

export default function MeasurementControl({ 
  measurementMode, 
  setMeasurementMode, 
  imageId, 
  calibrationData, 
  setCalibrationData,
  isCalibrating,
  setIsCalibrating,
  calibrationLine,
  setCalibrationLine,
  refreshResults
}) {
  const [realDistance, setRealDistance] = useState('');
  const [unit, setUnit] = useState('meters');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleCalibrate = async () => {
    if (!calibrationLine || calibrationLine.length !== 2) return;
    if (!realDistance) return;

    // Calculate pixel distance (Simple Euclidean distance since we're using simple CRS)
    const [p1, p2] = calibrationLine;
    const pxDist = Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2));

    setIsSubmitting(true);
    try {
      const response = await axios.post(`/api/calibrate/${imageId}`, {
        pixel_distance: pxDist,
        real_distance: parseFloat(realDistance),
        unit: unit
      });
      setCalibrationData(response.data.calibration);
      setIsCalibrating(false);
      setCalibrationLine([]);
      setRealDistance('');
      // Reload results to format areas correctly
      if (refreshResults) refreshResults('calibrated');
    } catch (error) {
      console.error("Calibration failed", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const cancelCalibration = () => {
    setIsCalibrating(false);
    setCalibrationLine([]);
    setRealDistance('');
  };

  return (
    <div className="glass-panel" style={{ padding: '20px', marginBottom: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
        <div style={{ background: 'rgba(59, 130, 246, 0.15)', padding: '6px', borderRadius: '8px', color: '#3B82F6' }}>
          <Ruler size={16} />
        </div>
        <h4 style={{ fontSize: '15px', fontWeight: '800', color: '#F8FAFC' }}>
          Measurement Mode
        </h4>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '20px' }}>
        {/* Pixels */}
        <label style={{
          display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer',
          padding: '10px 14px', borderRadius: '10px',
          background: measurementMode === 'pixels' ? 'rgba(30, 41, 59, 0.75)' : 'transparent',
          border: `1px solid ${measurementMode === 'pixels' ? 'rgba(59, 130, 246, 0.4)' : 'rgba(255,255,255,0.05)'}`
        }}>
          <input 
            type="radio" 
            name="measurement_mode" 
            checked={measurementMode === 'pixels'} 
            onChange={() => { setMeasurementMode('pixels'); refreshResults('pixels'); }}
            style={{ accentColor: '#3B82F6' }}
          />
          <Monitor size={15} color={measurementMode === 'pixels' ? '#3B82F6' : '#94A3B8'} />
          <span style={{ fontSize: '13px', color: measurementMode === 'pixels' ? '#FFF' : '#94A3B8' }}>Pixels (Default)</span>
        </label>

        {/* Calibrated Scale */}
        <label style={{
          display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer',
          padding: '10px 14px', borderRadius: '10px',
          background: measurementMode === 'calibrated' ? 'rgba(30, 41, 59, 0.75)' : 'transparent',
          border: `1px solid ${measurementMode === 'calibrated' ? 'rgba(16, 185, 129, 0.4)' : 'rgba(255,255,255,0.05)'}`
        }}>
          <input 
            type="radio" 
            name="measurement_mode" 
            checked={measurementMode === 'calibrated'} 
            onChange={() => { setMeasurementMode('calibrated'); refreshResults('calibrated'); }}
            style={{ accentColor: '#10B981' }}
          />
          <PenTool size={15} color={measurementMode === 'calibrated' ? '#10B981' : '#94A3B8'} />
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '13px', color: measurementMode === 'calibrated' ? '#FFF' : '#94A3B8' }}>Calibrated Scale</span>
            {calibrationData && (
              <span style={{ fontSize: '11px', color: '#10B981' }}>Active: {calibrationData.meters_per_pixel.toFixed(4)} m/px</span>
            )}
          </div>
        </label>

        {/* Geographic */}
        <label style={{
          display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer',
          padding: '10px 14px', borderRadius: '10px',
          background: measurementMode === 'geographic' ? 'rgba(30, 41, 59, 0.75)' : 'transparent',
          border: `1px solid ${measurementMode === 'geographic' ? 'rgba(245, 158, 11, 0.4)' : 'rgba(255,255,255,0.05)'}`
        }}>
          <input 
            type="radio" 
            name="measurement_mode" 
            checked={measurementMode === 'geographic'} 
            onChange={() => { setMeasurementMode('geographic'); refreshResults('geographic'); }}
            style={{ accentColor: '#F59E0B' }}
          />
          <Compass size={15} color={measurementMode === 'geographic' ? '#F59E0B' : '#94A3B8'} />
          <span style={{ fontSize: '13px', color: measurementMode === 'geographic' ? '#FFF' : '#94A3B8' }}>Geographic (GeoTIFF)</span>
        </label>
      </div>

      {measurementMode === 'calibrated' && !isCalibrating && (
        <button 
          onClick={() => setIsCalibrating(true)}
          className="btn-secondary"
          style={{ width: '100%', justifyContent: 'center', marginBottom: '16px' }}
        >
          <Ruler size={14} /> Calibrate Image
        </button>
      )}

      {isCalibrating && (
        <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: '12px', borderRadius: '10px', border: '1px solid rgba(16, 185, 129, 0.3)', marginBottom: '16px' }}>
          <h5 style={{ color: '#10B981', fontSize: '12.5px', marginBottom: '8px' }}>Calibration Mode</h5>
          
          {calibrationLine.length < 2 ? (
            <p style={{ fontSize: '11.5px', color: '#94A3B8', marginBottom: '8px' }}>
              Click two points on the map to draw a reference line.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <p style={{ fontSize: '11.5px', color: '#34D399' }}>Line drawn! Enter actual distance:</p>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input 
                  type="number" 
                  value={realDistance}
                  onChange={(e) => setRealDistance(e.target.value)}
                  placeholder="e.g. 100"
                  style={{ flex: 1, background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: '#FFF', padding: '6px 10px', borderRadius: '6px', fontSize: '12px' }}
                />
                <select 
                  value={unit} 
                  onChange={(e) => setUnit(e.target.value)}
                  style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: '#FFF', padding: '6px', borderRadius: '6px', fontSize: '12px' }}
                >
                  <option value="meters">meters</option>
                  <option value="feet">feet</option>
                  <option value="kilometers">km</option>
                </select>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button onClick={handleCalibrate} disabled={isSubmitting || !realDistance} className="btn-primary" style={{ flex: 1, padding: '8px', fontSize: '12px', justifyContent: 'center' }}>
                  Save Calibration
                </button>
                <button onClick={cancelCalibration} className="btn-secondary" style={{ padding: '8px', fontSize: '12px' }}>
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Accuracy Warning */}
      <div style={{
        padding: '12px',
        background: 'rgba(245, 158, 11, 0.1)',
        border: '1px dashed rgba(245, 158, 11, 0.4)',
        borderRadius: '8px',
        display: 'flex',
        gap: '8px',
        alignItems: 'flex-start'
      }}>
        <AlertTriangle size={14} color="#F59E0B" style={{ flexShrink: 0, marginTop: '2px' }} />
        <p style={{ fontSize: '10.5px', color: '#FCD34D', lineHeight: '1.4' }}>
          <strong>⚠ Accuracy Warning:</strong> Calibrated measurement is an estimate. Accuracy depends on image quality, perspective, reference-distance accuracy and image distortion. For official cadastral measurements, use properly georeferenced survey data.
        </p>
      </div>

    </div>
  );
}
