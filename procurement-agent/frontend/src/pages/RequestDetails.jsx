import { RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client.js";
import JsonBlock from "../components/JsonBlock.jsx";
import PageHeader from "../components/PageHeader.jsx";
import StatusBadge from "../components/StatusBadge.jsx";

export default function RequestDetails() {
  const { requestId } = useParams();
  const [details, setDetails] = useState(null);
  const [error, setError] = useState("");

  async function load() {
    try {
      setDetails(await api.getRequest(requestId));
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, [requestId]);

  const latestAction = details?.actions?.[details.actions.length - 1];
  const proposed = useMemo(() => {
    if (!latestAction) return null;
    try {
      return JSON.parse(latestAction.ProposedOutput);
    } catch {
      return latestAction.ProposedOutput;
    }
  }, [latestAction]);

  return (
    <>
      <PageHeader
        title={`Request #${requestId}`}
        subtitle="Original request, attachments, extraction results, source traceability, RFQ drafts, and logs."
        actions={<button className="button secondary" onClick={load}><RefreshCw size={16} />Refresh</button>}
      />
      {error ? <div className="alert danger">{error}</div> : null}
      {details ? (
        <div className="detail-grid">
          <section className="panel">
            <div className="section-title">
              <h2>Request</h2>
              <StatusBadge status={details.request.Status} />
            </div>
            <p className="body-text">{details.request.OriginalText}</p>
            <dl className="field-list">
              <div><dt>Requester</dt><dd>{details.request.RequesterName || "-"}</dd></div>
              <div><dt>Department</dt><dd>{details.request.Department || "-"}</dd></div>
              <div><dt>Category</dt><dd>{details.request.Category || "-"}</dd></div>
              <div><dt>Quantity</dt><dd>{details.request.Quantity || "-"}</dd></div>
              <div><dt>Budget</dt><dd>{details.request.Budget || "-"}</dd></div>
              <div><dt>Urgency</dt><dd>{details.request.Urgency || "-"}</dd></div>
            </dl>
          </section>

          <section className="panel">
            <h2>Attachments</h2>
            {details.attachments.length ? (
              <table>
                <thead><tr><th>File</th><th>Type</th><th>Size</th><th>Status</th></tr></thead>
                <tbody>
                  {details.attachments.map((attachment) => (
                    <tr key={attachment.AttachmentID}>
                      <td>{attachment.OriginalFileName}</td>
                      <td>{attachment.SourceType}</td>
                      <td>{(attachment.FileSize / 1024).toFixed(1)} KB</td>
                      <td><StatusBadge status={attachment.ExtractionStatus} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p>No attachments uploaded.</p>
            )}
          </section>

          <section className="panel">
            <h2>Proposed action</h2>
            {latestAction ? (
              <>
                <div className="action-summary">
                  <StatusBadge status={latestAction.Status} />
                  <span>Confidence {(latestAction.ConfidenceScore * 100).toFixed(0)}%</span>
                </div>
                <JsonBlock value={proposed} />
              </>
            ) : (
              <p>No proposed action yet.</p>
            )}
          </section>

          <section className="panel full">
            <h2>Document extraction results</h2>
            {details.document_extractions.length ? (
              <div className="extraction-grid">
                {details.document_extractions.map((result) => (
                  <article className="extract-card" key={result.ExtractionID}>
                    <div className="section-title">
                      <div>
                        <h3>{result.SourceFile || result.SourceType}</h3>
                        <p>Confidence {(result.ExtractionConfidence * 100).toFixed(0)}%</p>
                      </div>
                      <StatusBadge status={result.RequiresReview ? "NeedsReview" : "Completed"} />
                    </div>
                    {result.ExtractionErrors ? <JsonBlock value={result.ExtractionErrors} /> : null}
                    {result.StructuredData ? <JsonBlock value={result.StructuredData} /> : null}
                    {result.ExtractedTables ? <JsonBlock value={result.ExtractedTables} /> : null}
                  </article>
                ))}
              </div>
            ) : (
              <p>No document extraction results yet.</p>
            )}
          </section>

          {proposed?.conflicts?.length ? (
            <section className="panel full">
              <h2>Detected conflicts</h2>
              <JsonBlock value={proposed.conflicts} />
            </section>
          ) : null}

          {proposed?.source_traceability ? (
            <section className="panel full">
              <h2>Source traceability</h2>
              <JsonBlock value={proposed.source_traceability} />
            </section>
          ) : null}

          <section className="panel full">
            <h2>Email logs</h2>
            <table>
              <thead><tr><th>Recipient</th><th>Subject</th><th>Status</th><th>Created</th></tr></thead>
              <tbody>
                {details.email_logs.map((log) => (
                  <tr key={log.EmailLogID}>
                    <td>{log.RecipientEmail}</td>
                    <td>{log.Subject}</td>
                    <td><StatusBadge status={log.Status} /></td>
                    <td>{new Date(log.CreatedAt).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="panel full">
            <h2>Execution logs</h2>
            <table>
              <thead><tr><th>Node</th><th>Status</th><th>Message</th><th>Created</th></tr></thead>
              <tbody>
                {details.execution_logs.map((log) => (
                  <tr key={log.LogID}>
                    <td>{log.NodeName}</td>
                    <td><StatusBadge status={log.Status} /></td>
                    <td>{log.Message}</td>
                    <td>{new Date(log.CreatedAt).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </div>
      ) : null}
    </>
  );
}
