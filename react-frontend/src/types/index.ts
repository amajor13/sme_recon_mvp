export interface ReconciliationMetrics {
  total_matches: number;
  high_confidence: number;
  medium_confidence: number;
  low_confidence: number;
  average_score: number;
  unmatched_total: number;
  unmatched_gstr2b: number;
  unmatched_tally: number;
  // Enhanced financial metrics
  total_gstr2b_amount?: number;
  total_tally_amount?: number;
  total_amount_difference?: number;
  largest_discrepancy?: number;
  perfect_matches?: number;
  total_transactions?: number;
}

export interface ReconciledTransaction {
  match_score: number;
  gstr2b_invoice_no: string;
  gstr2b_date: string;
  gstr2b_supplier_gstin: string;
  gstr2b_total_amount: number;
  gstr2b_taxable_value: number;
  gstr2b_igst: number;
  gstr2b_cgst: number;
  gstr2b_sgst: number;
  tally_invoice_no: string;
  tally_date: string;
  tally_supplier_gstin: string;
  tally_total_amount: number;
  tally_base_amount: number;
  tally_tax_amount: number;
  tally_type: string;
  amount_difference?: number;
}

export interface UnmatchedTransaction {
  date: string;
  invoice_no: string;
  supplier_gstin: string;
  total_amount: number;
  taxable_value?: number;
  igst?: number;
  cgst?: number;
  sgst?: number;
  base_amount?: number;
  tax_amount?: number;
  type?: string;
}

export interface DuplicateGroup {
  field: string;
  value: string;
  count: number;
  transactions: UnmatchedTransaction[];
}

export interface ReconciliationResponse {
  metrics: ReconciliationMetrics;
  reconciled: ReconciledTransaction[];
  unmatched_bank: UnmatchedTransaction[];
  unmatched_ledger: UnmatchedTransaction[];
  duplicates: DuplicateGroup[];
}

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
}

export type ConfidenceLevel = 'all' | 'high' | 'medium' | 'low';

export interface ApiError {
  detail: string;
  status?: number;
}