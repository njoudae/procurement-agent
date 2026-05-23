import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { api } from "./api/client.js";
import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import CreateRequest from "./pages/CreateRequest.jsx";
import Requests from "./pages/Requests.jsx";
import RequestDetails from "./pages/RequestDetails.jsx";
import PendingApprovals from "./pages/PendingApprovals.jsx";
import Vendors from "./pages/Vendors.jsx";

export default function App() {
  useEffect(() => {
    if (import.meta.env.DEV) {
      api.devLogin().catch(() => {
        // Page-level API calls surface backend/auth setup errors.
      });
    }
  }, []);

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/requests/new" element={<CreateRequest />} />
        <Route path="/requests" element={<Requests />} />
        <Route path="/requests/:requestId" element={<RequestDetails />} />
        <Route path="/approvals" element={<PendingApprovals />} />
        <Route path="/vendors" element={<Vendors />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
