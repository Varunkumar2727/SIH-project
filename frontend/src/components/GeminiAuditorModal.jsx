import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  Key, 
  FileText, 
  RefreshCw, 
  X, 
  Building, 
  Compass, 
  ExternalLink 
} from 'lucide-react';

export default function GeminiAuditorModal({ isOpen, onClose, imageMeta, results }) {
  const [apiKey, setApiKey] = useState('');
  const [isConfigured, setIsConfigured] = useState(false);
  const [isSavingKey, setIsSavingKey] = useState(false);
  const [showKeyInput, setShowKeyInput] = useState(false);
  const [auditData, setAuditData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const imageId = imageMeta?.image_id || results?.image_id;

  // Check Gemini status on open
  useEffect(() => {
    if (!isOpen) return;
    checkStatus();
  }, [isOpen]);

  const checkStatus = async () => {
    try {
      const res = await fetch('/api/gemini/status');
      const data = await res.json();
      setIsConfigured(Boolean(data?.configured));
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveKey = async (e) => {
    e.preventDefault();
    if (!apiKey.trim()) return;
    setIsSavingKey(true);
    setErrorMsg('');
    try {
      const res = await fetch('/api/gemini/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey.trim() })
      });
      if (res.ok) {
        setIsConfigured(true);
        setShowKeyInput(false);
        setApiKey('');
      } else {
        const err = await res.json();
        setErrorMsg(err.detail || 'Failed to save API key');
      }
    } catch (err) {
      setErrorMsg('Failed to connect to backend server');
    } finally {
      setIsSavingKey(false);
    }
  };

  const runAudit = async () => {
    if (!imageId) return;
    setIsLoading(true);
    setErrorMsg('');
    try {
      const res = await fetch(`/api/gemini/audit/${imageId}`, {
        method: 'POST'
      });
      if (!res.ok) {
        throw new Error('Audit request failed');
      }
      const data = await res.json();
      setAuditData(data);
    } catch (err) {
      setErrorMsg('Failed to run Gemini audit. Please check your network or try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 9999,
      background: 'rgba(15, 23, 42, 0.85)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{
        background: '#0F172A',
        border: '1px solid rgba(56, 189, 248, 0.25)',
        borderRadius: '16px',
        width: '100%',
        maxWidth: '840px',
        maxHeight: '90vh',
        overflowY: 'auto',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.75)',
        color: '#E2E8F0',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'linear-gradient(90deg, rgba(6, 182, 212, 0.1), transparent)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              background: 'linear-gradient(135deg, #06B6D4, #3B82F6)',
              padding: '10px',
              borderRadius: '10px',
              display: 'flex'
            }}>
              <Sparkles size={22} color="#FFF" />
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 800, color: '#FFF' }}>
                Gemini Vision Cadastral Auditor
              </h2>
              <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '2px' }}>
                AI Semantic Land Use, Setback Compliance & Encroachment Reasoner
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{
              fontSize: '11px',
              padding: '4px 10px',
              borderRadius: '20px',
              fontWeight: 700,
              background: isConfigured ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
              color: isConfigured ? '#34D399' : '#FBBF24',
              border: `1px solid ${isConfigured ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`
            }}>
              {isConfigured ? '● Live Gemini 1.5 Active' : '○ Spatial Fallback Mode'}
            </span>

            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#94A3B8',
                cursor: 'pointer',
                padding: '4px'
              }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* API Key Configuration Dropdown */}
        <div style={{
          padding: '12px 24px',
          background: 'rgba(30, 41, 59, 0.5)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <span style={{ fontSize: '12px', color: '#94A3B8' }}>
            Google Gemini API Integration
          </span>
          <button
            onClick={() => setShowKeyInput(!showKeyInput)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#38BDF8',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Key size={14} /> {showKeyInput ? 'Hide Settings' : isConfigured ? 'Change API Key' : 'Configure Free API Key'}
          </button>
        </div>

        {showKeyInput && (
          <form onSubmit={handleSaveKey} style={{
            padding: '16px 24px',
            background: 'rgba(15, 23, 42, 0.95)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            display: 'flex',
            gap: '12px',
            alignItems: 'center'
          }}>
            <input
              type="password"
              placeholder="Paste your Google AI Studio Gemini API Key..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              style={{
                flex: 1,
                background: '#1E293B',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                borderRadius: '8px',
                padding: '9px 14px',
                color: '#FFF',
                fontSize: '13px'
              }}
            />
            <button
              type="submit"
              disabled={isSavingKey || !apiKey.trim()}
              style={{
                background: '#0284C7',
                color: '#FFF',
                border: 'none',
                borderRadius: '8px',
                padding: '9px 18px',
                fontWeight: 700,
                fontSize: '12px',
                cursor: 'pointer'
              }}
            >
              {isSavingKey ? 'Saving...' : 'Save Key'}
            </button>
          </form>
        )}

        {/* Content Body */}
        <div style={{ padding: '24px', flex: 1, overflowY: 'auto' }}>
          {errorMsg && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '8px',
              padding: '12px 16px',
              marginBottom: '16px',
              color: '#F87171',
              fontSize: '13px'
            }}>
              {errorMsg}
            </div>
          )}

          {!auditData && !isLoading && (
            <div style={{
              textAlign: 'center',
              padding: '40px 20px',
              background: 'rgba(30, 41, 59, 0.3)',
              borderRadius: '12px',
              border: '1px dashed rgba(255, 255, 255, 0.1)'
            }}>
              <Sparkles size={36} color="#38BDF8" style={{ marginBottom: '12px' }} />
              <h3 style={{ margin: '0 0 8px 0', fontSize: '16px', color: '#FFF' }}>
                Run Multimodal Cadastral Audit
              </h3>
              <p style={{ margin: '0 auto 20px auto', maxWidth: '460px', fontSize: '13px', color: '#94A3B8' }}>
                Gemini Vision analyzes high-resolution drone/aerial pixels to verify setback compliance, identify building roof types, and flag encroachments into road rights-of-way.
              </p>
              <button
                onClick={runAudit}
                disabled={!imageId}
                style={{
                  background: 'linear-gradient(135deg, #06B6D4, #2563EB)',
                  color: '#FFF',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '11px 24px',
                  fontSize: '13px',
                  fontWeight: 700,
                  cursor: imageId ? 'pointer' : 'not-allowed',
                  boxShadow: '0 4px 14px rgba(6, 182, 212, 0.35)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                <Sparkles size={16} /> Audit Current Survey Image
              </button>
            </div>
          )}

          {isLoading && (
            <div style={{ textAlign: 'center', padding: '60px 20px' }}>
              <RefreshCw size={36} color="#38BDF8" className="animate-spin" style={{ marginBottom: '16px' }} />
              <h4 style={{ margin: '0 0 6px 0', fontSize: '15px', color: '#FFF' }}>
                Analyzing Spatial Cadastral Context...
              </h4>
              <p style={{ margin: 0, fontSize: '12px', color: '#94A3B8' }}>
                Evaluating building footprints, boundary clearances, and street frontages.
              </p>
            </div>
          )}

          {auditData && (
            <div>
              {/* Score & Land Use Overview Banner */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 220px',
                gap: '16px',
                marginBottom: '20px'
              }}>
                <div style={{
                  background: 'rgba(30, 41, 59, 0.6)',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  border: '1px solid rgba(255, 255, 255, 0.08)'
                }}>
                  <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 700, textTransform: 'uppercase' }}>
                    Identified Land Use Classification
                  </div>
                  <div style={{ fontSize: '18px', fontWeight: 800, color: '#38BDF8', marginTop: '4px' }}>
                    {auditData.land_use_type}
                  </div>
                  <div style={{ fontSize: '12px', color: '#CBD5E1', marginTop: '8px', lineHeight: 1.4 }}>
                    {auditData.structures_summary}
                  </div>
                </div>

                <div style={{
                  background: 'rgba(30, 41, 59, 0.6)',
                  borderRadius: '12px',
                  padding: '16px 20px',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 700, textTransform: 'uppercase' }}>
                    Cadastral Compliance
                  </div>
                  <div style={{
                    fontSize: '32px',
                    fontWeight: 900,
                    color: (auditData.overall_compliance_score || 0) >= 80 ? '#34D399' : '#FBBF24',
                    margin: '4px 0'
                  }}>
                    {auditData.overall_compliance_score}%
                  </div>
                  <div style={{ fontSize: '11px', color: '#94A3B8' }}>
                    {(auditData.overall_compliance_score || 0) >= 80 ? 'Surveyor Standard Met' : 'Review Required'}
                  </div>
                </div>
              </div>

              {/* Encroachments & Setback Warning Box */}
              {auditData.encroachment_risks && auditData.encroachment_risks.length > 0 && (
                <div style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                  borderRadius: '12px',
                  padding: '14px 18px',
                  marginBottom: '20px'
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontWeight: 800,
                    fontSize: '13px',
                    color: '#F87171',
                    marginBottom: '8px'
                  }}>
                    <ShieldAlert size={16} /> Encroachment & Setback Advisory
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '12.5px', color: '#FCA5A5' }}>
                    {auditData.encroachment_risks.map((risk, idx) => (
                      <li key={idx} style={{ marginBottom: '4px' }}>{risk}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Detected Structures Table */}
              {auditData.structures && auditData.structures.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                  <h4 style={{ margin: '0 0 10px 0', fontSize: '13px', color: '#FFF', fontWeight: 800 }}>
                    Audited Building Envelopes
                  </h4>
                  <div style={{ display: 'grid', gap: '8px' }}>
                    {auditData.structures.map((st, idx) => (
                      <div key={idx} style={{
                        background: 'rgba(30, 41, 59, 0.4)',
                        border: '1px solid rgba(255, 255, 255, 0.05)',
                        borderRadius: '8px',
                        padding: '12px 16px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between'
                      }}>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: '13px', color: '#FFF' }}>
                            {st.structure_name}
                          </div>
                          <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '2px' }}>
                            {st.estimated_use} • Condition: {st.structural_condition}
                          </div>
                          <div style={{ fontSize: '11.5px', color: '#CBD5E1', marginTop: '4px' }}>
                            {st.observation}
                          </div>
                        </div>

                        <span style={{
                          fontSize: '10.5px',
                          padding: '3px 8px',
                          borderRadius: '4px',
                          fontWeight: 800,
                          textTransform: 'uppercase',
                          background: st.compliance_status === 'COMPLIANT' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                          color: st.compliance_status === 'COMPLIANT' ? '#34D399' : '#FBBF24',
                          border: `1px solid ${st.compliance_status === 'COMPLIANT' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`
                        }}>
                          {st.compliance_status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Legal Cadastral Narrative */}
              <div style={{
                background: 'rgba(30, 41, 59, 0.4)',
                borderRadius: '12px',
                padding: '16px 20px',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                marginBottom: '20px'
              }}>
                <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 700, textTransform: 'uppercase', marginBottom: '6px' }}>
                  Official Cadastral Audit Report
                </div>
                <p style={{ margin: 0, fontSize: '12.5px', lineHeight: 1.6, color: '#E2E8F0' }}>
                  {auditData.legal_cadastral_summary}
                </p>
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button
                  onClick={runAudit}
                  style={{
                    background: 'rgba(255, 255, 255, 0.08)',
                    color: '#FFF',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '8px 16px',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <RefreshCw size={14} /> Re-Audit
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
