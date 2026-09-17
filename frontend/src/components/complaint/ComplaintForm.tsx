import React, { useState } from "react";
import { useSelector } from "react-redux";
import { ComplaintField } from "./ComplaintField";
import { saveComplaint } from "../../api/complaint";
import { RootState } from "../../app/store";

export const ComplaintForm: React.FC = () => {
  const complaintId = useSelector((state: RootState) => state.complaintForm.complaintId);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const handleReset = () => {
    // A complete reload ensures all Redux state is wiped clean and a new session ID is generated
    window.location.reload();
  };

  const handleSave = async () => {
    if (!complaintId) {
      setSaveStatus("No complaint data to save yet.");
      setTimeout(() => setSaveStatus(null), 3000);
      return;
    }
    
    try {
      await saveComplaint(complaintId);
      setSaveStatus("Complaint stored successfully!");
    } catch (err) {
      setSaveStatus("Failed to store complaint.");
    }
    
    setTimeout(() => setSaveStatus(null), 3000);
  };

  return (
    <div className="complaint-form-container">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <h2>Complaint Structured Data</h2>
      </div>



      <p className="form-helper-text">
        Complaint fields are populated and updated by the Copilot.
      </p>

      <section className="form-section">
        <h3>Complaint Information</h3>
        <div className="field-grid">
          <ComplaintField label="Complaint Source" fieldKey="complaint_source" />
          <ComplaintField label="Complaint Date" fieldKey="complaint_date" />
          <ComplaintField label="Complaint Type" fieldKey="complaint_type" />
        </div>
        <div className="field-full">
          <ComplaintField
            label="Detailed Description"
            fieldKey="detailed_description"
            isTextArea
          />
        </div>
      </section>

      <section className="form-section">
        <h3>Product Information</h3>
        <div className="field-grid">
          <ComplaintField label="Product Name" fieldKey="product_name" />
          <ComplaintField
            label="Strength / Grade"
            fieldKey="product_strength_grade"
          />
          <ComplaintField label="Dosage Form" fieldKey="dosage_form" />
          <ComplaintField label="Batch / Lot Number" fieldKey="batch_lot_number" />
          <ComplaintField label="Affected Quantity" fieldKey="affected_quantity" />
        </div>
      </section>

      <section className="form-section">
        <h3>Manufacturing Information</h3>
        <div className="field-grid">
          <ComplaintField label="Manufacturing Date" fieldKey="manufacturing_date" />
          <ComplaintField label="Expiry Date" fieldKey="expiry_date" />
        </div>
      </section>

      <section className="form-section">
        <h3>Customer Information</h3>
        <div className="field-grid">
          <ComplaintField label="Customer Name" fieldKey="customer_name" />
        </div>
      </section>

      {saveStatus && (
        <div style={{ padding: "0.75rem", backgroundColor: saveStatus.includes("Failed") || saveStatus.includes("No complaint") ? "#fed7d7" : "#c6f6d5", color: saveStatus.includes("Failed") || saveStatus.includes("No complaint") ? "#c53030" : "#22543d", borderRadius: "4px", marginTop: "1rem", marginBottom: "1rem", fontSize: "0.875rem" }}>
          {saveStatus}
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "space-between", marginTop: "1.5rem", borderTop: "1px solid #e2e8f0", paddingTop: "1.5rem" }}>
        <button 
          onClick={handleReset}
          style={{ padding: "0.5rem 1rem", backgroundColor: "#e2e8f0", border: "1px solid #cbd5e0", borderRadius: "4px", cursor: "pointer", fontWeight: 600, color: "#4a5568" }}
        >
          Reset Form
        </button>
        <button 
          onClick={handleSave}
          style={{ padding: "0.5rem 1rem", backgroundColor: "#3182ce", border: "none", borderRadius: "4px", cursor: "pointer", fontWeight: 600, color: "white" }}
        >
          Save Complaint
        </button>
      </div>
    </div>
  );
};
