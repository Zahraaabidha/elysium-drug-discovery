// frontend/src/api/client.ts
import axios from "axios";
import type { AxiosRequestHeaders } from "axios";
import type { DiscoverRequest, DiscoverResponse } from "./elysium";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const API_KEY = import.meta.env.VITE_API_KEY || "changeme"; // 🔑 matches backend

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach API key to every request
apiClient.interceptors.request.use((config) => {
  (config.headers as AxiosRequestHeaders)["X-API-KEY"] = API_KEY;
  return config;
});

// Simple synchronous discovery call
export async function runDiscovery(
  payload: DiscoverRequest
): Promise<DiscoverResponse> {
  const res = await apiClient.post<DiscoverResponse>("/discover", payload);
  return res.data;
}
