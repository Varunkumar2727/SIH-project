import React, { useState, useRef } from 'react';
import { UploadCloud, Image as ImageIcon, Sparkles, AlertCircle, FileCheck, Play, Cpu, CheckCircle2, RefreshCw } from 'lucide-react';
import { uploadImage, analyzeImage, trainModel } from '../services/api';

export default function ImageUpload({ onUploadSuccess, onAnalysisComplete, isProcessing, setIsProcessing }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploadedImageMeta, setUploadedImageMeta] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isTraining, setIsTraining] = useState(false);
  const [trainHistory, setTrainHistory] = useState(null);
  
  const fileInputRef = useRef(null);

  const handleFileSelect = (file) => {
    setErrorMsg(null);
    if (!file) return;

    const validExtensions = ['image/jpeg', 'image/png', 'image/tiff', 'image/jpg'];
    const fileName = file.name.toLowerCase();
    const isTiff = fileName.endsWith('.tif') || fileName.endsWith('.tiff');
    
    if (!validExtensions.includes(file.type) && !isTiff) {
      setErrorMsg('Unsupported format. Please upload JPG, PNG, TIFF, or GeoTIFF.');
      return;
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUploadAndAnalyze = async (fileToUse = null) => {
    const targetFile = fileToUse || selectedFile;
    if (!targetFile) return;

    setIsProcessing(true);
    setErrorMsg(null);

    try {
      const meta = await uploadImage(targetFile);
      setUploadedImageMeta(meta);
      if (onUploadSuccess) onUploadSuccess(meta);

      const results = await analyzeImage(meta.image_id);
      if (onAnalysisComplete) onAnalysisComplete(results, meta);

    } catch (err) {
      console.error(err);
      setErrorMsg(err.response?.data?.detail || 'Failed to process image. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleLoadSampleAndAnalyze = async (sampleFileName) => {
    setIsProcessing(true);
    setErrorMsg(null);

    try {
      const response = await fetch(`/${sampleFileName}`);
      if (!response.ok) throw new Error('Could not fetch sample image');
      const mimeType = sampleFileName.endsWith('.png') ? 'image/png' : 'image/jpeg';
      const file = new File([blob], sampleFileName, { type: mimeType });
      
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      
      await handleUploadAndAnalyze(file);
    } catch (err) {
      setErrorMsg('Failed to load sample image. Please upload a local image file.');
      setIsProcessing(false);
    }
  };

  const handleTrainModel = async () => {
    setIsTraining(true);
    setTrainHistory(null);
    try {
      const res = await trainModel(5);
      setTrainHistory(res.training_history);
    } catch (err) {
      console.error(err);
      setErrorMsg('Model training failed.');
    } finally {
      setIsTraining(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '22px', marginBottom: '20px' }}>
      <h3 style={{ fontSize: '16px', fontWeight: '800', color: '#F8FAFC', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{
          background: 'rgba(6, 182, 212, 0.15)',
          padding: '8px',
          borderRadius: '10px',
          color: '#06B6D4'
        }}>
          <UploadCloud size={18} />
        </div>
        Upload Aerial / Satellite Image
      </h3>

      {/* Drag & Drop Target */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${isDragOver ? '#06B6D4' : selectedFile ? '#10B981' : 'rgba(255, 255, 255, 0.14)'}`,
          background: isDragOver ? 'rgba(6, 182, 212, 0.1)' : selectedFile ? 'rgba(16, 185, 129, 0.05)' : 'rgba(15, 23, 42, 0.45)',
          borderRadius: '12px',
          padding: '22px 16px',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.25s ease',
          marginBottom: '16px',
          boxShadow: isDragOver ? '0 0 25px rgba(6, 182, 212, 0.3)' : 'none'
        }}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => handleFileSelect(e.target.files[0])}
          accept=".jpg,.jpeg,.png,.tif,.tiff"
          style={{ display: 'none' }}
        />

        {previewUrl ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
            <img
              src={previewUrl}
              alt="Uploaded Aerial Preview"
              style={{ maxHeight: '130px', maxWidth: '100%', borderRadius: '8px', objectFit: 'contain', boxShadow: '0 4px 16px rgba(0,0,0,0.4)' }}
            />
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12.5px', color: '#10B981', fontWeight: '700' }}>
              <FileCheck size={16} />
              {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
            <div style={{
              background: 'rgba(255,255,255,0.05)',
              padding: '12px',
              borderRadius: '50%',
              color: '#64748B'
            }}>
              <ImageIcon size={32} />
            </div>
            <div>
              <p style={{ fontSize: '13.5px', color: '#E2E8F0', fontWeight: '600' }}>
                Drag & drop imagery here, or <span style={{ color: '#06B6D4', textDecoration: 'underline' }}>browse</span>
              </p>
              <p style={{ fontSize: '11.5px', color: '#64748B', marginTop: '4px' }}>
                Formats: JPG, JPEG, PNG, TIFF, GeoTIFF
              </p>
            </div>
          </div>
        )}
      </div>

      {errorMsg && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          background: 'rgba(244, 63, 94, 0.15)',
          border: '1px solid rgba(244, 63, 94, 0.3)',
          color: '#FDA4AF',
          padding: '10px 14px',
          borderRadius: '8px',
          fontSize: '12.5px',
          marginBottom: '16px'
        }}>
          <AlertCircle size={16} />
          {errorMsg}
        </div>
      )}

      {/* Main Action Buttons */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <button
          className="btn-primary"
          onClick={() => handleUploadAndAnalyze()}
          disabled={!selectedFile || isProcessing}
          style={{ justifyContent: 'center', width: '100%', padding: '12px' }}
        >
          {isProcessing ? (
            <>
              <RefreshCw size={16} className="spin" style={{ animation: 'spin 1s linear infinite' }} />
              Running Spatial Computer Vision AI...
            </>
          ) : (
            <>
              <Sparkles size={16} />
              Analyze Selected Image
            </>
          )}
        </button>

        {/* Model Training Trigger */}
        <button
          onClick={handleTrainModel}
          disabled={isTraining || isProcessing}
          style={{
            background: 'linear-gradient(135deg, #8B5CF6, #6D28D9)',
            color: '#FFF',
            border: 'none',
            padding: '10px 14px',
            borderRadius: '10px',
            fontSize: '12.5px',
            fontWeight: '700',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            boxShadow: '0 4px 16px rgba(139, 92, 246, 0.35)',
            transition: 'all 0.2s ease'
          }}
        >
          <Cpu size={15} />
          {isTraining ? 'Training AI Model (5 Epochs)...' : 'Train AI Model on Aerial Dataset'}
        </button>

        {/* Training Result Box */}
        {trainHistory && (
          <div style={{
            background: 'rgba(139, 92, 246, 0.12)',
            border: '1px solid rgba(168, 85, 247, 0.4)',
            borderRadius: '10px',
            padding: '12px 14px',
            fontSize: '12px',
            color: '#E9D5FF'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 'bold', color: '#F3E8FF', marginBottom: '4px' }}>
              <CheckCircle2 size={14} color="#A855F7" /> Model Weights Trained & Deployed!
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: '#D8B4FE', fontSize: '11px', marginTop: '4px' }}>
              <span>Validation Accuracy: <strong>{(trainHistory[trainHistory.length - 1].val_accuracy * 100).toFixed(2)}%</strong></span>
              <span>Mean IoU: <strong>{trainHistory[trainHistory.length - 1].val_mean_iou}</strong></span>
            </div>
          </div>
        )}

        {/* Real Aerial Presets Title */}
        <div style={{ margin: '10px 0 2px 0', fontSize: '11px', fontWeight: '700', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          Test Real Aerial Datasets:
        </div>

        {/* Real Aerial Card Buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {[
            { filename: 'real_aerial_1.jpg', title: 'Real Aerial 1', desc: '64 Buildings | 96 Parcels', color: '#06B6D4' },
            { filename: 'real_aerial_2.jpg', title: 'Real Aerial 2', desc: '52 Buildings | 66 Parcels', color: '#10B981' },
            { filename: 'cadastrevision_north.png', title: 'CadastreVision North', desc: 'CadNET Benchmark Sector', color: '#F59E0B' },
            { filename: 'cadastrevision_south.png', title: 'CadastreVision South', desc: 'CadNET Benchmark Sector', color: '#EC4899' }
          ].map((preset, idx) => (
            <button
              key={idx}
              className="btn-secondary"
              onClick={() => handleLoadSampleAndAnalyze(preset.filename)}
              disabled={isProcessing}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '9px 12px',
                width: '100%'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Play size={13} color={preset.color} />
                <span style={{ fontWeight: '600', fontSize: '12px' }}>{preset.title}</span>
              </div>
              <span style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>{preset.desc}</span>
            </button>
          ))}
        </div>
      </div>

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
