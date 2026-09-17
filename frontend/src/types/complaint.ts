export type ComplaintFields = {
  complaint_source?: string;
  customer_name?: string;
  product_name?: string;
  product_strength_grade?: string;
  batch_lot_number?: string;
  affected_quantity?: string;
  manufacturing_date?: string;
  expiry_date?: string;
  dosage_form?: "API" | "FDF";
  complaint_type?: string;
  complaint_date?: string;
  detailed_description?: string;
};

export type RiskAssessment = {
  severity?: "Minor" | "Major" | "Critical";
  occurrence?: number;
  detectability?: number;
  rpn?: number;
  recommended_action?: string;
  root_cause_hint?: string;
  capa_recommendation?: string;
  regulatory_flag?: boolean;
  ai_reasoning_summary?: string;
};

export type DuplicateStatus = "UNIQUE" | "POSSIBLE_DUPLICATE" | "DUPLICATE";

export type DuplicateMatch = {
  similarity_score: number;
  matched_complaint_id: string;
  matched_complaint_summary?: string;
};
