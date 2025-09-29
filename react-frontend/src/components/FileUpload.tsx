import { useState } from 'react';
import { Upload, Play, CheckCircle, AlertCircle, Info } from 'lucide-react';
import { ReconciliationResponse } from '../types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '../contexts/AuthContext';

interface FileUploadProps {
  onSuccess: (data: ReconciliationResponse) => void;
  onLoadingChange: (loading: boolean) => void;
}

interface StatusMessage {
  type: 'success' | 'error' | 'info';
  message: string;
}

export default function FileUpload({ onSuccess, onLoadingChange }: FileUploadProps) {
  const [gstr2bFile, setGstr2bFile] = useState<File | null>(null);
  const [tallyFile, setTallyFile] = useState<File | null>(null);
  const [status, setStatus] = useState<StatusMessage | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const { toast } = useToast();
  const { getAccessTokenSilently } = useAuth();

  const handleFileChange = (type: 'gstr2b' | 'tally', file: File | null) => {
    if (type === 'gstr2b') {
      setGstr2bFile(file);
    } else {
      setTallyFile(file);
    }
    // Clear status when files change
    setStatus(null);
  };

  const updateStatus = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    setStatus({ message, type });
    
    // Also show toast notification
    toast({
      title: type === 'success' ? 'Success' : type === 'error' ? 'Error' : 'Info',
      description: message,
      variant: type === 'error' ? 'destructive' : 'default',
    });
  };

  const handleUpload = async () => {
    if (!gstr2bFile || !tallyFile) {
      updateStatus('Please select both GSTR2B and Tally files', 'error');
      return;
    }

    setIsUploading(true);
    onLoadingChange(true);
    updateStatus('Uploading and processing files...', 'info');

    try {
      // Get access token for authenticated API calls
      const token = await getAccessTokenSilently();

      const formData = new FormData();
      formData.append('bank_file', gstr2bFile);
      formData.append('ledger_file', tallyFile);

      const response = await fetch('/api/upload/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      updateStatus('Files processed successfully!', 'success');
      onSuccess(data);
    } catch (error) {
      console.error('Upload error:', error);
      updateStatus(error instanceof Error ? error.message : 'Upload failed', 'error');
    } finally {
      setIsUploading(false);
      onLoadingChange(false);
    }
  };

  const StatusIcon = ({ type }: { type: 'success' | 'error' | 'info' }) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Info className="w-5 h-5 text-blue-600" />;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <Upload className="w-5 h-5 text-green-600" />
          </div>
          <CardTitle className="text-2xl">Upload Files</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* GSTR2B Upload */}
          <div className="space-y-3">
            <label htmlFor="gstr2bFile" className="block text-sm font-medium text-foreground">
              GSTR2B File
            </label>
            <Input
              type="file" 
              id="gstr2bFile" 
              accept=".xlsx,.xls,.csv"
              onChange={(e) => handleFileChange('gstr2b', e.target.files?.[0] || null)}
              className="cursor-pointer"
            />
            <p className="text-xs text-muted-foreground">Supports CSV, XLS, XLSX formats</p>
            {gstr2bFile && (
              <p className="text-sm text-green-600 flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                {gstr2bFile.name}
              </p>
            )}
          </div>

          {/* Tally Upload */}
          <div className="space-y-3">
            <label htmlFor="tallyFile" className="block text-sm font-medium text-foreground">
              Tally File
            </label>
            <Input
              type="file" 
              id="tallyFile" 
              accept=".xlsx,.xls,.csv"
              onChange={(e) => handleFileChange('tally', e.target.files?.[0] || null)}
              className="cursor-pointer"
            />
            <p className="text-xs text-muted-foreground">Supports CSV, XLS, XLSX formats</p>
            {tallyFile && (
              <p className="text-sm text-green-600 flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                {tallyFile.name}
              </p>
            )}
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4">
          <Button 
            onClick={handleUpload}
            disabled={isUploading || !gstr2bFile || !tallyFile}
            className="flex items-center justify-center space-x-2"
            size="lg"
          >
            {isUploading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span>Start Reconciliation</span>
              </>
            )}
          </Button>
        </div>

        {/* Status Messages */}
        {status && (
          <div className="mt-6">
            <div className={`flex items-center space-x-3 p-4 rounded-lg border ${
              status.type === 'success' ? 'bg-green-50 border-green-200 text-green-800' :
              status.type === 'error' ? 'bg-red-50 border-red-200 text-red-800' :
              'bg-blue-50 border-blue-200 text-blue-800'
            }`}>
              <StatusIcon type={status.type} />
              <span>{status.message}</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}