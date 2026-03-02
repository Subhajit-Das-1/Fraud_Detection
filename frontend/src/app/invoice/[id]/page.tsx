"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface InvoiceDetail {
    invoice: {
        id: number; invoice_id: string; seller_gstin: string; buyer_gstin: string;
        invoice_amount: number; cgst: number; sgst: number; igst: number;
        hsn_code: string; invoice_date: string; created_at: string;
    };
    features: {
        tax_ratio: number; avg_seller_invoice: number; deviation_from_avg: number;
        transaction_frequency: number; seller_risk_history: number;
        buyer_risk_history: number; invoice_time_gap: number;
    } | null;
    analysis: {
        rule_score: number; rule_flags: string[]; ml_score: number;
        anomaly_prediction: number; final_score: number; risk_level: string;
        analyzed_at: string;
    } | null;
}

export default function InvoiceDetailPage() {
    const params = useParams();
    const id = params?.id as string;
    const [data, setData] = useState<InvoiceDetail | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!id) return;
        fetch(`${API}/api/invoices/${id}`)
            .then(r => r.json())
            .then(setData)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [id]);

    if (loading) return <div className="loading-container"><div className="spinner"></div>Loading invoice details...</div>;
    if (!data) return <div className="loading-container">Invoice not found</div>;

    const { invoice, features, analysis } = data;
    const totalTax = invoice.cgst + invoice.sgst + invoice.igst;

    const scoreBreakdown = analysis ? [
        { name: "Rule Score", value: analysis.rule_score, fill: "#f59e0b" },
        { name: "ML Score", value: analysis.ml_score, fill: "#8b5cf6" },
        { name: "Final Score", value: analysis.final_score, fill: analysis.risk_level === "High" ? "#ef4444" : analysis.risk_level === "Medium" ? "#f59e0b" : "#10b981" },
    ] : [];

    const getRiskClass = (level: string) => level?.toLowerCase() || "low";

    return (
        <div className="animate-in">
            <Link href="/invoices" className="back-link">← Back to Invoices</Link>

            {/* Header with Risk Badge */}
            <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                    <h2>Invoice {invoice.invoice_id}</h2>
                    <p className="subtitle">Created {invoice.created_at ? new Date(invoice.created_at).toLocaleString() : "—"}</p>
                </div>
                {analysis && (
                    <span className={`risk-badge ${getRiskClass(analysis.risk_level)}`} style={{ fontSize: "14px", padding: "8px 20px" }}>
                        <span className="badge-dot"></span>
                        {analysis.risk_level} Risk
                    </span>
                )}
            </div>

            {/* Invoice Details + Score Gauge */}
            <div className="detail-grid">
                <div className="detail-card animate-in stagger-1">
                    <h3>📄 Invoice Details</h3>
                    <div className="detail-row">
                        <span className="detail-label">Invoice ID</span>
                        <span className="detail-value">{invoice.invoice_id}</span>
                    </div>
                    <div className="detail-row">
                        <span className="detail-label">Seller GSTIN</span>
                        <span className="detail-value" style={{ fontFamily: "monospace" }}>{invoice.seller_gstin}</span>
                    </div>
                    <div className="detail-row">
                        <span className="detail-label">Buyer GSTIN</span>
                        <span className="detail-value" style={{ fontFamily: "monospace" }}>{invoice.buyer_gstin}</span>
                    </div>
                    <div className="detail-row">
                        <span className="detail-label">Amount</span>
                        <span className="detail-value">₹{invoice.invoice_amount.toLocaleString()}</span>
                    </div>
                    <div className="detail-row">
                        <span className="detail-label">CGST / SGST / IGST</span>
                        <span className="detail-value">₹{invoice.cgst.toLocaleString()} / ₹{invoice.sgst.toLocaleString()} / ₹{invoice.igst.toLocaleString()}</span>
                    </div>
                    <div className="detail-row">
                        <span className="detail-label">Total Tax</span>
                        <span className="detail-value">₹{totalTax.toLocaleString()}</span>
                    </div>
                    <div className="detail-row">
                        <span className="detail-label">HSN Code</span>
                        <span className="detail-value">{invoice.hsn_code || "—"}</span>
                    </div>
                    <div className="detail-row">
                        <span className="detail-label">Invoice Date</span>
                        <span className="detail-value">{invoice.invoice_date ? new Date(invoice.invoice_date).toLocaleDateString() : "—"}</span>
                    </div>
                </div>

                {/* Risk Score Gauge */}
                {analysis && (
                    <div className="detail-card animate-in stagger-2">
                        <h3>🎯 Risk Score</h3>
                        <div className="score-gauge">
                            <div
                                className={`gauge-circle ${getRiskClass(analysis.risk_level)}`}
                                style={{ "--pct": `${analysis.final_score}%` } as React.CSSProperties}
                            >
                                <span>{analysis.final_score.toFixed(0)}</span>
                            </div>
                            <div className="gauge-label">{analysis.risk_level} Risk — Score {analysis.final_score.toFixed(1)}/100</div>
                        </div>

                        {/* Score Breakdown Bars */}
                        <div className="score-breakdown">
                            <div className="score-bar-row">
                                <span className="score-bar-label">Rule Score</span>
                                <div className="score-bar-track">
                                    <div className="score-bar-fill" style={{ width: `${analysis.rule_score}%`, background: "linear-gradient(90deg, #f59e0b, #f97316)" }}></div>
                                </div>
                                <span className="score-bar-value" style={{ color: "#f59e0b" }}>{analysis.rule_score.toFixed(0)}</span>
                            </div>
                            <div className="score-bar-row">
                                <span className="score-bar-label">ML Score</span>
                                <div className="score-bar-track">
                                    <div className="score-bar-fill" style={{ width: `${analysis.ml_score}%`, background: "linear-gradient(90deg, #8b5cf6, #ec4899)" }}></div>
                                </div>
                                <span className="score-bar-value" style={{ color: "#8b5cf6" }}>{analysis.ml_score.toFixed(0)}</span>
                            </div>
                            <div className="score-bar-row">
                                <span className="score-bar-label">Final Score</span>
                                <div className="score-bar-track">
                                    <div className="score-bar-fill" style={{
                                        width: `${analysis.final_score}%`,
                                        background: analysis.risk_level === "High" ? "linear-gradient(90deg, #ef4444, #dc2626)" :
                                            analysis.risk_level === "Medium" ? "linear-gradient(90deg, #f59e0b, #f97316)" :
                                                "linear-gradient(90deg, #10b981, #06b6d4)"
                                    }}></div>
                                </div>
                                <span className="score-bar-value" style={{
                                    color: analysis.risk_level === "High" ? "#ef4444" : analysis.risk_level === "Medium" ? "#f59e0b" : "#10b981"
                                }}>{analysis.final_score.toFixed(0)}</span>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Rule Flags + Score Chart + Features */}
            <div className="detail-grid">
                {/* Rule Flags */}
                {analysis && (
                    <div className="detail-card animate-in stagger-3">
                        <h3>🚩 Rule Triggers ({analysis.rule_flags?.length || 0})</h3>
                        {analysis.rule_flags && analysis.rule_flags.length > 0 ? (
                            <div className="flag-list">
                                {analysis.rule_flags.map((flag, idx) => (
                                    <div key={idx} className="flag-item">
                                        <span className="flag-icon">⚠️</span>
                                        <span>{flag}</span>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p style={{ color: "var(--text-muted)", fontSize: "14px", padding: "12px 0" }}>
                                ✅ No rule violations detected
                            </p>
                        )}
                    </div>
                )}

                {/* Score Breakdown Chart */}
                {analysis && (
                    <div className="detail-card animate-in stagger-4">
                        <h3>📊 Score Breakdown</h3>
                        <ResponsiveContainer width="100%" height={250}>
                            <BarChart data={scoreBreakdown} layout="vertical" margin={{ left: 20 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" />
                                <XAxis type="number" domain={[0, 100]} stroke="#64748b" fontSize={11} />
                                <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={12} width={90} />
                                <Tooltip
                                    contentStyle={{
                                        background: "#1a2035",
                                        border: "1px solid rgba(148,163,184,0.1)",
                                        borderRadius: "8px",
                                        color: "#f1f5f9",
                                    }}
                                />
                                <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={28}>
                                    {scoreBreakdown.map((entry, idx) => (
                                        <Cell key={idx} fill={entry.fill} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                )}
            </div>

            {/* Engineered Features */}
            {features && (
                <div className="detail-card animate-in stagger-4" style={{ marginBottom: "32px" }}>
                    <h3>🧪 Engineered Features</h3>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px" }}>
                        {[
                            { label: "Tax Ratio", value: `${(features.tax_ratio * 100).toFixed(1)}%` },
                            { label: "Avg Seller Invoice", value: `₹${features.avg_seller_invoice.toLocaleString()}` },
                            { label: "Deviation from Avg", value: `${(features.deviation_from_avg * 100).toFixed(1)}%` },
                            { label: "Tx Frequency (30d)", value: features.transaction_frequency },
                            { label: "Seller Risk History", value: features.seller_risk_history.toFixed(1) },
                            { label: "Buyer Risk History", value: features.buyer_risk_history.toFixed(1) },
                            { label: "Invoice Time Gap", value: `${features.invoice_time_gap.toFixed(1)} days` },
                        ].map((feat, idx) => (
                            <div key={idx} className="detail-row" style={{ flexDirection: "column", alignItems: "flex-start", gap: "4px" }}>
                                <span className="detail-label">{feat.label}</span>
                                <span className="detail-value">{feat.value}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {!analysis && (
                <div className="detail-card" style={{ textAlign: "center", padding: "48px" }}>
                    <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>
                        ⏳ This invoice hasn't been analyzed yet. Run the fraud analysis from the Dashboard.
                    </p>
                </div>
            )}
        </div>
    );
}
