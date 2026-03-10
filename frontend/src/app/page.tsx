"use client";

import { useEffect, useState } from "react";
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Legend,
  ScatterChart, Scatter, ZAxis,
} from "recharts";

import { api } from "@/lib/api";

const RISK_COLORS: Record<string, string> = {
  High: "#ef4444",
  Medium: "#f59e0b",
  Low: "#10b981",
};

interface Stats {
  total_invoices: number;
  high_risk: number;
  medium_risk: number;
  low_risk: number;
  fraud_percentage: number;
  total_amount: number;
  flagged_amount: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [riskDist, setRiskDist] = useState<any[]>([]);
  const [riskTrend, setRiskTrend] = useState<any[]>([]);
  const [heatmap, setHeatmap] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [showResetModal, setShowResetModal] = useState(false);
  const [resetting, setResetting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [s, d, t, h] = await Promise.all([
        api.get<Stats>("/api/dashboard/stats"),
        api.get<any[]>("/api/dashboard/risk-distribution"),
        api.get<any[]>("/api/dashboard/risk-trend"),
        api.get<any[]>("/api/dashboard/seller-heatmap"),
      ]);
      setStats(s);
      setRiskDist(d);
      setRiskTrend(t);
      setHeatmap(h);
    } catch (e) {
      console.error("Error fetching dashboard data:", e);
    }
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  const generateData = async () => {
    setGenerating(true);
    try {
      await api.post("/api/generate-data");
      await fetchData();
    } catch (e) { console.error(e); }
    setGenerating(false);
  };

  const runAnalysis = async () => {
    setAnalyzing(true);
    try {
      await api.post("/api/analyze");
      await fetchData();
    } catch (e) { console.error(e); }
    setAnalyzing(false);
  };

  const resetData = async () => {
    setResetting(true);
    try {
      await api.delete("/api/reset-data");
      setShowResetModal(false);
      await fetchData();
    } catch (e) { console.error(e); }
    setResetting(false);
  };

  if (loading) return (
    <div className="loading-container">
      <div className="spinner"></div>
      Loading dashboard...
    </div>
  );

  return (
    <div className="animate-in">
      <div className="page-header">
        <h2>📊 Fraud Detection Dashboard</h2>
        <p className="subtitle">Real-time overview of GST invoice fraud analysis</p>
      </div>

      {/* Action Buttons */}
      <div className="actions-bar">
        <button className="btn btn-primary" onClick={generateData} disabled={generating}>
          {generating ? "⏳ Generating..." : "🎲 Generate Sample Data"}
        </button>
        <button className="btn btn-success" onClick={runAnalysis} disabled={analyzing}>
          {analyzing ? "⏳ Analyzing..." : "🔍 Run Fraud Analysis"}
        </button>
        <button className="btn btn-secondary" onClick={fetchData}>
          🔄 Refresh
        </button>
        <button className="btn btn-danger" onClick={() => setShowResetModal(true)} disabled={resetting}>
          🗑️ Reset All Data
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card blue animate-in stagger-1">
            <div className="label">Total Invoices</div>
            <div className="value">{stats.total_invoices.toLocaleString()}</div>
            <div className="sub">₹{(stats.total_amount / 100000).toFixed(1)}L total value</div>
            <div className="icon-bg">📄</div>
          </div>
          <div className="stat-card red animate-in stagger-2">
            <div className="label">High Risk</div>
            <div className="value">{stats.high_risk}</div>
            <div className="sub">Immediate review needed</div>
            <div className="icon-bg">🚨</div>
          </div>
          <div className="stat-card orange animate-in stagger-3">
            <div className="label">Medium Risk</div>
            <div className="value">{stats.medium_risk}</div>
            <div className="sub">Under investigation</div>
            <div className="icon-bg">⚠️</div>
          </div>
          <div className="stat-card purple animate-in stagger-4">
            <div className="label">Fraud Percentage</div>
            <div className="value">{stats.fraud_percentage}%</div>
            <div className="sub">₹{(stats.flagged_amount / 100000).toFixed(1)}L flagged</div>
            <div className="icon-bg">📈</div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="charts-grid">
        {/* Risk Distribution Pie */}
        <div className="chart-card animate-in stagger-2">
          <h3><span className="dot"></span>Risk Distribution</h3>
          {riskDist.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={riskDist}
                  cx="50%"
                  cy="50%"
                  innerRadius={70}
                  outerRadius={110}
                  paddingAngle={4}
                  dataKey="count"
                  nameKey="risk_level"
                  stroke="none"
                >
                  {riskDist.map((entry: any, idx: number) => (
                    <Cell key={idx} fill={RISK_COLORS[entry.risk_level] || "#64748b"} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "#1a2035",
                    border: "1px solid rgba(148,163,184,0.1)",
                    borderRadius: "8px",
                    color: "#f1f5f9",
                    fontSize: "13px",
                  }}
                />
                <Legend
                  formatter={(value: string) => <span style={{ color: "#94a3b8", fontSize: "13px" }}>{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="loading-container">No data — generate & analyze first</div>
          )}
        </div>

        {/* Risk Trend Line */}
        <div className="chart-card animate-in stagger-3">
          <h3><span className="dot" style={{ background: "#8b5cf6" }}></span>Risk Trend Over Time</h3>
          {riskTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={riskTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" />
                <XAxis
                  dataKey="date"
                  stroke="#64748b"
                  fontSize={11}
                  tickFormatter={(d: string) => d.slice(5)}
                />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    background: "#1a2035",
                    border: "1px solid rgba(148,163,184,0.1)",
                    borderRadius: "8px",
                    color: "#f1f5f9",
                    fontSize: "13px",
                  }}
                />
                <Line type="monotone" dataKey="high" stroke="#ef4444" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="medium" stroke="#f59e0b" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="low" stroke="#10b981" strokeWidth={2} dot={false} />
                <Legend
                  formatter={(value: string) => <span style={{ color: "#94a3b8", fontSize: "13px" }}>{value}</span>}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="loading-container">No data — generate & analyze first</div>
          )}
        </div>

        {/* Seller Heatmap / Scatter */}
        <div className="chart-card animate-in stagger-4" style={{ gridColumn: "1 / -1" }}>
          <h3><span className="dot" style={{ background: "#ec4899" }}></span>Seller Risk Heatmap</h3>
          {heatmap.length > 0 ? (
            <ResponsiveContainer width="100%" height={350}>
              <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" />
                <XAxis
                  type="number"
                  dataKey="invoice_count"
                  name="Invoices"
                  stroke="#64748b"
                  fontSize={11}
                  label={{ value: "Invoice Count", position: "bottom", fill: "#64748b", fontSize: 12 }}
                />
                <YAxis
                  type="number"
                  dataKey="avg_risk_score"
                  name="Avg Risk"
                  stroke="#64748b"
                  fontSize={11}
                  label={{ value: "Avg Risk Score", angle: -90, position: "insideLeft", fill: "#64748b", fontSize: 12 }}
                />
                <ZAxis type="number" dataKey="total_amount" range={[50, 500]} name="Total Amount" />
                <Tooltip
                  contentStyle={{
                    background: "#1a2035",
                    border: "1px solid rgba(148,163,184,0.1)",
                    borderRadius: "8px",
                    color: "#f1f5f9",
                    fontSize: "13px",
                  }}
                  formatter={(value: any, name?: string) => {
                    if (name === "Total Amount") return [`₹${Number(value).toLocaleString()}`, name];
                    return [value, name || ""];
                  }}
                  labelFormatter={(label: any) => `GSTIN: ${label}`}
                />
                <Scatter data={heatmap} fill="#3b82f6">
                  {heatmap.map((entry: any, idx: number) => (
                    <Cell key={idx} fill={RISK_COLORS[entry.risk_level] || "#64748b"} fillOpacity={0.8} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          ) : (
            <div className="loading-container">No data — generate & analyze first</div>
          )}
        </div>
      </div>

      {/* Reset Confirmation Modal */}
      {showResetModal && (
        <div className="modal-overlay" onClick={() => !resetting && setShowResetModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-icon">⚠️</div>
            <h3 className="modal-title">Reset All Data?</h3>
            <p className="modal-desc">
              This will permanently delete <strong>all invoices</strong>, <strong>engineered features</strong>,
              <strong> fraud analyses</strong>, and the <strong>trained ML model</strong>. This action cannot be undone.
            </p>
            <div className="modal-actions">
              <button
                className="btn btn-secondary"
                onClick={() => setShowResetModal(false)}
                disabled={resetting}
              >
                Cancel
              </button>
              <button
                className="btn btn-danger"
                onClick={resetData}
                disabled={resetting}
              >
                {resetting ? "⏳ Deleting..." : "🗑️ Yes, Delete Everything"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
