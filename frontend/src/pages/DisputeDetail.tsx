import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { RefreshCw, Scale } from "lucide-react";
import { api } from "../lib/api";
import { Badge, Button, GhostButton, Panel } from "../components/ui";

export function DisputeDetail() {
  const { id = "" } = useParams();
  const qc = useQueryClient();
  const dispute = useQuery({ queryKey: ["dispute", id], queryFn: () => api.dispute(id), enabled: Boolean(id), refetchInterval: 5000 });
  const verdict = useQuery({ queryKey: ["verdict", id], queryFn: () => api.verdict(id), enabled: Boolean(id), refetchInterval: 5000 });
  const deliberate = useMutation({ mutationFn: () => api.deliberate(id), onSuccess: () => qc.invalidateQueries() });
  const appeal = useMutation({ mutationFn: () => api.appeal(id), onSuccess: () => qc.invalidateQueries() });

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_380px]">
      <Panel>
        <div className="flex items-center justify-between gap-3">
          <h1 className="text-xl font-semibold">Dispute</h1>
          {dispute.data ? <Badge tone={dispute.data.status === "executed" ? "good" : "warn"}>{dispute.data.status}</Badge> : null}
        </div>
        <p className="mt-4 text-slate-300">{dispute.data?.claim ?? "Loading..."}</p>
        <div className="mt-5 text-sm text-slate-400">Requested outcome: {dispute.data?.requested_outcome}</div>
        <div className="mt-5 space-y-2">
          {dispute.data?.evidence.map((item) => (
            <a key={item.sha256} href={item.url} className="block rounded-md border border-court-line p-3 text-sm hover:border-court-mint">
              {item.filename}
            </a>
          ))}
        </div>
      </Panel>
      <Panel className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Live Verdict</h2>
          <RefreshCw size={16} className="text-slate-500" />
        </div>
        {verdict.data ? (
          <div className="space-y-3">
            <Badge tone={verdict.data.kind === "refund" ? "bad" : verdict.data.kind === "partial_release" ? "warn" : "good"}>{verdict.data.kind}</Badge>
            <div className="text-3xl font-semibold">{verdict.data.release_to_seller_pct}%</div>
            <div className="text-sm text-slate-400">Confidence {Number(verdict.data.confidence).toFixed(2)}</div>
            <p className="text-sm text-slate-300">{verdict.data.rationale}</p>
            <div className="text-xs text-slate-500">Payout: {verdict.data.payout_tx_id ?? "pending"}</div>
          </div>
        ) : (
          <p className="text-sm text-slate-400">No verdict yet.</p>
        )}
        <Button onClick={() => deliberate.mutate()} disabled={deliberate.isPending} className="w-full"><Scale size={16} /> Run Jury</Button>
        <GhostButton onClick={() => appeal.mutate()} disabled={appeal.isPending} className="w-full">Appeal to Larger Panel</GhostButton>
      </Panel>
    </div>
  );
}
