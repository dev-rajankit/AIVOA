import { ComplaintFields, RiskAssessment } from "./complaint";

export type CopilotMessageRequest = {
  session_id: string;
  message: string;
  input_type?: "text" | "document";
  current_form?: ComplaintFields;
};

export type CopilotMessageResponse = {
  assistant_reply: string;
  form_patch?: ComplaintFields;
  risk_patch?: RiskAssessment;
  changed_fields: string[];
  completeness_pct: number;
  missing_fields: string[];
  intent: string;
};
