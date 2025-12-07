import React, { useState } from "react";
import { Link } from "react-router-dom";
import { discoverMolecules } from "../api/elysium";
import type { Molecule } from "../api/elysium";

const defaultTarget = "EGFR";

const DiscoverPage: React.FC = () => {
  const [targetId, setTargetId] = useState(defaultTarget);
  const [numMolecules, setNumMolecules] = useState(5);
  const [lipinskiOnly, setLipinskiOnly] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [results, setResults] = useState<Molecule[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setRunId(null);
    setResults([]);

    try {
      const data = await discoverMolecules({
        target_id: targetId,
        num_molecules: numMolecules,
        lipinski_only: lipinskiOnly,
      });
      setRunId(data.run_id);
      setResults(data.molecules);
    } catch (err: any) {
      console.error(err);
      setError(
        err?.response?.data?.detail ??
          "Failed to run discovery. Check if backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between bg-slate-950/80 backdrop-blur">
        <h1 className="text-xl font-semibold tracking-wide">
          ELYSIUM <span className="text-sky-400">Discovery</span>
        </h1>
        <span className="text-xs text-slate-400">
          Backend: <code>FastAPI · DeepPurpose · RDKit</code>
        </span>
      </header>

      <main className="flex-1 px-6 py-6 grid gap-6 md:grid-cols-[minmax(0,360px)_1fr]">
        {/* Left: form */}
        <section className="border border-slate-800 rounded-xl p-4 bg-slate-900/60">
          <h2 className="text-lg font-medium mb-4">New Discovery Run</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm mb-1" htmlFor="target">
                Target ID
              </label>
              <input
                id="target"
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none focus:border-sky-400"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                placeholder="EGFR"
              />
              <p className="text-xs text-slate-400 mt-1">
                Later we&apos;ll connect this to a target registry / UniProt.
              </p>
            </div>

            <div>
              <label className="block text-sm mb-1" htmlFor="num">
                Number of molecules
              </label>
              <input
                id="num"
                type="number"
                min={1}
                max={100}
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none focus:border-sky-400"
                value={numMolecules}
                onChange={(e) => setNumMolecules(Number(e.target.value))}
              />
            </div>

            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={lipinskiOnly}
                onChange={(e) => setLipinskiOnly(e.target.checked)}
                className="h-4 w-4 rounded border-slate-600 bg-slate-900"
              />
              Only keep molecules that pass Lipinski (ADMET filter)
            </label>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-md bg-sky-500 hover:bg-sky-400 disabled:bg-slate-600 py-2 text-sm font-medium text-slate-950 transition-colors"
            >
              {loading ? "Running pipeline..." : "Run discovery"}
            </button>

            {error && (
              <p className="text-sm text-red-400 bg-red-950/40 border border-red-700 rounded-md px-3 py-2">
                {error}
              </p>
            )}

            {runId && (
              <p className="text-xs text-slate-400 mt-1">
                Run ID: {" "}
                <Link
                  to={`/runs/${runId}`}
                  className="text-sky-400 hover:text-sky-300"
                >
                    {runId}
                </Link>
              </p>
            )}
          </form>
        </section>

        {/* Right: results */}
        <section className="border border-slate-800 rounded-xl p-4 bg-slate-900/40 overflow-auto">
          <h2 className="text-lg font-medium mb-4">
            Results{" "}
            <span className="text-xs text-slate-400">
              ({results.length} molecules)
            </span>
          </h2>

          {results.length === 0 && !loading && (
            <p className="text-sm text-slate-400">
              Run a discovery to see candidate molecules scored by DeepPurpose,
              annotated with similarity + ADMET.
            </p>
          )}

          <div className="space-y-3">
            {results.map((mol, idx) => (
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
        </section>
      </main>
    </div>
  );
};

export default DiscoverPage;
