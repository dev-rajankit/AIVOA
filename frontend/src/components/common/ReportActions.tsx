import React, { useState } from "react";
import { useAppSelector } from "../../app/hooks";
import { downloadPdfReport, emailPdfReport } from "../../api/report";

export const ReportActions: React.FC = () => {
  const { currentForm } = useAppSelector((state) => state.complaintForm);
  const { currentRisk } = useAppSelector((state) => state.riskAssessment);
  const sessionId = useAppSelector((state) => state.session.sessionId);

  const [email, setEmail] = useState("");
  const [loadingPdf, setLoadingPdf] = useState(false);
  const [loadingEmail, setLoadingEmail] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Derive a simple complaint ID from session if none exists
  const complaintId = sessionId.substring(0, 8).toUpperCase();

  const handleDownload = async () => {
    setLoadingPdf(true);
    setMessage(null);
    try {
      await downloadPdfReport(complaintId, currentForm, currentRisk);
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Failed to download PDF." });
    } finally {
      setLoadingPdf(false);
    }
  };

  const handleEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setLoadingEmail(true);
    setMessage(null);
    try {
      const response = await emailPdfReport(complaintId, email, currentForm, currentRisk);
      setMessage({ type: "success", text: response.message });
      setEmail("");
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Failed to send email." });
    } finally {
      setLoadingEmail(false);
    }
  };

  return (
    <div className="report-actions" style={{ marginTop: "1rem", padding: "1rem", backgroundColor: "#f9f9f9", borderRadius: "8px" }}>
      <h3 style={{ marginTop: 0 }}>Report Actions</h3>
      
      <button 
        onClick={handleDownload} 
        disabled={loadingPdf}
        style={{ marginBottom: "1rem", width: "100%", padding: "0.5rem" }}
      >
        {loadingPdf ? "Generating PDF..." : "Download PDF Report"}
      </button>

      <form onSubmit={handleEmail} style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        <input 
          type="email" 
          placeholder="Recipient Email" 
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={{ padding: "0.5rem" }}
        />
        <button 
          type="submit" 
          disabled={loadingEmail || !email}
          style={{ padding: "0.5rem" }}
        >
          {loadingEmail ? "Sending..." : "Email Report"}
        </button>
      </form>

      {message && (
        <div style={{ 
          marginTop: "1rem", 
          padding: "0.5rem", 
          borderRadius: "4px",
          backgroundColor: message.type === "success" ? "#d4edda" : "#f8d7da",
          color: message.type === "success" ? "#155724" : "#721c24"
        }}>
          {message.text}
        </div>
      )}
    </div>
  );
};
