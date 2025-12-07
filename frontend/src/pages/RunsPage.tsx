import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listRuns } from "../api/elysium";
import type { RunSummary } from "../api/elysium";

const RunsPage: React.FC = () => {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRuns = async () => {
      try {
        const data = await listRuns();
        setRuns(data.runs);
      } catch (err) {
        console.error(err);
        setError("Failed to load runs. Is the backend running?");
      } finally {
        setLoading(false);
      }
    };

    fetchRuns();
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between bg-slate-950/80 backdrop-blur">
        <h1 className="text-xl font-semibold tracking-wide">
          ELYSIUM <span className="text-sky-400">Runs</span>
        </h1>

        <Link to="/discover" className="text-xs text-sky-400 hover:text-sky-300">
          ← Back to discovery
        </Link>
      </header>

      <main className="flex-1 px-6 py-6">
        {loading && <p className="text-sm text-slate-400">Loading runs…</p>}

        {error && (
          <p className="text-sm text-red-400 bg-red-950/40 border border-red-700 rounded-md px-3 py-2">
            {error}
          </p>
        )}

        {!loading && !error && runs.length === 0 && (
          <p className="text-sm text-slate-400">No runs yet. Run discovery first.</p>
        )}

        {runs.length > 0 && (
          <div className="overflow-x-auto border border-slate-800 rounded-xl bg-slate-950/60">
            <table className="w-full text-sm">
              <thead className="bg-slate-900/80 text-slate-300">
                <tr>
                  <th className="px-4 py-2 text-left">Run ID</th>
                  <th className="px-4 py-2 text-left">Target</th>
                  <th className="px-4 py-2 text-right">Molecules</th>
                  <th className="px-4 py-2 text-left">Created</th>
                </tr>
              </thead>

              <tbody>
                {runs.map((run, index) => (
                  <tr
                    key={run.run_id}
                    className="border-t border-slate-800 hover:bg-slate-900/70"
                  >
                    <td className="px-4 py-2 font-mono text-xs">
                      <div className="flex items-center gap-2">
                        <Link
                          to={`/runs/${run.run_id}`}
                          className="text-sky-400 hover:text-sky-300"
                        >
                          {run.run_id}
                        </Link>

                        {index === 0 && (
                          <span className="ml-1 text-[10px] text-emerald-300 bg-emerald-900/40 px-1.5 py-0.5 rounded">
                            latest
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="px-4 py-2 text-xs">{run.target_id}</td>

                    <td className="px-4 py-2 text-xs text-right">
                      {run.num_molecules}
                    </td>

                    <td className="px-4 py-2 text-xs text-slate-400">
                      {new Date(run.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
};

export default RunsPage;
