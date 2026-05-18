import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { Upload } from "lucide-react";
import { api } from "../lib/api";
import type { EvidenceItem } from "../lib/types";
import { Button, Input, Panel, Textarea } from "../components/ui";

export function RaiseDispute() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const upload = useMutation({ mutationFn: api.upload, onSuccess: (item) => setEvidence((old) => [...old, item]) });
  const create = useMutation({
    mutationFn: api.createDispute,
    onSuccess: (dispute) => navigate(`/disputes/${dispute.id}`)
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    create.mutate({
      contract_id: id,
      raised_by: form.get("raised_by"),
      claim: form.get("claim"),
      requested_outcome: form.get("requested_outcome"),
      evidence
    });
  }

  return (
    <Panel className="mx-auto max-w-3xl">
      <h1 className="mb-4 text-xl font-semibold">Raise Dispute</h1>
      <form onSubmit={submit} className="grid gap-4">
        <Input name="raised_by" placeholder="Your wallet or agent id" required />
        <Textarea name="claim" placeholder="Explain what happened and what the jury should decide" required />
        <select name="requested_outcome" className="h-10 rounded-md border border-court-line bg-[#10141d] px-3 text-sm">
          <option value="full_release">Full release</option>
          <option value="partial_release">Partial release</option>
          <option value="refund">Refund</option>
          <option value="needs_more_evidence">Needs more evidence</option>
        </select>
        <label className="flex cursor-pointer items-center justify-center gap-2 rounded-md border border-dashed border-court-line p-5 text-sm text-slate-300 hover:border-court-mint">
          <Upload size={16} />
          Upload evidence
          <input type="file" className="hidden" onChange={(event) => event.target.files?.[0] && upload.mutate(event.target.files[0])} />
        </label>
        {evidence.map((item) => <div key={item.sha256} className="text-sm text-slate-400">{item.filename} uploaded</div>)}
        <Button disabled={create.isPending}>{create.isPending ? "Submitting..." : "Submit Dispute"}</Button>
      </form>
    </Panel>
  );
}
