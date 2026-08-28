import React from 'react';
import { Home, Compass, Trees, Box, MapPin, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function StatsCards({ stats, meta }) {
  const isGeoreferenced = meta?.is_georeferenced || false;
  const crsInfo = meta?.crs || 'Image is not georeferenced';

  const cards = [
    {
      title: 'Buildings Detected',
      value: stats?.buildings_detected ?? 0,
      icon: Home,
      color: '#F43F5E',
      glow: 'rgba(244, 63, 94, 0.25)',
      gradient: 'linear-gradient(135deg, #F43F5E, #E11D48)',
      tag: 'Structures'
    },
    {
      title: 'Road Areas',
      value: stats?.road_areas ?? 0,
      icon: Compass,
      color: '#06B6D4',
      glow: 'rgba(6, 182, 212, 0.25)',
      gradient: 'linear-gradient(135deg, #06B6D4, #0284C7)',
      tag: 'Transport'
    },
    {
      title: 'Vegetation Areas',
      value: stats?.vegetation_areas ?? 0,
      icon: Trees,
      color: '#10B981',
      glow: 'rgba(16, 185, 129, 0.25)',
      gradient: 'linear-gradient(135deg, #10B981, #059669)',
      tag: 'Canopy/Grass'
    },
    {
      title: 'Proposed Parcels',
      value: stats?.proposed_parcels ?? 0,
      icon: Box,
      color: '#A855F7',
      glow: 'rgba(168, 85, 247, 0.25)',
      gradient: 'linear-gradient(135deg, #A855F7, #7C3AED)',
      tag: 'AI Cadastral'
    }
  ];

  return (
    <div style={{ marginBottom: '20px' }}>
      {/* 4 Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', marginBottom: '12px' }}>
        {cards.map((card, idx) => {
          const IconComponent = card.icon;
          return (
            <div
              key={idx}
              className="glass-panel"
              style={{
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
                position: 'relative',
                overflow: 'hidden'
              }}
            >
              {/* Subtle top border color glow */}
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: '2px',
                background: card.gradient
              }} />

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '11.5px', color: 'var(--text-secondary)', fontWeight: '500' }}>
                  {card.title}
                </span>
                
                <div style={{
                  background: card.glow,
                  padding: '7px',
                  borderRadius: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: `0 0 12px ${card.glow}`
                }}>
                  <IconComponent size={15} color={card.color} />
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
                <div style={{ fontSize: '26px', fontWeight: '900', color: '#F8FAFC', letterSpacing: '-0.02em' }}>
                  {card.value}
                </div>
                
                <span style={{
                  fontSize: '10px',
                  fontWeight: '600',
                  color: card.color,
                  background: 'rgba(255,255,255,0.05)',
                  padding: '2px 6px',
                  borderRadius: '4px'
                }}>
                  {card.tag}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Georeference Spatial Status Bar */}
      <div
        className="glass-panel"
        style={{
          padding: '14px 18px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(15, 23, 42, 0.65)',
          border: '1px solid rgba(255, 255, 255, 0.08)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <MapPin size={18} color={isGeoreferenced ? '#10B981' : '#F59E0B'} />
          <div>
            <div style={{ fontSize: '12px', fontWeight: '600', color: '#F1F5F9' }}>
              {isGeoreferenced ? 'Georeferenced Spatial Image' : 'Image is not georeferenced'}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              {isGeoreferenced ? `CRS: ${crsInfo}` : 'Using local pixel coordinate system (CRS.Simple)'}
            </div>
          </div>
        </div>

        <span style={{
          fontSize: '10.5px',
          color: isGeoreferenced ? '#10B981' : '#F59E0B',
          background: isGeoreferenced ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
          border: `1px solid ${isGeoreferenced ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
          padding: '4px 10px',
          borderRadius: '6px',
          fontWeight: '700',
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          {isGeoreferenced ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
          {isGeoreferenced ? 'WGS84 EPSG:4326' : 'Pixel Mode'}
        </span>
      </div>
    </div>
  );
}
