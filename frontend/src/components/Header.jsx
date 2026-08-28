import React, { useState } from 'react';
import { ShieldAlert, Info, Cpu, Layers, Activity, Sparkles } from 'lucide-react';

export default function Header({ detectionMode = 'Prototype Computer Vision' }) {
  const [showModal, setShowModal] = useState(false);

  return (
    <header className="glass-panel glass-panel-glow" style={{ padding: '18px 28px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '20px' }}>
        
        {/* Left: Brand Identity */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #06B6D4, #3B82F6, #8B5CF6)',
            padding: '12px',
            borderRadius: '14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 20px rgba(6, 182, 212, 0.4)'
          }}>
            <Layers size={28} color="#FFFFFF" />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <h1 style={{
                fontSize: '24px',
                fontWeight: '900',
                letterSpacing: '-0.03em',
                background: 'linear-gradient(90deg, #FFFFFF 30%, #38BDF8 70%, #A855F7 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}>
                GeoCadastral AI
              </h1>
              
              <span style={{
                background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(168, 85, 247, 0.2))',
                color: '#38BDF8',
                border: '1px solid rgba(56, 189, 248, 0.4)',
                padding: '3px 10px',
                borderRadius: '999px',
                fontSize: '11px',
                fontWeight: '700',
                letterSpacing: '0.06em',
                display: 'flex',
                alignItems: 'center',
                gap: '5px'
              }}>
                <Sparkles size={11} /> SIH 2026 PROTOTYPE
              </span>
            </div>

            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '3px', fontWeight: '400' }}>
              AI-Assisted Cadastral Mapping & Spatial Land Feature Segmentation
            </p>
          </div>
        </div>

        {/* Right: Realtime Indicators & Legal Modal Button */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          
          {/* Live System Indicator */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            padding: '6px 12px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: '600',
            color: '#34D399'
          }}>
            <div className="pulse-dot" style={{ backgroundColor: '#10B981', boxShadow: '0 0 10px #10B981' }} />
            SYSTEM ONLINE
          </div>

          {/* Engine Mode */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(15, 23, 42, 0.7)',
            border: '1px solid rgba(255, 255, 255, 0.12)',
            padding: '6px 14px',
            borderRadius: '20px',
            fontSize: '12px'
          }}>
            <Cpu size={14} color="#06B6D4" />
            <span style={{ color: 'var(--text-muted)' }}>Detection Engine:</span>
            <span style={{ color: '#F1F5F9', fontWeight: '600' }}>{detectionMode}</span>
          </div>

          {/* Disclaimer Button */}
          <button
            onClick={() => setShowModal(true)}
            className="btn-secondary"
            style={{ fontSize: '12px', padding: '7px 14px' }}
          >
            <Info size={14} color="#F59E0B" />
            Legal Disclaimer
          </button>
        </div>
      </div>

      {/* Mandatory SIH Disclaimer Modal */}
      {showModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(3, 7, 18, 0.85)',
          backdropFilter: 'blur(12px)',
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px'
        }}>
          <div className="glass-panel" style={{ maxWidth: '540px', width: '100%', padding: '28px', position: 'relative', border: '1px solid rgba(245, 158, 11, 0.4)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px', color: '#F59E0B' }}>
              <ShieldAlert size={32} />
              <div>
                <h3 style={{ fontSize: '19px', fontWeight: '800', color: '#FFF' }}>Cadastral Mapping Disclaimer</h3>
                <span style={{ fontSize: '11px', color: '#FCD34D' }}>SIH 2026 Prototype Notice</span>
              </div>
            </div>
            
            <p style={{ color: '#CBD5E1', fontSize: '14px', lineHeight: '1.65', marginBottom: '24px' }}>
              "This prototype generates AI-assisted proposed land-feature and parcel boundaries from imagery. Outputs are not legally authoritative cadastral records and require verification by an authorized surveyor/government authority."
            </p>
            
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                className="btn-primary"
                onClick={() => setShowModal(false)}
                style={{ fontSize: '13px', padding: '10px 24px' }}
              >
                I Understand & Acknowledge
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
