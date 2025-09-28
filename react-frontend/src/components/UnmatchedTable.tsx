import { AlertCircle, Download, CheckCircle } from 'lucide-react';
import { UnmatchedTransaction } from '../types';
import { formatCurrency, formatDate, downloadFile } from '../utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';


interface UnmatchedTableProps {
  gstr2bData: UnmatchedTransaction[];
  tallyData: UnmatchedTransaction[];
}

export default function UnmatchedTable({ gstr2bData, tallyData }: UnmatchedTableProps) {
  const handleExportGSTR2B = async () => {
    if (!gstr2bData || gstr2bData.length === 0) return;
    
    const exportData = gstr2bData.map(row => ({
      'Date': formatDate(row.date),
      'Invoice No': row.invoice_no,
      'Supplier GSTIN': row.supplier_gstin,
      'Total Amount': row.total_amount,
      'Taxable Value': row.taxable_value || 0,
      'IGST': row.igst || 0,
      'CGST': row.cgst || 0,
      'SGST': row.sgst || 0
    }));

    const filename = `unmatched_gstr2b_${new Date().toISOString().split('T')[0]}.xlsx`;
    await downloadFile(exportData, filename);
  };

  const handleExportTally = async () => {
    if (!tallyData || tallyData.length === 0) return;
    
    const exportData = tallyData.map(row => ({
      'Date': formatDate(row.date),
      'Invoice No': row.invoice_no,
      'Supplier GSTIN': row.supplier_gstin,
      'Total Amount': row.total_amount,
      'Base Amount': row.base_amount || 0,
      'Tax Amount': row.tax_amount || 0,
      'Type': row.type || ''
    }));

    const filename = `unmatched_tally_${new Date().toISOString().split('T')[0]}.xlsx`;
    await downloadFile(exportData, filename);
  };

  const handleExportAll = async () => {
    const allUnmatched = [
      ...gstr2bData.map(row => ({ ...row, source: 'GSTR2B' })),
      ...tallyData.map(row => ({ ...row, source: 'Tally' }))
    ];

    const exportData = allUnmatched.map(row => ({
      'Source': row.source,
      'Date': formatDate(row.date),
      'Invoice No': row.invoice_no,
      'Supplier GSTIN': row.supplier_gstin,
      'Total Amount': row.total_amount,
      'Taxable Value': row.taxable_value || '',
      'IGST': row.igst || '',
      'CGST': row.cgst || '',
      'SGST': row.sgst || '',
      'Base Amount': row.base_amount || '',
      'Tax Amount': row.tax_amount || '',
      'Type': row.type || ''
    }));

    const filename = `all_unmatched_transactions_${new Date().toISOString().split('T')[0]}.xlsx`;
    await downloadFile(exportData, filename);
  };

  const renderUnmatchedSection = (data: UnmatchedTransaction[], source: 'GSTR2B' | 'Tally') => {
    if (!data || data.length === 0) {
      return (
        <div className="text-center py-8">
          <div className="mx-auto h-12 w-12 text-green-400 mb-4">
            <CheckCircle className="w-12 h-12" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No unmatched {source} transactions</h3>
          <p className="text-gray-500">All {source} transactions were successfully matched!</p>
        </div>
      );
    }

    const columns = source === 'GSTR2B' 
      ? ['Date', 'Invoice No', 'Supplier GSTIN', 'Total Amount', 'Taxable Value', 'IGST', 'CGST', 'SGST']
      : ['Date', 'Invoice No', 'Supplier GSTIN', 'Total Amount', 'Base Amount', 'Tax Amount', 'Type'];

    return (
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className={`text-lg font-semibold flex items-center space-x-2 ${
            source === 'GSTR2B' ? 'text-blue-700' : 'text-purple-700'
          }`}>
            <span className={`source-indicator ${source === 'GSTR2B' ? 'source-gstr2b' : 'source-tally'}`}>
              {source}
            </span>
            <span>({data.length} records)</span>
          </h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="modern-table">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column}>{column}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, index) => (
                <tr key={index}>
                  <td>{formatDate(row.date)}</td>
                  <td className="font-medium">{row.invoice_no}</td>
                  <td>{row.supplier_gstin}</td>
                  <td>{formatCurrency(row.total_amount)}</td>
                  {source === 'GSTR2B' ? (
                    <>
                      <td>{formatCurrency(row.taxable_value)}</td>
                      <td>{formatCurrency(row.igst)}</td>
                      <td>{formatCurrency(row.cgst)}</td>
                      <td>{formatCurrency(row.sgst)}</td>
                    </>
                  ) : (
                    <>
                      <td>{formatCurrency(row.base_amount)}</td>
                      <td>{formatCurrency(row.tax_amount)}</td>
                      <td>{row.type}</td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const hasAnyUnmatched = (gstr2bData && gstr2bData.length > 0) || (tallyData && tallyData.length > 0);

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertCircle className="w-5 h-5 text-red-600" />
            </div>
            <CardTitle className="text-2xl">Unmatched Transactions</CardTitle>
            {hasAnyUnmatched && (
              <Badge variant="destructive">
                {(gstr2bData?.length || 0) + (tallyData?.length || 0)} records
              </Badge>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button 
              onClick={handleExportGSTR2B}
              disabled={!gstr2bData || gstr2bData.length === 0}
              variant="default"
              size="sm"
            >
              <Download className="w-4 h-4 mr-2" />
              GSTR2B ({gstr2bData?.length || 0})
            </Button>
            <Button 
              onClick={handleExportTally}
              disabled={!tallyData || tallyData.length === 0}
              variant="secondary"
              size="sm"
            >
              <Download className="w-4 h-4 mr-2" />
              Tally ({tallyData?.length || 0})
            </Button>
            <Button 
              onClick={handleExportAll}
              disabled={!hasAnyUnmatched}
              variant="outline"
              size="sm"
            >
              <Download className="w-4 h-4 mr-2" />
              All Unmatched
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {!hasAnyUnmatched ? (
          <div className="text-center py-12">
            <div className="mx-auto h-12 w-12 text-green-400 mb-4">
              <CheckCircle className="w-12 h-12" />
            </div>
            <h3 className="text-lg font-medium mb-2">Perfect reconciliation!</h3>
            <p className="text-muted-foreground">All transactions were successfully matched between GSTR2B and Tally files.</p>
          </div>
        ) : (
          <>
            {renderUnmatchedSection(gstr2bData, 'GSTR2B')}
            {renderUnmatchedSection(tallyData, 'Tally')}
          </>
        )}
      </CardContent>
    </Card>
  );
}