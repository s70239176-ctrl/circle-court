import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Terminal } from "lucide-react";
import { api } from "../lib/api";
import { Button, Panel, Textarea } from "../components/ui";

export function AgentCommand() {
  const [output, setOutput] = useState<Record<string, unknown> | null>(null);
  const mutation = useMutation({ mutationFn: api.command, onSuccess: setOutput });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    mutation.mutate({ actor: "web-agent", command: form.get("command"), dry_run: false });
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[420px_1fr]">
      <Panel>
        <h1 className="mb-4 flex items-center gap-2 text-xl font-semibold"><Terminal size={18} /> Agent Command Center</h1>
        <form onSubmit={submit} className="space-y-4">
          <Textarea name="command" defaultValue="list contracts" />
          <Button disabled={mutation.isPending}>{mutation.isPending ? "Running..." : "Execute"}</Button>
        </form>
      </Panel>
      <Panel>
        <pre className="max-h-[560px] overflow-auto whitespace-pre-wrap text-sm text-slate-300">{output ? JSON.stringify(output, null, 2) : "Awaiting command..."}</pre>
      </Panel>
    </div>
  );
}
