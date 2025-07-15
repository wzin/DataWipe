import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  CheckCircle, 
  XCircle, 
  Clock,
  AlertTriangle,
  Mail,
  Settings
} from 'lucide-react';
import { toast } from 'react-toastify';
import { 
  getAccounts, 
  getDeletionTasks, 
  startDeletion, 
  confirmDeletion,
  sendEmailDeletion
} from '../services/api';

const Deletion = () => {
  const [selectedAccounts, setSelectedAccounts] = useState([]);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const queryClient = useQueryClient();

  const { data: accounts, isLoading: accountsLoading } = useQuery(
    ['accounts', { status: 'pending' }],
    () => getAccounts({ status: 'pending' })
  );

  const { data: deletionTasks, isLoading: tasksLoading } = useQuery(
    'deletionTasks',
    getDeletionTasks
  );

  const startDeletionMutation = useMutation(startDeletion, {
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries('deletionTasks');
      queryClient.invalidateQueries('accounts');
      setSelectedAccounts([]);
      setShowConfirmModal(false);
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to start deletion');
    }
  });

  const confirmDeletionMutation = useMutation(confirmDeletion, {
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries('deletionTasks');
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to confirm deletion');
    }
  });

  const sendEmailMutation = useMutation(sendEmailDeletion, {
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries('deletionTasks');
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to send email');
    }
  });

  const handleStartDeletion = () => {
    if (selectedAccounts.length === 0) {
      toast.warning('Please select accounts to delete');
      return;
    }
    setShowConfirmModal(true);
  };

  const handleConfirmStart = () => {
    startDeletionMutation.mutate(selectedAccounts);
  };

  const handleAccountToggle = (accountId) => {
    setSelectedAccounts(prev => 
      prev.includes(accountId) 
        ? prev.filter(id => id !== accountId)
        : [...prev, accountId]
    );
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'in_progress': return <Play className="h-4 w-4 text-blue-500" />;
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      default: return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const statusClasses = {
      pending: 'status-badge status-pending',
      in_progress: 'status-badge status-in-progress',
      completed: 'status-badge status-completed',
      failed: 'status-badge status-failed'
    };
    
    return (
      <span className={statusClasses[status] || 'status-badge status-pending'}>
        {status.replace('_', ' ')}
      </span>
    );
  };

  if (accountsLoading || tasksLoading) {
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
          <h1 className="text-3xl font-bold text-gray-900">Account Deletion</h1>
          <p className="text-gray-600 mt-2">
            Start the deletion process for your selected accounts
          </p>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={handleStartDeletion}
            disabled={selectedAccounts.length === 0 || startDeletionMutation.isLoading}
            className="btn btn-danger"
          >
            <Play className="h-4 w-4 mr-2" />
            Start Deletion ({selectedAccounts.length})
          </button>
          
          <a href="/settings" className="btn btn-secondary">
            <Settings className="h-4 w-4 mr-2" />
            Email Settings
          </a>
        </div>
      </div>

      {/* Accounts Ready for Deletion */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Accounts Ready for Deletion ({accounts?.length || 0})
          </h2>
        </div>
        
        <div className="p-6">
          {accounts?.length === 0 ? (
            <div className="text-center py-8">
              <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No accounts selected for deletion</p>
              <a href="/accounts" className="btn btn-primary btn-sm mt-4">
                Select Accounts
              </a>
            </div>
          ) : (
            <div className="space-y-4">
              {accounts.map((account) => (
                <div
                  key={account.id}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedAccounts.includes(account.id)
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => handleAccountToggle(account.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={selectedAccounts.includes(account.id)}
                        onChange={() => {}}
                        className="h-4 w-4 text-blue-600 rounded"
                      />
                      <div>
                        <p className="font-medium text-gray-900">{account.site_name}</p>
                        <p className="text-sm text-gray-500">{account.username}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          sendEmailMutation.mutate(account.id);
                        }}
                        className="btn btn-secondary btn-sm"
                        title="Send email deletion request"
                      >
                        <Mail className="h-4 w-4" />
                      </button>
                      {getStatusBadge(account.status)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Active Deletion Tasks */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Deletion Progress ({deletionTasks?.length || 0})
          </h2>
        </div>
        
        <div className="p-6">
          {deletionTasks?.length === 0 ? (
            <div className="text-center py-8">
              <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No active deletion tasks</p>
            </div>
          ) : (
            <div className="space-y-4">
              {deletionTasks.map((task) => (
                <div key={task.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(task.status)}
                      <div>
                        <p className="font-medium text-gray-900">
                          {task.account?.site_name || 'Unknown Site'}
                        </p>
                        <p className="text-sm text-gray-500">
                          {task.account?.username || 'Unknown User'}
                        </p>
                        <p className="text-xs text-gray-400">
                          Method: {task.method} • Attempts: {task.attempts}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {task.status === 'pending' && (
                        <button
                          onClick={() => confirmDeletionMutation.mutate(task.id)}
                          className="btn btn-success btn-sm"
                        >
                          <CheckCircle className="h-4 w-4 mr-1" />
                          Confirm
                        </button>
                      )}
                      
                      {task.status === 'failed' && (
                        <div className="text-right">
                          <p className="text-sm text-red-600">Failed</p>
                          <p className="text-xs text-gray-500">
                            {task.last_error}
                          </p>
                        </div>
                      )}
                      
                      {getStatusBadge(task.status)}
                    </div>
                  </div>
                  
                  {task.status === 'in_progress' && (
                    <div className="mt-3">
                      <div className="progress-bar">
                        <div 
                          className="progress-bar-fill"
                          style={{ width: '60%' }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        Processing deletion request...
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3 className="text-lg font-semibold text-gray-900">
                Confirm Account Deletion
              </h3>
            </div>
            
            <div className="modal-body">
              <div className="mb-4">
                <AlertTriangle className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
                <p className="text-center text-gray-700">
                  You are about to start the deletion process for{' '}
                  <strong>{selectedAccounts.length}</strong> account(s).
                </p>
              </div>
              
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h4 className="font-medium text-yellow-900 mb-2">
                  What will happen:
                </h4>
                <ul className="text-sm text-yellow-800 space-y-1">
                  <li>• The system will attempt automated deletion first</li>
                  <li>• If automation fails, email requests will be sent</li>
                  <li>• You can monitor progress in real-time</li>
                  <li>• Manual confirmation may be required for some sites</li>
                </ul>
              </div>
              
              <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
                <h4 className="font-medium text-red-900 mb-2">
                  Important:
                </h4>
                <p className="text-sm text-red-800">
                  Account deletion is permanent and cannot be undone. Make sure you have 
                  backed up any important data before proceeding.
                </p>
              </div>
            </div>
            
            <div className="modal-footer">
              <button
                onClick={() => setShowConfirmModal(false)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmStart}
                disabled={startDeletionMutation.isLoading}
                className="btn btn-danger"
              >
                {startDeletionMutation.isLoading ? 'Starting...' : 'Start Deletion'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Deletion;