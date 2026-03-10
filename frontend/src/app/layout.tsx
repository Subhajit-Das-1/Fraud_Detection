"use client";

import "./globals.css";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

const navItems = [
  { href: "/", label: "Dashboard", icon: "📊" },
  { href: "/invoices", label: "Invoices", icon: "📄" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  const isLoginPage = pathname === "/login";

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token && !isLoginPage) {
      setIsAuthenticated(false);
      router.push("/login");
    } else if (token) {
      setIsAuthenticated(true);
      if (isLoginPage) {
        router.push("/");
      }
    } else {
      setIsAuthenticated(false);
    }
  }, [pathname, isLoginPage, router]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    setIsAuthenticated(false);
    router.push("/login");
  };

  // Don't render until we've checked auth (to avoid flickers)
  if (isAuthenticated === null && !isLoginPage) {
    return (
      <html lang="en">
        <head>
          <title>GST Fraud Detection System</title>
        </head>
        <body className="loading-bg">
          <div className="loader-container">
            <div className="loader"></div>
          </div>
        </body>
      </html>
    );
  }

  return (
    <html lang="en">
      <head>
        <title>GST Fraud Detection System</title>
        <meta name="description" content="Intelligent GST Fraud Pattern Detection with Rule Engine + ML" />
      </head>
      <body>
        {isLoginPage ? (
          <main>{children}</main>
        ) : (
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
                <button onClick={handleLogout} className="logout-btn">
                  <span className="icon">🚪</span>
                  Logout
                </button>
                <div className="status">
                  <span className="status-dot"></span>
                  System Online
                </div>
              </div>
            </aside>

            {/* Main Content */}
            <main className="main-content">{children}</main>
          </div>
        )}
      </body>
    </html>
  );
}
