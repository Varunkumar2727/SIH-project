import React from 'react';
import { Download, FileJson, Image as ImageIcon } from 'lucide-react';
import { getGeoJsonUrl, getImageUrl } from '../services/api';

export default function GeoJsonExport({ imageId, overlayUrl }) {
  if (!imageId) return null;

  const handleDownloadGeoJson = () => {
    const url = getGeoJsonUrl(imageId);
    const a = document.createElement('a');
    a.href = url;
    a.download = `geocadastral_${imageId}.geojson`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleDownloadImage = () => {
    if (!overlayUrl) return;
    const url = getImageUrl(overlayUrl);
    const a = document.createElement('a');
    a.href = url;
    a.download = `geocadastral_${imageId}_overlay.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="glass-panel" style={{ padding: '16px', marginBottom: '20px' }}>
      <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#F8FAFC', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Download size={16} color="#06B6D4" />
        Export Spatial Results
      </h4>

      <div style={{ display: 'flex', gap: '10px' }}>
        <button
          className="btn-primary"
          onClick={handleDownloadGeoJson}
          style={{ flex: 1, justifyContent: 'center', fontSize: '12px', padding: '10px' }}
        >
          <FileJson size={16} />
          Download GeoJSON
        </button>

        <button
          className="btn-secondary"
          onClick={handleDownloadImage}
          disabled={!overlayUrl}
          style={{ flex: 1, justifyContent: 'center', fontSize: '12px', padding: '10px' }}
        >
          <ImageIcon size={16} color="#06B6D4" />
          Download Detection Image
        </button>
      </div>
    </div>
  );
}
