import { Paperclip, Send } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client.js";
import PageHeader from "../components/PageHeader.jsx";

const exampleText = "Sarah from IT needs 12 business laptops for onboarding next month. Budget is around 18000 USD. Please request quotes from approved IT hardware vendors.";

export default function CreateRequest() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ original_text: exampleText, requester_name: "", department: "" });
  const [files, setFiles] = useState([]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      let request;
      if (files.length) {
        const data = new FormData();
        data.append("email_body", form.original_text);
        if (form.requester_name) data.append("requester_name", form.requester_name);
        if (form.department) data.append("department", form.department);
        files.forEach((file) => data.append("files", file));
        request = await api.createEmailRequest(data);
      } else {
        const payload = Object.fromEntries(Object.entries(form).filter(([, value]) => value !== ""));
        request = await api.createRequest(payload);
      }
      navigate(`/requests/${request.RequestID}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <PageHeader title="Create Request" subtitle="Submit email text, attachments, or both. Documents are extracted, sanitized, merged, and held for approval." />
      <form className="form-panel" onSubmit={submit}>
        {error ? <div className="alert danger">{error}</div> : null}
        <label>
          Purchase request text
          <textarea value={form.original_text} onChange={(event) => update("original_text", event.target.value)} rows={8} required />
        </label>
        <div className="form-grid">
          <label>
            Requester
            <input value={form.requester_name} onChange={(event) => update("requester_name", event.target.value)} />
          </label>
          <label>
            Department
            <input value={form.department} onChange={(event) => update("department", event.target.value)} />
          </label>
        </div>
        <label>
          Attachments
          <input
            type="file"
            multiple
            accept=".pdf,.xlsx,.xls,.csv,.docx,.txt,.png,.jpg,.jpeg"
            onChange={(event) => setFiles(Array.from(event.target.files || []))}
          />
        </label>
        {files.length ? (
          <div className="file-list">
            <Paperclip size={16} />
            <span>{files.map((file) => file.name).join(", ")}</span>
          </div>
        ) : null}
        <button className="button primary" type="submit" disabled={saving}>
          <Send size={16} />
          {saving ? "Creating..." : "Start workflow"}
        </button>
      </form>
    </>
  );
}
