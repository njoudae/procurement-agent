import { ClipboardList, FilePlus2, Gauge, MailCheck, PackageSearch, Users } from "lucide-react";
import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/", label: "Overview", icon: Gauge },
  { to: "/requests/new", label: "Create Request", icon: FilePlus2 },
  { to: "/requests", label: "Requests", icon: ClipboardList },
  { to: "/approvals", label: "Approvals", icon: MailCheck },
  { to: "/vendors", label: "Vendors", icon: Users }
];

export default function Layout({ children }) {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <PackageSearch size={24} />
          <div>
            <strong>ProcureAI</strong>
            <span>Admin Console</span>
          </div>
        </div>
        <nav className="nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
                <Icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
