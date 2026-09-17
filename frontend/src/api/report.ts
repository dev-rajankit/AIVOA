import { ComplaintFields, RiskAssessment } from "../types/complaint";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

interface ReportRequest {
  complaint_id: string;
  complaint: ComplaintFields;
  risk?: RiskAssessment | null;
}

interface EmailReportRequest extends ReportRequest {
  recipient_email: string;
}

export async function downloadPdfReport(
  complaint_id: string,
  complaint: ComplaintFields,
  risk: RiskAssessment | null
): Promise<void> {
  const request: ReportRequest = {
    complaint_id,
    complaint,
    risk,
  };

  const response = await fetch(`${API_BASE_URL}/api/report/pdf`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error("Failed to generate PDF report.");
  }

  // Handle file download
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `AIVOA_${complaint_id}_report.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function emailPdfReport(
  complaint_id: string,
  recipient_email: string,
  complaint: ComplaintFields,
  risk: RiskAssessment | null
): Promise<{ status: string; message: string }> {
  const request: EmailReportRequest = {
    complaint_id,
    recipient_email,
    complaint,
    risk,
  };

  const response = await fetch(`${API_BASE_URL}/api/report/email`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || "Failed to send email report.");
  }

  return response.json();
}
