"use client";

import "./globals.css";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Dashboard", icon: "📊" },
  { href: "/invoices", label: "Invoices", icon: "📄" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <html lang="en">
      <head>
        <title>GST Fraud Detection System</title>
        <meta name="description" content="Intelligent GST Fraud Pattern Detection with Rule Engine + ML" />
      </head>
      <body>
        <div className="app-container">
          {/* Sidebar */}
          <aside className="sidebar">
            <div className="sidebar-brand">
              <div className="logo">G</div>
              <div>
                <h1>GST Shield</h1>
                <div className="subtitle">Fraud Detection</div>
              </div>
            </div>

            <nav className="sidebar-nav">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`nav-link ${pathname === item.href ? "active" : ""}`}
                >
                  <span className="icon">{item.icon}</span>
                  {item.label}
                </Link>
              ))}
            </nav>

            <div className="sidebar-footer">
              <div className="status">
                <span className="status-dot"></span>
                System Online
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="main-content">{children}</main>
        </div>
      </body>
    </html>
  );
}
