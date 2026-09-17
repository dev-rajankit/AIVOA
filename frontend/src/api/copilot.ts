import { CopilotMessageRequest, CopilotMessageResponse } from "../types/copilot";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function sendCopilotMessage(
  request: CopilotMessageRequest
): Promise<CopilotMessageResponse> {
  let response: Response;
  
  try {
    response = await fetch(`${API_BASE_URL}/api/copilot/message`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });
  } catch (error) {
    // Network failure (TypeError typically thrown by fetch when server is unreachable)
    throw new Error("Unable to connect to the server. Please try again.");
  }

  if (!response.ok) {
    if (response.status >= 500) {
      // 5xx Server errors
      throw new Error("An unexpected server error occurred. Please try again.");
    } else if (response.status >= 400 && response.status < 500) {
      // 4xx Client/Validation errors
      try {
        const errorData = await response.json();
        // FastAPI returns validation errors in a "detail" array or string
        if (errorData.detail) {
          const message = Array.isArray(errorData.detail)
            ? errorData.detail.map((e: any) => e.msg || e.type).join(", ")
            : errorData.detail;
          throw new Error(`Validation Error: ${message}`);
        }
      } catch (e) {
        // Fallback if parsing json fails or we already threw an Error inside the try block
        if (e instanceof Error && e.message.startsWith("Validation Error")) {
          throw e;
        }
      }
      throw new Error(`API error: ${response.statusText}`);
    }
  }

  return response.json();
}
