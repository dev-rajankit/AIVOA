import React from "react";
import { ComplaintField } from "./ComplaintField";

export const ComplaintForm: React.FC = () => {
  return (
    <div className="complaint-form-container">
      <h2>Complaint Structured Data</h2>
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
    </div>
  );
};
