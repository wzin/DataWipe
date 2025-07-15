import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  Eye, 
  EyeOff, 
  Search, 
  Filter, 
  Download,
  Calendar,
  User,
  AlertCircle,
  CheckCircle,
  Info
} from 'lucide-react';
import { toast } from 'react-toastify';
import { 
  getAuditLogs, 
  revealCredentials,
  getAuditActions,
  getAuditSummary
} from '../services/api';

const Audit = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAction, setSelectedAction] = useState('');
  const [revealedLogs, setRevealedLogs] = useState(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  const queryClient = useQueryClient();

  const itemsPerPage = 50;

  const { data: auditLogs, isLoading: logsLoading } = useQuery(
    ['auditLogs', { skip: (currentPage - 1) * itemsPerPage, limit: itemsPerPage, action: selectedAction }],
    () => getAuditLogs({ 
      skip: (currentPage - 1) * itemsPerPage, 
      limit: itemsPerPage,
      action: selectedAction || undefined
    }),
    {
      keepPreviousData: true,
    }
  );

  const { data: actions } = useQuery('auditActions', getAuditActions);
  const { data: summary } = useQuery('auditSummary', getAuditSummary);

  const revealMutation = useMutation(revealCredentials, {
    onSuccess: (data, logId) => {
      setRevealedLogs(prev => new Set([...prev, logId]));
      queryClient.setQueryData(['auditLogs'], (oldData) => {
        return oldData?.map(log => 
          log.id === logId 
            ? { ...log, revealed_details: data.details }
            : log
        );
      });
      toast.success('Credentials revealed');
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to reveal credentials');
    }
  });

  const handleRevealCredentials = (logId) => {
    revealMutation.mutate(logId);
  };

  const getActionIcon = (action) => {
    switch (action) {
      case 'deletion_attempt': return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'deletion_email_sent': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'credentials_revealed': return <Eye className="h-4 w-4 text-yellow-500" />;
      case 'account_removed': return <User className="h-4 w-4 text-gray-500" />;
      default: return <Info className="h-4 w-4 text-blue-500" />;
    }
  };

  const getActionColor = (action) => {
    switch (action) {
      case 'deletion_attempt': return 'text-red-700 bg-red-50';
      case 'deletion_email_sent': return 'text-green-700 bg-green-50';
      case 'credentials_revealed': return 'text-yellow-700 bg-yellow-50';
      case 'account_removed': return 'text-gray-700 bg-gray-50';
      default: return 'text-blue-700 bg-blue-50';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const renderLogDetails = (log) => {
    const details = revealedLogs.has(log.id) ? log.revealed_details : log.details;
    
    return (
      <div className="mt-2 p-3 bg-gray-50 rounded text-sm">
        <div className="flex items-center justify-between mb-2">
          <span className="font-medium text-gray-700">Details:</span>
          {log.masked_credentials && !revealedLogs.has(log.id) && (
            <button
              onClick={() => handleRevealCredentials(log.id)}
              disabled={revealMutation.isLoading}
              className="btn btn-secondary btn-sm"
            >
              <Eye className="h-3 w-3 mr-1" />
              Reveal
            </button>
          )}
        </div>
        
        <pre className="text-xs text-gray-600 whitespace-pre-wrap">
          {JSON.stringify(details, null, 2)}
        </pre>
      </div>
    );
  };

  const filteredLogs = auditLogs?.filter(log => 
    !searchTerm || 
    log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
    JSON.stringify(log.details).toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (logsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Audit Log</h1>
          <p className="text-gray-600 mt-2">
            Complete audit trail of all system actions
          </p>
        </div>
        
        <div className="flex space-x-2">
          <button className="btn btn-secondary">
            <Download className="h-4 w-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Info className="h-5 w-5 text-blue-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Total Logs</p>
                <p className="text-lg font-bold text-gray-900">{summary.total_logs}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <Calendar className="h-5 w-5 text-green-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Recent (24h)</p>
                <p className="text-lg font-bold text-gray-900">{summary.recent_activity}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Eye className="h-5 w-5 text-yellow-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Credential Reveals</p>
                <p className="text-lg font-bold text-gray-900">{summary.credential_reveals}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 rounded-lg">
                <AlertCircle className="h-5 w-5 text-red-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Deletion Attempts</p>
                <p className="text-lg font-bold text-gray-900">
                  {summary.actions?.deletion_attempt || 0}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <input
                type="text"
                placeholder="Search audit logs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="form-input pl-10"
              />
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <select
                value={selectedAction}
                onChange={(e) => setSelectedAction(e.target.value)}
                className="form-select"
              >
                <option value="">All Actions</option>
                {actions?.actions?.map(action => (
                  <option key={action} value={action}>
                    {action.replace('_', ' ')}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Audit Logs */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Audit Entries ({filteredLogs?.length || 0})
          </h2>
        </div>
        
        <div className="divide-y divide-gray-200">
          {filteredLogs?.length === 0 ? (
            <div className="text-center py-8">
              <Info className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No audit logs found</p>
            </div>
          ) : (
            filteredLogs?.map((log) => (
              <div key={log.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    {getActionIcon(log.action)}
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getActionColor(log.action)}`}>
                          {log.action.replace('_', ' ')}
                        </span>
                        {log.masked_credentials && (
                          <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full">
                            Masked
                          </span>
                        )}
                      </div>
                      
                      <div className="mt-2">
                        <p className="text-sm text-gray-900">
                          Account ID: {log.account_id || 'System'}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatDate(log.created_at)}
                          {log.ip_address && ` • ${log.ip_address}`}
                          {log.user_agent && ` • ${log.user_agent.substring(0, 50)}...`}
                        </p>
                      </div>
                      
                      {renderLogDetails(log)}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
        
        {/* Pagination */}
        {filteredLogs?.length === itemsPerPage && (
          <div className="px-6 py-4 border-t border-gray-200 flex justify-center">
            <div className="flex space-x-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="btn btn-secondary btn-sm"
              >
                Previous
              </button>
              <span className="px-3 py-1 text-sm text-gray-700">
                Page {currentPage}
              </span>
              <button
                onClick={() => setCurrentPage(prev => prev + 1)}
                disabled={filteredLogs?.length < itemsPerPage}
                className="btn btn-secondary btn-sm"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Security Notice */}
      <div className="bg-yellow-50 rounded-lg p-4">
        <div className="flex items-start">
          <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5 mr-3" />
          <div>
            <h3 className="font-medium text-yellow-900">Security Notice</h3>
            <p className="text-sm text-yellow-800 mt-1">
              Credential reveals are logged for security purposes. Only reveal credentials when necessary 
              and ensure you're in a secure environment.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Audit;