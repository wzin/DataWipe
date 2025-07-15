import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload as UploadIcon, FileText, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { toast } from 'react-toastify';
import { uploadCSV } from '../services/api';

const Upload = () => {
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [supportedFormats, setSupportedFormats] = useState(null);

  const onDrop = async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    // Validate file type
    if (!file.name.endsWith('.csv')) {
      toast.error('Please upload a CSV file');
      return;
    }

    setUploading(true);
    setUploadResult(null);

    try {
      const result = await uploadCSV(file);
      setUploadResult(result);
      toast.success(`Successfully processed ${result.accounts_discovered} accounts`);
    } catch (error) {
      toast.error(error.message || 'Upload failed');
      setUploadResult({ error: error.message });
    } finally {
      setUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv']
    },
    maxFiles: 1
  });

  React.useEffect(() => {
    // Load supported formats info
    fetch('/api/upload/formats')
      .then(res => res.json())
      .then(data => setSupportedFormats(data))
      .catch(err => console.error('Error loading formats:', err));
  }, []);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h1 className="text-2xl font-bold text-gray-900">Upload Password Manager Export</h1>
          <p className="mt-2 text-sm text-gray-600">
            Upload your Bitwarden or LastPass CSV export to discover accounts for deletion
          </p>
        </div>

        <div className="p-6">
          {/* Upload Area */}
          <div
            {...getRootProps()}
            className={`dropzone ${isDragActive ? 'active' : ''} ${uploading ? 'pointer-events-none opacity-50' : ''}`}
          >
            <input {...getInputProps()} />
            <div className="flex flex-col items-center justify-center py-12">
              <UploadIcon className="h-12 w-12 text-gray-400 mb-4" />
              {uploading ? (
                <div className="text-center">
                  <div className="spinner mx-auto mb-4"></div>
                  <p className="text-lg text-gray-600">Processing your file...</p>
                  <p className="text-sm text-gray-500">This may take a few minutes</p>
                </div>
              ) : (
                <div className="text-center">
                  <p className="text-lg text-gray-600">
                    {isDragActive ? 'Drop the file here' : 'Drag and drop your CSV file here'}
                  </p>
                  <p className="text-sm text-gray-500 mt-2">or click to select a file</p>
                  <p className="text-xs text-gray-400 mt-1">Maximum file size: 10MB</p>
                </div>
              )}
            </div>
          </div>

          {/* Upload Result */}
          {uploadResult && (
            <div className="mt-6">
              {uploadResult.error ? (
                <div className="notification notification-error">
                  <div className="flex items-center">
                    <XCircle className="h-5 w-5 mr-2" />
                    <span className="font-medium">Upload Failed</span>
                  </div>
                  <p className="mt-1">{uploadResult.error}</p>
                </div>
              ) : (
                <div className="notification notification-success">
                  <div className="flex items-center">
                    <CheckCircle className="h-5 w-5 mr-2" />
                    <span className="font-medium">Upload Successful</span>
                  </div>
                  <p className="mt-1">
                    Discovered {uploadResult.accounts_discovered} accounts ready for processing
                  </p>
                  <div className="mt-4">
                    <a
                      href="/accounts"
                      className="btn btn-primary btn-sm"
                    >
                      View Accounts →
                    </a>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Supported Formats */}
          {supportedFormats && (
            <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  <FileText className="h-5 w-5 inline mr-2" />
                  Bitwarden Format
                </h3>
                <div className="space-y-2 text-sm">
                  <p className="text-gray-600">Expected columns:</p>
                  <ul className="list-disc list-inside text-gray-500">
                    {supportedFormats.expected_columns.bitwarden.map(col => (
                      <li key={col}>{col}</li>
                    ))}
                  </ul>
                </div>
                <div className="mt-4 bg-white p-3 rounded border">
                  <p className="text-xs text-gray-500 mb-1">Example:</p>
                  <pre className="text-xs text-gray-700">
                    {JSON.stringify(supportedFormats.sample_data.bitwarden, null, 2)}
                  </pre>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  <FileText className="h-5 w-5 inline mr-2" />
                  LastPass Format
                </h3>
                <div className="space-y-2 text-sm">
                  <p className="text-gray-600">Expected columns:</p>
                  <ul className="list-disc list-inside text-gray-500">
                    {supportedFormats.expected_columns.lastpass.map(col => (
                      <li key={col}>{col}</li>
                    ))}
                  </ul>
                </div>
                <div className="mt-4 bg-white p-3 rounded border">
                  <p className="text-xs text-gray-500 mb-1">Example:</p>
                  <pre className="text-xs text-gray-700">
                    {JSON.stringify(supportedFormats.sample_data.lastpass, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {/* Instructions */}
          <div className="mt-8 bg-blue-50 rounded-lg p-6">
            <h3 className="text-lg font-medium text-blue-900 mb-4">
              <AlertCircle className="h-5 w-5 inline mr-2" />
              How to Export Your Data
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
              <div>
                <h4 className="font-medium text-blue-900 mb-2">Bitwarden</h4>
                <ol className="list-decimal list-inside space-y-1 text-blue-700">
                  <li>Open Bitwarden web vault</li>
                  <li>Go to Tools → Export Vault</li>
                  <li>Select "CSV" as file format</li>
                  <li>Enter your master password</li>
                  <li>Download the CSV file</li>
                </ol>
              </div>
              <div>
                <h4 className="font-medium text-blue-900 mb-2">LastPass</h4>
                <ol className="list-decimal list-inside space-y-1 text-blue-700">
                  <li>Open LastPass web vault</li>
                  <li>Go to Advanced Options → Export</li>
                  <li>Enter your master password</li>
                  <li>Copy the data to a CSV file</li>
                  <li>Save the file with .csv extension</li>
                </ol>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Upload;