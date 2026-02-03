import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext({});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

useEffect(() => {
  const initAuth = async () => {
    const token = localStorage.getItem('token');

    if (token) {
      try {
        // Проверяем токен и получаем пользователя
        const response = await api.get('/profile');
        setUser(response.data);
      } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
      }
    }

    setLoading(false);
  };

  initAuth();
}, []);

  const loadUser = async () => {
    try {
      const response = await api.get('/profile');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to load user:', error);
      localStorage.removeItem('token');
      delete api.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

const login = async (email, password) => {
  try {
    // 1. Логинимся и получаем токен
    const response = await api.post('/login', {
      username: email,
      password
    });

    const { access_token } = response.data;
    localStorage.setItem('token', access_token);

    // 2. Получаем данные пользователя с сервера
    const userResponse = await api.get('/profile');
    const userData = userResponse.data;

    // 3. Сохраняем пользователя в localStorage и состоянии
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);

    console.log('User logged in:', userData);

  } catch (error) {
    console.error('Login error:', error.response?.data);
    throw error;
  }
};

  const register = async (userData) => {
    await api.post('/register', userData);
    await login(userData.email, userData.password);
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
  };

  const updateUser = (updates) => {
    setUser(prev => ({ ...prev, ...updates }));
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      register,
      logout,
      updateUser
    }}>
      {children}
    </AuthContext.Provider>
  );
};