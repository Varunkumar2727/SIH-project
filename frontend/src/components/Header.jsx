import React, { useState } from 'react';
import { ShieldAlert, Info, Cpu, Layers, Activity, Sparkles } from 'lucide-react';
import ReviewQueueModal from './ReviewQueueModal';
import AiStudioModal from './AiStudioModal';
import SaasApiModal from './SaasApiModal';
import ProductionStatusModal from './ProductionStatusModal';

export default function Header({ detectionMode = 'Prototype Computer Vision' }) {
  const [showModal, setShowModal] = useState(false);
  const [showReviews, setShowReviews] = useState(false);
  const [showAiStudio, setShowAiStudio] = useState(false);
  const [showSaas, setShowSaas] = useState(false);
  const [showProd, setShowProd] = useState(false);

  return (
    <header className="glass-panel glass-panel-glow" style={{ padding: '16px 24px', marginBottom: '20px' }}>
      {/* Top Bar: Brand + System Status */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '14px' }}>
        
        {/* Left: Brand Identity */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #06B6D4, #3B82F6, #8B5CF6)',
            padding: '10px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(6, 182, 212, 0.35)'
          }}>
            <Layers size={24} color="#FFFFFF" />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{
                fontSize: '22px',
                fontWeight: '900',
                letterSpacing: '-0.02em',
                background: 'linear-gradient(90deg, #FFFFFF 30%, #38BDF8 70%, #A855F7 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                margin: 0
              }}>
                GeoCadastral AI
              </h1>
              
              <span style={{
                background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(168, 85, 247, 0.2))',
                color: '#38BDF8',
                border: '1px solid rgba(56, 189, 248, 0.35)',
                padding: '2px 8px',
                borderRadius: '999px',
                fontSize: '10px',
                fontWeight: '700',
                letterSpacing: '0.05em',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}>
                <Sparkles size={10} /> SIH 2026 PLATFORM
              </span>
            </div>

            <p style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '2px', marginBottom: 0 }}>
              AI-Assisted Cadastral Mapping & Geospatial Land Intelligence Platform
            </p>
          </div>
        </div>

        {/* Right: Live Diagnostics & Statutory Notice */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            padding: '5px 10px',
            borderRadius: '16px',
            fontSize: '11px',
            fontWeight: '600',
            color: '#34D399'
          }}>
            <div className="pulse-dot" style={{ backgroundColor: '#10B981', boxShadow: '0 0 8px #10B981' }} />
            SYSTEM ONLINE
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            padding: '5px 12px',
            borderRadius: '16px',
            fontSize: '11px'
          }}>
            <Cpu size={13} color="#06B6D4" />
            <span style={{ color: 'var(--text-muted)' }}>Engine:</span>
            <span style={{ color: '#F1F5F9', fontWeight: '600' }}>{detectionMode}</span>
          </div>

          <button
            onClick={() => setShowModal(true)}
            className="btn-secondary"
            style={{ fontSize: '11px', padding: '5px 12px', borderColor: 'rgba(245, 158, 11, 0.4)', color: '#FCD34D' }}
          >
            <Info size={13} color="#F59E0B" />
            Statutory Notice
          </button>
        </div>
      </div>

      {/* Bottom Ribbon: Navigation Tabs */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', paddingTop: '12px', overflowX: 'auto' }}>
        <span style={{ fontSize: '11px', color: '#64748B', fontWeight: '700', textTransform: 'uppercase', marginRight: '4px', letterSpacing: '0.05em' }}>
          Platform Modules:
        </span>

        <button
          onClick={() => setShowReviews(true)}
          className="btn-secondary"
          style={{ fontSize: '12px', padding: '6px 14px', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.08)', borderColor: 'rgba(56, 189, 248, 0.25)' }}
        >
          <Activity size={13} color="#38BDF8" /> Review Queue
        </button>

        <button
          onClick={() => setShowAiStudio(true)}
          className="btn-secondary"
          style={{ fontSize: '12px', padding: '6px 14px', borderRadius: '8px', background: 'rgba(168, 85, 247, 0.08)', borderColor: 'rgba(168, 85, 247, 0.25)' }}
        >
          <Cpu size={13} color="#A855F7" /> AI Training Studio
        </button>

        <button
          onClick={() => setShowSaas(true)}
          className="btn-secondary"
          style={{ fontSize: '12px', padding: '6px 14px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.08)', borderColor: 'rgba(16, 185, 129, 0.25)' }}
        >
          <Layers size={13} color="#34D399" /> SaaS & API
        </button>

        <button
          onClick={() => setShowProd(true)}
          className="btn-secondary"
          style={{ fontSize: '12px', padding: '6px 14px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.08)', borderColor: 'rgba(245, 158, 11, 0.25)' }}
        >
          <ShieldAlert size={13} color="#F59E0B" /> Production Scorecard
        </button>
      </div>

      <ReviewQueueModal isOpen={showReviews} onClose={() => setShowReviews(false)} />
      <AiStudioModal isOpen={showAiStudio} onClose={() => setShowAiStudio(false)} />
      <SaasApiModal isOpen={showSaas} onClose={() => setShowSaas(false)} />
      <ProductionStatusModal isOpen={showProd} onClose={() => setShowProd(false)} />

      {/* Mandatory Statutory Disclaimer Modal */}
      {showModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(3, 7, 18, 0.85)',
          backdropFilter: 'blur(12px)',
          zIndex: 99999,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'flex-start',
          overflowY: 'auto',
          padding: '40px 16px'
        }}>
          <div className="glass-panel" style={{
            maxWidth: '540px',
            width: '100%',
            margin: 'auto 0',
            padding: '28px',
            position: 'relative',
            border: '1px solid rgba(245, 158, 11, 0.4)',
            borderRadius: '16px',
            background: '#0F172A',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px', color: '#F59E0B' }}>
              <ShieldAlert size={32} />
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#FFF', margin: 0 }}>Cadastral Mapping Disclaimer</h3>
                <span style={{ fontSize: '11px', color: '#FCD34D' }}>Statutory Technical Notice</span>
              </div>
            </div>

            <p style={{ fontSize: '13px', color: '#CBD5E1', lineHeight: '1.6', marginBottom: '14px' }}>
              <strong>Decision-Support Notice:</strong> All parcel boundaries, classifications, and access pathways delineated by GeoCadastral AI are <strong>AI-proposed and preliminary</strong>. They do not constitute legal title, ownership deeds, or statutory cadastral certification.
            </p>

            <p style={{ fontSize: '13px', color: '#CBD5E1', lineHeight: '1.6', marginBottom: '20px' }}>
              Boundary reconciliation, easement determination, and property registrations must be verified by an authorized surveyor under relevant state revenue laws.
            </p>

            <button
              onClick={() => setShowModal(false)}
              className="btn-primary"
              style={{ width: '100%', background: '#F59E0B', color: '#000', fontWeight: '700' }}
            >
              I Understand & Acknowledge
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
