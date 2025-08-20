import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  PlusCircle, 
  Search, 
  AlertCircle, 
  CheckCircle,
  Eye,
  EyeOff,
  Info
} from 'lucide-react';
import api from '../services/api';
import { AuthContext } from '../contexts/AuthContext';

function ManualEntry() {
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);
  const [formData, setFormData] = useState({
    site_name: '',
    site_url: '',
    username: '',
    password: '',
    email: '',
    notes: ''
  });
  const [suggestions, setSuggestions] = useState([]);
  const [showPassword, setShowPassword] = useState(false);
  const [isDuplicate, setIsDuplicate] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (!user) {
      navigate('/login');
    }
  }, [user, navigate]);

  // Fetch site suggestions
  useEffect(() => {
    const fetchSuggestions = async () => {
      if (searchQuery.length > 1) {
        try {
          const response = await api.get(`/accounts/suggestions?query=${searchQuery}`);
          setSuggestions(response.data);
        } catch (err) {
          console.error('Failed to fetch suggestions:', err);
        }
      } else {
        setSuggestions([]);
      }
    };

    const debounce = setTimeout(fetchSuggestions, 300);
    return () => clearTimeout(debounce);
  }, [searchQuery]);

  // Check for duplicates
  useEffect(() => {
    const checkDuplicate = async () => {
      if (formData.site_url && formData.username) {
        try {
          const response = await api.get('/accounts/check-duplicate', {
            params: {
              site_url: formData.site_url,
              username: formData.username
            }
          });
          setIsDuplicate(response.data.is_duplicate);
        } catch (err) {
          console.error('Failed to check duplicate:', err);
        }
      }
    };

    const debounce = setTimeout(checkDuplicate, 500);
    return () => clearTimeout(debounce);
  }, [formData.site_url, formData.username]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    // Update search query for site name
    if (name === 'site_name') {
      setSearchQuery(value);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setFormData(prev => ({
      ...prev,
      site_name: suggestion.name,
      site_url: suggestion.url
    }));
    setSuggestions([]);
    setSearchQuery('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // Validation
    if (!formData.site_name || !formData.site_url || !formData.username || !formData.password) {
      setError('Please fill in all required fields');
      return;
    }

    if (isDuplicate) {
      setError('This account already exists in your list');
      return;
    }

    setLoading(true);

    try {
      const response = await api.post('/accounts/manual', formData);
      setSuccess(`Account for ${response.data.site_name} added successfully!`);
      
      // Reset form after success
      setTimeout(() => {
        setFormData({
          site_name: '',
          site_url: '',
          username: '',
          password: '',
          email: '',
          notes: ''
        });
        setSuccess('');
        // Optionally navigate to accounts page
        // navigate('/accounts');
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add account');
    } finally {
      setLoading(false);
    }
  };

  const handleAddAnother = () => {
    setFormData({
      site_name: '',
      site_url: '',
      username: '',
      password: '',
      email: '',
      notes: ''
    });
    setSuccess('');
    setError('');
    setIsDuplicate(false);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Add Account Manually</h1>
        <p className="text-gray-600">
          Add individual accounts that need to be deleted. Perfect for accounts not in your password manager.
        </p>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start">
            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 mr-3 flex-shrink-0" />
            <div className="flex-1">
              <span className="text-green-700">{success}</span>
              <button
                onClick={handleAddAnother}
                className="ml-4 text-green-600 hover:text-green-700 underline text-sm"
              >
                Add another account
              </button>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="space-y-6">
          {/* Site Name with Suggestions */}
          <div className="relative">
            <label htmlFor="site_name" className="block text-sm font-medium text-gray-700 mb-2">
              Site Name *
            </label>
            <div className="relative">
              <input
                type="text"
                id="site_name"
                name="site_name"
                value={formData.site_name}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., Facebook, Google, Netflix"
                required
              />
              <Search className="absolute right-3 top-2.5 w-5 h-5 text-gray-400" />
            </div>

            {/* Suggestions Dropdown */}
            {suggestions.length > 0 && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center justify-between border-b border-gray-100 last:border-b-0"
                  >
                    <div>
                      <div className="font-medium text-gray-900">{suggestion.name}</div>
                      <div className="text-sm text-gray-500">{suggestion.url}</div>
                    </div>
                    <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">
                      {suggestion.category}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Site URL */}
          <div>
            <label htmlFor="site_url" className="block text-sm font-medium text-gray-700 mb-2">
              Site URL *
            </label>
            <input
              type="text"
              id="site_url"
              name="site_url"
              value={formData.site_url}
              onChange={handleInputChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="https://www.example.com"
              required
            />
            <p className="mt-1 text-sm text-gray-500">
              The website URL where you log in to this account
            </p>
          </div>

          {/* Username */}
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
              Username *
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                isDuplicate ? 'border-yellow-400' : 'border-gray-300'
              }`}
              placeholder="Your username or login ID"
              required
            />
            {isDuplicate && (
              <p className="mt-1 text-sm text-yellow-600 flex items-center">
                <AlertCircle className="w-4 h-4 mr-1" />
                This account already exists in your list
              </p>
            )}
          </div>

          {/* Password */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              Password *
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-10"
                placeholder="Your account password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? (
                  <EyeOff className="w-5 h-5" />
                ) : (
                  <Eye className="w-5 h-5" />
                )}
              </button>
            </div>
            <div className="mt-1 flex items-start text-sm text-gray-500">
              <Info className="w-4 h-4 mr-1 mt-0.5 flex-shrink-0" />
              <span>Password is encrypted and stored securely</span>
            </div>
          </div>

          {/* Email (Optional) */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email (Optional)
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Email associated with this account"
            />
          </div>

          {/* Notes (Optional) */}
          <div>
            <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-2">
              Notes (Optional)
            </label>
            <textarea
              id="notes"
              name="notes"
              value={formData.notes}
              onChange={handleInputChange}
              rows="3"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Any additional information about this account"
            />
          </div>
        </div>

        {/* Form Actions */}
        <div className="mt-8 flex gap-4">
          <button
            type="submit"
            disabled={loading || isDuplicate}
            className={`flex-1 flex items-center justify-center px-6 py-3 rounded-lg font-medium transition-colors ${
              loading || isDuplicate
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Adding Account...
              </>
            ) : (
              <>
                <PlusCircle className="w-5 h-5 mr-2" />
                Add Account
              </>
            )}
          </button>

          <button
            type="button"
            onClick={() => navigate('/accounts')}
            className="px-6 py-3 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>

      {/* Tips Section */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-3">Tips for Adding Accounts</h3>
        <ul className="space-y-2 text-sm text-blue-800">
          <li className="flex items-start">
            <span className="mr-2">•</span>
            <span>Start typing the site name to see suggestions from our database of popular services</span>
          </li>
          <li className="flex items-start">
            <span className="mr-2">•</span>
            <span>Make sure to use the exact username/email you use to log in</span>
          </li>
          <li className="flex items-start">
            <span className="mr-2">•</span>
            <span>The password is needed for automated deletion - it's encrypted and never shown</span>
          </li>
          <li className="flex items-start">
            <span className="mr-2">•</span>
            <span>Add notes if there's anything special about deleting this account</span>
          </li>
        </ul>
      </div>
    </div>
  );
}

export default ManualEntry;