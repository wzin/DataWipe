import React from 'react';
import { useQuery } from 'react-query';
import { 
  Users, 
  Trash2, 
  CheckCircle, 
  XCircle, 
  Clock, 
  TrendingUp,
  AlertTriangle,
  DollarSign
} from 'lucide-react';
import { getStats, getAccountsSummary } from '../services/api';

const Dashboard = () => {
  const { data: stats, isLoading: statsLoading } = useQuery('stats', getStats);
  const { data: summary, isLoading: summaryLoading } = useQuery('summary', getAccountsSummary);

  const StatCard = ({ title, value, icon: Icon, color, subtitle }) => (
    <div className="bg-white rounded-lg shadow p-6 card-hover">
      <div className="flex items-center">
        <div className={`p-3 rounded-full ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
      </div>
    </div>
  );

  const getStatusColor = (status) => {
    switch (status) {
      case 'discovered': return 'bg-gray-500';
      case 'pending': return 'bg-yellow-500';
      case 'in_progress': return 'bg-blue-500';
      case 'completed': return 'bg-green-500';
      case 'failed': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'discovered': return 'Discovered';
      case 'pending': return 'Pending';
      case 'in_progress': return 'In Progress';
      case 'completed': return 'Completed';
      case 'failed': return 'Failed';
      default: return status;
    }
  };

  if (statsLoading || summaryLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Overview of your account deletion progress
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Accounts"
          value={stats?.total_accounts || 0}
          icon={Users}
          color="bg-blue-500"
        />
        <StatCard
          title="Pending Deletions"
          value={stats?.pending_deletions || 0}
          icon={Clock}
          color="bg-yellow-500"
        />
        <StatCard
          title="Completed"
          value={stats?.completed_deletions || 0}
          icon={CheckCircle}
          color="bg-green-500"
        />
        <StatCard
          title="Failed"
          value={stats?.failed_deletions || 0}
          icon={XCircle}
          color="bg-red-500"
        />
      </div>

      {/* Progress Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Account Status Breakdown */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Account Status Breakdown
          </h2>
          {summary?.by_status ? (
            <div className="space-y-3">
              {Object.entries(summary.by_status).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full ${getStatusColor(status)} mr-3`}></div>
                    <span className="text-sm font-medium text-gray-700">
                      {getStatusLabel(status)}
                    </span>
                  </div>
                  <span className="text-sm font-bold text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No accounts found. Upload a CSV file to get started.</p>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Quick Actions
          </h2>
          <div className="space-y-3">
            <a
              href="/upload"
              className="flex items-center p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
            >
              <TrendingUp className="h-5 w-5 text-blue-600 mr-3" />
              <div>
                <p className="font-medium text-blue-900">Upload CSV File</p>
                <p className="text-sm text-blue-600">Import accounts from password manager</p>
              </div>
            </a>
            
            <a
              href="/accounts"
              className="flex items-center p-3 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
            >
              <Users className="h-5 w-5 text-green-600 mr-3" />
              <div>
                <p className="font-medium text-green-900">Manage Accounts</p>
                <p className="text-sm text-green-600">Review and select accounts for deletion</p>
              </div>
            </a>
            
            <a
              href="/deletion"
              className="flex items-center p-3 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
            >
              <Trash2 className="h-5 w-5 text-red-600 mr-3" />
              <div>
                <p className="font-medium text-red-900">Start Deletion</p>
                <p className="text-sm text-red-600">Begin the account deletion process</p>
              </div>
            </a>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          System Status
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <DollarSign className="h-8 w-8 text-green-500 mx-auto mb-2" />
            <p className="text-sm font-medium text-gray-900">Budget Status</p>
            <p className="text-xs text-gray-500">Under daily limit</p>
          </div>
          
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <CheckCircle className="h-8 w-8 text-blue-500 mx-auto mb-2" />
            <p className="text-sm font-medium text-gray-900">API Status</p>
            <p className="text-xs text-gray-500">All services online</p>
          </div>
          
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <AlertTriangle className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
            <p className="text-sm font-medium text-gray-900">Rate Limiting</p>
            <p className="text-xs text-gray-500">Normal operation</p>
          </div>
        </div>
      </div>

      {/* Getting Started */}
      {(!summary || summary.total_accounts === 0) && (
        <div className="bg-blue-50 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-blue-900 mb-4">
            Getting Started
          </h2>
          <div className="space-y-4">
            <div className="flex items-start">
              <div className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3 mt-0.5">
                1
              </div>
              <div>
                <p className="font-medium text-blue-900">Export your password manager data</p>
                <p className="text-sm text-blue-700">Download CSV export from Bitwarden or LastPass</p>
              </div>
            </div>
            
            <div className="flex items-start">
              <div className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3 mt-0.5">
                2
              </div>
              <div>
                <p className="font-medium text-blue-900">Upload your CSV file</p>
                <p className="text-sm text-blue-700">Use the upload page to import your accounts</p>
              </div>
            </div>
            
            <div className="flex items-start">
              <div className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3 mt-0.5">
                3
              </div>
              <div>
                <p className="font-medium text-blue-900">Review and select accounts</p>
                <p className="text-sm text-blue-700">Choose which accounts you want to delete</p>
              </div>
            </div>
            
            <div className="flex items-start">
              <div className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3 mt-0.5">
                4
              </div>
              <div>
                <p className="font-medium text-blue-900">Start deletion process</p>
                <p className="text-sm text-blue-700">Begin automated deletion with AI assistance</p>
              </div>
            </div>
          </div>
          
          <div className="mt-6">
            <a
              href="/upload"
              className="btn btn-primary"
            >
              Get Started →
            </a>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;