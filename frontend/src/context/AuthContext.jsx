import { createContext, useContext, useState, useCallback, useEffect } from "react";

const AuthContext = createContext(null);

const TOKEN_KEY = "pfd_token";
const USER_KEY  = "pfd_user";

export function AuthProvider({ children }) {
  const [token, setToken]   = useState(() => localStorage.getItem(TOKEN_KEY) || null);
  const [user,  setUser]    = useState(() => {
    try { return JSON.parse(localStorage.getItem(USER_KEY) || "null"); }
    catch { return null; }
  });

  const login = useCallback((tokenData) => {
    localStorage.setItem(TOKEN_KEY, tokenData.access_token);
    const u = { username: tokenData.username, role: tokenData.role };
    localStorage.setItem(USER_KEY, JSON.stringify(u));
    setToken(tokenData.access_token);
    setUser(u);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isAdmin: user?.role === "admin" }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
};
