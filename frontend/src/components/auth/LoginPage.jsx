import { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { login as apiLogin } from "../../services/api";

export default function LoginPage() {
  const { login } = useAuth();
  const [form,    setForm]    = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await apiLogin(form.username, form.password);
      login(data);
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-navy-900 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="text-3xl mb-3">🔬</div>
          <div className="text-[10px] text-slate-600 uppercase tracking-widest font-mono mb-1">
            Agentic AI
          </div>
          <h1 className="text-xl font-bold text-accent-blue font-mono">Pipeline Debugger</h1>
          <p className="text-xs text-slate-600 mt-1">Sign in to access the debug console</p>
        </div>

        {/* Card */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <span>🔑</span> Authentication
            </div>
          </div>
          <form onSubmit={handleSubmit} className="p-5 space-y-4">
            {error && (
              <div className="bg-red-950 border border-red-900/50 text-accent-red text-xs font-mono px-3 py-2 rounded flex items-center gap-2">
                <span>⚠</span> {error}
              </div>
            )}

            <div>
              <div className="field-label">Username</div>
              <input
                className="field-input"
                type="text"
                placeholder="admin or demo"
                value={form.username}
                onChange={(e) => setForm((p) => ({ ...p, username: e.target.value }))}
                required
                autoFocus
              />
            </div>

            <div>
              <div className="field-label">Password</div>
              <input
                className="field-input"
                type="password"
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => setForm((p) => ({ ...p, password: e.target.value }))}
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn btn-primary justify-center flex items-center gap-2 py-2"
            >
              {loading ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-blue-800 border-t-blue-400 rounded-full animate-spin-slow" />
                  Signing in...
                </>
              ) : (
                "Sign In →"
              )}
            </button>
          </form>
        </div>

        {/* Hint */}
        <div className="mt-4 text-center text-[10px] text-slate-700 font-mono space-y-1">
          <div>Default credentials:</div>
          <div className="text-slate-600">admin / admin123 &nbsp;·&nbsp; demo / demo123</div>
        </div>
      </div>
    </div>
  );
}
