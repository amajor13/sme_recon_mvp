export interface ReconciliationMetrics {
  // Core metrics
  total_records: number;
  total_matches: number;
  total_matched_records: number;
  total_unmatched_records: number;
  match_rate: number;
  
  // Match quality metrics
  perfect_amount_matches: number;
  high_confidence: number;
  medium_confidence: number;
  low_confidence: number;
  average_score: number;
  
  // Financial metrics
  gstr2b_total: number;
  tally_total: number;
  matched_gstr2b_total: number;
  matched_tally_total: number;
  unmatched_gstr2b_total: number;
  unmatched_tally_total: number;
  total_variance: number;
  total_amount_differences: number;
  largest_discrepancy: number;
  
  // Legacy fields for compatibility
  unmatched_total: number;
  unmatched_gstr2b?: number;
  unmatched_tally?: number;
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