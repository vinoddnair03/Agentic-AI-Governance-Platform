import React, { useState } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  Cpu, 
  FileText, 
  Layers, 
  GitCompare, 
  Download, 
  Copy, 
  CheckCircle2, 
  Sparkles, 
  BookOpen, 
  Sliders 
} from 'lucide-react';

const PRESETS = [
  {
    name: "Tier 0: FAQ Support Bot",
    spec: {
      name: "Customer Support FAQ Bot",
      description: "Read-only assistance bot answering general customer inquiries.",
      domain: "Customer Service",
      autonomy_scope: "Read-only Q&A. No autonomous actions or database mutations permitted.",
      integrations: "Knowledge Base Read-Only API",
      human_in_loop_level: "Human approves all escalations"
    }
  },
  {
    name: "Tier 2: Loan Approval Agent",
    spec: {
      name: "Financial Loan Approval Agent",
      description: "Evaluates credit risk and approves low-risk micro-loans.",
      domain: "Fintech / Banking",
      autonomy_scope: "Approves loans under $10,000 without human review. Flagged loans routed to human underwriter.",
      integrations: "Credit Bureau API, Core Banking API, Fraud Detection Engine",
      human_in_loop_level: "Approval gate for loans > $10,000"
    }
  },
  {
    name: "Tier 4: Autonomous Trader",
    spec: {
      name: "HFT Liquidity Arbitrage Agent",
      description: "Self-executing multi-exchange cryptocurrency trading engine.",
      domain: "Financial Markets",
      autonomy_scope: "Fully autonomous order routing, position sizing, and goal re-balancing without human intervention.",
      integrations: "Binance API, Coinbase Pro API, Direct Order Routing FIX Protocol",
      human_in_loop_level: "None (Full Autonomy)"
    }
  }
];

export default function App() {
  const [activeTab, setActiveTab] = useState('assess');
  const [loading, setLoading] = useState(false);
  const [compareLoading, setCompareLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);
  
  const [formData, setFormData] = useState({
    name: "Financial Loan Approval Agent",
    description: "Evaluates credit risk and approves low-risk micro-loans.",
    domain: "Fintech / Banking",
    autonomy_scope: "Approves loans under $10,000 without human review. Flagged loans routed to human underwriter.",
    integrations: "Credit Bureau API, Core Banking API, Fraud Engine",
    human_in_loop_level: "Approval-Gate for transactions over threshold"
  });

  const [currentAssessment, setCurrentAssessment] = useState(null);
  const [compareId1, setCompareId1] = useState('');
  const [compareId2, setCompareId2] = useState('');
  const [compareResult, setCompareResult] = useState(null);

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const applyPreset = (presetSpec) => {
    setFormData(presetSpec);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setCurrentAssessment(null);
    try {
      const res = await fetch('/api/v1/assess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server error ${res.status}`);
      }
      const data = await res.json();
      setCurrentAssessment(data);
    } catch (err) {
      console.error("Assessment error:", err);
      setError(err.message || "Error connecting to backend API. Make sure FastAPI is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleCompare = async (e) => {
    e.preventDefault();
    if (!compareId1 || !compareId2) {
      alert("Please provide two valid Assessment IDs");
      return;
    }
    setCompareLoading(true);
    try {
      const res = await fetch('/api/v1/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assessment_id_1: compareId1, assessment_id_2: compareId2 })
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server error ${res.status}`);
      }
      const data = await res.json();
      setCompareResult(data);
    } catch (err) {
      alert(`Error comparing assessments: ${err.message}`);
    } finally {
      setCompareLoading(false);
    }
  };

  const handleExportJSON = () => {
    if (!currentAssessment) return;
    const jsonStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentAssessment, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", jsonStr);
    downloadAnchor.setAttribute("download", `${currentAssessment.agent_name.toLowerCase().replace(/\s+/g, '_')}_assessment.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handleCopyPlaybook = () => {
    if (!currentAssessment?.playbook_md) return;
    navigator.clipboard.writeText(currentAssessment.playbook_md)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      })
      .catch(() => alert("Clipboard access denied. Please copy the playbook manually."));
  };

  return (
    <div className="app-layout">
      {/* Header */}
      <header className="header-bar">
        <div className="brand">
          <div className="brand-icon">
            <ShieldCheck size={24} />
          </div>
          <div>
            <h1 className="brand-title">Agentic AI Governance Platform</h1>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              ReAct-Powered Autonomy Classification & Governance Engine
            </span>
          </div>
        </div>

        <nav className="nav-tabs">
          <button 
            className={`nav-tab ${activeTab === 'assess' ? 'active' : ''}`}
            onClick={() => { setActiveTab('assess'); setError(null); }}
          >
            <Cpu size={16} /> Assessment
          </button>
          <button 
            className={`nav-tab ${activeTab === 'compare' ? 'active' : ''}`}
            onClick={() => { setActiveTab('compare'); setError(null); }}
          >
            <GitCompare size={16} /> Compare Agents
          </button>
        </nav>
      </header>

      {activeTab === 'assess' ? (
        <div className="main-grid">
          {/* Left Panel: Specification Form */}
          <div className="glass-panel">
            <div className="section-header">
              <h2 className="section-title">
                <Sliders size={20} style={{ color: 'var(--accent-indigo)' }} />
                Agent Specification
              </h2>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <span className="form-label">Quick Load Case Studies:</span>
              <div className="preset-pills">
                {PRESETS.map((p, idx) => (
                  <button 
                    key={idx} 
                    className="preset-pill"
                    onClick={() => applyPreset(p.spec)}
                  >
                    {p.name}
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Agent Name</label>
                <input 
                  type="text" 
                  name="name"
                  className="form-input"
                  value={formData.name}
                  onChange={handleInputChange}
                  required 
                />
              </div>

              <div className="form-group">
                <label className="form-label">Domain / Industry</label>
                <input 
                  type="text" 
                  name="domain"
                  className="form-input"
                  value={formData.domain}
                  onChange={handleInputChange}
                  required 
                />
              </div>

              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea 
                  name="description"
                  className="form-textarea"
                  value={formData.description}
                  onChange={handleInputChange}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Autonomy Scope & Action Boundaries</label>
                <textarea 
                  name="autonomy_scope"
                  className="form-textarea"
                  value={formData.autonomy_scope}
                  onChange={handleInputChange}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Integrations & External APIs</label>
                <input 
                  type="text" 
                  name="integrations"
                  className="form-input"
                  value={formData.integrations}
                  onChange={handleInputChange}
                  required 
                />
              </div>

              <div className="form-group">
                <label className="form-label">Human-in-the-Loop Level</label>
                <select 
                  name="human_in_loop_level"
                  className="form-select"
                  value={formData.human_in_loop_level}
                  onChange={handleInputChange}
                >
                  <option value="None (Full Autonomy)">None (Full Autonomy)</option>
                  <option value="Periodic Review">Periodic Review</option>
                  <option value="Approval-Gate for transactions over threshold">Approval-Gate</option>
                  <option value="Direct Human Supervision">Direct Human Supervision</option>
                  <option value="Human approves all outputs">Human approves all outputs (Read-Only)</option>
                </select>
              </div>

              {error && (
                <div style={{ color: 'var(--accent-rose)', background: 'rgba(244,63,94,0.1)', border: '1px solid var(--accent-rose)', borderRadius: '8px', padding: '10px 14px', marginBottom: '12px', fontSize: '0.88rem' }}>
                  {error}
                </div>
              )}

              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? (
                  <>
                    <div className="loading-spinner"></div>
                    Executing ReAct Loop...
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    Run Governance Assessment
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Right Panel: Assessment Results */}
          <div>
            {currentAssessment ? (
              <div className="glass-panel">
                {/* Result Header */}
                <div className="results-header-card">
                  <div className="agent-title-group">
                    <h2>{currentAssessment.agent_name}</h2>
                    <div className="agent-meta-text">
                      ID: <code style={{ color: 'var(--accent-cyan)' }}>{currentAssessment.assessment_id}</code> | Domain: {currentAssessment.domain}
                    </div>
                  </div>
                  <div className={`tier-badge tier-${currentAssessment.autonomy_tier}`}>
                    <Layers size={18} />
                    {currentAssessment.autonomy_tier_label}
                  </div>
                </div>

                {/* Dashboard Grid */}
                <div className="dashboard-grid">
                  {/* Risks */}
                  <div className="dash-card">
                    <h3>
                      <AlertTriangle size={18} style={{ color: 'var(--accent-amber)' }} />
                      Identified Risk Factors
                    </h3>
                    <ul className="item-list">
                      {currentAssessment.risks.map((risk, i) => (
                        <li key={i}>
                          <span style={{ color: 'var(--accent-rose)' }}>•</span>
                          {risk}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Controls */}
                  <div className="dash-card">
                    <h3>
                      <ShieldCheck size={18} style={{ color: 'var(--accent-emerald)' }} />
                      Required Operational Controls
                    </h3>
                    <ul className="item-list">
                      {currentAssessment.controls.map((ctrl, i) => (
                        <li key={i}>
                          <span style={{ color: 'var(--accent-emerald)' }}>✓</span>
                          {ctrl}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Compliance Frameworks */}
                <div className="dash-card" style={{ marginBottom: '24px' }}>
                  <h3>
                    <BookOpen size={18} style={{ color: 'var(--accent-cyan)' }} />
                    Regulatory Compliance Mapping
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginTop: '12px' }}>
                    <div>
                      <strong style={{ fontSize: '0.85rem', color: 'var(--accent-indigo)' }}>ISO 42001</strong>
                      <ul className="item-list" style={{ marginTop: '6px' }}>
                        {currentAssessment.compliance.iso_42001?.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <strong style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)' }}>NIST AI RMF</strong>
                      <ul className="item-list" style={{ marginTop: '6px' }}>
                        {currentAssessment.compliance.nist_ai_rmf?.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <strong style={{ fontSize: '0.85rem', color: 'var(--accent-purple)' }}>EU AI Act</strong>
                      <ul className="item-list" style={{ marginTop: '6px' }}>
                        {currentAssessment.compliance.eu_ai_act?.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Incident Response Playbook */}
                <div style={{ marginBottom: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <FileText size={18} style={{ color: 'var(--accent-indigo)' }} />
                      Incident Response Playbook
                    </h3>
                    <button className="btn-secondary" onClick={handleCopyPlaybook}>
                      {copied ? <CheckCircle2 size={14} style={{ color: 'var(--accent-emerald)' }} /> : <Copy size={14} />}
                      {copied ? 'Copied!' : 'Copy Markdown'}
                    </button>
                  </div>
                  <div className="playbook-container">
                    {currentAssessment.playbook_md}
                  </div>
                </div>

                {/* Export Actions */}
                <div className="export-actions">
                  <button className="btn-secondary" onClick={handleExportJSON}>
                    <Download size={16} /> Export Assessment JSON
                  </button>
                </div>
              </div>
            ) : (
              <div className="glass-panel" style={{ textAlign: 'center', padding: '80px 20px', color: 'var(--text-secondary)' }}>
                <Cpu size={48} style={{ color: 'var(--border-glow)', marginBottom: '16px' }} />
                <h3 style={{ color: 'var(--text-primary)', marginBottom: '8px' }}>No Active Assessment</h3>
                <p style={{ maxWidth: '400px', margin: '0 auto', fontSize: '0.9rem' }}>
                  Fill out the agent specification on the left or select a preset to run the ReAct reasoning governance classification.
                </p>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Compare Tab */
        <div className="glass-panel">
          <div className="section-header">
            <h2 className="section-title">
              <GitCompare size={20} style={{ color: 'var(--accent-cyan)' }} />
              Agent Specification Comparison
            </h2>
          </div>

          <form onSubmit={handleCompare} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '16px', alignItems: 'end', marginBottom: '32px' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">First Assessment ID</label>
              <input 
                type="text" 
                className="form-input"
                placeholder="e.g. assess_9f82a1"
                value={compareId1}
                onChange={(e) => setCompareId1(e.target.value)}
                required
              />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Second Assessment ID</label>
              <input 
                type="text" 
                className="form-input"
                placeholder="e.g. assess_3b11c4"
                value={compareId2}
                onChange={(e) => setCompareId2(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="btn-primary" style={{ height: '44px' }} disabled={compareLoading}>
              {compareLoading ? 'Comparing...' : 'Compare Agents'}
            </button>
          </form>

          {compareResult && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              <div className="dash-card">
                <h3>{compareResult.agent_1.agent_name}</h3>
                <div className={`tier-badge tier-${compareResult.agent_1.autonomy_tier}`} style={{ marginBottom: '16px' }}>
                  Tier {compareResult.agent_1.autonomy_tier}
                </div>
                <p><strong>Domain:</strong> {compareResult.agent_1.domain}</p>
                <p><strong>Scope:</strong> {compareResult.agent_1.autonomy_scope}</p>
                <p style={{ marginTop: '12px' }}><strong>Risks:</strong></p>
                <ul className="item-list">
                  {compareResult.agent_1.risks.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </div>

              <div className="dash-card">
                <h3>{compareResult.agent_2.agent_name}</h3>
                <div className={`tier-badge tier-${compareResult.agent_2.autonomy_tier}`} style={{ marginBottom: '16px' }}>
                  Tier {compareResult.agent_2.autonomy_tier}
                </div>
                <p><strong>Domain:</strong> {compareResult.agent_2.domain}</p>
                <p><strong>Scope:</strong> {compareResult.agent_2.autonomy_scope}</p>
                <p style={{ marginTop: '12px' }}><strong>Risks:</strong></p>
                <ul className="item-list">
                  {compareResult.agent_2.risks.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
