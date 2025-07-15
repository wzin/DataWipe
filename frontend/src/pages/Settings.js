import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  Mail, 
  Settings as SettingsIcon, 
  Save, 
  TestTube,
  CheckCircle,
  AlertCircle,
  Info,
  ExternalLink
} from 'lucide-react';
import { toast } from 'react-toastify';
import { 
  getEmailSettings, 
  configureEmail, 
  testEmailSettings,
  getSupportedEmailProviders
} from '../services/api';

const Settings = () => {
  const [emailConfig, setEmailConfig] = useState({
    email: '',
    password: '',
    name: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const queryClient = useQueryClient();

  const { data: currentSettings, isLoading } = useQuery('emailSettings', getEmailSettings, {
    onSuccess: (data) => {
      setEmailConfig({
        email: data.email || '',
        password: '', // Don't show stored password
        name: data.name || ''
      });
    },
    onError: () => {
      // Settings not configured yet
    }
  });

  const { data: providers } = useQuery('emailProviders', getSupportedEmailProviders);

  const saveSettingsMutation = useMutation(configureEmail, {
    onSuccess: (data) => {
      toast.success('Email settings saved successfully');
      queryClient.invalidateQueries('emailSettings');
      setTestResult({ success: true, ...data });
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to save settings');
    }
  });

  const testSettingsMutation = useMutation(testEmailSettings, {
    onSuccess: (data) => {
      toast.success('Email configuration is working');
      setTestResult({ success: true, ...data });
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Email test failed');
      setTestResult({ success: false, error: error.response?.data?.detail });
    }
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setEmailConfig(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSave = (e) => {
    e.preventDefault();
    if (!emailConfig.email || !emailConfig.password) {
      toast.error('Email and password are required');
      return;
    }
    saveSettingsMutation.mutate(emailConfig);
  };

  const handleTest = () => {
    if (!emailConfig.email || !emailConfig.password) {
      toast.error('Email and password are required');
      return;
    }
    testSettingsMutation.mutate(emailConfig);
  };

  const getProviderInfo = (email) => {
    if (!providers || !email) return null;
    const domain = email.split('@')[1];
    return providers.providers.find(p => p.domain === domain);
  };

  const providerInfo = getProviderInfo(emailConfig.email);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-2">
          Configure your email settings to send GDPR deletion requests
        </p>
      </div>

      {/* Email Configuration */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center">
            <Mail className="h-5 w-5 mr-2" />
            Email Configuration
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Configure your email account to send deletion requests from your own email
          </p>
        </div>

        <div className="p-6">
          <form onSubmit={handleSave} className="space-y-6">
            {/* Current Status */}
            {currentSettings && (
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full mr-3 ${
                      currentSettings.configured ? 'bg-green-500' : 'bg-red-500'
                    }`}></div>
                    <div>
                      <p className="font-medium text-gray-900">Current Configuration</p>
                      <p className="text-sm text-gray-600">
                        {currentSettings.email} ({currentSettings.provider})
                      </p>
                    </div>
                  </div>
                  <span className={`status-badge ${
                    currentSettings.configured ? 'status-completed' : 'status-failed'
                  }`}>
                    {currentSettings.configured ? 'Working' : 'Failed'}
                  </span>
                </div>
              </div>
            )}

            {/* Email Input */}
            <div className="form-group">
              <label htmlFor="email" className="form-label">
                Email Address
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={emailConfig.email}
                onChange={handleInputChange}
                className="form-input"
                placeholder="your-email@gmail.com"
                required
              />
            </div>

            {/* Password Input */}
            <div className="form-group">
              <label htmlFor="password" className="form-label">
                Password / App Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  name="password"
                  value={emailConfig.password}
                  onChange={handleInputChange}
                  className="form-input pr-10"
                  placeholder="Enter your password or app password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>
            </div>

            {/* Name Input */}
            <div className="form-group">
              <label htmlFor="name" className="form-label">
                Your Name (optional)
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={emailConfig.name}
                onChange={handleInputChange}
                className="form-input"
                placeholder="Your full name"
              />
              <p className="text-sm text-gray-500 mt-1">
                This will be used in email signatures
              </p>
            </div>

            {/* Provider-specific Info */}
            {providerInfo && (
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-start">
                  <Info className="h-5 w-5 text-blue-600 mt-0.5 mr-3" />
                  <div>
                    <h4 className="font-medium text-blue-900">
                      {providerInfo.name} Setup Instructions
                    </h4>
                    {providerInfo.app_password_required && (
                      <div className="mt-2 p-2 bg-yellow-100 rounded border border-yellow-200">
                        <p className="text-sm text-yellow-800 font-medium">
                          ⚠️ App Password Required
                        </p>
                        <p className="text-sm text-yellow-700 mt-1">
                          You need to generate an app password, not your regular password
                        </p>
                      </div>
                    )}
                    <ul className="mt-2 space-y-1 text-sm text-blue-700">
                      {providerInfo.setup_instructions.map((instruction, index) => (
                        <li key={index} className="flex items-start">
                          <span className="mr-2">{index + 1}.</span>
                          {instruction}
                        </li>
                      ))}
                    </ul>
                    <a
                      href={providerInfo.help_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center mt-2 text-sm text-blue-600 hover:text-blue-800"
                    >
                      Help & Documentation
                      <ExternalLink className="h-4 w-4 ml-1" />
                    </a>
                  </div>
                </div>
              </div>
            )}

            {/* Test Result */}
            {testResult && (
              <div className={`rounded-lg p-4 ${
                testResult.success ? 'bg-green-50' : 'bg-red-50'
              }`}>
                <div className="flex items-center">
                  {testResult.success ? (
                    <CheckCircle className="h-5 w-5 text-green-600 mr-3" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-600 mr-3" />
                  )}
                  <div>
                    <p className={`font-medium ${
                      testResult.success ? 'text-green-900' : 'text-red-900'
                    }`}>
                      {testResult.success ? 'Configuration Test Passed' : 'Configuration Test Failed'}
                    </p>
                    {testResult.success && (
                      <p className="text-sm text-green-700 mt-1">
                        Connected to {testResult.provider} via {testResult.smtp_server}
                      </p>
                    )}
                    {testResult.error && (
                      <p className="text-sm text-red-700 mt-1">
                        {testResult.error}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex space-x-4">
              <button
                type="button"
                onClick={handleTest}
                disabled={testSettingsMutation.isLoading}
                className="btn btn-secondary"
              >
                <TestTube className="h-4 w-4 mr-2" />
                {testSettingsMutation.isLoading ? 'Testing...' : 'Test Configuration'}
              </button>
              
              <button
                type="submit"
                disabled={saveSettingsMutation.isLoading}
                className="btn btn-primary"
              >
                <Save className="h-4 w-4 mr-2" />
                {saveSettingsMutation.isLoading ? 'Saving...' : 'Save Configuration'}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Security Notice */}
      <div className="bg-yellow-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-yellow-900 mb-4">
          <AlertCircle className="h-5 w-5 inline mr-2" />
          Security & Privacy Notice
        </h3>
        <div className="space-y-3 text-sm text-yellow-800">
          <p>
            <strong>Your email credentials are:</strong>
          </p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>Encrypted and stored locally in your browser/system</li>
            <li>Never sent to external servers except for email sending</li>
            <li>Used only to send deletion requests from your own email account</li>
            <li>Can be deleted at any time from settings</li>
          </ul>
          <p>
            <strong>Why use your own email?</strong> Deletion requests are more effective when sent from your personal email address rather than a generic service email.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Settings;