import { CheckCircle, Download, FileX } from 'lucide-react';
import { ReconciledTransaction, ConfidenceLevel } from '../types';
import { formatCurrency, formatDate, getConfidenceBadge, downloadFile } from '../utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

interface ReconciledTableProps {
  data: ReconciledTransaction[];
  confidenceFilter: ConfidenceLevel;
  onConfidenceFilterChange: (filter: ConfidenceLevel) => void;
}

export default function ReconciledTable({ data, confidenceFilter, onConfidenceFilterChange }: ReconciledTableProps) {
  // Filter data based on confidence level
  const filteredData = data.filter(row => {
    const score = parseFloat(String(row.match_score)) || 0;
    switch(confidenceFilter) {
      case 'high': return score >= 0.95;
      case 'medium': return score >= 0.85 && score < 0.95;
      case 'low': return score < 0.85;
      default: return true;
    }
  });

  const handleExport = async () => {
    try {
      const exportData = filteredData.map(row => ({
        'Match Score': getConfidenceBadge(parseFloat(String(row.match_score))),
        'GSTR2B Invoice': row.gstr2b_invoice_no,
        'GSTR2B Date': formatDate(row.gstr2b_date),
        'GSTR2B GSTIN': row.gstr2b_supplier_gstin,
        'GSTR2B Amount': row.gstr2b_total_amount,
        'GSTR2B Taxable': row.gstr2b_taxable_value,
        'GSTR2B IGST': row.gstr2b_igst,
        'GSTR2B CGST': row.gstr2b_cgst,
        'GSTR2B SGST': row.gstr2b_sgst,
        'Tally Invoice': row.tally_invoice_no,
        'Tally Date': formatDate(row.tally_date),
        'Tally GSTIN': row.tally_supplier_gstin,
        'Tally Amount': row.tally_total_amount,
        'Tally Base': row.tally_base_amount,
        'Tally Tax': row.tally_tax_amount,
        'Tally Type': row.tally_type,
        'Amount Difference': Math.abs(row.gstr2b_total_amount - row.tally_total_amount)
      }));

      const filename = `reconciled_transactions_${confidenceFilter}_${new Date().toISOString().split('T')[0]}.xlsx`;
      await downloadFile(exportData, filename);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  if (!data || data.length === 0) {
    return (
      <Card className="w-full">
        <CardHeader>
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <CardTitle className="text-2xl">Reconciled Transactions</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <div className="mx-auto h-12 w-12 text-muted-foreground mb-4">
              <FileX className="w-12 h-12" />
            </div>
            <h3 className="text-lg font-medium mb-2">No reconciled transactions</h3>
            <p className="text-muted-foreground">Upload files to see reconciled data here.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <CardTitle className="text-2xl">Reconciled Transactions</CardTitle>
            <Badge variant="secondary" className="bg-green-100 text-green-800">
              {filteredData.length} records
            </Badge>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            <select 
              value={confidenceFilter}
              onChange={(e) => onConfidenceFilterChange(e.target.value as ConfidenceLevel)}
              className="px-3 py-2 border border-input rounded-md text-sm focus:ring-2 focus:ring-ring focus:border-transparent bg-background"
            >
              <option value="all">All Matches</option>
              <option value="high">High Confidence (≥95%)</option>
              <option value="medium">Medium Confidence (85-95%)</option>
              <option value="low">Low Confidence (&lt;85%)</option>
            </select>
            <Button onClick={handleExport} variant="default" size="sm">
              <Download className="w-4 h-4 mr-2" />
              Export Excel
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-center">Score</TableHead>
                <TableHead>Invoice</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Vendor</TableHead>
                <TableHead>GSTR2B Amount</TableHead>
                <TableHead>Tally Amount</TableHead>
                <TableHead>Difference</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredData.map((row, index) => {
                const score = parseFloat(String(row.match_score)) || 0;

                const amountDiff = Math.abs(row.gstr2b_total_amount - row.tally_total_amount);
                const isExactAmount = amountDiff < 0.01;
                
                const getConfidenceBadgeVariant = (score: number) => {
                  if (score >= 0.95) return 'default';
                  if (score >= 0.85) return 'secondary';
                  return 'destructive';
                };
                
                return (
                  <TableRow key={index}>
                    <TableCell className="text-center">
                      <Badge variant={getConfidenceBadgeVariant(score)}>
                        {getConfidenceBadge(score)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="text-sm font-medium">{row.gstr2b_invoice_no}</div>
                        <div className="text-xs text-muted-foreground">{row.tally_invoice_no}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="text-sm">{formatDate(row.gstr2b_date)}</div>
                        <div className="text-xs text-muted-foreground">{formatDate(row.tally_date)}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="text-sm font-medium">{row.gstr2b_supplier_gstin}</div>
                        <div className="text-xs text-muted-foreground">{row.tally_supplier_gstin}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="mb-1 text-blue-700 border-blue-200">GSTR2B</Badge>
                      <div>{formatCurrency(row.gstr2b_total_amount)}</div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="mb-1 text-purple-700 border-purple-200">Tally</Badge>
                      <div>{formatCurrency(row.tally_total_amount)}</div>
                    </TableCell>
                    <TableCell>
                      <span className={isExactAmount ? 'text-green-600 font-semibold' : 'text-amber-600'}>
                        {isExactAmount ? 'Exact Match' : formatCurrency(amountDiff)}
                      </span>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
        
        {filteredData.length === 0 && (
          <div className="text-center py-8">
            <p className="text-muted-foreground">No transactions match the selected confidence level.</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}