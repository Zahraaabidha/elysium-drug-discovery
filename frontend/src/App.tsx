// src/App.tsx
import React from "react";
import { Routes, Route, Navigate, Link } from "react-router-dom";
import DiscoverPage from "./pages/DiscoverPage";
import RunsPage from "./pages/RunsPage";
import RunDetailPage from "./pages/RunDetailPage";
import GraphsHomePage from "./pages/GraphsHomePage";
import TargetGraphPage from "./pages/TargetGraphPage";
import DrugGraphPage from "./pages/DrugGraphPage";

const App: React.FC = () => {
  return (
    <div className="min-h-screen">
      <nav className="flex gap-4 px-6 py-2 text-xs bg-slate-950/80 border-b border-slate-900">
        <Link
          to="/discover"
          className="text-sky-400 hover:text-sky-300"
        >
          Discovery
        </Link>
        <Link to="/runs" className="text-slate-300 hover:text-slate-100">
          Runs
        </Link>
        <Link to="/graphs" className="text-slate-300 hover:text-slate-100">
          Graphs
        </Link>
      </nav>

      <Routes>
        <Route path="/discover" element={<DiscoverPage />} />
        <Route path="/runs" element={<RunsPage />} />
        <Route path="/runs/:runId" element={<RunDetailPage />} />
        <Route path="/graphs" element={<GraphsHomePage />} />
        <Route path="/graph/target/:targetId" element={<TargetGraphPage />} />
        <Route path="/graph/drug/:drugName" element={<DrugGraphPage />} />
        <Route path="*" element={<Navigate to="/discover" replace />} />
      </Routes>
    </div>
  );
};

export default App;
