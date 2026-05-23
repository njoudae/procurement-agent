import { Check, Pencil, RefreshCw, X } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import JsonBlock from "../components/JsonBlock.jsx";
import PageHeader from "../components/PageHeader.jsx";

export default function PendingApprovals() {
  const [items, setItems] = useState([]);
  const [editing, setEditing] = useState(null);
  const [editText, setEditText] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      setItems(await api.pendingApprovals());
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function approve(actionId) {
    await api.approve(actionId, { admin_comment: "Approved from dashboard", approved_by: "admin" });
    await load();
  }

  async function reject(actionId) {
    await api.reject(actionId, { admin_comment: "Rejected from dashboard", approved_by: "admin" });
    await load();
  }

  async function editApprove(actionId) {
    try {
      JSON.parse(editText);
      await api.editApprove(actionId, {
        proposed_output: JSON.parse(editText),
        admin_comment: "Edited and approved from dashboard",
        approved_by: "admin"
      });
      setEditing(null);
      setEditText("");
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <>
      <PageHeader
        title="Pending Approvals"
        subtitle="RFQ drafts are stored first. Execution only happens after an admin approves."
        actions={<button className="button secondary" onClick={load}><RefreshCw size={16} />Refresh</button>}
      />
      {error ? <div className="alert danger">{error}</div> : null}
      <div className="approval-list">
        {items.map(({ action, request }) => (
          <section className="panel" key={action.ActionID}>
            <div className="section-title">
              <div>
                <h2>Action #{action.ActionID}</h2>
                <p>{request.ItemDescription || request.OriginalText}</p>
              </div>
              <span className="confidence">{(action.ConfidenceScore * 100).toFixed(0)}%</span>
            </div>
            {editing === action.ActionID ? (
              <>
                <textarea className="code-editor" value={editText} onChange={(event) => setEditText(event.target.value)} rows={16} />
                <div className="button-row">
                  <button className="button primary" onClick={() => editApprove(action.ActionID)}><Check size={16} />Save and approve</button>
                  <button className="button secondary" onClick={() => setEditing(null)}>Cancel</button>
                </div>
              </>
            ) : (
              <>
                <JsonBlock value={action.ProposedOutput} />
                <div className="button-row">
                  <button className="button success" onClick={() => approve(action.ActionID)}><Check size={16} />Approve</button>
                  <button
                    className="button secondary"
                    onClick={() => {
                      setEditing(action.ActionID);
                      setEditText(JSON.stringify(JSON.parse(action.ProposedOutput), null, 2));
                    }}
                  >
                    <Pencil size={16} />Edit
                  </button>
                  <button className="button danger" onClick={() => reject(action.ActionID)}><X size={16} />Reject</button>
                </div>
              </>
            )}
          </section>
        ))}
        {!items.length ? <section className="panel empty">No approvals waiting right now.</section> : null}
      </div>
    </>
  );
}
