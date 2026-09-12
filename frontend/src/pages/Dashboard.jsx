import React, { useState } from 'react';
import Header from '../components/Header';
import ImageUpload from '../components/ImageUpload';
import StatsCards from '../components/StatsCards';
import LayerControl from '../components/LayerControl';
import MeasurementControl from '../components/MeasurementControl';
import MapViewer from '../components/MapViewer';
import BeforeAfterSlider from '../components/BeforeAfterSlider';
import GeoJsonExport from '../components/GeoJsonExport';
import { Map, SlidersHorizontal, CheckCircle2, ShieldAlert, Cpu } from 'lucide-react';

export default function Dashboard() {
  const [imageMeta, setImageMeta] = useState(null);
  const [results, setResults] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState('map');
  
  // Measurement States
  const [measurementMode, setMeasurementMode] = useState('pixels');
  const [calibrationData, setCalibrationData] = useState(null);
  const [isCalibrating, setIsCalibrating] = useState(false);
  const [calibrationLine, setCalibrationLine] = useState([]);

  const [layers, setLayers] = useState({
    buildings: true,
    roads: true,
    vegetation: true,
    open_land: true,
    parcels: true,
  });
  const [opacity, setOpacity] = useState(0.75);

  const handleUploadSuccess = (meta) => {
    setImageMeta(meta);
    setResults(null);
  };

  const handleAnalysisComplete = (res, meta) => {
    setResults(res);
    setImageMeta(meta);
    if (res.calibration) {
      setCalibrationData(res.calibration);
    }
  };

  const fetchResults = async (mode = measurementMode) => {
    if (!imageMeta?.image_id) return;
    try {
      const response = await fetch(`/api/results/${imageMeta.image_id}?measurement_mode=${mode}`);
      const data = await response.json();
      setResults(data);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div
  className="geo-dashboard"
  style={{
    maxWidth: '1480px',
    margin: '0 auto',
    padding: '24px 20px',
    minHeight: '100vh',
    position: 'relative'
  }}
>
      {/* Top Navigation Header */}
      <Header detectionMode={results?.detection_mode || 'Prototype Computer Vision'} />

      {/* Main Grid Layout */}
      <div
  className="geo-dashboard-layout animate-fade-in-up"
  style={{
    display: 'grid',
    gridTemplateColumns: 'minmax(340px, 390px) 1fr',
    gap: '24px',
    alignItems: 'start'
  }}
>
        
        {/* LEFT CONTROL PANEL */}
        <div className="animate-fade-in-up stagger-1" style={{ display: 'flex', flexDirection: 'column' }}>
          <ImageUpload
            onUploadSuccess={handleUploadSuccess}
            onAnalysisComplete={handleAnalysisComplete}
            isProcessing={isProcessing}
            setIsProcessing={setIsProcessing}
          />

          <StatsCards
            stats={results?.stats}
            meta={imageMeta}
          />

          {results && (
            <MeasurementControl
              measurementMode={measurementMode}
              setMeasurementMode={setMeasurementMode}
              imageId={imageMeta?.image_id}
              calibrationData={calibrationData}
              setCalibrationData={setCalibrationData}
              isCalibrating={isCalibrating}
              setIsCalibrating={setIsCalibrating}
              calibrationLine={calibrationLine}
              setCalibrationLine={setCalibrationLine}
              refreshResults={fetchResults}
            />
          )}

          {results && (
            <LayerControl
              layers={layers}
              setLayers={setLayers}
              opacity={opacity}
              setOpacity={setOpacity}
            />
          )}

          <GeoJsonExport
            imageId={imageMeta?.image_id}
            overlayUrl={results?.overlay_url}
          />
        </div>

        {/* RIGHT / MAIN MAP & VISUALIZATION PANEL */}
        <div className="glass-panel animate-fade-in-up stagger-2" style={{ padding: '24px', display: 'flex', flexDirection: 'column', minHeight: '720px' }}>
          
          {/* Main Visualizer Header & Navigation Tabs */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '14px' }}>
            
            {/* View Mode Tabs */}
            <div style={{
              display: 'flex',
              gap: '6px',
              background: 'rgba(15, 23, 42, 0.75)',
              padding: '5px',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <button
                onClick={() => setActiveTab('map')}
                style={{
                  background: activeTab === 'map' ? 'linear-gradient(135deg, #06B6D4, #2563EB)' : 'transparent',
                  color: activeTab === 'map' ? '#FFF' : '#94A3B8',
                  border: 'none',
                  padding: '8px 18px',
                  borderRadius: '8px',
                  fontSize: '12.5px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  boxShadow: activeTab === 'map' ? '0 4px 14px rgba(6, 182, 212, 0.35)' : 'none',
                  transition: 'all 0.2s ease'
                }}
              >
                <Map size={15} /> Interactive Map View
              </button>

              <button
                onClick={() => setActiveTab('comparison')}
                disabled={!results}
                style={{
                  background: activeTab === 'comparison' ? 'linear-gradient(135deg, #06B6D4, #8B5CF6)' : 'transparent',
                  color: activeTab === 'comparison' ? '#FFF' : '#94A3B8',
                  border: 'none',
                  padding: '8px 18px',
                  borderRadius: '8px',
                  fontSize: '12.5px',
                  fontWeight: '700',
                  cursor: results ? 'pointer' : 'not-allowed',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  opacity: results ? 1 : 0.45,
                  boxShadow: activeTab === 'comparison' ? '0 4px 14px rgba(139, 92, 246, 0.35)' : 'none',
                  transition: 'all 0.2s ease'
                }}
              >
                <SlidersHorizontal size={15} /> Before / After Split Comparison
              </button>
            </div>

            {results && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                color: '#34D399',
                fontSize: '13px',
                fontWeight: '700',
                background: 'rgba(16, 185, 129, 0.1)',
                padding: '6px 14px',
                borderRadius: '20px',
                border: '1px solid rgba(16, 185, 129, 0.3)'
              }}>
                <CheckCircle2 size={16} color="#10B981" />
                Analysis Complete
              </div>
            )}
          </div>

          {/* Main Visualizer Canvas */}
          <div style={{ flex: 1, position: 'relative', display: 'flex', flexDirection: 'column' }}>
            {activeTab === 'map' ? (
              <MapViewer
                rawImageUrl={imageMeta?.url}
                results={results}
                layers={layers}
                opacity={opacity}
                isCalibrating={isCalibrating}
                calibrationLine={calibrationLine}
                setCalibrationLine={setCalibrationLine}
              />
            ) : (
              <BeforeAfterSlider
                rawImageUrl={imageMeta?.url}
                overlayImageUrl={results?.overlay_url}
                width={results?.dimensions?.width}
                height={results?.dimensions?.height}
              />
            )}
          </div>

          {/* Structured Analysis Results Summary Box */}
          {results && (
            <div style={{
              marginTop: '20px',
              padding: '18px 22px',
              background: 'rgba(15, 23, 42, 0.75)',
              border: '1px solid rgba(6, 182, 212, 0.3)',
              borderRadius: '12px',
              fontFamily: 'var(--font-mono)',
              fontSize: '13px',
              lineHeight: '1.7',
              color: '#F1F5F9',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.4)'
            }}>
              <div style={{ color: '#06B6D4', fontWeight: 'bold', fontSize: '14px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle2 size={16} />
                Analysis Complete
              </div>
              <div>Buildings detected: <strong style={{ color: '#F43F5E' }}>{results.stats.buildings_detected}</strong></div>
              <div>Road areas detected: <strong style={{ color: '#06B6D4' }}>{results.stats.road_areas}</strong></div>
              <div>Vegetation areas detected: <strong style={{ color: '#10B981' }}>{results.stats.vegetation_areas}</strong></div>
              <div>AI-proposed parcels: <strong style={{ color: '#A855F7' }}>{results.stats.proposed_parcels}</strong></div>
              
              <div style={{ marginTop: '12px', padding: '12px', background: 'rgba(0,0,0,0.3)', borderRadius: '8px' }}>
                <div style={{ color: '#94A3B8', fontSize: '11px', marginBottom: '4px' }}>Measurement Profile</div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Mode:</span>
                  <span style={{ color: '#FCD34D', fontWeight: 'bold' }}>
                    {measurementMode.charAt(0).toUpperCase() + measurementMode.slice(1)}
                  </span>
                </div>
                {results.parcels && results.parcels.length > 0 && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px' }}>
                    <span>Sample Parcel (AI-P001) Area:</span>
                    <span style={{ color: '#A855F7', whiteSpace: 'pre-line', textAlign: 'right' }}>
                      {results.parcels[0].formatted_area || `${results.parcels[0].area_px} px²`}
                    </span>
                  </div>
                )}
              </div>

              <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px dashed rgba(255,255,255,0.1)', color: '#94A3B8' }}>
                Detection mode:<br />
                <span style={{ color: '#06B6D4', fontWeight: 'bold' }}>{results.detection_mode}</span>
              </div>
            </div>
          )}

          {/* Mandatory SIH Disclaimer Footer Banner */}
          <div style={{
            marginTop: '20px',
            padding: '12px 18px',
            background: 'rgba(245, 158, 11, 0.08)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            color: '#FCD34D',
            fontSize: '12px',
            lineHeight: '1.5'
          }}>
            <ShieldAlert size={20} style={{ flexShrink: 0 }} />
            <span>
              <strong>SIH Prototype Disclaimer:</strong> This prototype generates AI-assisted proposed land-feature and parcel boundaries from imagery. Outputs are not legally authoritative cadastral records and require verification by an authorized surveyor/government authority.
            </span>
          </div>

        </div>
      </div>
    </div>
  );
}
