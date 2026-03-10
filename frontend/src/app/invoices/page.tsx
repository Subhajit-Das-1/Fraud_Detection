"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";

import { api } from "@/lib/api";

interface InvoiceItem {
    id: number;
    invoice_id: string;
    seller_gstin: string;
    buyer_gstin: string;
    invoice_amount: number;
    total_tax: number;
    invoice_date: string | null;
    risk_level: string | null;
    final_score: number | null;
}

export default function InvoicesPage() {
    const [invoices, setInvoices] = useState<InvoiceItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [filter, setFilter] = useState("");
    const [tab, setTab] = useState<"list" | "upload" | "manual">("list");
    const [uploading, setUploading] = useState(false);
    const [uploadMsg, setUploadMsg] = useState("");
    const fileRef = useRef<HTMLInputElement>(null);

    // Manual form state
    const [form, setForm] = useState({
        invoice_id: "", seller_gstin: "", buyer_gstin: "",
        invoice_amount: "", cgst: "", sgst: "", igst: "",
        hsn_code: "", invoice_date: "",
    });

    const fetchInvoices = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (search) params.set("search", search);
            if (filter) params.set("risk_level", filter);
            const data = await api.get<{ invoices: InvoiceItem[] }>(`/api/invoices?${params}&limit=100`);
            setInvoices(data.invoices || []);
        } catch (e) { console.error(e); }
        setLoading(false);
    };

    useEffect(() => { fetchInvoices(); }, [search, filter]);

    const handleUpload = async (file: File) => {
        setUploading(true);
        setUploadMsg("");
        const fd = new FormData();
        fd.append("file", file);
        try {
            const data = await api.post<{ uploaded: number, errors: any[] }>("/api/invoices/upload-csv", fd);
            setUploadMsg(`✅ Uploaded ${data.uploaded} invoices. ${data.errors?.length || 0} errors.`);
            fetchInvoices();
        } catch (e) {
            setUploadMsg("❌ Upload failed");
        }
        setUploading(false);
    };

    const handleManualSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const body = {
                ...form,
                invoice_amount: parseFloat(form.invoice_amount) || 0,
                cgst: parseFloat(form.cgst) || 0,
                sgst: parseFloat(form.sgst) || 0,
                igst: parseFloat(form.igst) || 0,
                invoice_date: form.invoice_date ? new Date(form.invoice_date).toISOString() : null,
            };
            await api.post("/api/invoices", body);
            setForm({ invoice_id: "", seller_gstin: "", buyer_gstin: "", invoice_amount: "", cgst: "", sgst: "", igst: "", hsn_code: "", invoice_date: "" });
            setTab("list");
            fetchInvoices();
        } catch (e) { console.error(e); }
    };

    const getRiskBadge = (level: string | null) => {
        if (!level) return <span className="risk-badge low"><span className="badge-dot"></span>Pending</span>;
        const cls = level.toLowerCase();
        return (
            <span className={`risk-badge ${cls}`}>
                <span className="badge-dot"></span>
                {level}
            </span>
        );
    };

    return (
        <div className="animate-in">
            <div className="page-header">
                <h2>📄 Invoice Management</h2>
                <p className="subtitle">Upload, view, and analyze GST invoices</p>
            </div>

            {/* Tabs */}
            <div className="tab-bar">
                <button className={`tab-item ${tab === "list" ? "active" : ""}`} onClick={() => setTab("list")}>📋 Invoice List</button>
                <button className={`tab-item ${tab === "upload" ? "active" : ""}`} onClick={() => setTab("upload")}>📤 CSV Upload</button>
                <button className={`tab-item ${tab === "manual" ? "active" : ""}`} onClick={() => setTab("manual")}>✏️ Manual Entry</button>
            </div>

            {/* CSV Upload Tab */}
            {tab === "upload" && (
                <div className="animate-in">
                    <div
                        className="upload-zone"
                        onClick={() => fileRef.current?.click()}
                        onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add("dragover"); }}
                        onDragLeave={(e) => e.currentTarget.classList.remove("dragover")}
                        onDrop={(e) => {
                            e.preventDefault();
                            e.currentTarget.classList.remove("dragover");
                            const file = e.dataTransfer.files[0];
                            if (file) handleUpload(file);
                        }}
                    >
                        <div className="icon">📁</div>
                        <h4>{uploading ? "Uploading..." : "Drop CSV file here or click to browse"}</h4>
                        <p>Accepts .csv files with columns: invoice_id, seller_gstin, buyer_gstin, invoice_amount, cgst, sgst, igst, hsn_code, invoice_date</p>
                        <input
                            ref={fileRef}
                            type="file"
                            accept=".csv"
                            style={{ display: "none" }}
                            onChange={(e) => {
                                const file = e.target.files?.[0];
                                if (file) handleUpload(file);
                            }}
                        />
                    </div>
                    {uploadMsg && <p style={{ marginTop: "16px", fontSize: "14px", color: "var(--accent-green)" }}>{uploadMsg}</p>}
                </div>
            )}

            {/* Manual Entry Tab */}
            {tab === "manual" && (
                <div className="animate-in">
                    <div className="detail-card">
                        <h3>✏️ New Invoice</h3>
                        <form onSubmit={handleManualSubmit}>
                            <div className="form-grid">
                                <div className="form-group">
                                    <label>Invoice ID</label>
                                    <input value={form.invoice_id} onChange={(e) => setForm({ ...form, invoice_id: e.target.value })} required placeholder="INV-2024-000001" />
                                </div>
                                <div className="form-group">
                                    <label>Seller GSTIN</label>
                                    <input value={form.seller_gstin} onChange={(e) => setForm({ ...form, seller_gstin: e.target.value })} required placeholder="29ABCDE1234F1Z5" />
                                </div>
                                <div className="form-group">
                                    <label>Buyer GSTIN</label>
                                    <input value={form.buyer_gstin} onChange={(e) => setForm({ ...form, buyer_gstin: e.target.value })} required placeholder="27XYZAB5678G1Z3" />
                                </div>
                                <div className="form-group">
                                    <label>Invoice Amount (₹)</label>
                                    <input type="number" step="0.01" value={form.invoice_amount} onChange={(e) => setForm({ ...form, invoice_amount: e.target.value })} required placeholder="50000" />
                                </div>
                                <div className="form-group">
                                    <label>CGST (₹)</label>
                                    <input type="number" step="0.01" value={form.cgst} onChange={(e) => setForm({ ...form, cgst: e.target.value })} placeholder="4500" />
                                </div>
                                <div className="form-group">
                                    <label>SGST (₹)</label>
                                    <input type="number" step="0.01" value={form.sgst} onChange={(e) => setForm({ ...form, sgst: e.target.value })} placeholder="4500" />
                                </div>
                                <div className="form-group">
                                    <label>IGST (₹)</label>
                                    <input type="number" step="0.01" value={form.igst} onChange={(e) => setForm({ ...form, igst: e.target.value })} placeholder="0" />
                                </div>
                                <div className="form-group">
                                    <label>HSN Code</label>
                                    <input value={form.hsn_code} onChange={(e) => setForm({ ...form, hsn_code: e.target.value })} placeholder="8471" />
                                </div>
                                <div className="form-group">
                                    <label>Invoice Date</label>
                                    <input type="date" value={form.invoice_date} onChange={(e) => setForm({ ...form, invoice_date: e.target.value })} />
                                </div>
                            </div>
                            <div style={{ marginTop: "20px", display: "flex", gap: "12px" }}>
                                <button type="submit" className="btn btn-primary">💾 Save Invoice</button>
                                <button type="button" className="btn btn-secondary" onClick={() => setTab("list")}>Cancel</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Invoice List Tab */}
            {tab === "list" && (
                <div className="data-table-container animate-in">
                    <div className="table-header">
                        <h3>All Invoices ({invoices.length})</h3>
                        <div className="table-actions">
                            <input
                                className="search-input"
                                placeholder="🔍 Search by ID, GSTIN..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                            />
                            <select
                                className="search-input"
                                style={{ width: "140px" }}
                                value={filter}
                                onChange={(e) => setFilter(e.target.value)}
                            >
                                <option value="">All Risks</option>
                                <option value="High">🔴 High</option>
                                <option value="Medium">🟡 Medium</option>
                                <option value="Low">🟢 Low</option>
                            </select>
                        </div>
                    </div>

                    {loading ? (
                        <div className="loading-container">
                            <div className="spinner"></div>
                            Loading invoices...
                        </div>
                    ) : (
                        <table>
                            <thead>
                                <tr>
                                    <th>Invoice ID</th>
                                    <th>Seller GSTIN</th>
                                    <th>Buyer GSTIN</th>
                                    <th>Amount</th>
                                    <th>Tax</th>
                                    <th>Date</th>
                                    <th>Risk</th>
                                    <th>Score</th>
                                </tr>
                            </thead>
                            <tbody>
                                {invoices.map((inv) => (
                                    <tr key={inv.id}>
                                        <td>
                                            <Link href={`/invoice/${inv.id}`} style={{ color: "var(--accent-blue)" }}>
                                                {inv.invoice_id}
                                            </Link>
                                        </td>
                                        <td style={{ fontFamily: "monospace", fontSize: "12px" }}>{inv.seller_gstin}</td>
                                        <td style={{ fontFamily: "monospace", fontSize: "12px" }}>{inv.buyer_gstin}</td>
                                        <td>₹{inv.invoice_amount?.toLocaleString()}</td>
                                        <td>₹{inv.total_tax?.toLocaleString()}</td>
                                        <td>{inv.invoice_date ? new Date(inv.invoice_date).toLocaleDateString() : "—"}</td>
                                        <td>{getRiskBadge(inv.risk_level)}</td>
                                        <td style={{ fontWeight: 700 }}>{inv.final_score !== null ? inv.final_score.toFixed(1) : "—"}</td>
                                    </tr>
                                ))}
                                {invoices.length === 0 && (
                                    <tr>
                                        <td colSpan={8} style={{ textAlign: "center", padding: "48px", color: "var(--text-muted)" }}>
                                            No invoices found. Generate sample data or upload a CSV to get started.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    )}
                </div>
            )}
        </div>
    );
}
