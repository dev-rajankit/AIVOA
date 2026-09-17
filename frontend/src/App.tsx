import React from "react";
import { ComplaintForm } from "./components/complaint/ComplaintForm";
import { CopilotChat } from "./components/copilot/CopilotChat";
import { CompletenessIndicator } from "./components/common/CompletenessIndicator";
import { RiskPanel } from "./components/risk/RiskPanel";
import "./App.css";

const App: React.FC = () => {
  return (
    <div className="app-layout">
      <header className="app-header">
        <h1>AIVOA Complaint Copilot</h1>
      </header>
      
      <main className="app-main-grid">
        <div className="left-panel">
          <ComplaintForm />
          <CompletenessIndicator />
        </div>
        
        <div className="center-panel">
          <CopilotChat />
        </div>
        
        <div className="right-panel">
          <RiskPanel />
        </div>
      </main>
    </div>
  );
};

export default App;
