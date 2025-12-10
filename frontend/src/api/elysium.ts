// src/api/elysium.ts
import { apiClient } from "./client";

export interface ADMET {
  molecular_weight: number;
  logp: number;
  hbd: number;
  hba: number;
  rotatable_bonds: number;
  tpsa: number;
  lipinski_violations: number;
  lipinski_pass: boolean;
}

export interface SimilarDrug {
  name: string;
  smiles: string;
  indication: string | null;
  similarity: number | null;
  semantic_similarity: number | null;
}

export interface Molecule {
  smiles: string;
  score: number;
  source: string;
  notes: string | null;
  similar_drug: SimilarDrug | null;
  similar_drug_semantic: SimilarDrug | null;
  admet: ADMET | null;
}

export interface DiscoverRequest {
  target_id: string;
  num_molecules: number;
  lipinski_only?: boolean;
}

export interface DiscoverResponse {
  run_id: string;
  target_id: string;
  num_molecules: number;
  molecules: Molecule[];
}

/* ---------- runs ---------- */

export interface RunSummary {
  run_id: string;
  target_id: string;
  num_molecules: number;
  created_at: string;
}

export interface RunsListResponse {
  runs: RunSummary[];
}

/* ---------- graph types ---------- */

export interface TargetGraphEntry {
  run_id: string;
  molecule_index: number;
  smiles: string;
  score: number;
  similar_drug: SimilarDrug | null;
}

export interface TargetGraphResponse {
  target_id: string;
  molecules: TargetGraphEntry[];
}

export interface DrugGraphEntry {
  target_id: string;
  run_id: string;
  molecule_index: number;
  smiles: string;
  score: number;
}

export interface DrugGraphResponse {
  drug_name: string;
  molecules: DrugGraphEntry[];
}

/* ---------- API functions ---------- */

export async function discoverMolecules(
  payload: DiscoverRequest
): Promise<DiscoverResponse> {
  const { data } = await apiClient.post<DiscoverResponse>(
    "/discover",
    payload
  );
  return data;
}

export async function listRuns(): Promise<RunsListResponse> {
  const { data } = await apiClient.get<RunsListResponse>("/runs");
  return data;
}

export async function getRun(runId: string): Promise<DiscoverResponse> {
  const { data } = await apiClient.get<DiscoverResponse>(`/runs/${runId}`);
  return data;
}

export async function getTargetGraph(
  targetId: string
): Promise<TargetGraphResponse> {
  const { data } = await apiClient.get<TargetGraphResponse>(
    `/graph/target/${encodeURIComponent(targetId)}`
  );
  return data;
}

export async function getDrugGraph(
  drugName: string
): Promise<DrugGraphResponse> {
  const { data } = await apiClient.get<DrugGraphResponse>(
    `/graph/drug/${encodeURIComponent(drugName)}`
  );
  return data;
}
