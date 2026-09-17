import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { RootState } from "../../app/store";
import { getComplaintAuditLog } from "../../api/complaint";
import "./AuditPanel.css";

export const AuditPanel: React.FC = () => {
  const complaintId = useSelector((state: RootState) => state.complaintForm.complaintId);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!complaintId) return;

    let mounted = true;
    const fetchAudit = async () => {
      setLoading(true);
      try {
        const logs = await getComplaintAuditLog(complaintId);
        if (mounted) {
          setAuditLogs(logs);
        }
      } catch (err) {
        console.error("Failed to fetch audit log", err);
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };
    
    // Slight delay to ensure DB transaction finishes before fetching
    const timer = setTimeout(() => fetchAudit(), 500);
    return () => {
      mounted = false;
      clearTimeout(timer);
    };
  }, [complaintId]);

  if (!complaintId) return null;

  return (
    <div className="audit-panel card">
      <h3>Processing History</h3>
      {loading && <p>Loading audit trail...</p>}
      {!loading && auditLogs.length === 0 && <p>No events recorded yet.</p>}
      {!loading && auditLogs.length > 0 && (
        <ul className="audit-list">
          {auditLogs.map((log) => (
            <li key={log.id} className="audit-item">
              <div className="audit-time">
                {new Date(log.created_at).toLocaleTimeString()}
              </div>
              <div className="audit-detail">
                <strong>{log.field_name}</strong> updated by <em>{log.changed_by}</em>
                {log.old_value && <div className="audit-old">from: {log.old_value}</div>}
                <div className="audit-new">to: {log.new_value}</div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
