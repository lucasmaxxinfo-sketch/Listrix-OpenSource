import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getMe, login as apiLogin, register as apiRegister } from "@/lib/api";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  // Hydrate the session from a persisted token (no-op when auth is not in use).
  const hydrate = useCallback(async () => {
    if (!localStorage.getItem("listrix_token")) { setReady(true); return; }
    try { setUser(await getMe()); } catch { localStorage.removeItem("listrix_token"); }
    setReady(true);
  }, []);

  useEffect(() => { hydrate(); }, [hydrate]);

  const login = useCallback(async (email, password) => {
    const data = await apiLogin({ email, password });
    localStorage.setItem("listrix_token", data.access_token);
    setUser(data.user);
    return data;
  }, []);

  const register = useCallback(async (email, password, name, acceptedTerms) => {
    const data = await apiRegister({ email, password, name, accepted_terms: !!acceptedTerms });
    localStorage.setItem("listrix_token", data.access_token);
    setUser(data.user);
    try { sessionStorage.setItem("listrix:just-registered", "1"); } catch {}
    return data;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("listrix_token");
    setUser(null);
  }, []);

  return <AuthContext.Provider value={{ user, ready, login, register, logout }}>{children}</AuthContext.Provider>;
}
