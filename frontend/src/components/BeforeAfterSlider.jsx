import React, { useState, useRef, useEffect } from 'react';
import { SlidersHorizontal, Image as ImageIcon, Sparkles } from 'lucide-react';
import { getImageUrl } from '../services/api';

export default function BeforeAfterSlider({ rawImageUrl, overlayImageUrl }) {
  const [sliderPos, setSliderPos] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const [containerWidth, setContainerWidth] = useState(0);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const updateWidth = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.clientWidth);
      }
    };
    updateWidth();
    const observer = new ResizeObserver(updateWidth);
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  const handleMove = (clientX) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    let pos = (x / rect.width) * 100;
    if (pos < 0) pos = 0;
    if (pos > 100) pos = 100;
    setSliderPos(pos);
  };

  const handleTouchMove = (e) => {
    if (isDragging && e.touches[0]) {
      handleMove(e.touches[0].clientX);
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging) {
      handleMove(e.clientX);
    }
  };

  useEffect(() => {
    const handleMouseUp = () => setIsDragging(false);
    window.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('touchend', handleMouseUp);
    return () => {
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('touchend', handleMouseUp);
    };
  }, []);

  const rawUrl = getImageUrl(rawImageUrl);
  const overlayUrl = getImageUrl(overlayImageUrl);

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
        <h4 style={{ fontSize: '15px', fontWeight: '800', color: '#F8FAFC', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ background: 'rgba(6, 182, 212, 0.15)', padding: '6px', borderRadius: '8px', color: '#06B6D4' }}>
            <SlidersHorizontal size={16} />
          </div>
          Before & After Image Comparison Slider
        </h4>
        
        <div style={{ display: 'flex', gap: '14px', fontSize: '12px', fontWeight: '600' }}>
          <span style={{
            background: 'rgba(255, 255, 255, 0.08)',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            padding: '4px 10px',
            borderRadius: '6px',
            color: '#CBD5E1',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <ImageIcon size={14} color="#94A3B8" /> Raw Aerial (Left)
          </span>
          <span style={{
            background: 'rgba(6, 182, 212, 0.15)',
            border: '1px solid rgba(6, 182, 212, 0.35)',
            padding: '4px 10px',
            borderRadius: '6px',
            color: '#38BDF8',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <Sparkles size={14} color="#06B6D4" /> AI Detection Overlay (Right)
          </span>
        </div>
      </div>

      {/* Slider Viewport Container */}
      <div
        ref={containerRef}
        onMouseDown={(e) => { setIsDragging(true); handleMove(e.clientX); }}
        onTouchStart={(e) => { setIsDragging(true); if (e.touches[0]) handleMove(e.touches[0].clientX); }}
        onMouseMove={handleMouseMove}
        onTouchMove={handleTouchMove}
        style={{
          position: 'relative',
          width: '100%',
          flex: 1,
          minHeight: '450px',
          overflow: 'hidden',
          borderRadius: '12px',
          cursor: 'col-resize',
          userSelect: 'none',
          background: '#070A11',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}
      >
        {/* Background Image: AI Overlay */}
        <img
          src={overlayUrl || rawUrl}
          alt="AI Detection Overlay"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'contain'
          }}
        />

        {/* Clipped Foreground Image: Raw Image */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            bottom: 0,
            width: `${sliderPos}%`,
            overflow: 'hidden'
          }}
        >
          <img
            src={rawUrl}
            alt="Original Satellite Image"
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: containerWidth ? `${containerWidth}px` : '100%',
              height: '100%',
              objectFit: 'contain'
            }}
          />
        </div>

        {/* Vertical Split Divider */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            bottom: 0,
            left: `${sliderPos}%`,
            width: '3px',
            background: 'linear-gradient(180deg, #06B6D4, #8B5CF6)',
            transform: 'translateX(-50%)',
            boxShadow: '0 0 15px rgba(6, 182, 212, 0.9)',
            zIndex: 10
          }}
        >
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #06B6D4, #8B5CF6)',
            color: '#FFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 20px rgba(0,0,0,0.6)',
            fontSize: '14px',
            border: '2px solid #FFF'
          }}>
            ↔
          </div>
        </div>
      </div>
    </div>
  );
}
