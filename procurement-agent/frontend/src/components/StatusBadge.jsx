const tones = {
  New: "neutral",
  Processing: "info",
  NeedsReview: "warning",
  PendingApproval: "warning",
  Approved: "info",
  Rejected: "danger",
  Executed: "success",
  Completed: "success",
  Failed: "danger",
  ReadyToSend: "info",
  Sent: "success"
};

export default function StatusBadge({ status }) {
  return <span className={`badge ${tones[status] || "neutral"}`}>{status || "Unknown"}</span>;
}
