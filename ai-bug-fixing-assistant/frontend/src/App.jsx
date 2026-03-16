import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Analysis from "./pages/Analysis";
import Chat from "./pages/Chat";
import Sidebar from "./components/Sidebar";
import "./index.css";

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [session, setSession] = useState(null);

  return (
    <div className="app-shell">
      <Sidebar activePage={page} onNavigate={setPage} session={session} />
      <main className="app-main">
        {page === "dashboard" && <Dashboard onStartAnalysis={() => setPage("analysis")} />}
        {page === "analysis" && <Analysis onComplete={(s) => { setSession(s); setPage("chat"); }} />}
        {page === "chat" && <Chat session={session} onBack={() => setPage("dashboard")} />}
      </main>
    </div>
  );
}
