import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number | string | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(Number(amount)) || amount === '') {
    return '₹0.00';
  }
  
  const numAmount = parseFloat(String(amount));
  if (isNaN(numAmount)) {
    return '₹0.00';
  }
  
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR'
  }).format(numAmount);
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr || dateStr === '' || dateStr === 'nan' || dateStr === 'null') {
    return '-';
  }
  
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) {
    return '-';
  }
  
  return date.toLocaleDateString('en-IN');
}

export function getConfidenceClass(score: number): string {
  if (score >= 0.95) return 'confidence-high';
  if (score >= 0.85) return 'confidence-medium';
  return 'confidence-low';
}

export function getConfidenceBadge(score: number): string {
  const percentage = (score * 100).toFixed(1);
  return `${percentage}%`;
}

export async function downloadFile(data: any[], filename: string) {
  try {
    // Dynamic import to avoid bundle size issues
    const XLSX = await import('xlsx');
    
    // Create worksheet from JSON data
    const worksheet = XLSX.utils.json_to_sheet(data);
    
    // Create workbook and add worksheet
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Sheet1');
    
    // Download file
    XLSX.writeFile(workbook, filename);
    
    console.log(`✅ Downloaded ${filename} with ${data.length} records`);
  } catch (error) {
    console.error('Export failed:', error);
    // Fallback to CSV download
    downloadCSV(data, filename.replace('.xlsx', '.csv'));
  }
}

function downloadCSV(data: any[], filename: string) {
  if (data.length === 0) return;
  
  // Get headers from first object
  const headers = Object.keys(data[0]);
  
  // Create CSV content
  const csvContent = [
    headers.join(','),
    ...data.map(row => 
      headers.map(header => {
        const value = row[header];
        // Escape quotes and wrap in quotes if contains comma
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      }).join(',')
    )
  ].join('\n');
  
  // Create and download file
  const blob = new Blob([csvContent], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  window.URL.revokeObjectURL(url);
}

// Enhanced metrics calculation
export function calculateEnhancedMetrics(reconciled: any[], unmatched_gstr2b: any[], unmatched_tally: any[]) {
  const totalGstr2bAmount = reconciled.reduce((sum, r) => sum + (r.gstr2b_total_amount || 0), 0) +
                           unmatched_gstr2b.reduce((sum, u) => sum + (u.total_amount || 0), 0);
  
  const totalTallyAmount = reconciled.reduce((sum, r) => sum + (r.tally_total_amount || 0), 0) +
                          unmatched_tally.reduce((sum, u) => sum + (u.total_amount || 0), 0);
  
  const totalAmountDifference = reconciled.reduce((sum, r) => 
    sum + Math.abs((r.gstr2b_total_amount || 0) - (r.tally_total_amount || 0)), 0);
  
  const largestDiscrepancy = Math.max(...reconciled.map(r => 
    Math.abs((r.gstr2b_total_amount || 0) - (r.tally_total_amount || 0))), 0);
  
  const perfectMatches = reconciled.filter(r => 
    Math.abs((r.gstr2b_total_amount || 0) - (r.tally_total_amount || 0)) < 0.01).length;
  
  return {
    total_gstr2b_amount: totalGstr2bAmount,
    total_tally_amount: totalTallyAmount,
    total_amount_difference: totalAmountDifference,
    largest_discrepancy: largestDiscrepancy,
    perfect_matches: perfectMatches,
    total_transactions: reconciled.length + unmatched_gstr2b.length + unmatched_tally.length
  };
}