export type ContractStatus = "draft" | "funded" | "active" | "disputed" | "resolved" | "cancelled";
export type DisputeStatus = "raised" | "deliberating" | "decided" | "appealed" | "executed";
export type VerdictKind = "full_release" | "partial_release" | "refund" | "needs_more_evidence";

export interface Contract {
  id: string;
  title: string;
  description: string;
  buyer_address: string;
  seller_address: string;
  arbiter_agent?: string | null;
  success_criteria: string[];
  subjective_clauses: string[];
  deadline: string;
  amount_usdc: string;
  status: ContractStatus;
  circle_payment_id?: string | null;
  circle_escrow_wallet_id?: string | null;
  chain_escrow_id?: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface EvidenceItem {
  filename: string;
  content_type?: string | null;
  url: string;
  sha256: string;
  size_bytes: number;
}

export interface Dispute {
  id: string;
  contract_id: string;
  raised_by: string;
  claim: string;
  requested_outcome: VerdictKind;
  evidence: EvidenceItem[];
  status: DisputeStatus;
  appeal_count: number;
  created_at: string;
  updated_at: string;
}

export interface Verdict {
  id: string;
  dispute_id: string;
  kind: VerdictKind;
  release_to_seller_pct: string;
  confidence: string;
  rationale: string;
  leader: Record<string, unknown>;
  validators: Record<string, unknown>[];
  semantic_agreement: Record<string, unknown>;
  payout_tx_id?: string | null;
  created_at: string;
}
