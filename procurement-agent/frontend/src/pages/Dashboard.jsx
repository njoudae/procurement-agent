import { AlertTriangle, CheckCircle2, Clock3, FileText } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";
import PageHeader from "../components/PageHeader.jsx";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.overview().then(setStats).catch((err) => setError(err.message));
  }, []);

  const cards = [
    { label: "Total requests", value: stats?.total_requests ?? "-", icon: FileText },
    { label: "Pending approvals", value: stats?.pending_approvals ?? "-", icon: Clock3 },
    { label: "Completed actions", value: stats?.completed_actions ?? "-", icon: CheckCircle2 },
    { label: "Failed actions", value: stats?.failed_actions ?? "-", icon: AlertTriangle }
  ];

  return (
    <>
      <PageHeader
        title="Procurement Control Center"
        subtitle="Review agent output, approve RFQ drafts, and keep every action auditable."
        actions={<Link className="button primary" to="/requests/new">New request</Link>}
      />
      {error ? <div className="alert danger">{error}</div> : null}
      <section className="metric-grid">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <article className="metric-card" key={card.label}>
              <Icon size={22} />
              <span>{card.label}</span>
              <strong>{card.value}</strong>
            </article>
          );
        })}
      </section>
      <section className="panel">
        <h2>Operating model</h2>
        <div className="workflow-strip">
          <span>Request</span>
          <span>Extract</span>
          <span>Match vendors</span>
          <span>Draft RFQ</span>
          <span>Approve</span>
          <span>Execute</span>
        </div>
      </section>
    </>
  );
}
