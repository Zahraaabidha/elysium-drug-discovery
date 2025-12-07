// src/pages/GraphsHomePage.tsx
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const GraphsHomePage: React.FC = () => {
  const [targetId, setTargetId] = useState("EGFR");
  const [drugName, setDrugName] = useState("Ibuprofen");
  const navigate = useNavigate();

  const goTarget = (e: React.FormEvent) => {
    e.preventDefault();
    navigate(`/graph/target/${encodeURIComponent(targetId)}`);
  };

  const goDrug = (e: React.FormEvent) => {
    e.preventDefault();
    navigate(`/graph/drug/${encodeURIComponent(drugName)}`);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between bg-slate-950/80 backdrop-blur">
        <h1 className="text-xl font-semibold tracking-wide">
          ELYSIUM <span className="text-sky-400">Graphs</span>
        </h1>
        <Link
          to="/discover"
          className="text-xs text-sky-400 hover:text-sky-300"
        >
          ← Back to discovery
        </Link>
      </header>

      <main className="flex-1 px-6 py-6 grid gap-6 md:grid-cols-2">
        <section className="border border-slate-800 rounded-xl p-4 bg-slate-900/60">
          <h2 className="text-lg font-medium mb-3">By target</h2>
          <form className="space-y-3" onSubmit={goTarget}>
            <div>
              <label className="block text-sm mb-1" htmlFor="target-graph">
                Target ID
              </label>
              <input
                id="target-graph"
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none focus:border-sky-400"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
              />
            </div>
            <button
              type="submit"
              className="rounded-md bg-sky-500 hover:bg-sky-400 py-2 px-4 text-sm font-medium text-slate-950"
            >
              View target graph
            </button>
          </form>
        </section>

        <section className="border border-slate-800 rounded-xl p-4 bg-slate-900/60">
          <h2 className="text-lg font-medium mb-3">By known drug</h2>
          <form className="space-y-3" onSubmit={goDrug}>
            <div>
              <label className="block text-sm mb-1" htmlFor="drug-graph">
                Drug name
              </label>
              <input
                id="drug-graph"
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none focus:border-sky-400"
                value={drugName}
                onChange={(e) => setDrugName(e.target.value)}
              />
            </div>
            <button
              type="submit"
              className="rounded-md bg-sky-500 hover:bg-sky-400 py-2 px-4 text-sm font-medium text-slate-950"
            >
              View drug graph
            </button>
          </form>
        </section>
      </main>
    </div>
  );
};

export default GraphsHomePage;
