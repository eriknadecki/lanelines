import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { clearTokens, getAccessToken, getMe, setTokens } from "../api/client";
import type { TokenResponse, UserOut } from "../api/types";

interface AuthContextValue {
  user: UserOut | null;
  loading: boolean;
  applyTokens: (tokens: TokenResponse, remember?: boolean) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getAccessToken()) {
      setLoading(false);
      return;
    }
    getMe()
      .then(setUser)
      .catch(() => clearTokens())
      .finally(() => setLoading(false));
  }, []);

  async function applyTokens(tokens: TokenResponse, remember: boolean = true) {
    setTokens(tokens, remember);
    setUser(await getMe());
  }

  function logout() {
    clearTokens();
    setUser(null);
  }

  return <AuthContext.Provider value={{ user, loading, applyTokens, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
