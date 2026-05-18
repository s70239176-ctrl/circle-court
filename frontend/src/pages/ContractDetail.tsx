import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { FileWarning } from "lucide-react";
import { api } from "../lib/api";
import { Badge, Button, Panel } from "../components/ui";

export function ContractDetail() {
  const { id = "" } = useParams();
  const contract = useQuery({ queryKey: ["contract", id], queryFn: () => api.contract(id), enabled: Boolean(id) });
  if (!contract.data) return <Panel>Loading contract...</Panel>;
  const item = contract.data;
  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_340px]">
      <Panel>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold">{item.title}</h1>
          <Badge tone={item.status === "resolved" ? "good" : item.status === "disputed" ? "warn" : "neutral"}>{item.status}</Badge>
        </div>
        <p className="mt-4 text-slate-300">{item.description}</p>
        <h2 className="mt-6 font-semibold">Success Criteria</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-300">
          {item.success_criteria.map((criterion) => <li key={criterion}>{criterion}</li>)}
        </ul>
        <h2 className="mt-6 font-semibold">Subjective Clauses</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-300">
          {item.subjective_clauses.map((clause) => <li key={clause}>{clause}</li>)}
        </ul>
      </Panel>
      <Panel className="space-y-4">
        <div>
          <div className="text-sm text-slate-400">Amount</div>
          <div className="text-2xl font-semibold">{item.amount_usdc} USDC</div>
        </div>
        <div className="text-sm text-slate-300">
          <div>Buyer: {item.buyer_address}</div>
          <div>Seller: {item.seller_address}</div>
          <div>Deadline: {new Date(item.deadline).toLocaleString()}</div>
          <div>Circle wallet: {item.circle_escrow_wallet_id ?? "pending"}</div>
          <div>Chain escrow: {item.chain_escrow_id ?? "pending"}</div>
        </div>
        <Link to={`/contracts/${item.id}/dispute`}>
          <Button className="w-full"><FileWarning size={16} /> Raise Dispute</Button>
        </Link>
      </Panel>
    </div>
  );
}
