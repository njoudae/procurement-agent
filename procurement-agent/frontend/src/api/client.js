const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  const headers = {
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...(options.headers || {})
  };

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers
  });

  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Keep default message.
    }
    throw new Error(message);
  }

  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  devLogin: () => request("/auth/dev-login", { method: "POST" }),
  me: () => request("/auth/me"),
  logout: () => request("/auth/logout", { method: "POST" }),
  overview: () => request("/requests/overview"),
  listRequests: () => request("/requests"),
  createRequest: (payload) => request("/requests", { method: "POST", body: JSON.stringify(payload) }),
  createEmailRequest: (payload) => request("/requests/email", { method: "POST", body: payload }),
  getRequest: (id) => request(`/requests/${id}`),
  pendingApprovals: () => request("/approvals/pending"),
  approve: (actionId, payload) => request(`/approvals/${actionId}/approve`, { method: "POST", body: JSON.stringify(payload) }),
  reject: (actionId, payload) => request(`/approvals/${actionId}/reject`, { method: "POST", body: JSON.stringify(payload) }),
  editApprove: (actionId, payload) => request(`/approvals/${actionId}/edit-approve`, { method: "POST", body: JSON.stringify(payload) }),
  logs: (requestId) => request(`/logs/${requestId}`),
  vendors: () => request("/vendors"),
  createVendor: (payload) => request("/vendors", { method: "POST", body: JSON.stringify(payload) }),
  updateVendor: (vendorId, payload) => request(`/vendors/${vendorId}`, { method: "PUT", body: JSON.stringify(payload) })
};
