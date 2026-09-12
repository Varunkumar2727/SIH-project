import React from 'react';
import { Home, Compass, Trees, Box, MapPin, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function StatsCards({ stats, meta, results }) {
  const isGcpActive = results?.active_georeferencing === 'gcp' || results?.georeferencing_method === 'GCP Affine Transformation' || meta?.active_georeferencing === 'gcp';
  const isGeoreferenced = isGcpActive || meta?.is_georeferenced || false;
  const crsInfo = isGcpActive 
    ? (results?.gcp_transformation?.crs || meta?.gcp_transformation?.crs || 'EPSG:32643')
    : (meta?.crs || 'Image is not georeferenced');
  const geo = meta?.geospatial;
  const gcpRmse = results?.gcp_transformation?.rmse || meta?.gcp_transformation?.rmse;

  const georefMethod = isGcpActive 
    ? 'GCP Affine Transformation' 
    : (meta?.is_georeferenced ? 'GeoTIFF Native CRS/Transform' : (meta?.calibration ? 'Manual Calibration' : 'Pixel Mode'));

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

      {/* Georeference Spatial Status Card */}
      <div
        className="glass-panel"
        style={{
          padding: '16px 18px',
          background: 'rgba(15, 23, 42, 0.75)',
          border: `1px solid ${isGeoreferenced ? 'rgba(16, 185, 129, 0.25)' : 'rgba(245, 158, 11, 0.25)'}`,
          display: 'flex',
          flexDirection: 'column',
          gap: '10px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <MapPin size={16} color={isGeoreferenced ? '#10B981' : '#F59E0B'} />
            <span style={{ fontSize: '11px', fontWeight: '800', letterSpacing: '0.05em', color: isGeoreferenced ? '#34D399' : '#FBBF24', textTransform: 'uppercase' }}>
              GEOSPATIAL
            </span>
          </div>
          <span style={{
            fontSize: '10px',
            color: isGeoreferenced ? '#10B981' : '#F59E0B',
            background: isGeoreferenced ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
            border: `1px solid ${isGeoreferenced ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
            padding: '3px 8px',
            borderRadius: '6px',
            fontWeight: '700',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}>
            {isGeoreferenced ? <CheckCircle2 size={11} /> : <AlertTriangle size={11} />}
            Georeferenced: {isGeoreferenced ? 'Yes' : 'No'}
          </span>
        </div>

        {/* Active Georeferencing Method Banner */}
        <div style={{
          padding: '6px 10px',
          background: isGcpActive ? 'rgba(6, 182, 212, 0.15)' : 'rgba(255, 255, 255, 0.04)',
          border: `1px solid ${isGcpActive ? 'rgba(6, 182, 212, 0.35)' : 'rgba(255, 255, 255, 0.08)'}`,
          borderRadius: '6px',
          fontSize: '11px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div>
            <span style={{ color: '#94A3B8', fontSize: '10px' }}>Georeferencing: </span>
            <strong style={{ color: isGcpActive ? '#38BDF8' : '#F1F5F9' }}>{georefMethod}</strong>
          </div>
          {isGcpActive && gcpRmse !== undefined && (
            <span style={{ color: '#34D399', fontSize: '10px', fontWeight: '700' }}>
              RMSE: {gcpRmse.toFixed(2)}m
            </span>
          )}
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '8px',
          background: 'rgba(0, 0, 0, 0.25)',
          padding: '10px 12px',
          borderRadius: '8px',
          fontSize: '11.5px',
          fontFamily: 'var(--font-mono, monospace)'
        }}>
          <div>
            <span style={{ color: 'var(--text-muted, #94A3B8)', display: 'block', fontSize: '10px' }}>CRS</span>
            <strong style={{ color: '#F1F5F9' }}>{isGeoreferenced ? (geo?.crs || crsInfo) : 'Not available'}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted, #94A3B8)', display: 'block', fontSize: '10px' }}>
              {isGeoreferenced ? 'Coordinate System' : 'Measurement'}
            </span>
            <strong style={{ color: isGeoreferenced ? '#38BDF8' : '#FBBF24' }}>
              {isGeoreferenced
                ? (geo?.coordinate_type ? (geo.coordinate_type.charAt(0).toUpperCase() + geo.coordinate_type.slice(1)) : 'Projected')
                : 'Pixel / Manual Calibration'}
            </strong>
          </div>
          {isGeoreferenced && (
            <>
              <div>
                <span style={{ color: 'var(--text-muted, #94A3B8)', display: 'block', fontSize: '10px' }}>Units</span>
                <strong style={{ color: '#A78BFA' }}>{geo?.units || 'meters'}</strong>
              </div>
              {geo?.pixel_size && (
                <div>
                  <span style={{ color: 'var(--text-muted, #94A3B8)', display: 'block', fontSize: '10px' }}>Pixel Resolution</span>
                  <strong style={{ color: '#34D399' }}>{geo.pixel_size.x?.toFixed(2)}m × {geo.pixel_size.y?.toFixed(2)}m</strong>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
