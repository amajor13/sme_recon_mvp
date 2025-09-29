import { useState } from 'react';
import GSTLogo from './GSTLogo';
import FileUpload from './FileUpload';
import MetricsPanel from './MetricsPanel';
import ReconciledTable from './ReconciledTable';
import UnmatchedTable from './UnmatchedTable';
import DuplicatesPanel from './DuplicatesPanel';
import LoadingOverlay from './LoadingOverlay';
import UserProfile from './UserProfile';
import { ReconciliationResponse, ConfidenceLevel } from '../types';
import { calculateEnhancedMetrics } from '../utils';

export default function Dashboard() {
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
      <header className="border-b bg-gradient-to-r from-blue-50 to-indigo-50 shadow-sm">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <GSTLogo size="lg" className="drop-shadow-sm" />
              <div className="border-l border-gray-300 pl-4">
                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  GST Reconciliation
                </h1>
                <p className="text-sm text-gray-600 mt-1">
                  Automated reconciliation for GSTR2B and Tally transactions
                </p>
              </div>
            </div>
            <UserProfile />
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
    </div>
  );
}