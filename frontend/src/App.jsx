import './App.css';

/**
 * AIVOA — Root Application Component (Chunk 1)
 *
 * Placeholder landing page showing system identity and backend readiness.
 * This will be replaced with the full complaint management UI
 * (form panel, copilot chat, risk assessment) in later chunks.
 */
function App() {
  return (
    <div className="app-container">
      {/* Logo */}
      <div className="app-logo">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
      </div>

      {/* Title */}
      <h1 className="app-title">AIVOA</h1>
      <p className="app-subtitle">
        AI-Powered Customer Complaint Management System
      </p>

      {/* Status */}
      <div className="status-card">
        <span className="status-dot" />
        Backend: Ready
      </div>

      {/* Build phase indicator */}
      <div className="chunk-badge">Chunk 1 — Foundation</div>
    </div>
  );
}

export default App;
