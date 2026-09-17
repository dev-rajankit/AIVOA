import React from "react";
import { useAppSelector } from "../../app/hooks";

interface ComplaintFieldProps {
  label: string;
  fieldKey: string;
  isTextArea?: boolean;
}

export const ComplaintField: React.FC<ComplaintFieldProps> = ({
  label,
  fieldKey,
  isTextArea = false,
}) => {
  const { currentForm, changedFields } = useAppSelector(
    (state) => state.complaintForm
  );

  const value = currentForm[fieldKey as keyof typeof currentForm] || "";
  const isChanged = changedFields.includes(fieldKey);

  const className = `complaint-field ${isChanged ? "highlight-changed" : ""}`;

  return (
    <div className={className}>
      <label>{label}</label>
      {isTextArea ? (
        <textarea readOnly value={value} />
      ) : (
        <input type="text" readOnly value={value} />
      )}
    </div>
  );
};
