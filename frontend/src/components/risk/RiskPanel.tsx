import React from "react";
import { useAppSelector } from "../../app/hooks";

export const RiskPanel: React.FC = () => {
  const { currentRisk } = useAppSelector((state) => state.riskAssessment);

  if (!currentRisk || currentRisk.rpn === undefined) {
    return (
      <div className="risk-panel empty">
        <h3>Risk Assessment</h3>
        <p>Risk assessment will appear here when available.</p>
      </div>
    );
  }

  // Get color based on risk level
  const riskClass = currentRisk.risk_level?.toLowerCase() || "low";

  return (
    <div className="risk-panel">
      <h3>Risk Assessment</h3>
      
      <div className={`risk-level-banner ${riskClass}`}>
        <strong>Risk Level:</strong> {currentRisk.risk_level}
      </div>

      <div className="risk-metrics">
        <div className="metric">
          <span className="label">Severity:</span>
          <span className="value">{currentRisk.severity_score}/10</span>
        </div>
        <div className="metric">
          <span className="label">Occurrence:</span>
          <span className="value">{currentRisk.occurrence}/10</span>
        </div>
        <div className="metric">
          <span className="label">Detection:</span>
          <span className="value">{currentRisk.detectability}/10</span>
        </div>
        <div className="metric">
          <span className="label">RPN:</span>
          <span className="value">{currentRisk.rpn}</span>
        </div>
      </div>

      {(currentRisk.corrective_action || currentRisk.preventive_action) && (
        <div className="capa-section">
          <h3>CAPA Recommendation</h3>
          {currentRisk.corrective_action && (
            <div className="risk-detail">
              <h4>Corrective Action</h4>
              <p>{currentRisk.corrective_action}</p>
            </div>
          )}
          {currentRisk.preventive_action && (
            <div className="risk-detail">
              <h4>Preventive Action</h4>
              <p>{currentRisk.preventive_action}</p>
            </div>
          )}
        </div>
      )}
      
      {currentRisk.root_cause_hint && (
        <div className="risk-detail hint">
          <h4>Root Cause Hint</h4>
          <p>{currentRisk.root_cause_hint}</p>
        </div>
      )}
    </div>
  );
};
