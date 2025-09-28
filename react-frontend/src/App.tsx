import { useState } from 'react';
import { Calculator } from 'lucide-react';
import FileUpload from './components/FileUpload';
import MetricsPanel from './components/MetricsPanel';
import ReconciledTable from './components/ReconciledTable';
import UnmatchedTable from './components/UnmatchedTable';
import DuplicatesPanel from './components/DuplicatesPanel';
import LoadingOverlay from './components/LoadingOverlay';
import { Toaster } from '@/components/ui/toaster';
import { ReconciliationResponse, ConfidenceLevel } from './types';
import { calculateEnhancedMetrics } from './utils';

function App() {
  const [data, setData] = useState<ReconciliationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [confidenceFilter, setConfidenceFilter] = useState<ConfidenceLevel>('all');

  const handleUploadSuccess = (response: ReconciliationResponse) => {
    // Calculate enhanced metrics
    const enhancedMetrics = calculateEnhancedMetrics(
      response.reconciled,
      response.unmatched_bank,
      response.unmatched_ledger
    );
    
    // Merge with existing metrics
    const updatedResponse = {
      ...response,
      metrics: {
        ...response.metrics,
        ...enhancedMetrics
      }
    };
    
    setData(updatedResponse);
  };

  const handleLoadingChange = (isLoading: boolean) => {
    setLoading(isLoading);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {loading && <LoadingOverlay />}
      
      {/* Header */}
      <header className="border-b bg-white">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-600 rounded-lg">
              <Calculator className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">SME Reconciliation</h1>
              <p className="text-gray-600">Automated reconciliation for GSTR2B and Tally transactions</p>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 space-y-8">
        {/* Upload Section */}
        <FileUpload 
          onSuccess={handleUploadSuccess}
          onLoadingChange={handleLoadingChange}
        />

        {/* Metrics Dashboard */}
        {data && (
          <MetricsPanel metrics={data.metrics} />
        )}

        {/* Reconciled Transactions */}
        {data && (
          <ReconciledTable 
            data={data.reconciled}
            confidenceFilter={confidenceFilter}
            onConfidenceFilterChange={setConfidenceFilter}
          />
        )}

        {/* Unmatched Transactions */}
        {data && (
          <UnmatchedTable 
            gstr2bData={data.unmatched_bank}
            tallyData={data.unmatched_ledger}
          />
        )}

        {/* Duplicates Panel */}
        {data && data.duplicates.length > 0 && (
          <DuplicatesPanel duplicates={data.duplicates} />
        )}
      </main>
      <Toaster />
    </div>
  );
}

export default App;