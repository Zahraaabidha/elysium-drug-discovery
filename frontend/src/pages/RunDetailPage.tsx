import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getRun } from "../api/elysium";
import type { DiscoverResponse } from "../api/elysium";
import type { Molecule } from "../api/elysium";

const RunDetailPage: React.FC = () => {
  const { runId } = useParams<{ runId: string }>();
  const [run, setRun] = useState<DiscoverResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) return;

    const fetchRun = async () => {
      try {
        const data = await getRun(runId);
        setRun(data);
      } catch (err) {
        console.error(err);
        setError("Failed to load run.");
      } finally {
        setLoading(false);
      }
    };

    fetchRun();
  }, [runId]);

  const molecules: Molecule[] = run?.molecules ?? [];

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between bg-slate-950/80 backdrop-blur">
        <div>
          <h1 className="text-xl font-semibold tracking-wide">
            Run <span className="text-sky-400">{runId?.slice(0, 8)}…</span>
          </h1>
          {run && (
            <p className="text-xs text-slate-400 mt-1">
              Target: <span className="font-semibold">{run.target_id}</span> ·{" "}
              Molecules: <span className="font-semibold">{run.num_molecules}</span>
            </p>
          )}
        </div>
        <div className="flex gap-3 text-xs">
          <Link to="/runs" className="text-sky-400 hover:text-sky-300">
            ← All runs
          </Link>
          <Link
            to={`/graph/target/${run?.target_id ?? "EGFR"}`}
            className="text-slate-400 hover:text-slate-200"
          >
            View target graph
          </Link>
        </div>
      </header>

      <main className="flex-1 px-6 py-6">
        {loading && <p className="text-sm text-slate-400">Loading run…</p>}
        {error && (
          <p className="text-sm text-red-400 bg-red-950/40 border border-red-700 rounded-md px-3 py-2">
            {error}
          </p>
        )}

        {!loading && !error && run && (
          <div className="space-y-3">
            {molecules.map((mol, idx) => (
              <div
                key={idx}
                className="border border-slate-800 rounded-lg p-3 bg-slate-950/70 text-sm"
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="font-mono text-xs text-slate-400">
                    {mol.smiles}
                  </span>
                  <span className="text-xs">
                    Score:{" "}
                    <span className="font-semibold text-sky-300">
                      {mol.score.toFixed(3)}
                    </span>
                  </span>
                </div>

                {mol.similar_drug && (
                  <p className="text-xs text-slate-300">
                    Similar to{" "}
                    <span className="font-semibold">
                      {mol.similar_drug.name}
                    </span>{" "}
                    (Tanimoto{" "}
                    {mol.similar_drug.similarity?.toFixed(2) ?? "–"})
                  </p>
                )}

                {mol.admet && (
                  <p className="text-xs text-slate-400 mt-1">
                    MW {mol.admet.molecular_weight.toFixed(1)} · logP{" "}
                    {mol.admet.logp.toFixed(2)} · HBD {mol.admet.hbd} · HBA{" "}
                    {mol.admet.hba} · TPSA {mol.admet.tpsa.toFixed(1)} ·{" "}
                    <span
                      className={
                        mol.admet.lipinski_pass
                          ? "text-emerald-300"
                          : "text-red-300"
                      }
                    >
                      Lipinski:{" "}
                      {mol.admet.lipinski_pass
                        ? "PASS"
                        : `FAIL (${mol.admet.lipinski_violations})`}
                    </span>
                  </p>
                )}

                {mol.notes && (
                  <p className="text-[11px] text-slate-500 mt-1">
                    {mol.notes}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default RunDetailPage;
