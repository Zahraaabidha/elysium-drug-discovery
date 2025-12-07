// src/pages/TargetGraphPage.tsx
import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getTargetGraph} from "../api/elysium";
import type { TargetGraphEntry} from "../api/elysium";
import type { TargetGraphResponse,} from "../api/elysium";

const TargetGraphPage: React.FC = () => {
  const { targetId } = useParams<{ targetId: string }>();
  const [graph, setGraph] = useState<TargetGraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!targetId) return;

    const fetchGraph = async () => {
      try {
        const data = await getTargetGraph(targetId);
        setGraph(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load target graph.");
      } finally {
        setLoading(false);
      }
    };

    fetchGraph();
  }, [targetId]);

  const entries: TargetGraphEntry[] = graph?.molecules ?? [];

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between bg-slate-950/80 backdrop-blur">
        <div>
          <h1 className="text-xl font-semibold tracking-wide">
            Target graph:{" "}
            <span className="text-sky-400">{targetId}</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Generated molecules that bind this target + their closest known drug.
          </p>
        </div>
        <div className="flex gap-3 text-xs">
          <Link to="/graphs" className="text-sky-400 hover:text-sky-300">
            ← Graph explorer
          </Link>
          <Link to="/runs" className="text-slate-400 hover:text-slate-200">
            Runs
          </Link>
        </div>
      </header>

      <main className="flex-1 px-6 py-6">
        {loading && <p className="text-sm text-slate-400">Loading graph…</p>}
        {error && (
          <p className="text-sm text-red-400 bg-red-950/40 border border-red-700 rounded-md px-3 py-2">
            {error}
          </p>
        )}

        {!loading && !error && entries.length === 0 && (
          <p className="text-sm text-slate-400">
            No molecules found for this target yet. Run discovery first.
          </p>
        )}

        <div className="space-y-3">
          {entries.map((e, idx) => (
            <div
              key={idx}
              className="border border-slate-800 rounded-lg p-3 bg-slate-950/70 text-sm"
            >
              <div className="flex items-center justify-between">
                <div className="flex flex-col gap-1">
                  <span className="font-mono text-xs text-slate-400">
                    {e.smiles}
                  </span>
                  <span className="text-xs text-slate-400">
                    Run:{" "}
                    <Link
                      to={`/runs/${e.run_id}`}
                      className="text-sky-400 hover:text-sky-300"
                    >
                      {e.run_id.slice(0, 8)}…
                    </Link>{" "}
                    · index {e.molecule_index}
                  </span>
                </div>
                <span className="text-xs">
                  Score:{" "}
                  <span className="font-semibold text-sky-300">
                    {e.score.toFixed(3)}
                  </span>
                </span>
              </div>

              {e.similar_drug && (
                <p className="text-xs text-slate-300 mt-1">
                  Nearest known drug:{" "}
                  <span className="font-semibold">
                    {e.similar_drug.name}
                  </span>{" "}
                  (Tanimoto{" "}
                  {e.similar_drug.similarity?.toFixed(2) ?? "–"})
                </p>
              )}
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default TargetGraphPage;
