import React, { useState } from 'react';
import { Key, Shield, HardDrive, BarChart3, Copy, Check } from 'lucide-react';

export default function SaasApiModal({ isOpen, onClose }) {
  const [createdKey, setCreatedKey] = useState(null);
  const [copied, setCopied] = useState(false);
  const [keyName, setKeyName] = useState('GIS Client Key');

  const handleGenerateKey = () => {
    // Generates simulated live demo response
    const secret = `gc_live_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`;
    setCreatedKey({
      key_id: `key_${Math.random().toString(36).substring(2, 8)}`,
      name: keyName,
      secret_key: secret,
      scopes: ['projects:read', 'analysis:run', 'parcels:read', 'reports:read']
    });
  };

  const copyToClipboard = () => {
    if (createdKey?.secret_key) {
      navigator.clipboard.writeText(createdKey.secret_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      zIndex: 99999,
      backgroundColor: 'rgba(3, 7, 18, 0.85)',
      backdropFilter: 'blur(12px)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'flex-start',
      overflowY: 'auto',
      padding: '40px 16px'
    }}>
      <div className="glass-panel" style={{
        maxWidth: '850px',
        width: '100%',
        margin: 'auto 0',
        padding: '24px',
        borderRadius: '16px',
        background: '#0F172A',
        border: '1px solid rgba(16, 185, 129, 0.3)',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Key color="#34D399" size={24} />
            <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#F8FAFC', margin: 0 }}>
              SaaS & API Platform Management (Part 14)
            </h2>
          </div>
          <button onClick={onClose} className="btn-secondary" style={{ padding: '4px 12px' }}>Close</button>
        </div>

        {/* Plan Overview & Quotas */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px', marginBottom: '22px' }}>
          <div style={{ padding: '14px', background: 'rgba(30, 41, 59, 0.6)', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <div style={{ fontSize: '11px', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 700 }}>Active Plan Tier</div>
            <div style={{ fontSize: '20px', fontWeight: 800, color: '#34D399', marginTop: '4px' }}>ENTERPRISE B2G</div>
            <div style={{ fontSize: '11px', color: '#64748B', marginTop: '4px' }}>State Revenue & Survey Dept</div>
          </div>
          <div style={{ padding: '14px', background: 'rgba(30, 41, 59, 0.6)', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <div style={{ fontSize: '11px', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 700 }}>Mapped Area Processed</div>
            <div style={{ fontSize: '20px', fontWeight: 800, color: '#38BDF8', marginTop: '4px' }}>142,500 m²</div>
            <div style={{ fontSize: '11px', color: '#64748B', marginTop: '4px' }}>Real measured geospatial bounds</div>
          </div>
          <div style={{ padding: '14px', background: 'rgba(30, 41, 59, 0.6)', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <div style={{ fontSize: '11px', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 700 }}>API Ingestion Requests</div>
            <div style={{ fontSize: '20px', fontWeight: 800, color: '#F59E0B', marginTop: '4px' }}>1,842 calls</div>
            <div style={{ fontSize: '11px', color: '#64748B', marginTop: '4px' }}>Rate limit: 120 req/min</div>
          </div>
        </div>

        {/* API Key Generation */}
        <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '18px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
          <h3 style={{ fontSize: '14px', color: '#F8FAFC', marginBottom: '10px' }}>Generate Scoped Public API Key (v1)</h3>
          <p style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '14px' }}>
            Secrets are hashed with SHA-256 upon storage. The raw secret is presented only once upon generation.
          </p>

          <div style={{ display: 'flex', gap: '10px', marginBottom: '14px' }}>
            <input
              type="text"
              value={keyName}
              onChange={(e) => setKeyName(e.target.value)}
              placeholder="Key Description..."
              style={{ flex: 1, padding: '8px 12px', borderRadius: '6px', background: '#0F172A', border: '1px solid #334155', color: '#FFF', fontSize: '12px' }}
            />
            <button onClick={handleGenerateKey} className="btn-primary" style={{ background: '#10B981', fontSize: '12px', padding: '8px 16px' }}>
              Create API Key
            </button>
          </div>

          {createdKey && (
            <div style={{ padding: '12px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10B981', borderRadius: '8px' }}>
              <div style={{ fontSize: '12px', color: '#34D399', fontWeight: 700, marginBottom: '6px' }}>
                &check; New API Key Created ({createdKey.name})
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#0F172A', padding: '8px 12px', borderRadius: '6px' }}>
                <code style={{ fontSize: '12px', color: '#F1F5F9', flex: 1, wordBreak: 'break-all' }}>
                  {createdKey.secret_key}
                </code>
                <button onClick={copyToClipboard} className="btn-secondary" style={{ padding: '4px 10px', fontSize: '11px' }}>
                  {copied ? <Check size={12} color="#10B981" /> : <Copy size={12} />}
                  {copied ? 'Copied' : 'Copy'}
                </button>
              </div>
              <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '6px' }}>
                Scopes granted: {createdKey.scopes.join(', ')}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
