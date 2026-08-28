import React from 'react';
import { ArrowRight, Map, Cpu, ShieldAlert, Layers } from 'lucide-react';

export default function Landing({ onLaunch }) {
  return (
    <div className="bg-mesh-pattern" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', color: '#F8FAFC' }}>
      
      {/* Top Navigation */}
      <nav style={{ padding: '24px 40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #06B6D4, #3B82F6)',
            padding: '10px',
            borderRadius: '12px',
            boxShadow: '0 4px 15px rgba(6, 182, 212, 0.4)'
          }}>
            <Layers size={24} color="#FFF" />
          </div>
          <span className="font-heading" style={{ fontSize: '22px', fontWeight: '800', letterSpacing: '0.5px' }}>
            GeoCadastral <span style={{ color: '#06B6D4' }}>AI</span>
          </span>
        </div>
        
        <div style={{
          background: 'rgba(255, 255, 255, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          padding: '6px 16px',
          borderRadius: '20px',
          fontSize: '13px',
          fontWeight: '600',
          color: '#38BDF8'
        }}>
          SIH 2026 PROTOTYPE
        </div>
      </nav>

      {/* Hero Section */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '0 20px', textAlign: 'center' }}>
        
        <div className="animate-fade-in-up" style={{ marginBottom: '24px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(16, 185, 129, 0.1)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: '#34D399',
            padding: '8px 16px',
            borderRadius: '30px',
            fontSize: '14px',
            fontWeight: '600',
            marginBottom: '24px'
          }}>
            <span className="pulse-dot" style={{ background: '#10B981' }}></span>
            System Online & Ready
          </div>
          
          <h1 className="font-heading" style={{ fontSize: 'clamp(48px, 6vw, 82px)', lineHeight: '1.1', fontWeight: '900', marginBottom: '20px', letterSpacing: '-1px' }}>
            Next-Generation <br />
            <span className="text-gradient">Spatial Intelligence</span>
          </h1>
          
          <p style={{ maxWidth: '640px', margin: '0 auto', fontSize: '18px', color: '#94A3B8', lineHeight: '1.6', fontWeight: '400' }}>
            AI-powered feature segmentation and dynamic cadastral boundary proposals from aerial imagery. Built for SIH 2026.
          </p>
        </div>

        <div className="animate-fade-in-up stagger-1" style={{ marginTop: '40px', marginBottom: '60px' }}>
          <div className="animate-float">
            <button 
              onClick={onLaunch}
              className="btn-primary" 
              style={{ fontSize: '16px', padding: '16px 32px', borderRadius: '14px' }}
            >
              Launch Interactive Dashboard <ArrowRight size={20} />
            </button>
          </div>
        </div>

        {/* Feature Cards Grid */}
        <div className="animate-fade-in-up stagger-2" style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '24px',
          maxWidth: '1080px',
          width: '100%',
          marginTop: '20px'
        }}>
          {/* Card 1 */}
          <div className="glass-panel" style={{ padding: '30px 24px', textAlign: 'left', transition: 'transform 0.3s ease' }}>
            <div style={{ background: 'rgba(6, 182, 212, 0.15)', padding: '12px', borderRadius: '12px', display: 'inline-block', marginBottom: '16px' }}>
              <Cpu size={24} color="#06B6D4" />
            </div>
            <h3 className="font-heading" style={{ fontSize: '20px', fontWeight: '700', marginBottom: '12px' }}>Multi-Spectrum Detection</h3>
            <p style={{ color: '#94A3B8', fontSize: '14px', lineHeight: '1.6' }}>
              Advanced computer vision extracts buildings, roads, and vegetation from raw aerial and satellite imagery instantly.
            </p>
          </div>

          {/* Card 2 */}
          <div className="glass-panel" style={{ padding: '30px 24px', textAlign: 'left', transition: 'transform 0.3s ease' }}>
            <div style={{ background: 'rgba(168, 85, 247, 0.15)', padding: '12px', borderRadius: '12px', display: 'inline-block', marginBottom: '16px' }}>
              <Map size={24} color="#A855F7" />
            </div>
            <h3 className="font-heading" style={{ fontSize: '20px', fontWeight: '700', marginBottom: '12px' }}>Boundary Proposals</h3>
            <p style={{ color: '#94A3B8', fontSize: '14px', lineHeight: '1.6' }}>
              Automatically generates and maps AI-proposed cadastral parcels using spatial clustering and void detection.
            </p>
          </div>

          {/* Card 3 */}
          <div className="glass-panel" style={{ padding: '30px 24px', textAlign: 'left', transition: 'transform 0.3s ease' }}>
            <div style={{ background: 'rgba(245, 158, 11, 0.15)', padding: '12px', borderRadius: '12px', display: 'inline-block', marginBottom: '16px' }}>
              <ShieldAlert size={24} color="#F59E0B" />
            </div>
            <h3 className="font-heading" style={{ fontSize: '20px', fontWeight: '700', marginBottom: '12px' }}>SIH 2026 Prototype</h3>
            <p style={{ color: '#94A3B8', fontSize: '14px', lineHeight: '1.6' }}>
              Developed as a proof of concept. Generates GeoJSON data for external verification. Not for authoritative legal use.
            </p>
          </div>
        </div>

      </main>

      {/* Footer */}
      <footer style={{ padding: '24px', textAlign: 'center', color: '#64748B', fontSize: '13px' }}>
        GeoCadastral AI © 2026. Designed for Smart India Hackathon.
      </footer>
    </div>
  );
}
