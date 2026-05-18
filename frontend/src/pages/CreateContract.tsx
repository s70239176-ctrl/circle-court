import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { Button, Input, Panel, Textarea } from "../components/ui";

export function CreateContract() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [criteria, setCriteria] = useState("Final deliverable accepted by buyer\nAll source files provided");
  const mutation = useMutation({
    mutationFn: api.createContract,
    onSuccess: (contract) => {
      qc.invalidateQueries({ queryKey: ["contracts"] });
      navigate(`/contracts/${contract.id}`);
    }
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    mutation.mutate({
      title: form.get("title"),
      description: form.get("description"),
      buyer_address: form.get("buyer_address"),
      seller_address: form.get("seller_address"),
      arbiter_agent: form.get("arbiter_agent") || null,
      success_criteria: criteria.split("\n"),
      subjective_clauses: String(form.get("subjective_clauses") ?? "").split("\n"),
      deadline: new Date(String(form.get("deadline"))).toISOString(),
      amount_usdc: form.get("amount_usdc"),
      metadata_json: { source: "web" }
    });
  }

  return (
    <Panel className="mx-auto max-w-3xl">
      <h1 className="mb-4 text-xl font-semibold">Create Intelligent Escrow</h1>
      <form onSubmit={submit} className="grid gap-4">
        <Input name="title" placeholder="Contract title" defaultValue="Agent Landing Page Delivery" required />
        <Textarea name="description" placeholder="Natural-language contract description" defaultValue="Seller will design and ship a responsive landing page for the buyer's autonomous agent product, including source files and deployment notes." required />
        <div className="grid gap-4 sm:grid-cols-2">
          <Input name="buyer_address" placeholder="Buyer wallet or agent id" defaultValue="buyer-agent-demo" required />
          <Input name="seller_address" placeholder="Seller wallet or agent id" defaultValue="seller-wallet-demo" required />
        </div>
        <Textarea value={criteria} onChange={(e) => setCriteria(e.target.value)} placeholder="Success criteria, one per line" required />
        <Textarea name="subjective_clauses" placeholder="Subjective clauses, one per line" defaultValue="Design should feel polished, original, and appropriate for a fintech audience" />
        <div className="grid gap-4 sm:grid-cols-3">
          <Input name="deadline" type="datetime-local" required />
          <Input name="amount_usdc" type="number" min="1" step="0.01" defaultValue="100" required />
          <Input name="arbiter_agent" placeholder="Optional arbiter agent" />
        </div>
        <Button disabled={mutation.isPending}>{mutation.isPending ? "Creating..." : "Create and Fund Escrow"}</Button>
        {mutation.error ? <p className="text-sm text-court-coral">{String(mutation.error)}</p> : null}
      </form>
    </Panel>
  );
}
