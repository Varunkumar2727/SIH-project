import React from 'react';
import { Layers, Eye, EyeOff, Sliders } from 'lucide-react';

export default function LayerControl({ layers, setLayers, opacity, setOpacity }) {
  const layerConfigs = [
    { key: 'buildings', label: 'Buildings (Roof Vectors)', color: '#F43F5E', bg: 'rgba(244, 63, 94, 0.15)' },
    { key: 'roads', label: 'Road Infrastructure', color: '#06B6D4', bg: 'rgba(6, 182, 212, 0.15)' },
    { key: 'vegetation', label: 'Vegetation Canopy', color: '#10B981', bg: 'rgba(16, 185, 129, 0.15)' },
    { key: 'open_land', label: 'Open / Bare Land', color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.15)' },
    { key: 'parcels', label: 'AI Proposed Boundaries', color: '#A855F7', bg: 'rgba(168, 85, 247, 0.15)' },
  ];

  const toggleLayer = (key) => {
    setLayers(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="glass-panel" style={{ padding: '20px', marginBottom: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
        <h4 style={{ fontSize: '15px', fontWeight: '800', color: '#F8FAFC', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ background: 'rgba(6, 182, 212, 0.15)', padding: '6px', borderRadius: '8px', color: '#06B6D4' }}>
            <Layers size={16} />
          </div>
          GIS Layer Visibility Controls
        </h4>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11.5px', color: 'var(--text-muted)', fontWeight: '600' }}>
          <Sliders size={13} color="#06B6D4" />
          <span>{Math.round(opacity * 100)}% Opacity</span>
        </div>
      </div>

      {/* Layer Visibility Toggles */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
        {layerConfigs.map(layer => {
          const isActive = layers[layer.key];
          return (
            <div
              key={layer.key}
              onClick={() => toggleLayer(layer.key)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: '10px',
                background: isActive ? 'rgba(30, 41, 59, 0.75)' : 'rgba(15, 23, 42, 0.4)',
                border: `1px solid ${isActive ? 'rgba(255, 255, 255, 0.14)' : 'transparent'}`,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: isActive ? `0 0 15px ${layer.bg}` : 'none'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  backgroundColor: layer.color,
                  boxShadow: isActive ? `0 0 10px ${layer.color}` : 'none'
                }} />
                <span style={{ fontSize: '13px', fontWeight: isActive ? '600' : '400', color: isActive ? '#F8FAFC' : '#94A3B8' }}>
                  {layer.label}
                </span>
              </div>

              <div style={{
                background: isActive ? layer.bg : 'transparent',
                padding: '5px',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                {isActive ? (
                  <Eye size={15} color={layer.color} />
                ) : (
                  <EyeOff size={15} color="#64748B" />
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Opacity Slider */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
          <span>Vector Transparency</span>
          <span>{Math.round(opacity * 100)}%</span>
        </div>
        <input
          type="range"
          min="0.1"
          max="1.0"
          step="0.05"
          value={opacity}
          onChange={(e) => setOpacity(parseFloat(e.target.value))}
          style={{
            width: '100%',
            accentColor: '#06B6D4',
            cursor: 'pointer',
            height: '6px',
            borderRadius: '3px'
          }}
        />
      </div>
    </div>
  );
}
