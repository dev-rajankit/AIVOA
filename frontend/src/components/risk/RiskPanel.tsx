import React from "react";
import { useAppSelector } from "../../app/hooks";

export const RiskPanel: React.FC = () => {
  const { currentRisk } = useAppSelector((state) => state.riskAssessment);

  if (!currentRisk) {
    return (
      <div className="risk-panel empty">
        <h3>Risk Assessment</h3>
        <p>Risk assessment will appear here when available.</p>
      </div>
    );
  }

  return (
    <div className="risk-panel">
      <h3>Risk Assessment</h3>
      <div className="risk-metrics">
        <div className="metric">
          <span className="label">Severity:</span>
          <span className={`value ${currentRisk.severity?.toLowerCase()}`}>
            {currentRisk.severity || "N/A"}
          </span>
        </div>
        {currentRisk.rpn !== undefined && (
          <div className="metric">
            <span className="label">RPN:</span>
            <span className="value">{currentRisk.rpn}</span>
          </div>
        )}
      </div>

      {currentRisk.recommended_action && (
        <div className="risk-detail">
          <h4>Recommended Action</h4>
          <p>{currentRisk.recommended_action}</p>
        </div>
      )}
      
      {currentRisk.ai_reasoning_summary && (
        <div className="risk-detail">
          <h4>AI Reasoning</h4>
          <p>{currentRisk.ai_reasoning_summary}</p>
        </div>
      )}
    </div>
  );
};
