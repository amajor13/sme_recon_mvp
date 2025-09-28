import { Copy } from 'lucide-react';
import { DuplicateGroup } from '../types';
import { formatCurrency, formatDate } from '../utils';

interface DuplicatesPanelProps {
  duplicates: DuplicateGroup[];
}

export default function DuplicatesPanel({ duplicates }: DuplicatesPanelProps) {
  if (!duplicates || duplicates.length === 0) {
    return null;
  }

  return (
    <section className="bg-white rounded-lg shadow-sm border">
      <div className="p-6 border-b">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-yellow-100 rounded-lg">
            <Copy className="w-5 h-5 text-yellow-600" />
          </div>
          <h2 className="text-2xl font-semibold text-gray-900">Potential Duplicates</h2>
          <span className="bg-yellow-100 text-yellow-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
            {duplicates.length} groups
          </span>
        </div>
      </div>
      
      <div className="p-6">
        <div className="space-y-6">
          {duplicates.map((group, groupIndex) => (
            <div key={groupIndex} className="border border-yellow-200 rounded-lg p-4 bg-yellow-50">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900">
                  Duplicate {group.field}: {group.value}
                </h3>
                <span className="bg-yellow-200 text-yellow-800 text-xs font-medium px-2 py-1 rounded">
                  {group.count} records
                </span>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-yellow-200">
                      <th className="text-left py-2">Date</th>
                      <th className="text-left py-2">Invoice No</th>
                      <th className="text-left py-2">Supplier GSTIN</th>
                      <th className="text-left py-2">Total Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {group.transactions.map((transaction, transIndex) => (
                      <tr key={transIndex} className="border-b border-yellow-100 last:border-b-0">
                        <td className="py-2">{formatDate(transaction.date)}</td>
                        <td className="py-2 font-medium">{transaction.invoice_no}</td>
                        <td className="py-2">{transaction.supplier_gstin}</td>
                        <td className="py-2">{formatCurrency(transaction.total_amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}