import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { AlertTriangle, CircleDollarSign, Scale } from "lucide-react";
import { api } from "../lib/api";
import { Badge, Panel } from "../components/ui";

export function Dashboard() {
  const contracts = useQuery({ queryKey: ["contracts"], queryFn: api.contracts });
  const disputes = useQuery({ queryKey: ["disputes"], queryFn: api.disputes });
  const total = contracts.data?.reduce((sum, item) => sum + Number(item.amount_usdc), 0) ?? 0;

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-3">
        <Panel>
          <div className="flex items-center justify-between text-slate-400"><span>Escrowed USDC</span><CircleDollarSign size={18} /></div>
          <div className="mt-3 text-3xl font-semibold">{total.toFixed(2)}</div>
        </Panel>
        <Panel>
          <div className="flex items-center justify-between text-slate-400"><span>Contracts</span><Scale size={18} /></div>
          <div className="mt-3 text-3xl font-semibold">{contracts.data?.length ?? 0}</div>
        </Panel>
        <Panel>
          <div className="flex items-center justify-between text-slate-400"><span>Open Disputes</span><AlertTriangle size={18} /></div>
          <div className="mt-3 text-3xl font-semibold">{disputes.data?.filter((d) => d.status !== "executed").length ?? 0}</div>
        </Panel>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <Panel>
          <div className="mb-3 flex items-center justify-between">
            <h1 className="text-lg font-semibold">Active Contracts</h1>
            <Link className="text-sm text-court-mint" to="/create">New contract</Link>
          </div>
          <div className="divide-y divide-court-line">
            {contracts.data?.map((contract) => (
              <Link key={contract.id} to={`/contracts/${contract.id}`} className="grid gap-2 py-3 hover:bg-white/[0.02] sm:grid-cols-[1fr_auto]">
                <div>
                  <div className="font-medium">{contract.title}</div>
                  <div className="line-clamp-1 text-sm text-slate-400">{contract.description}</div>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <Badge tone={contract.status === "resolved" ? "good" : contract.status === "disputed" ? "warn" : "neutral"}>{contract.status}</Badge>
                  <span>{contract.amount_usdc} USDC</span>
                </div>
              </Link>
            ))}
          </div>
        </Panel>

        <Panel>
          <h2 className="mb-3 text-lg font-semibold">Dispute Queue</h2>
          <div className="space-y-3">
            {disputes.data?.map((dispute) => (
              <Link key={dispute.id} to={`/disputes/${dispute.id}`} className="block rounded-md border border-court-line p-3 hover:border-court-mint">
                <div className="flex items-center justify-between gap-3">
                  <Badge tone={dispute.status === "executed" ? "good" : "warn"}>{dispute.status}</Badge>
                  <span className="text-xs text-slate-500">{dispute.requested_outcome}</span>
                </div>
                <p className="mt-2 line-clamp-3 text-sm text-slate-300">{dispute.claim}</p>
              </Link>
            ))}
          </div>
        </Panel>
      </section>
    </div>
  );
}
