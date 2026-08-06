import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getWorkspaces } from "@/lib/api";

const WorkspaceContext = createContext(null);
export const useWorkspace = () => useContext(WorkspaceContext);

// hex -> "H S% L%" for CSS variable injection
function hexToHslString(hex) {
  if (!hex) return null;
  let h = hex.replace("#", "");
  if (h.length === 3) h = h.split("").map((c) => c + c).join("");
  const r = parseInt(h.slice(0, 2), 16) / 255, g = parseInt(h.slice(2, 4), 16) / 255, b = parseInt(h.slice(4, 6), 16) / 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b); let hue = 0, s = 0; const l = (max + min) / 2;
  if (max !== min) {
    const d = max - min; s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    hue = max === r ? (g - b) / d + (g < b ? 6 : 0) : max === g ? (b - r) / d + 2 : (r - g) / d + 4; hue /= 6;
  }
  return `${Math.round(hue * 360)} ${Math.round(s * 100)}% ${Math.round(l * 100)}%`;
}

export function applyBranding(ws) {
  const root = document.documentElement;
  const p = hexToHslString(ws?.primary_color);
  if (p) { root.style.setProperty("--primary", p); root.style.setProperty("--accent", p); root.style.setProperty("--ring", p); }
  else { root.style.removeProperty("--primary"); root.style.removeProperty("--accent"); root.style.removeProperty("--ring"); }
}

export function WorkspaceProvider({ children }) {
  const qc = useQueryClient();
  const [workspaces, setWorkspaces] = useState([]);
  const [current, setCurrent] = useState(null);
  const [ready, setReady] = useState(false);

  const refresh = useCallback(async (preferId) => {
    const list = await getWorkspaces();
    setWorkspaces(list);
    const savedId = preferId || localStorage.getItem("listrix_workspace_id");
    const active = list.find((w) => w.id === savedId) || list.find((w) => w.is_default) || list[0];
    if (active) {
      localStorage.setItem("listrix_workspace_id", active.id);
      setCurrent(active);
      applyBranding(active);
    }
    return active;
  }, []);

  useEffect(() => { refresh().finally(() => setReady(true)); }, [refresh]);

  const switchWorkspace = useCallback(async (id) => {
    const list = workspaces.length ? workspaces : await getWorkspaces();
    const active = list.find((w) => w.id === id);
    if (!active) return;
    localStorage.setItem("listrix_workspace_id", id);
    setCurrent(active);
    applyBranding(active);
    qc.invalidateQueries(); // refetch all data for the new workspace
  }, [workspaces, qc]);

  const value = { workspaces, current, ready, refresh, switchWorkspace, setCurrent, applyBranding };
  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}
