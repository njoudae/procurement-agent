import { Plus, RefreshCw, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import PageHeader from "../components/PageHeader.jsx";
import StatusBadge from "../components/StatusBadge.jsx";

const emptyVendor = { company_name: "", category: "", department: "", email: "", phone: "", rating: 4, is_active: true };

export default function Vendors() {
  const [vendors, setVendors] = useState([]);
  const [form, setForm] = useState(emptyVendor);
  const [error, setError] = useState("");

  async function load() {
    try {
      setVendors(await api.vendors());
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    try {
      const payload = { ...form, rating: Number(form.rating), department: form.department || null, phone: form.phone || null };
      await api.createVendor(payload);
      setForm(emptyVendor);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <>
      <PageHeader
        title="Vendors"
        subtitle="Maintain approved vendors manually. The agent only reads and ranks active vendor records."
        actions={<button className="button secondary" onClick={load}><RefreshCw size={16} />Refresh</button>}
      />
      {error ? <div className="alert danger">{error}</div> : null}
      <form className="form-panel compact" onSubmit={submit}>
        <div className="form-grid vendor-grid">
          <input placeholder="Company name" value={form.company_name} onChange={(event) => update("company_name", event.target.value)} required />
          <input placeholder="Category" value={form.category} onChange={(event) => update("category", event.target.value)} required />
          <input placeholder="Department" value={form.department} onChange={(event) => update("department", event.target.value)} />
          <input placeholder="Email" type="email" value={form.email} onChange={(event) => update("email", event.target.value)} required />
          <input placeholder="Phone" value={form.phone} onChange={(event) => update("phone", event.target.value)} />
          <input placeholder="Rating" type="number" min="0" max="5" step="0.1" value={form.rating} onChange={(event) => update("rating", event.target.value)} />
        </div>
        <button className="button primary" type="submit"><Plus size={16} />Add vendor</button>
      </form>
      <section className="panel">
        <table>
          <thead><tr><th>Company</th><th>Category</th><th>Department</th><th>Email</th><th>Rating</th><th>Status</th></tr></thead>
          <tbody>
            {vendors.map((vendor) => (
              <tr key={vendor.VendorID}>
                <td>{vendor.CompanyName}</td>
                <td>{vendor.Category}</td>
                <td>{vendor.Department || "-"}</td>
                <td>{vendor.Email}</td>
                <td>{vendor.Rating.toFixed(1)}</td>
                <td><StatusBadge status={vendor.IsActive ? "Active" : "Inactive"} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
