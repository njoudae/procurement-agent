import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";
import PageHeader from "../components/PageHeader.jsx";
import StatusBadge from "../components/StatusBadge.jsx";

export default function Requests() {
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      setRequests(await api.listRequests());
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <>
      <PageHeader
        title="Requests"
        subtitle="Track extracted procurement requests and their approval state."
        actions={<button className="button secondary" onClick={load}><RefreshCw size={16} />Refresh</button>}
      />
      {error ? <div className="alert danger">{error}</div> : null}
      <section className="panel">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Item</th>
              <th>Category</th>
              <th>Department</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((request) => (
              <tr key={request.RequestID}>
                <td><Link to={`/requests/${request.RequestID}`}>#{request.RequestID}</Link></td>
                <td>{request.ItemDescription || "Pending extraction"}</td>
                <td>{request.Category || "-"}</td>
                <td>{request.Department || "-"}</td>
                <td><StatusBadge status={request.Status} /></td>
                <td>{new Date(request.CreatedAt).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
