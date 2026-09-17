import React from "react";
import { useAppSelector } from "../../app/hooks";

export const CompletenessIndicator: React.FC = () => {
  const { completenessPct, missingFields } = useAppSelector(
    (state) => state.complaintForm
  );

  return (
    <div className="completeness-panel">
      <h3>Completeness: {Math.round(completenessPct)}%</h3>
      {missingFields.length > 0 ? (
        <div className="missing-fields">
          <strong>Missing required fields:</strong>
          <ul>
            {missingFields.map((field) => (
              <li key={field}>{field.replace(/_/g, " ")}</li>
            ))}
          </ul>
        </div>
      ) : (
        <div className="complete-message">
          ✓ All required fields are present.
        </div>
      )}
    </div>
  );
};
