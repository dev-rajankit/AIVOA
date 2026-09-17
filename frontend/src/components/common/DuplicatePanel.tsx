import React from "react";
import { useAppSelector } from "../../app/hooks";

export const DuplicatePanel: React.FC = () => {
  const { duplicateStatus, duplicateMatches } = useAppSelector(
    (state) => state.complaintForm
  );

  if (duplicateStatus === "UNIQUE") {
    return (
      <div className="duplicate-panel" style={{ marginTop: "1rem", padding: "1rem", backgroundColor: "#e2e3e5", borderRadius: "8px" }}>
        <h4>Duplicate Check</h4>
        <p style={{ color: "#383d41" }}>Potential duplicate: No</p>
      </div>
    );
  }

  const bestMatch = duplicateMatches && duplicateMatches.length > 0 ? duplicateMatches[0] : null;

  const isDuplicate = duplicateStatus === "DUPLICATE";
  const bgColor = isDuplicate ? "#f8d7da" : "#fff3cd";
  const textColor = isDuplicate ? "#721c24" : "#856404";
  const title = isDuplicate ? "Similar complaint already exists" : "Possible duplicate detected";

  return (
    <div className="duplicate-panel" style={{ marginTop: "1rem", padding: "1rem", backgroundColor: bgColor, borderRadius: "8px", color: textColor }}>
      <h4 style={{ marginTop: 0 }}>{title}</h4>
      {bestMatch && (
        <div style={{ marginTop: "0.5rem", fontSize: "0.9rem" }}>
          <strong>Match ID:</strong> {bestMatch.matched_complaint_id.substring(0, 8).toUpperCase()}<br/>
          <strong>Similarity:</strong> {(bestMatch.similarity_score * 100).toFixed(1)}%<br/>
          <strong>Summary:</strong> {bestMatch.matched_complaint_summary}
        </div>
      )}
    </div>
  );
};
