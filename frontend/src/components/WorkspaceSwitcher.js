import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Boxes, ChevronDown, Plus, Check, Settings, Loader2 } from "lucide-react";
import { useWorkspace } from "@/context/WorkspaceContext";
import { createWorkspace } from "@/lib/api";
import { toast } from "sonner";

export default function WorkspaceSwitcher() {
  const { workspaces, current, switchWorkspace, refresh } = useWorkspace();
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const create = async () => {
    if (!name.trim()) return;
    setBusy(true);
    try {
      const ws = await createWorkspace({ name: name.trim() });
      await refresh(ws.id);
      await switchWorkspace(ws.id);
      toast.success(`Workspace "${ws.name}" created`);
      setName(""); setCreating(false); setOpen(false);
    } catch { toast.error("Failed to create workspace"); } finally { setBusy(false); }
  };

  return (
    <div className="relative px-3 py-3 border-b border-border">
      <button data-testid="workspace-switcher" onClick={() => setOpen((o) => !o)} className="flex w-full items-center gap-2.5 rounded-lg border border-border bg-card/70 px-3 py-2 text-left hover:border-primary/30">
        {current?.logo ? <img src={current.logo} alt="logo" className="h-8 w-8 rounded-md object-cover" /> : <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground"><Boxes size={16} /></span>}
        <div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold">{current?.name || "Workspace"}</p><p className="truncate text-[10px] uppercase tracking-widest text-muted-foreground">{current?.business_type || "Business"}</p></div>
        <ChevronDown size={16} className="text-muted-foreground" />
      </button>
      {open && (
        <div className="absolute left-3 right-3 top-full z-30 mt-1 rounded-lg border border-border bg-popover p-1.5 shadow-panel">
          <div className="max-h-52 overflow-y-auto lx-scroll">
            {workspaces.map((w) => (
              <button key={w.id} data-testid="workspace-option" onClick={() => { switchWorkspace(w.id); setOpen(false); }} className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm hover:bg-muted/50">
                {w.logo ? <img src={w.logo} alt="" className="h-6 w-6 rounded object-cover" /> : <span className="flex h-6 w-6 items-center justify-center rounded bg-muted text-muted-foreground"><Boxes size={13} /></span>}
                <span className="flex-1 truncate">{w.name}</span>
                {current?.id === w.id && <Check size={15} className="text-primary" />}
              </button>
            ))}
          </div>
          {creating ? (
            <div className="mt-1 flex gap-1.5 border-t border-border pt-2">
              <input autoFocus value={name} onChange={(e) => setName(e.target.value)} onKeyDown={(e) => e.key === "Enter" && create()} placeholder="Business name" className="flex-1 rounded-md border border-border bg-muted/30 px-2 py-1.5 text-sm outline-none focus:border-primary/50" />
              <button onClick={create} disabled={busy} className="rounded-md bg-primary px-2.5 text-primary-foreground disabled:opacity-60">{busy ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}</button>
            </div>
          ) : (
            <div className="mt-1 border-t border-border pt-1">
              <button data-testid="create-workspace-button" onClick={() => setCreating(true)} className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm text-muted-foreground hover:bg-muted/50 hover:text-foreground"><Plus size={15} /> New workspace</button>
              <button onClick={() => { navigate("/settings"); setOpen(false); }} className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm text-muted-foreground hover:bg-muted/50 hover:text-foreground"><Settings size={15} /> Workspace settings</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
