import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';

const AuthContext = createContext(null);

// Configure axios defaults
axios.defaults.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Add request interceptor to include auth token
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle auth errors
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sessionDuration, setSessionDuration] = useState(24);

  useEffect(() => {
    // Check for existing session
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        setSessionDuration(parsedUser.session_duration_hours || 24);
        
        // Verify token is still valid
        axios.get('/api/auth/me')
          .then(response => {
            setUser(response.data);
            localStorage.setItem('user', JSON.stringify(response.data));
          })
          .catch(() => {
            // Token invalid, clear storage
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            setUser(null);
          });
      } catch (error) {
        console.error('Error parsing user data:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
      }
    }
    
    setLoading(false);
  }, []);

  const register = async (username, email, password, sessionHours = 24) => {
    try {
      const response = await axios.post('/api/auth/register', {
        username,
        email,
        password,
        session_duration_hours: sessionHours
      });
      
      const { access_token, user: userData, expires_in } = response.data;
      
      // Store token and user data
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      
      // Set expiration time
      const expirationTime = new Date().getTime() + (expires_in * 1000);
      localStorage.setItem('token_expiration', expirationTime.toString());
      
      setUser(userData);
      setSessionDuration(userData.session_duration_hours);
      
      toast.success('Registration successful!');
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || 'Registration failed';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  const login = async (username, password) => {
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await axios.post('/api/auth/login', formData);
      
      const { access_token, user: userData, expires_in } = response.data;
      
      // Store token and user data
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      
      // Set expiration time
      const expirationTime = new Date().getTime() + (expires_in * 1000);
      localStorage.setItem('token_expiration', expirationTime.toString());
      
      setUser(userData);
      setSessionDuration(userData.session_duration_hours);
      
      toast.success('Login successful!');
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || 'Login failed';
      
      // Handle account lockout
      if (error.response?.status === 423) {
        toast.error(message);
      } else {
        toast.error('Invalid username or password');
      }
      
      return { success: false, error: message };
    }
  };

  const logout = async () => {
    try {
      await axios.post('/api/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      localStorage.removeItem('token_expiration');
      
      setUser(null);
      toast.info('Logged out successfully');
      
      // Redirect to login
      window.location.href = '/login';
    }
  };

  const changePassword = async (currentPassword, newPassword) => {
    try {
      await axios.post('/api/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword
      });
      
      toast.success('Password changed successfully');
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to change password';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  const requestPasswordReset = async (email) => {
    try {
      await axios.post('/api/auth/password-reset-request', { email });
      toast.success('If the email exists, a password reset link has been sent');
      return { success: true };
    } catch (error) {
      toast.error('Failed to send password reset email');
      return { success: false };
    }
  };

  const resetPassword = async (token, newPassword) => {
    try {
      await axios.post('/api/auth/password-reset-confirm', {
        token,
        new_password: newPassword
      });
      
      toast.success('Password reset successfully');
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to reset password';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  const updateSessionDuration = async (hours) => {
    try {
      await axios.put('/api/auth/session-duration', {
        session_duration_hours: hours
      });
      
      setSessionDuration(hours);
      
      // Update user data in storage
      const userData = JSON.parse(localStorage.getItem('user') || '{}');
      userData.session_duration_hours = hours;
      localStorage.setItem('user', JSON.stringify(userData));
      
      toast.success('Session duration updated');
      return { success: true };
    } catch (error) {
      toast.error('Failed to update session duration');
      return { success: false };
    }
  };

  const refreshToken = async () => {
    try {
      const response = await axios.post('/api/auth/refresh');
      const { access_token, expires_in } = response.data;
      
      localStorage.setItem('access_token', access_token);
      
      const expirationTime = new Date().getTime() + (expires_in * 1000);
      localStorage.setItem('token_expiration', expirationTime.toString());
      
      return { success: true };
    } catch (error) {
      console.error('Token refresh failed:', error);
      return { success: false };
    }
  };

  // Auto-refresh token before expiration
  useEffect(() => {
    if (!user) return;
    
    const checkTokenExpiration = () => {
      const expiration = localStorage.getItem('token_expiration');
      if (!expiration) return;
      
      const expirationTime = parseInt(expiration);
      const currentTime = new Date().getTime();
      const timeUntilExpiration = expirationTime - currentTime;
      
      // Refresh token 5 minutes before expiration
      if (timeUntilExpiration < 5 * 60 * 1000 && timeUntilExpiration > 0) {
        refreshToken();
      }
    };
    
    // Check every minute
    const interval = setInterval(checkTokenExpiration, 60 * 1000);
    
    return () => clearInterval(interval);
  }, [user]);

  const value = {
    user,
    loading,
    sessionDuration,
    register,
    login,
    logout,
    changePassword,
    requestPasswordReset,
    resetPassword,
    updateSessionDuration,
    refreshToken,
    isAuthenticated: !!user
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};