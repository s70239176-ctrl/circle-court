import type { Contract, Dispute, EvidenceItem, Verdict } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";
const API_KEY = import.meta.env.VITE_API_KEY ?? "dev-circle-court-key";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}/api${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
      ...(init.headers ?? {})
    }
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<T>;
}

export const api = {
  contracts: () => request<Contract[]>("/contracts"),
  contract: (id: string) => request<Contract>(`/contracts/${id}`),
  createContract: (payload: unknown) => request<Contract>("/contracts", { method: "POST", body: JSON.stringify(payload) }),
  disputes: () => request<Dispute[]>("/disputes"),
  dispute: (id: string) => request<Dispute>(`/disputes/${id}`),
  createDispute: (payload: unknown) => request<Dispute>("/disputes", { method: "POST", body: JSON.stringify(payload) }),
  verdict: (id: string) => request<Verdict | null>(`/disputes/${id}/verdict`),
  deliberate: (id: string) => request<Verdict>(`/disputes/${id}/deliberate`, { method: "POST" }),
  appeal: (id: string) => request<Verdict>(`/disputes/${id}/appeal`, { method: "POST" }),
  command: (payload: unknown) => request<{ action: string; message: string; data: Record<string, unknown> }>("/agent/command", { method: "POST", body: JSON.stringify(payload) }),
  upload: async (file: File): Promise<EvidenceItem> => {
    const body = new FormData();
    body.append("file", file);
    const response = await fetch(`${API_BASE}/api/evidence/upload`, { method: "POST", headers: { "X-API-Key": API_KEY }, body });
    if (!response.ok) throw new Error(await response.text());
    return response.json() as Promise<EvidenceItem>;
  }
};
