import React, { useState, useEffect } from 'react';
import { CheckCircle2, XCircle, ClipboardList, MapPin } from 'lucide-react';

export default function ReviewQueueModal({ isOpen, onClose }) {
  const [cases, setCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [officerName, setOfficerName] = useState('Survey Officer Rajesh Kumar');
  const [notes, setNotes] = useState('');
  const [message, setMessage] = useState('');

  const fetchCases = async () => {
    try {
      const res = await fetch('/api/v1/reviews');
      const data = await res.json();
      if (data?.data) {
        setCases(data.data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchCases();
    }
  }, [isOpen]);

  const handleDecision = async (decision) => {
    if (!selectedCase) return;
    try {
      await fetch(`/api/v1/reviews/${selectedCase.case_id}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': 'DEMO' },
        body: JSON.stringify({ decision, notes, officer_name: officerName })
      });
      setMessage(`Decision recorded: ${decision}`);
      fetchCases();
      setSelectedCase(null);
      setNotes('');
    } catch {
      setMessage('Error recording decision.');
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
        border: '1px solid rgba(56, 189, 248, 0.3)',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <ClipboardList color="#38BDF8" size={24} />
            <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#F8FAFC', margin: 0 }}>
              Survey Officer Review Queue (Part 7)
            </h2>
          </div>
          <button onClick={onClose} className="btn-secondary" style={{ padding: '4px 12px' }}>Close</button>
        </div>

        {message && (
          <div style={{ padding: '10px', background: 'rgba(16, 185, 129, 0.2)', color: '#34D399', borderRadius: '8px', marginBottom: '14px' }}>
            {message}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '18px' }}>
          {/* List of cases */}
          <div>
            <h3 style={{ fontSize: '14px', color: '#94A3B8', marginBottom: '10px' }}>Pending & Decided Verification Cases</h3>
            {cases.length === 0 ? (
              <div style={{ padding: '20px', textAlign: 'center', color: '#64748B', background: 'rgba(15, 23, 42, 0.5)', borderRadius: '10px' }}>
                No active review cases found. Create a case from detected changes or cadastral discrepancies.
              </div>
            ) : (
              cases.map(c => (
                <div key={c.case_id}
                  onClick={() => setSelectedCase(c)}
                  style={{
                    padding: '12px', marginBottom: '8px', borderRadius: '8px', cursor: 'pointer',
                    background: selectedCase?.case_id === c.case_id ? 'rgba(56, 189, 248, 0.2)' : 'rgba(30, 41, 59, 0.6)',
                    border: '1px solid rgba(255, 255, 255, 0.1)'
                  }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, fontSize: '13px', color: '#F1F5F9' }}>{c.entity_type.toUpperCase()}: {c.entity_id}</span>
                    <span style={{
                      fontSize: '11px', padding: '2px 8px', borderRadius: '10px',
                      background: c.status === 'CONFIRMED' ? '#10B981' : (c.status === 'FIELD_VERIFICATION_REQUIRED' ? '#F59E0B' : '#64748B'),
                      color: '#FFF'
                    }}>{c.status}</span>
                  </div>
                  <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '4px' }}>Case ID: {c.case_id}</div>
                </div>
              ))
            )}
          </div>

          {/* Decision panel */}
          <div style={{ background: 'rgba(15, 23, 42, 0.7)', padding: '16px', borderRadius: '10px', border: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <h3 style={{ fontSize: '14px', color: '#38BDF8', marginBottom: '12px' }}>Officer Decision & Field Dispatch</h3>
            {selectedCase ? (
              <div>
                <p style={{ fontSize: '12px', color: '#CBD5E1' }}><strong>Case ID:</strong> {selectedCase.case_id}</p>
                <p style={{ fontSize: '12px', color: '#CBD5E1' }}><strong>Entity:</strong> {selectedCase.entity_id} ({selectedCase.entity_type})</p>
                <p style={{ fontSize: '12px', color: '#CBD5E1' }}><strong>Current Status:</strong> {selectedCase.status}</p>

                <div style={{ marginTop: '12px' }}>
                  <label style={{ fontSize: '12px', color: '#94A3B8', display: 'block', marginBottom: '4px' }}>Officer Name / ID:</label>
                  <input
                    type="text"
                    value={officerName}
                    onChange={(e) => setOfficerName(e.target.value)}
                    style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#0F172A', border: '1px solid #334155', color: '#FFF' }}
                  />
                </div>

                <div style={{ marginTop: '10px' }}>
                  <label style={{ fontSize: '12px', color: '#94A3B8', display: 'block', marginBottom: '4px' }}>Decision Notes / Field Observations:</label>
                  <textarea
                    rows={3}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Enter survey findings or rationale..."
                    style={{ width: '100%', padding: '8px', borderRadius: '6px', background: '#0F172A', border: '1px solid #334155', color: '#FFF' }}
                  />
                </div>

                <div style={{ display: 'flex', gap: '8px', marginTop: '16px', flexWrap: 'wrap' }}>
                  <button onClick={() => handleDecision('CONFIRMED')} className="btn-primary" style={{ background: '#10B981', padding: '6px 12px', fontSize: '12px' }}>
                    <CheckCircle2 size={14} /> Confirm Finding
                  </button>
                  <button onClick={() => handleDecision('FIELD_VERIFICATION_REQUIRED')} className="btn-primary" style={{ background: '#F59E0B', padding: '6px 12px', fontSize: '12px' }}>
                    <MapPin size={14} /> Assign Field Task
                  </button>
                  <button onClick={() => handleDecision('REJECTED')} className="btn-secondary" style={{ color: '#EF4444', padding: '6px 12px', fontSize: '12px' }}>
                    <XCircle size={14} /> Reject Finding
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ color: '#64748B', fontSize: '13px', textAlign: 'center', marginTop: '40px' }}>
                Select a verification case on the left to review evidence and record an attestation decision.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
