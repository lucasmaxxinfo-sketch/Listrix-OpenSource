import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "@/context/AuthContext";
import { WorkspaceProvider, useWorkspace } from "@/context/WorkspaceContext";
import AppShell from "@/components/layout/AppShell";
import LandscapeGate from "@/components/deck/LandscapeGate";
import AIAssistant from "@/components/AIAssistant";
import Dashboard from "@/pages/Dashboard";
import Items from "@/pages/Items";
import ItemDetail from "@/pages/ItemDetail";
import Workflows from "@/pages/Workflows";
import AIManager from "@/pages/AIManager";
import Market from "@/pages/Market";
import Financials from "@/pages/Financials";
import AIControl from "@/pages/AIControl";
import Inbox from "@/pages/Inbox";
import IntegrationHub from "@/pages/IntegrationHub";
import Search from "@/pages/Search";
import Settings from "@/pages/Settings";
import Login from "@/pages/Login";
import { Loader2 } from "lucide-react";

function Shell() {
  const { ready } = useWorkspace();
  if (!ready) return <div className="flex min-h-screen items-center justify-center bg-background text-muted-foreground"><Loader2 className="animate-spin" size={28} /></div>;
  return (
    <>
      <AppShell>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/items" element={<Items />} />
          <Route path="/items/:id" element={<ItemDetail />} />
          <Route path="/workflows" element={<Workflows />} />
          <Route path="/ai-manager" element={<AIManager />} />
          <Route path="/market" element={<Market />} />
          <Route path="/financials" element={<Financials />} />
          <Route path="/search" element={<Search />} />
          <Route path="/inbox" element={<Inbox />} />
          <Route path="/integrations" element={<IntegrationHub />} />
          <Route path="/ai-control" element={<AIControl />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/login" element={<Login />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AppShell>
      <AIAssistant />
    </>
  );
}

function App() {
  return (
    <div className="App min-h-screen bg-background text-foreground">
      <BrowserRouter>
        <AuthProvider>
          <WorkspaceProvider>
            <Shell />
          </WorkspaceProvider>
        </AuthProvider>
        <Toaster position="top-right" theme="dark" richColors />
        <LandscapeGate />
      </BrowserRouter>
    </div>
  );
}

export default App;
