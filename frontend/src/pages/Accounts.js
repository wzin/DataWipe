import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  Search, 
  Filter, 
  CheckSquare, 
  Square, 
  ExternalLink,
  Trash2,
  Mail,
  Eye,
  EyeOff
} from 'lucide-react';
import { toast } from 'react-toastify';
import { getAccounts, bulkSelectAccounts, deleteAccount } from '../services/api';

const Accounts = () => {
  const [selectedAccounts, setSelectedAccounts] = useState(new Set());
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [showPasswords, setShowPasswords] = useState(new Set());
  const queryClient = useQueryClient();

  const itemsPerPage = 20;

  const { data: accounts, isLoading, error } = useQuery(
    ['accounts', { search, status: statusFilter, skip: (currentPage - 1) * itemsPerPage, limit: itemsPerPage }],
    () => getAccounts({ 
      search, 
      status: statusFilter || undefined, 
      skip: (currentPage - 1) * itemsPerPage, 
      limit: itemsPerPage 
    }),
    {
      keepPreviousData: true,
    }
  );

  const bulkSelectMutation = useMutation(bulkSelectAccounts, {
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries('accounts');
      setSelectedAccounts(new Set());
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Bulk selection failed');
    }
  });

  const deleteAccountMutation = useMutation(deleteAccount, {
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries('accounts');
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Delete failed');
    }
  });

  const handleSelectAll = () => {
    if (selectedAccounts.size === accounts?.length) {
      setSelectedAccounts(new Set());
    } else {
      setSelectedAccounts(new Set(accounts?.map(account => account.id) || []));
    }
  };

  const handleSelectAccount = (accountId) => {
    const newSelection = new Set(selectedAccounts);
    if (newSelection.has(accountId)) {
      newSelection.delete(accountId);
    } else {
      newSelection.add(accountId);
    }
    setSelectedAccounts(newSelection);
  };

  const handleBulkSelect = (action) => {
    if (selectedAccounts.size === 0) {
      toast.warning('Please select accounts first');
      return;
    }
    
    bulkSelectMutation.mutate({
      accountIds: Array.from(selectedAccounts),
      action
    });
  };

  const handleDeleteAccount = (accountId) => {
    if (window.confirm('Are you sure you want to remove this account from the system?')) {
      deleteAccountMutation.mutate(accountId);
    }
  };

  const togglePasswordVisibility = (accountId) => {
    const newShowPasswords = new Set(showPasswords);
    if (newShowPasswords.has(accountId)) {
      newShowPasswords.delete(accountId);
    } else {
      newShowPasswords.add(accountId);
    }
    setShowPasswords(newShowPasswords);
  };

  const getStatusBadge = (status) => {
    const statusClasses = {
      discovered: 'status-badge status-discovered',
      pending: 'status-badge status-pending',
      in_progress: 'status-badge status-in-progress',
      completed: 'status-badge status-completed',
      failed: 'status-badge status-failed'
    };
    
    return (
      <span className={statusClasses[status] || 'status-badge status-discovered'}>
        {status.replace('_', ' ')}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Error loading accounts: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Accounts</h1>
          <p className="text-gray-600 mt-2">
            Manage your discovered accounts and select them for deletion
          </p>
        </div>
        
        {selectedAccounts.size > 0 && (
          <div className="flex space-x-2">
            <button
              onClick={() => handleBulkSelect('select')}
              className="btn btn-primary btn-sm"
              disabled={bulkSelectMutation.isLoading}
            >
              Select for Deletion ({selectedAccounts.size})
            </button>
            <button
              onClick={() => handleBulkSelect('deselect')}
              className="btn btn-secondary btn-sm"
              disabled={bulkSelectMutation.isLoading}
            >
              Deselect
            </button>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <input
                type="text"
                placeholder="Search accounts..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="form-input pl-10"
              />
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="form-select"
              >
                <option value="">All Status</option>
                <option value="discovered">Discovered</option>
                <option value="pending">Pending</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Accounts Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="table">
          <thead>
            <tr>
              <th className="w-12">
                <button
                  onClick={handleSelectAll}
                  className="text-gray-400 hover:text-gray-600"
                >
                  {selectedAccounts.size === accounts?.length && accounts?.length > 0 ? (
                    <CheckSquare className="h-4 w-4" />
                  ) : (
                    <Square className="h-4 w-4" />
                  )}
                </button>
              </th>
              <th>Site</th>
              <th>Username</th>
              <th>Email</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {accounts?.map((account) => (
              <tr key={account.id}>
                <td>
                  <button
                    onClick={() => handleSelectAccount(account.id)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    {selectedAccounts.has(account.id) ? (
                      <CheckSquare className="h-4 w-4 text-blue-600" />
                    ) : (
                      <Square className="h-4 w-4" />
                    )}
                  </button>
                </td>
                <td>
                  <div className="flex items-center">
                    <div>
                      <p className="font-medium text-gray-900">{account.site_name}</p>
                      <p className="text-sm text-gray-500">{account.site_url}</p>
                    </div>
                    <a
                      href={account.site_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-2 text-gray-400 hover:text-gray-600"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </div>
                </td>
                <td>
                  <div className="flex items-center">
                    <span className="font-medium text-gray-900">{account.username}</span>
                    <button
                      onClick={() => togglePasswordVisibility(account.id)}
                      className="ml-2 text-gray-400 hover:text-gray-600"
                    >
                      {showPasswords.has(account.id) ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                  {showPasswords.has(account.id) && (
                    <p className="text-sm text-gray-500 mt-1">••••••••</p>
                  )}
                </td>
                <td>
                  <span className="text-gray-900">{account.email || '-'}</span>
                </td>
                <td>
                  {getStatusBadge(account.status)}
                </td>
                <td>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleDeleteAccount(account.id)}
                      className="text-red-600 hover:text-red-800"
                      title="Remove from system"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </div>
        
        {accounts?.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No accounts found.</p>
            <a href="/upload" className="btn btn-primary btn-sm mt-4">
              Upload CSV File
            </a>
          </div>
        )}
      </div>

      {/* Pagination */}
      {accounts?.length === itemsPerPage && (
        <div className="flex justify-center">
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
              disabled={accounts?.length < itemsPerPage}
              className="btn btn-secondary btn-sm"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Accounts;