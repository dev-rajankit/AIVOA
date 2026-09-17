const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function getComplaint(id: string) {
  const response = await fetch(`${API_BASE_URL}/api/complaints/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch complaint: ${response.statusText}`);
  }
  return response.json();
}

export async function getComplaintAuditLog(id: string) {
  const response = await fetch(`${API_BASE_URL}/api/complaints/${id}/audit`);
  if (!response.ok) {
    throw new Error(`Failed to fetch audit log: ${response.statusText}`);
  }
  return response.json();
}
