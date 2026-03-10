"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function LoginPage() {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            const formData = new FormData();
            formData.append("username", username);
            formData.append("password", password);

            const data = await api.post<{ access_token: string }>("/api/auth/login", formData);
            localStorage.setItem("token", data.access_token);
            router.push("/");
            router.refresh();
        } catch (err: any) {
            setError(err.message || "Invalid username or password");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-page">
            <div className="login-card glass-effect">
                <div className="login-header">
                    <div className="logo">G</div>
                    <h1>GST Shield</h1>
                    <p>Sign in to access the Dashboard</p>
                </div>

                <form onSubmit={handleLogin} className="login-form">
                    <div className="form-group">
                        <label htmlFor="username">Username</label>
                        <input
                            id="username"
                            type="text"
                            placeholder="Enter username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            id="password"
                            type="password"
                            placeholder="Enter password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>

                    {error && <div className="login-error">{error}</div>}

                    <button type="submit" className="btn-primary" disabled={loading}>
                        {loading ? "Signing in..." : "Sign In"}
                    </button>
                </form>

                <div className="login-footer">
                    <p>Demo Account: admin / AdminPassword123</p>
                </div>
            </div>

            <style jsx>{`
        .login-page {
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 100vh;
          background: radial-gradient(circle at top left, #1a1a2e, #16213e);
        }
        .login-card {
          width: 100%;
          max-width: 400px;
          padding: 2.5rem;
          border-radius: 20px;
          border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .login-header {
          text-align: center;
          margin-bottom: 2rem;
        }
        .login-header .logo {
          width: 50px;
          height: 50px;
          background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
          color: white;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.5rem;
          font-weight: bold;
          margin: 0 auto 1rem;
          box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);
        }
        .login-header h1 {
          font-size: 1.8rem;
          margin-bottom: 0.5rem;
          color: white;
        }
        .login-header p {
          color: rgba(255, 255, 255, 0.6);
          font-size: 0.9rem;
        }
        .login-form .form-group {
          margin-bottom: 1.5rem;
        }
        .login-form label {
          display: block;
          margin-bottom: 0.5rem;
          font-size: 0.9rem;
          color: rgba(255, 255, 255, 0.8);
        }
        .login-form input {
          width: 100%;
          padding: 0.8rem;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          color: white;
          outline: none;
          transition: all 0.3s ease;
        }
        .login-form input:focus {
          border-color: #4facfe;
          background: rgba(255, 255, 255, 0.1);
          box-shadow: 0 0 0 4px rgba(79, 172, 254, 0.1);
        }
        .login-error {
          background: rgba(231, 76, 60, 0.1);
          color: #ff6b6b;
          padding: 0.8rem;
          border-radius: 8px;
          font-size: 0.85rem;
          margin-bottom: 1.5rem;
          border: 1px solid rgba(231, 76, 60, 0.2);
          text-align: center;
        }
        .btn-primary {
          width: 100%;
          padding: 0.8rem;
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
          border: none;
          border-radius: 8px;
          color: white;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s ease, opacity 0.2s ease;
        }
        .btn-primary:hover {
          transform: translateY(-2px);
          opacity: 0.9;
        }
        .btn-primary:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }
        .login-footer {
          margin-top: 2rem;
          text-align: center;
          font-size: 0.8rem;
          color: rgba(255, 255, 255, 0.4);
        }
      `}</style>
        </div>
    );
}
