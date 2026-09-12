import React from 'react';
import {
  ArrowRight,
  BrainCircuit,
  Map,
  ScanLine,
  Layers,
  Satellite,
  ShieldCheck,
  BarChart3,
  Upload,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';

export default function Landing({ onLaunch }) {
  return (
    <div className="geo-landing">

      {/* ================= NAVBAR ================= */}
      <nav className="geo-nav">
        <div className="geo-brand">
          <div className="geo-brand-icon">
            <Layers size={22} />
          </div>

          <div>
            <div className="geo-brand-name">
              GeoCadastral <span>AI</span>
            </div>
            <div className="geo-brand-subtitle">
              SPATIAL INTELLIGENCE PLATFORM
            </div>
          </div>
        </div>

        <div className="geo-nav-links">
          <a href="#platform">Platform</a>
          <a href="#workflow">Workflow</a>
          <a href="#technology">Technology</a>
        </div>

        <div className="geo-nav-right">
          <div className="geo-status">
            <span className="geo-status-dot"></span>
            AI SYSTEM ONLINE
          </div>

          <button className="geo-nav-button" onClick={onLaunch}>
            Open Console
            <ArrowRight size={16} />
          </button>
        </div>
      </nav>

      {/* ================= HERO ================= */}
      <section className="geo-hero">

        <div className="geo-hero-content">

          <div className="geo-eyebrow">
            <Sparkles size={15} />
            SMART INDIA HACKATHON 2026
          </div>

          <h1>
            Turn Aerial Imagery
            <br />
            Into <span>Spatial Intelligence.</span>
          </h1>

          <p className="geo-hero-description">
            AI-powered cadastral intelligence that detects spatial features,
            proposes land boundaries, and transforms aerial imagery into
            actionable geospatial insights.
          </p>

          <div className="geo-hero-actions">
            <button className="geo-primary-button" onClick={onLaunch}>
              Launch GeoAI Console
              <ArrowRight size={19} />
            </button>

            <a href="#workflow" className="geo-secondary-button">
              Explore Workflow
            </a>
          </div>

          <div className="geo-trust-row">
            <div>
              <CheckCircle2 size={16} />
              AI-assisted analysis
            </div>

            <div>
              <CheckCircle2 size={16} />
              GeoJSON ready
            </div>

            <div>
              <CheckCircle2 size={16} />
              Interactive mapping
            </div>
          </div>
        </div>

        {/* ================= MAP VISUAL ================= */}
        <div className="geo-hero-visual">

          <div className="geo-map-glow"></div>

          <div className="geo-map-card">

            <div className="geo-map-toolbar">
              <div className="geo-map-title">
                <Satellite size={16} />
                LIVE SPATIAL ANALYSIS
              </div>

              <div className="geo-analysis-status">
                <span></span>
                PROCESSING
              </div>
            </div>

            <div className="geo-map-area">

              <div className="geo-grid"></div>

              {/* parcel shapes */}
              <div className="geo-parcel parcel-one"></div>
              <div className="geo-parcel parcel-two"></div>
              <div className="geo-parcel parcel-three"></div>
              <div className="geo-parcel parcel-four"></div>
              <div className="geo-parcel parcel-five"></div>

              {/* roads */}
              <div className="geo-road road-one"></div>
              <div className="geo-road road-two"></div>

              {/* detection box */}
              <div className="geo-detection-box">
                <span className="corner tl"></span>
                <span className="corner tr"></span>
                <span className="corner bl"></span>
                <span className="corner br"></span>

                <div className="geo-detection-label">
                  <ScanLine size={13} />
                  PARCEL DETECTED
                </div>
              </div>

              {/* map coordinates */}
              <div className="geo-coordinate coord-one">
                13°04'52"N
              </div>

              <div className="geo-coordinate coord-two">
                77°35'18"E
              </div>

              {/* analysis card */}
              <div className="geo-confidence-card">
                <div className="confidence-icon">
                  <BrainCircuit size={18} />
                </div>

                <div>
                  <small>AI CONFIDENCE</small>
                  <strong>94.7%</strong>
                </div>
              </div>

              {/* scale */}
              <div className="geo-scale">
                <span></span>
                100 m
              </div>

            </div>

            <div className="geo-map-footer">
              <div>
                <span className="legend-dot building"></span>
                Buildings
              </div>

              <div>
                <span className="legend-dot boundary"></span>
                Boundaries
              </div>

              <div>
                <span className="legend-dot road"></span>
                Roads
              </div>
            </div>

          </div>

          {/* floating stats */}
          <div className="geo-floating-card geo-floating-top">
            <div className="floating-icon">
              <ScanLine size={17} />
            </div>

            <div>
              <small>FEATURES DETECTED</small>
              <strong>1,284</strong>
            </div>
          </div>

          <div className="geo-floating-card geo-floating-bottom">
            <div className="floating-icon purple">
              <Map size={17} />
            </div>

            <div>
              <small>PARCELS PROPOSED</small>
              <strong>347</strong>
            </div>
          </div>

        </div>
      </section>

      {/* ================= PLATFORM STATS ================= */}
      <section className="geo-stats-section" id="platform">

        <div className="geo-section-label">
          <span></span>
          PLATFORM CAPABILITIES
        </div>

        <div className="geo-stats-grid">

          <div className="geo-stat-card">
            <div className="geo-stat-icon cyan">
              <BrainCircuit size={21} />
            </div>

            <div>
              <strong>AI Detection</strong>
              <p>Computer vision powered feature extraction</p>
            </div>
          </div>

          <div className="geo-stat-card">
            <div className="geo-stat-icon purple">
              <Map size={21} />
            </div>

            <div>
              <strong>Boundary Intelligence</strong>
              <p>Automated cadastral parcel proposals</p>
            </div>
          </div>

          <div className="geo-stat-card">
            <div className="geo-stat-icon blue">
              <BarChart3 size={21} />
            </div>

            <div>
              <strong>Spatial Analytics</strong>
              <p>Interactive measurement and analysis</p>
            </div>
          </div>

          <div className="geo-stat-card">
            <div className="geo-stat-icon green">
              <ShieldCheck size={21} />
            </div>

            <div>
              <strong>Data Ready</strong>
              <p>Export structured geospatial information</p>
            </div>
          </div>

        </div>
      </section>

      {/* ================= WORKFLOW ================= */}
      <section className="geo-workflow-section" id="workflow">

        <div className="geo-section-heading">
          <div className="geo-section-label">
            <span></span>
            HOW IT WORKS
          </div>

          <h2>
            From imagery to
            <span> intelligence.</span>
          </h2>

          <p>
            A streamlined AI workflow designed to transform complex aerial
            imagery into structured spatial information.
          </p>
        </div>

        <div className="geo-workflow">

          <div className="geo-workflow-line"></div>

          <div className="geo-workflow-item">
            <div className="workflow-number">01</div>

            <div className="workflow-icon">
              <Upload size={22} />
            </div>

            <h3>Upload</h3>

            <p>
              Upload aerial or satellite imagery into the GeoAI platform.
            </p>
          </div>

          <div className="geo-workflow-item">
            <div className="workflow-number">02</div>

            <div className="workflow-icon">
              <BrainCircuit size={22} />
            </div>

            <h3>Analyze</h3>

            <p>
              Computer vision analyzes spatial patterns and features.
            </p>
          </div>

          <div className="geo-workflow-item">
            <div className="workflow-number">03</div>

            <div className="workflow-icon">
              <ScanLine size={22} />
            </div>

            <h3>Detect</h3>

            <p>
              Buildings, roads and potential parcel boundaries are detected.
            </p>
          </div>

          <div className="geo-workflow-item">
            <div className="workflow-number">04</div>

            <div className="workflow-icon">
              <Map size={22} />
            </div>

            <h3>Visualize</h3>

            <p>
              Explore results through an interactive spatial map.
            </p>
          </div>

          <div className="geo-workflow-item">
            <div className="workflow-number">05</div>

            <div className="workflow-icon">
              <Layers size={22} />
            </div>

            <h3>Export</h3>

            <p>
              Generate structured geospatial outputs for further analysis.
            </p>
          </div>

        </div>
      </section>

      {/* ================= TECHNOLOGY ================= */}
      <section className="geo-tech-section" id="technology">

        <div className="geo-tech-content">

          <div className="geo-section-label">
            <span></span>
            BUILT FOR MODERN GIS
          </div>

          <h2>
            Intelligence at
            <br />
            <span>geospatial scale.</span>
          </h2>

          <p>
            GeoCadastral AI combines computer vision, spatial analysis,
            interactive mapping and structured geospatial data into a single
            intelligent workflow.
          </p>

          <div className="geo-tech-tags">
            <span>Computer Vision</span>
            <span>Spatial AI</span>
            <span>GIS</span>
            <span>GeoJSON</span>
            <span>Interactive Mapping</span>
          </div>

        </div>

        <div className="geo-tech-visual">

          <div className="tech-orbit orbit-one"></div>
          <div className="tech-orbit orbit-two"></div>
          <div className="tech-orbit orbit-three"></div>

          <div className="tech-core">
            <BrainCircuit size={42} />
            <strong>GeoAI</strong>
            <small>SPATIAL ENGINE</small>
          </div>

          <div className="tech-node node-one">
            <Satellite size={17} />
            <span>IMAGERY</span>
          </div>

          <div className="tech-node node-two">
            <ScanLine size={17} />
            <span>VISION</span>
          </div>

          <div className="tech-node node-three">
            <Map size={17} />
            <span>GIS</span>
          </div>

          <div className="tech-node node-four">
            <Layers size={17} />
            <span>GEOJSON</span>
          </div>

        </div>

      </section>

      {/* ================= CTA ================= */}
      <section className="geo-final-cta">

        <div className="geo-cta-glow"></div>

        <div className="geo-section-label">
          <span></span>
          READY TO EXPLORE
        </div>

        <h2>
          See spatial intelligence
          <br />
          <span>in action.</span>
        </h2>

        <p>
          Enter the interactive GeoCadastral AI dashboard and explore the
          complete analysis workflow.
        </p>

        <button className="geo-primary-button large" onClick={onLaunch}>
          Launch Interactive Dashboard
          <ArrowRight size={19} />
        </button>

      </section>

      {/* ================= FOOTER ================= */}
      <footer className="geo-footer">

        <div className="geo-footer-brand">
          <div className="geo-brand-icon small">
            <Layers size={17} />
          </div>

          <div>
            <strong>
              GeoCadastral <span>AI</span>
            </strong>

            <small>
              Spatial Intelligence Platform
            </small>
          </div>
        </div>

        <div className="geo-footer-center">
          Smart India Hackathon 2026 · Prototype
        </div>

        <div className="geo-footer-right">
          AI-assisted cadastral analysis
        </div>

      </footer>

    </div>
  );
}