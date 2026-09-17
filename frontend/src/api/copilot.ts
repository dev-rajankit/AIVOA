import { CopilotMessageRequest, CopilotMessageResponse } from "../types/copilot";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function sendCopilotMessage(
  request: CopilotMessageRequest
): Promise<CopilotMessageResponse> {
  const response = await fetch(`${API_BASE_URL}/api/copilot/message`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}
